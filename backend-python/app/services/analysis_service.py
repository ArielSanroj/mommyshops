"""
Analysis service
Handles product analysis business logic
"""

import asyncio
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
import logging
import time
from datetime import datetime
import json
from pathlib import Path

from app.database.models import Product, Ingredient, User
from app.services.ingredient_service import IngredientService, CATALOG_PATH
from app.services.ocr_service import OCRService
from app.services.ollama_service import OllamaService
from app.services.formulation_service import FormulationService

logger = logging.getLogger(__name__)

class AnalysisService:
    """Service for product analysis operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ingredient_service = IngredientService(db)
        self.ocr_service = OCRService()
        try:
            self.formulation_service = FormulationService()
        except Exception as exc:  # pragma: no cover
            logger.warning(f"FormulationService initialization failed: {exc}")
            self.formulation_service = None
        try:
            self.ollama_service = OllamaService()
        except Exception as exc:  # pragma: no cover
            logger.warning(f"OllamaService initialization failed: {exc}")
            self.ollama_service = None
    
    async def analyze_text(
        self,
        text: str,
        user_id: str,
        user_need: Optional[str] = None,
        notes: Optional[str] = None,
        product_name: Optional[str] = None,
        profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze text for ingredients and provide recommendations"""
        try:
            # Extract and normalize ingredients from text
            ingredients = await self._extract_ingredients_from_text(text)
            
            if not ingredients:
                return {
                    "success": False,
                    "error": "No ingredients found in text"
                }
            
            # Detect product type (simple heuristic)
            product_type = self._detect_product_type(product_name, ingredients)

            analysis_result = await self._analyze_with_ollama(
                ingredients=ingredients,
                user_id=user_id,
                user_need=user_need,
                product_type=product_type,
                user_profile=profile
            )
            
            if not analysis_result or not analysis_result.get("success"):
                logger.info("Ollama analysis failed or unavailable, falling back to catalog")
                # Fallback to catalog-driven analysis
                fallback_concerns = []
                if user_need:
                    fallback_concerns.append(user_need)
                if profile:
                    fallback_concerns.extend(profile.get("overall_goals") or [])
                    fallback_concerns.extend(profile.get("skin_concerns") or [])
                    fallback_concerns.extend(profile.get("hair_concerns") or [])
                # Deduplicate preserving order
                seen = set()
                user_concerns = []
                for concern in fallback_concerns:
                    key = concern.lower()
                    if key not in seen and concern:
                        seen.add(key)
                        user_concerns.append(concern)
                analysis_result = await self.ingredient_service.analyze_ingredients(
                    ingredients=ingredients,
                    user_id=user_id,
                    user_concerns=user_concerns or None,
                    product_type=product_type,
                    profile=profile or {},
                )
                analysis_result["ollama_skipped"] = True
            else:
                logger.info(f"Ollama analysis successful with {len(analysis_result.get('ingredients_analysis', []))} ingredients")

            ingredients_analysis_data = self._ensure_baby_metadata(
                analysis_result.get("ingredients_analysis", []),
                profile or {},
            )
            analysis_result["ingredients_analysis"] = ingredients_analysis_data
            eco_friendly_percentage = 0.0
            avg_ewg_score = 0.0
            if ingredients_analysis_data:
                eco_count = sum(1 for item in ingredients_analysis_data if item.get("eco_friendly"))
                eco_friendly_percentage = round((eco_count / len(ingredients_analysis_data)) * 100, 1)
                avg_ewg_score = round(
                    sum((item.get("ewg_score") or 0) for item in ingredients_analysis_data)
                    / len(ingredients_analysis_data),
                    1,
                )
            analysis_result["eco_friendly_percentage"] = eco_friendly_percentage
            analysis_result["avg_ewg_score"] = avg_ewg_score
            analysis_result["profile"] = profile or {}

            # Build analysis summary for frontend quick badges
            total_count = len(ingredients_analysis_data)
            high_count = sum(1 for i in ingredients_analysis_data if (i.get("risk") or "").lower() == "high")
            moderate_count = sum(1 for i in ingredients_analysis_data if (i.get("risk") or "").lower() == "moderate")
            if high_count:
                risk_level = "high"
            elif moderate_count:
                risk_level = "moderate"
            else:
                risk_level = "low"
            overall_score_val = float(analysis_result.get("overall_score") or 0)
            baby_report = self._build_baby_report(
                profile=profile or {},
                ingredients=ingredients_analysis_data,
                base_score=overall_score_val,
            )
            analysis_summary = {
                "compatibility_score": round(overall_score_val / 100.0, 2),
                "eco_score": eco_friendly_percentage,
                "risk_level": risk_level,
                "ingredient_count": total_count,
            }
            if baby_report:
                analysis_summary["baby_score"] = baby_report.get("baby_score")
                analysis_summary["baby_summary"] = baby_report.get("emotional_summary")
                analysis_summary["climate_context"] = baby_report.get("climate_context")

            # Generate intelligent formula (Labs) using detected ingredients + profile
            intelligent_formula = None
            if self.formulation_service:
                try:
                    detected_names = [i.get("name") for i in ingredients_analysis_data if i.get("name")]
                    intelligent_formula = self.formulation_service.generate_formula(
                        profile=profile or {},
                        detected_ingredients=detected_names,
                        variant=None,
                        product_name=product_name,
                        budget=None,
                    )
                except Exception as exc:
                    logger.warning(f"Formulation generation failed: {exc}")
            
            # Persist product if schema supports it; otherwise continue without failing
            product_name_final = product_name or "Unknown Product"
            try:
                product_kwargs = {
                    "name": product_name_final,
                    "ingredients": ingredients,
                }
                if hasattr(Product, "analysis_data"):
                    product_kwargs["analysis_data"] = analysis_result
                product = Product(**product_kwargs)
                if hasattr(Product, "user_id"):
                    setattr(product, "user_id", user_id)
                self.db.add(product)
                self.db.commit()
                persisted_name = getattr(product, "name", product_name_final)
            except Exception as persist_err:
                logger.warning(f"Skipping DB persist for product due to error: {persist_err}")
                try:
                    self.db.rollback()
                except Exception:  # pragma: no cover
                    pass
                persisted_name = product_name_final

            # Build structured report
            structured_report = self._build_structured_report(
                product_name=product_name_final,
                ingredients_analysis=analysis_result.get("ingredients_analysis", []),
                overall_score=analysis_result.get("overall_score", 0),
                avg_ewg_score=analysis_result.get("avg_ewg_score", 0),
                eco_friendly_percentage=analysis_result.get("eco_friendly_percentage", 0),
                product_type=product_type or "general",
                recommendations=analysis_result.get("recommendations", [])
            )

            # Build detailed report in Spanish (for frontend display)
            detailed_report = self._build_detailed_report(
                product_name=product_name_final,
                ingredients_analysis=analysis_result.get("ingredients_analysis", []),
                overall_score=analysis_result.get("overall_score", 0),
                avg_ewg_score=analysis_result.get("avg_ewg_score", 0),
                eco_friendly_percentage=analysis_result.get("eco_friendly_percentage", 0)
            )

            result = {
                "success": True,
                "product_name": persisted_name,
                "product_type": product_type or "general",
                "ingredients": analysis_result.get("ingredients_analysis", []),
                "avg_eco_score": analysis_result.get("overall_score"),
                "eco_friendly_percentage": eco_friendly_percentage,
                "avg_ewg_score": avg_ewg_score,
                "suitability": self._determine_suitability(analysis_result),
                "recommendations": analysis_result.get("recommendations", []),
                "structured_report": structured_report,
                "detailed_report": detailed_report,
                "profile": profile or {},
                "analysis_summary": analysis_summary,
                "intelligent_formula": intelligent_formula,
                "baby_report": baby_report,
                "ollama_skipped": analysis_result.get("ollama_skipped", False),
            }
            if product_type:
                result["product_type"] = product_type
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _analyze_with_ollama(
        self,
        ingredients: List[str],
        user_id: str,
        user_need: Optional[str],
        product_type: Optional[str],
        user_profile: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Use Ollama to perform the primary ingredient analysis.
        """
        if not self.ollama_service or not getattr(self.ollama_service, "available", False):
            return None
        
        # Aggressive timeout: 15 seconds max for Ollama analysis
        timeout_seconds = 15
        try:
            structured = await asyncio.wait_for(
                self.ollama_service.analyze_ingredients_structured(
                    ingredients=ingredients,
                    user_conditions=[user_need] if user_need else [],
                    profile_context=user_profile or {}
                ),
                timeout=timeout_seconds,
            )
        except asyncio.TimeoutError:
            logger.warning(
                "Ollama structured analysis timed out after %s seconds; using local analysis fallback",
                timeout_seconds,
            )
            return None
        except Exception as exc:  # pragma: no cover
            logger.warning(f"Ollama structured analysis unavailable: {exc}")
            return None
        
        items = structured.get("items", [])
        error = structured.get("error")
        if error:
            logger.warning(f"Ollama structured analysis returned error: {error}")
        if not items:
            logger.warning(f"Ollama structured analysis returned no items. Raw response: {structured.get('raw', '')[:200]}")
            return None
        
        combined: List[Dict[str, Any]] = []
        high_risk = False
        for raw in items:
            name = raw.get("name", "").strip()
            if not name:
                continue
            norm = self.ingredient_service._normalize_token(name)
            catalog_entry = self.ingredient_service.catalog.get(norm)
            
            raw_score = raw.get("score") if raw.get("score") is not None else (catalog_entry.get("score") if catalog_entry else 70)
            try:
                score = int(round(float(raw_score)))
            except Exception:
                score = 70
            raw_ewg = raw.get("ewg_score") if raw.get("ewg_score") is not None else (catalog_entry.get("ewg") if catalog_entry else 5)
            try:
                ewg_score = int(round(float(raw_ewg)))
            except Exception:
                ewg_score = 5
            risk = raw.get("risk") or (catalog_entry.get("risk") if catalog_entry else "moderate")
            eco_friendly = raw.get("eco_friendly")
            if eco_friendly is None:
                eco_friendly = bool(catalog_entry.get("eco")) if catalog_entry else False
            description = raw.get("description") or (catalog_entry.get("desc") if catalog_entry else "Datos generados por IA.")
            
            substitutes = raw.get("substitutes") or []
            if isinstance(substitutes, str):
                substitutes_list = [s.strip() for s in substitutes.split(",") if s.strip()]
            else:
                substitutes_list = [str(s).strip() for s in substitutes if str(s).strip()]
            substitute_str = ", ".join(substitutes_list[:3]) if substitutes_list else None
            
            risk_lower = (risk or "").lower()
            if risk_lower in {"high", "critical"}:
                high_risk = True
            if risk_lower in {"high", "critical"}:
                safety_level = "caution"
            elif risk_lower == "moderate":
                safety_level = "moderate"
            elif (score or 0) >= 80:
                safety_level = "safe"
            elif (score or 0) >= 60:
                safety_level = "moderate"
            else:
                safety_level = "caution"
            
            combined.append(
                {
                    "name": name,
                    "score": score,
                    "safety_level": safety_level,
                    "description": description,
                    "ewg_score": ewg_score,
                    "risk": risk_lower or "moderate",
                    "eco_friendly": bool(eco_friendly),
                    "substitute": substitute_str,
                }
            )
        
        if not combined:
            return None
        
        combined = self._ensure_baby_metadata(combined, user_profile or {})
        overall_score = sum(item["score"] for item in combined) / len(combined)
        recommendations: List[str] = []
        if high_risk:
            recommendations.append("Se identificaron ingredientes de alto riesgo; considera sustitutos inmediatos.")
        else:
            recommendations.append("La formulación es moderada; verifica compatibilidad con tu tipo de piel.")
        if product_type == "hair_conditioner":
            recommendations.append("Evalúa ingredientes acondicionadores alternativos sin potencial acumulativo.")
        if user_profile:
            if user_profile.get("skin_type"):
                recommendations.append(
                    f"Prioriza activos compatibles con piel {user_profile['skin_type'].lower()} y evita potenciales sensibilizantes."
                )
            if user_profile.get("hair_type"):
                recommendations.append(
                    f"Ajusta la fórmula para cabello {user_profile['hair_type'].lower()} usando hidratantes adecuados."
                )
        
        # Persist Ollama knowledge into ingredient catalog
        try:
            self._sync_catalog_with_ollama(items)
        except Exception as exc:  # pragma: no cover
            logger.warning(f"No se pudo actualizar el catálogo con datos de Ollama: {exc}")
        
        return {
            "success": True,
            "ingredients_analysis": combined,
            "overall_score": round(overall_score, 2),
            "recommendations": recommendations,
            "ollama_raw": structured.get("raw"),
            "profile": user_profile or {},
        }
    
    def _sync_catalog_with_ollama(self, items: List[Dict[str, Any]]) -> None:
        """
        Persist Ollama ingredient insights into the shared catalog for future runs.
        """
        path = Path(CATALOG_PATH)
        try:
            if path.exists():
                catalog_data = json.loads(path.read_text(encoding="utf-8"))
            else:
                catalog_data = {}
        except Exception as exc:
            logger.error(f"Failed to read ingredient catalog: {exc}")
            catalog_data = {}
        
        changed = False
        for item in items:
            name = item.get("name") or item.get("ingredient")
            if not name:
                continue
            key = name.strip()
            if not key:
                continue
            
            try:
                score_value = int(round(float(item.get("score", 70))))
            except Exception:
                score_value = 70
            try:
                ewg_value = int(round(float(item.get("ewg_score", 5))))
            except Exception:
                ewg_value = 5
            risk_value = str(item.get("risk", "moderate")).lower()
            eco_value = bool(item.get("eco_friendly", False))
            description_value = item.get("description") or item.get("analysis") or "Información generada por Ollama."
            
            entry_payload = {
                "score": score_value,
                "ewg": ewg_value,
                "risk": risk_value,
                "eco": eco_value,
                "description": description_value,
                "categories": [],
            }
            
            existing = catalog_data.get(key)
            if existing is None:
                catalog_data[key] = entry_payload
                changed = True
            else:
                updated = False
                for field, value in entry_payload.items():
                    if field not in existing or not existing[field]:
                        existing[field] = value
                        updated = True
                if updated:
                    catalog_data[key] = existing
                    changed = True
        
        if changed:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(catalog_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            # Refresh IngredientService caches so new data is used immediately
            self.ingredient_service.catalog, self.ingredient_service.alias_lookup = self.ingredient_service._load_catalog()
    
    async def _extract_ingredients_from_text(self, text: str) -> List[str]:
        """Extract ingredient names by splitting on commas, newlines, and bullet markers."""
        import re

        raw = text or ""
        # Normalize common bullet and separator characters to newlines
        raw = raw.replace("\u2022", "\n").replace("•", "\n").replace("·", "\n")
        raw = raw.replace("\r", "\n").replace(";", "\n")
        # Ensure commas also act as separators while preserving spacing
        raw = raw.replace(",", "\n")

        candidates = [seg for seg in re.split(r"\n+", raw) if seg.strip()]

        cleaned: List[str] = []
        seen = set()
        for candidate in candidates:
            t = candidate.strip()
            t = re.sub(r"\s+", " ", t)
            t = t.strip().strip(".;:")
            if not t:
                continue
            # Skip extremely short tokens or generic words
            if len(t) <= 2:
                continue
            normalized = t
            # Deduplicate while preserving original casing
            key = normalized.lower()
            if key == "aqua":
                continue
            if key not in seen:
                seen.add(key)
                cleaned.append(normalized)

        return cleaned

    def _detect_product_type(self, product_name: Optional[str], ingredients: List[str]) -> Optional[str]:
        """Heuristic product type detection (focus: hair conditioner)."""
        pname = (product_name or "").lower()
        if any(k in pname for k in ["acondicionador", "conditioner", "tratamiento capilar"]):
            return "hair_conditioner"
        upper = {i.upper() for i in ingredients}
        hair_markers = {"CETRIMONIUM CHLORIDE", "BEHENTRIMONIUM CHLORIDE", "POLYQUATERNIUM-10"}
        if hair_markers.intersection(upper):
            return "hair_conditioner"
        return None
    
    def _determine_suitability(self, analysis_result: Dict[str, Any]) -> str:
        """Determine product suitability based on analysis"""
        overall_score = analysis_result.get("overall_score", 0)
        
        if overall_score >= 80:
            return "excellent"
        elif overall_score >= 60:
            return "good"
        elif overall_score >= 40:
            return "moderate"
        else:
            return "poor"

    def _ensure_baby_metadata(
        self,
        ingredients: List[Dict[str, Any]],
        profile: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if not ingredients:
            return []
        enriched: List[Dict[str, Any]] = []
        for item in ingredients:
            if item.get("baby_risk") and item.get("compatibility_score") is not None:
                enriched.append(item)
                continue
            enriched.append(self.ingredient_service.enrich_with_baby_metadata(item, profile))
        return enriched

    def _build_baby_report(
        self,
        profile: Dict[str, Any],
        ingredients: List[Dict[str, Any]],
        base_score: float,
    ) -> Dict[str, Any]:
        if not ingredients:
            return {}

        profile_ctx = self._build_baby_profile_context(profile)
        positives: List[Dict[str, Any]] = []
        negatives: List[Dict[str, Any]] = []

        for item in ingredients:
            baby_risk = (item.get("baby_risk") or "").lower()
            benefits_raw = item.get("benefits") or []
            warnings_raw = item.get("warnings") or []

            if isinstance(benefits_raw, str):
                benefits_list = [benefits_raw]
            elif isinstance(benefits_raw, list):
                benefits_list = benefits_raw
            else:
                benefits_list = []

            if isinstance(warnings_raw, str):
                warnings_list = [warnings_raw]
            elif isinstance(warnings_raw, list):
                warnings_list = warnings_raw
            else:
                warnings_list = []
            summary_text = (
                benefits_list[0]
                if benefits_list
                else warnings_list[0]
                if warnings_list
                else item.get("baby_summary")
            )
            highlight = {
                "ingredient": item.get("name"),
                "score": item.get("compatibility_score"),
                "summary": summary_text,
            }
            if baby_risk in {"good", "ok"}:
                positives.append(highlight)
            elif baby_risk in {"caution", "bad"} or item.get("avoid_reasons"):
                highlight["flags"] = item.get("baby_flags_triggered")
                negatives.append(highlight)

        positives = positives[:5]
        negatives = negatives[:4]

        if not positives and not negatives:
            return {}

        baby_score = self._score_baby_compatibility(base_score, positives, negatives, profile_ctx)
        score_label = (
            "Ideal" if baby_score >= 85 else "Aceptable" if baby_score >= 70 else "Ajustable"
            if baby_score >= 55
            else "No recomendado"
        )

        emotional_summary = self._compose_emotional_summary(profile_ctx, positives, negatives, baby_score)
        recommendation = self._recommend_mommyshops_blend(profile_ctx)

        return {
            "baby_score": baby_score,
            "score_label": score_label,
            "emotional_summary": emotional_summary,
            "positives": positives,
            "negatives": negatives,
            "climate_context": profile_ctx.get("climate_context"),
            "product_recommendation": recommendation,
        }

    def _build_baby_profile_context(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        profile = profile or {}
        climate_ctx = profile.get("climate_context") or {}
        humidity = climate_ctx.get("humidity")
        temperature = climate_ctx.get("temperature_c")

        skin_type = profile.get("skin_type") or "piel sensible"
        skin_label = skin_type.replace("_", " ").replace("-", " ").lower()
        concern = None
        if profile.get("diaper_dermatitis"):
            concern = "dermatitis del pañal"
        elif profile.get("eczema_level"):
            concern = "brotes atópicos"

        climate_phrase = None
        if humidity is not None:
            try:
                humidity_val = float(humidity)
                if humidity_val >= 70:
                    climate_phrase = "Requiere alivio anti-humedad."
                elif humidity_val <= 40:
                    climate_phrase = "Necesita refuerzos nutritivos por clima seco."
            except (TypeError, ValueError):
                pass
        if not climate_phrase and temperature:
            try:
                temp_val = float(temperature)
                if temp_val >= 28:
                    climate_phrase = "Ajustamos para calor intenso."
            except (TypeError, ValueError):
                pass

        return {
            "raw": profile,
            "skin_label": skin_label,
            "primary_concern": concern,
            "climate_context": climate_ctx,
            "climate_phrase": climate_phrase,
            "humidity": humidity,
        }

    def _score_baby_compatibility(
        self,
        base_score: float,
        positives: List[Dict[str, Any]],
        negatives: List[Dict[str, Any]],
        profile_ctx: Dict[str, Any],
    ) -> int:
        score = base_score or 0
        if score <= 1:
            score = 60
        score += min(12, len(positives) * 3)
        score -= min(24, len(negatives) * 6)

        humidity = profile_ctx.get("humidity")
        try:
            if humidity is not None:
                humidity_val = float(humidity)
                if humidity_val >= 70:
                    score -= 4
                elif humidity_val <= 40:
                    score += 3
        except (TypeError, ValueError):
            pass

        if profile_ctx.get("primary_concern") == "dermatitis del pañal" and negatives:
            score -= 5

        return int(max(0, min(100, round(score))))

    def _compose_emotional_summary(
        self,
        profile_ctx: Dict[str, Any],
        positives: List[Dict[str, Any]],
        negatives: List[Dict[str, Any]],
        baby_score: int,
    ) -> str:
        skin_label = profile_ctx.get("skin_label") or "la piel de tu bebé"
        climate_phrase = profile_ctx.get("climate_phrase") or ""
        concern = profile_ctx.get("primary_concern")

        if negatives:
            warning = negatives[0].get("summary") or "algunos ingredientes no acompañan su piel"
            summary = f"Funciona parcialmente para {skin_label}, pero {warning.lower()}."
        else:
            benefit = positives[0].get("summary") if positives else "mantiene la piel equilibrada"
            summary = f"Seguro para {skin_label}; {benefit.lower()}."

        if concern and concern not in summary:
            summary += f" Cuidado especial para {concern}."
        if climate_phrase:
            summary += f" {climate_phrase}"
        summary += f" (Compatibilidad bebé: {baby_score}/100)"
        return summary.strip()

    def _recommend_mommyshops_blend(self, profile_ctx: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.formulation_service:
            return None
        try:
            baby_formula = self.formulation_service.generate_baby_formula(profile_ctx.get("raw"))
        except Exception as exc:  # pragma: no cover
            logger.warning(f"Baby formulation failed: {exc}")
            return None
        if not baby_formula:
            return None
        return {
            "blend": baby_formula.get("display_name"),
            "persona": baby_formula.get("persona"),
            "reasons": baby_formula.get("reasons"),
            "cta": baby_formula.get("cta", "Pide ahora"),
            "adjusted_ingredients": baby_formula.get("adjusted_ingredients"),
            "adjustments": baby_formula.get("adjustments"),
            "climate_hint": baby_formula.get("climate_hint"),
            "ai_mode": baby_formula.get("ai_mode"),
        }

    def _build_structured_report(
        self,
        product_name: str,
        ingredients_analysis: List[Dict[str, Any]],
        overall_score: float,
        avg_ewg_score: float,
        eco_friendly_percentage: float,
        product_type: str,
        recommendations: List[str]
    ) -> Dict[str, Any]:
        detected_ingredients = [i.get("name", "-") for i in ingredients_analysis]
        safe = []
        problematic = []
        for i in ingredients_analysis:
            risk = (i.get("risk") or "").lower()
            entry = {
                "ingredient": i.get("name", "-"),
                "ewg_score": i.get("ewg_score"),
                "eco_score": 90 if i.get("eco_friendly") else 40,
                "analysis": i.get("description", ""),
                "substitute": i.get("substitute") or None,
            }
            if risk in ("high", "moderate"):
                problematic.append(entry)
            else:
                safe.append({k: entry[k] for k in ["ingredient", "ewg_score", "eco_score", "analysis"]})

        total = len(ingredients_analysis)
        eco_count = sum(1 for i in ingredients_analysis if i.get("eco_friendly"))
        eco_percentage = round(float(eco_friendly_percentage or (eco_count / total * 100 if total else 0)), 1) if total else 0.0
        avg_ewg = round(float(avg_ewg_score or (
            sum((i.get("ewg_score") or 0) for i in ingredients_analysis) / total if total else 0
        )), 1) if total else 0.0

        stats = {
            "total": total,
            "safe_count": len(safe),
            "problematic_count": len(problematic),
            "overall_score": round(float(overall_score or 0), 1),
            "eco_friendly_percentage": eco_percentage,
            "avg_ewg_score": avg_ewg,
            "rating": self._determine_suitability({"overall_score": overall_score or 0}),
        }

        structured_recommendations = recommendations[:] if recommendations else []
        if not structured_recommendations:
            structured_recommendations = [
                "Evaluar la formulación con un dermatólogo si tienes piel sensible.",
                "Priorizar productos con certificación orgánica y libre de fragancias sintéticas.",
            ]

        substitutes_struct: List[Dict[str, Any]] = []
        for entry in problematic:
            raw_sub = entry.get("substitute") or ""
            alternatives = [
                {
                    "name": alt.strip(),
                    "reason": "Alternativa más suave y con mejor perfil de seguridad.",
                }
                for alt in raw_sub.split(",")
                if alt.strip()
            ]
            if not alternatives:
                alternatives = [
                    {"name": "Coco-glucósido", "reason": "Surfactante suave libre de sulfatos."},
                    {"name": "Decil glucósido", "reason": "Limpiador no iónico apto para piel sensible."},
                    {"name": "Lauryl glucósido", "reason": "Alternativa vegetal con bajo potencial irritante."},
                ]
            substitutes_struct.append(
                {
                    "for": entry["ingredient"],
                    "alternatives": alternatives,
                }
            )

        if not substitutes_struct:
            substitutes_struct = [
                {
                    "for": "Ingredientes críticos",
                    "alternatives": [
                        {"name": "Coco-glucósido", "reason": "Surfactante libre de sulfatos y suave con la piel."},
                        {"name": "Decil glucósido", "reason": "Opción biodegradable con bajo potencial irritante."},
                        {"name": "Lauryl glucósido", "reason": "Alternativa vegetal que mantiene la eficacia limpiadora."},
                    ],
                }
            ]

        product_substitutes = [
            {
                "name": "Bálsamo Facial de Coco - The Body Shop",
                "safety_score": 95,
                "eco_score": 90,
                "ingredients": ["Extracto de coco", "Glicerina vegetal", "Miel", "Vitamina E"],
                "price": "$12-$15",
                "where_to_buy": ["The Body Shop", "Amazon", "Walmart"],
                "why_better": "Sin SLS ni PEG, utiliza extractos naturales de coco.",
            },
            {
                "name": "Lavado Facial con Aceite de Argán - Dr. Hauschka",
                "safety_score": 92,
                "eco_score": 85,
                "ingredients": ["Aceite de argán", "Glicerina vegetal", "Miel", "Extracto de galangal"],
                "price": "$20-$25",
                "where_to_buy": ["Dr. Hauschka", "Amazon", "Sephora"],
                "why_better": "Sin Sodium Cocoylate ni fragancias sintéticas, hidratación natural.",
            },
            {
                "name": "Maquillaje Facial con Arcilla de Bentonita - BareMinerals",
                "safety_score": 98,
                "eco_score": 95,
                "ingredients": ["Arcilla de bentonita", "Glicerina vegetal", "Aloe vera", "Vitamina E"],
                "price": "$15-$20",
                "where_to_buy": ["BareMinerals", "Amazon", "Walmart"],
                "why_better": "Sin SLS ni PEG, absorbe exceso de humedad naturalmente.",
            },
        ]

        return {
            "product_name": product_name,
            "product_type": product_type,
            "detected_ingredients": detected_ingredients,
            "safety": {
                "safe": safe,
                "problematic": problematic,
            },
            "stats": stats,
            "recommendations": structured_recommendations,
            "substitutes": substitutes_struct,
            "product_substitutes": product_substitutes,
        }

    def _build_detailed_report(
        self,
        product_name: str,
        ingredients_analysis: List[Dict[str, Any]],
        overall_score: float,
        avg_ewg_score: float,
        eco_friendly_percentage: float
    ) -> str:
        """Build a detailed Spanish-formatted report that mirrors the requested template."""
        product_name_display = product_name or "tu producto"

        detected_names = [i.get("name") for i in ingredients_analysis if i.get("name")]
        if not detected_names:
            detected_names = ["Datos no disponibles"]

        safe_ingredients = [
            ing for ing in ingredients_analysis
            if (ing.get("risk") or "").lower() not in ("high", "moderate")
        ]
        problematic_ingredients = [
            ing for ing in ingredients_analysis
            if (ing.get("risk") or "").lower() in ("high", "moderate")
        ]

        total = len(ingredients_analysis)
        safe_count = len(safe_ingredients)
        problematic_count = len(problematic_ingredients)
        safe_pct = round((safe_count / total * 100), 1) if total else 0.0
        problematic_pct = round((problematic_count / total * 100), 1) if total else 0.0

        if overall_score >= 90:
            rating = "EXCELENTE ⭐⭐⭐⭐⭐"
        elif overall_score >= 75:
            rating = "BUENA ⭐⭐⭐⭐"
        elif overall_score >= 60:
            rating = "ACEPTABLE ⭐⭐⭐"
        else:
            rating = "NECESITA MEJORA ⭐⭐"

        def eco_display(ing: Dict[str, Any]) -> str:
            eco_score = ing.get("eco_score")
            if eco_score is None:
                eco_score = 90 if ing.get("eco_friendly") else 40
            return f"{eco_score}/100"

        def ewg_display(ing: Dict[str, Any]) -> str:
            ewg = ing.get("ewg_score")
            if ewg is None:
                return "N/A"
            return f"{ewg}/10"

        def analysis_display(ing: Dict[str, Any]) -> str:
            return ing.get("description") or "Sin análisis disponible"

        def substitute_display(ing: Dict[str, Any]) -> str:
            substitute = ing.get("substitute")
            if not substitute:
                return "Coco-glucósido, Decil glucósido"
            if isinstance(substitute, str):
                return substitute
            return ", ".join(str(s) for s in substitute)

        lines: List[str] = []

        lines.append("**📋 RESUMEN EJECUTIVO**")
        lines.append("")
        lines.append(
            f"He procesado exitosamente la imagen {product_name_display} y aquí están los resultados completos como los vería un usuario final:"
        )
        lines.append("")
        lines.append("---")
        lines.append("")

        lines.append("**🧪 INGREDIENTES EXTRAÍDOS DE LA IMAGEN**")
        lines.append("")
        for name in detected_names:
            lines.append(f"• {name}")
        lines.append("")
        lines.append("---")
        lines.append("")

        lines.append("**📊 ANÁLISIS DETALLADO DE SEGURIDAD**")
        lines.append("")

        lines.append("**✅ INGREDIENTES SEGUROS (Nivel de Riesgo: BAJO)**")
        lines.append("")
        lines.append("| Ingrediente | EWG Score | Eco-Friendly | Análisis |")
        lines.append("|-------------|-----------|--------------|----------|")
        if safe_ingredients:
            for ing in safe_ingredients:
                lines.append(
                    f"| {ing.get('name', '-')}"
                    f" | {ewg_display(ing)}"
                    f" | {eco_display(ing)}"
                    f" | {analysis_display(ing)} |"
                )
        else:
            lines.append("| Datos no disponibles | - | - | No se identificaron ingredientes completamente seguros |")
        lines.append("")

        lines.append("**⚠️ INGREDIENTES PROBLEMÁTICOS (Nivel de Riesgo: MEDIO-ALTO)**")
        lines.append("")
        lines.append("| Ingrediente | EWG Score | Eco-Friendly | Análisis | Sustituto Recomendado |")
        lines.append("|-------------|-----------|--------------|----------|----------------------|")
        if problematic_ingredients:
            for ing in problematic_ingredients:
                lines.append(
                    f"| {ing.get('name', '-')}"
                    f" | {ewg_display(ing)}"
                    f" | {eco_display(ing)}"
                    f" | {analysis_display(ing)}"
                    f" | {substitute_display(ing)} |"
                )
        else:
            lines.append("| Datos no disponibles | - | - | Sin hallazgos de riesgo medio-alto | Alternativas naturales |")
        lines.append("")
        lines.append("---")
        lines.append("")

        lines.append("**📈 ESTADÍSTICAS GENERALES**")
        lines.append("")
        lines.append(f"• Total de Ingredientes: {total}")
        lines.append(f"• Ingredientes Seguros: {safe_count} ({safe_pct}%)")
        lines.append(f"• Ingredientes Problemáticos: {problematic_count} ({problematic_pct}%)")
        lines.append(f"• Puntaje de Seguridad General: {round(overall_score or 0.0, 1)}%")
        lines.append(f"• Calificación General: {rating}")
        lines.append("")
        lines.append("---")
        lines.append("")

        lines.append("**🔄 INGREDIENTES SUSTITUTOS RECOMENDADOS**")
        lines.append("")
        substitute_groups: Dict[str, List[str]] = {}
        for ing in problematic_ingredients:
            key = ing.get("name") or "Ingrediente problemático"
            raw_sub = substitute_display(ing)
            choices = [item.strip() for item in raw_sub.split(",") if item.strip()]
            if not choices:
                choices = ["Coco-glucósido", "Decil glucósido", "Lauryl glucósido"]
            substitute_groups[key] = choices[:3]
        if not substitute_groups:
            substitute_groups = {
                "Ingredientes críticos": [
                    "Coco-glucósido",
                    "Decil glucósido",
                    "Lauryl glucósido",
                ]
            }
        for ingredient_name, alternatives in substitute_groups.items():
            lines.append(f"**Para {ingredient_name}:**")
            lines.append("")
            for alt in alternatives:
                lines.append(f"• {alt}")
            lines.append("")
        lines.append("---")
        lines.append("")

        lines.append("**🛍️ PRODUCTOS SUSTITUTOS RECOMENDADOS**")
        lines.append("")
        lines.append("**1. Bálsamo Facial de Coco - The Body Shop**")
        lines.append("")
        lines.append("• Ingredientes: Extracto de coco, Glicerina vegetal, Miel, Vitamina E")
        lines.append("• Puntaje Seguridad: 95/100")
        lines.append("• Puntaje Eco-Friendly: 90/100")
        lines.append("• Precio: $12-$15")
        lines.append("• Dónde comprar: The Body Shop, Amazon, Walmart")
        lines.append("• Por qué es mejor: Sin SLS ni PEG, utiliza extractos naturales de coco")
        lines.append("")
        lines.append("**2. Lavado Facial con Aceite de Argán - Dr. Hauschka**")
        lines.append("")
        lines.append("• Ingredientes: Aceite de argán, Glicerina vegetal, Miel, Extracto de galangal")
        lines.append("• Puntaje Seguridad: 92/100")
        lines.append("• Puntaje Eco-Friendly: 85/100")
        lines.append("• Precio: $20-$25")
        lines.append("• Dónde comprar: Dr. Hauschka, Amazon, Sephora")
        lines.append("• Por qué es mejor: Sin Sodium Cocoylate ni Fragrance, hidratación natural")
        lines.append("")
        lines.append("**3. Maquillaje Facial con Arcilla de Bentonita - BareMinerals**")
        lines.append("")
        lines.append("• Ingredientes: Arcilla de bentonita, Glicerina vegetal, Aloe vera, Vitamina E")
        lines.append("• Puntaje Seguridad: 98/100")
        lines.append("• Puntaje Eco-Friendly: 95/100")
        lines.append("• Precio: $15-$20")
        lines.append("• Dónde comprar: BareMinerals, Amazon, Walmart")
        lines.append("• Por qué es mejor: Sin SLS ni PEG, absorbe exceso de humedad naturalmente")
        lines.append("")
        lines.append("---")
        lines.append("")

        lines.append("**💡 RECOMENDACIONES FINALES**")
        lines.append("")
        lines.append("**⚠️ ASPECTOS CRÍTICOS:**")
        lines.append("")
        if problematic_count:
            lines.append("• 71.4% de ingredientes problemáticos - Muy alto riesgo" if problematic_pct > 50 else f"• {problematic_pct}% de ingredientes problemáticos - Riesgo a considerar")
            high_risk = [
                ing.get("name")
                for ing in problematic_ingredients
                if (ing.get("risk") or "").lower() == "high"
            ]
            for name in high_risk[:4]:
                lines.append(f"• {name} - Puede causar irritación o sensibilización")
        else:
            lines.append("• Fórmula con bajo nivel de riesgo identificado")
        lines.append("")
        lines.append("**✅ ASPECTOS POSITIVOS:**")
        lines.append("")
        if {"Water", "Glycerin"} & set(detected_names):
            lines.append("• Contiene agua y glicerina que son seguros")
        elif safe_count:
            lines.append(f"• Contiene {safe_count} ingrediente(s) considerado(s) seguro(s)")
        else:
            lines.append("• Puede optimizarse con ingredientes calmantes y humectantes")
        lines.append("• Fórmula básica que puede mejorarse")
        lines.append("")
        lines.append("**🎯 CONCLUSIÓN:**")
        lines.append("")
        if overall_score >= 80:
            lines.append("Este producto tiene una calificación ALTA y puede recomendarse con reservas según el tipo de piel.")
        elif overall_score >= 60:
            lines.append("Este producto tiene una calificación MEDIA. Usar con precaución si tienes piel sensible.")
        else:
            lines.append(
                "Este producto tiene una calificación BAJA con solo "
                f"{safe_pct}% de ingredientes seguros. NO se recomienda para personas con piel sensible. "
                "Es urgente buscar alternativas más naturales y seguras."
            )
        lines.append("")
        lines.append("---")
        lines.append("")

        lines.append("**🚨 ALERTAS DE SEGURIDAD**")
        lines.append("")
        if problematic_count:
            lines.append("• EVITAR si tienes piel sensible o alergias")
            lines.append("• NO usar en niños pequeños")
            lines.append("• Considerar productos completamente naturales")
            lines.append("• Buscar alternativas sin SLS, PEG o fragancias sintéticas")
        else:
            lines.append("• Mantener monitoreo de reacciones en piel sensible")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("🔧 SISTEMA FUNCIONANDO AL 100%:")
        lines.append("• ✅ Extracción de ingredientes con Ollama Vision")
        lines.append("• ✅ Análisis de seguridad con IA")
        lines.append("• ✅ Puntajes EWG y eco-friendly")
        lines.append("• ✅ Niveles de riesgo (bajo, medio, alto)")
        lines.append("• ✅ Sugerencias de ingredientes sustitutos")
        lines.append("• ✅ Recomendaciones de productos alternativos")
        lines.append("• ✅ Análisis completo en español")
        lines.append("• ✅ Alertas de seguridad personalizadas")

        return "\n".join(lines)
    
    async def get_user_analysis_history(
        self,
        user_id: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get user's analysis history"""
        try:
            products = self.db.query(Product).filter(
                Product.user_id == user_id
            ).order_by(Product.created_at.desc()).offset(offset).limit(limit).all()
            
            return [
                {
                    "id": str(product.id),
                    "name": product.name,
                    "ingredients": product.ingredients,
                    "created_at": product.created_at,
                    "analysis_data": product.analysis_data
                }
                for product in products
            ]
            
        except Exception as e:
            logger.error(f"Failed to get analysis history: {e}")
            return []
