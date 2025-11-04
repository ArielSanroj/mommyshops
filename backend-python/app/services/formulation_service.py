"""
MommyShops Labs - intelligent formulation service.
Translates detected ingredients + profile context into a proposed formula.
"""

from __future__ import annotations

import json
import logging
import unicodedata
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "labs_functional_catalog.json"

DEFAULT_NEEDS = ["hidratacion", "control_grasa", "antiinflamatorio", "anticaspa"]

FUNCTION_LABELS = {
    "hidratacion": "Hidratación profunda",
    "nutricion": "Nutrición vegetal",
    "antioxidante": "Antioxidante",
    "antiinflamatorio": "Antiinflamatorio",
    "barrera": "Refuerzo de barrera",
    "calmante": "Calmante",
    "fortalecimiento": "Fortalecimiento",
    "definicion_rizos": "Definición de rizos",
    "estimulacion": "Estimula folículos",
    "microcirculacion": "Microcirculación",
    "anticaspa": "Control de caspa",
    "antimicrobiano": "Acción antimicrobiana",
    "anticaida": "Control de caída",
    "regulacion_hormonal": "Regulación hormonal",
    "oxigenacion": "Oxigenación",
    "reparacion": "Reparación",
    "refrescante": "Efecto refrescante",
    "defensa_uv": "Defensa UV",
    "control_grasa": "Control de grasa",
    "barrera_cutanea": "Barrera cutánea",
    "nutricion_intensa": "Nutrición intensa",
    "microbioma": "Equilibrio microbioma",
    "definicion": "Definición",
    "oxigenacion_celular": "Oxigenación celular",
    "termoproteccion": "Termoprotección",
    "proteccion_solar": "Protección solar",
}


def _normalize_text(value: Optional[str]) -> str:
    if not value:
        return ""
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9\s\-&/]", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _normalize_need(value: Optional[str]) -> Optional[str]:
    norm = _normalize_text(value)
    return norm or None


def _title_case(value: str) -> str:
    return value[:1].upper() + value[1:] if value else value


@dataclass
class CatalogEntry:
    key: str
    data: Dict[str, Any]

    @property
    def id(self) -> str:
        return self.data.get("id", self.key)

    @property
    def inci(self) -> str:
        return self.data.get("inci_name", self.key.title())


class FormulationService:
    """Core logic for building a MommyShops Labs formula."""

    def __init__(self, catalog_path: Optional[Path] = None):
        self.catalog_path = catalog_path or CATALOG_PATH
        self.catalog, self.synonyms = self._load_catalog()
        self.function_keys = self._collect_function_keys()

    # -----------------------------
    # Public API
    # -----------------------------

    def generate_formula(
        self,
        profile: Optional[Dict[str, Any]],
        detected_ingredients: List[str],
        variant: Optional[str] = None,
        product_name: Optional[str] = None,
        budget: Optional[float] = None,
    ) -> Dict[str, Any]:
        profile_ctx = self._build_profile_context(profile)
        variant_key = self._determine_variant(variant, profile_ctx)

        resolved, unknown = self._resolve_ingredients(detected_ingredients)
        scored_entries = self._score_entries(resolved, profile_ctx)

        if not scored_entries:
            logger.info("No catalog matches from detected list; seeding with variant defaults")
            scored_entries = self._seed_from_catalog(profile_ctx, variant_key)

        coverage = self._aggregate_coverage(scored_entries, profile_ctx)
        gaps = self._find_function_gaps(coverage, profile_ctx)

        additions = self._suggest_additions(
            gaps=gaps,
            profile_ctx=profile_ctx,
            variant_key=variant_key,
            used_ids={entry["record"].id for entry in scored_entries},
        )

        formula_items = self._compose_formula(scored_entries, additions, profile_ctx, variant_key, budget)
        summary = self._build_summary(formula_items, coverage, gaps, profile_ctx, variant_key, product_name)
        original_descriptions = self._describe_originals(scored_entries, profile_ctx)
        substitutions = self._build_substitutions(additions, gaps)

        return {
            "new_formula": [
                {
                    "inci": item["record"].inci,
                    "percent": item["percent"],
                    "reason": item["reason"],
                    "function_tags": item["function_tags"],
                    "source": item["source"],
                }
                for item in formula_items
            ],
            "summary": summary,
            "original_ingredients": original_descriptions,
            "substitutions": substitutions,
            "unknown_ingredients": unknown,
            "mockup": self._build_mockup(summary, formula_items, product_name),
        }

    # -----------------------------
    # Catalog + normalization helpers
    # -----------------------------

    def _load_catalog(self) -> Tuple[Dict[str, CatalogEntry], Dict[str, str]]:
        entries: Dict[str, CatalogEntry] = {}
        synonyms: Dict[str, str] = {}

        raw_data: List[Dict[str, Any]] = []
        if self.catalog_path.exists():
            try:
                parsed = json.loads(self.catalog_path.read_text(encoding="utf-8"))
                if isinstance(parsed, dict):
                    raw_data = list(parsed.values())
                elif isinstance(parsed, list):
                    raw_data = parsed
            except json.JSONDecodeError as exc:
                logger.warning("Invalid labs catalog JSON: %s", exc)

        if not raw_data:
            raw_data = self._fallback_catalog()

        for entry in raw_data:
            inci = entry.get("inci_name")
            key = _normalize_text(inci or entry.get("id") or entry.get("name") or "")
            if not key:
                continue
            catalog_entry = CatalogEntry(key=key, data=entry)
            entries[key] = catalog_entry

            for syn in entry.get("synonyms", []) or []:
                syn_key = _normalize_text(syn)
                if syn_key:
                    synonyms[syn_key] = key

        return entries, synonyms

    def _resolve_ingredients(self, items: List[str]) -> Tuple[List[Dict[str, Any]], List[str]]:
        resolved: List[Dict[str, Any]] = []
        unknown: List[str] = []
        seen_keys: set[str] = set()
        for raw in items or []:
            cleaned = (raw or "").strip()
            if not cleaned:
                continue
            lookup = _normalize_text(cleaned)
            key = self.synonyms.get(lookup, lookup)
            entry = self.catalog.get(key)
            if entry and key not in seen_keys:
                seen_keys.add(key)
                resolved.append(
                    {
                        "input_name": cleaned,
                        "normalized": key,
                        "record": entry,
                    }
                )
            else:
                unknown.append(cleaned)
        return resolved, unknown

    def _build_profile_context(self, profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        profile = profile or {}

        def _clean_list(values: Any) -> List[str]:
            if not values:
                return []
            if isinstance(values, str):
                values = [v.strip() for v in values.split(",")]
            return [v for v in (str(item).strip() for item in values) if v]

        concerns = _clean_list(
            profile.get("concerns")
            or profile.get("skin_concerns")
            or profile.get("hair_concerns")
        )
        goals = _clean_list(profile.get("goals") or profile.get("overall_goals"))

        needs = []
        for raw_need in concerns + goals:
            canonical = self._canonical_need(raw_need)
            if canonical:
                needs.append(canonical)
        if not needs:
            needs = DEFAULT_NEEDS.copy()

        ctx = {
            "skin_type": _normalize_need(profile.get("skin_type")),
            "hair_type": _normalize_need(profile.get("hair_type")),
            "concerns": concerns,
            "goals": goals,
            "needs": needs,
        }
        ctx["is_sensitive"] = any("sensib" in n for n in needs)
        ctx["needs_display"] = {need: self._need_label(need) for need in needs}
        return ctx

    def _collect_function_keys(self) -> set[str]:
        keys = set(FUNCTION_LABELS.keys())
        for entry in self.catalog.values():
            keys.update(entry.data.get("functions", {}).keys())
        return keys

    def _canonical_need(self, value: Optional[str]) -> Optional[str]:
        norm = _normalize_need(value)
        if not norm:
            return None
        candidates = [
            norm,
            norm.replace(" ", "_"),
            norm.replace(" ", ""),
        ]
        # Remove connectors like "_de_" to match catalog keys
        candidates.extend([cand.replace("_de_", "_") for cand in candidates])
        for candidate in candidates:
            if candidate in self.function_keys:
                return candidate
        for candidate in candidates:
            for key in self.function_keys:
                if key and (candidate.startswith(key) or key in candidate):
                    return key
        return norm

    def _need_label(self, need: str) -> str:
        return FUNCTION_LABELS.get(need, _title_case(need.replace("_", " ")))

    def _determine_variant(self, variant: Optional[str], profile_ctx: Dict[str, Any]) -> str:
        if variant:
            normalized = _normalize_text(variant)
        else:
            normalized = ""

        if not normalized and profile_ctx.get("hair_type") in {"rizado", "ondulado"}:
            normalized = "botanical"
        if not normalized:
            normalized = "balanced"
        return normalized

    # -----------------------------
    # Scoring + heuristics
    # -----------------------------

    def _score_entries(self, entries: List[Dict[str, Any]], profile_ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
        scored = []
        for entry in entries:
            record = entry["record"]
            functions = record.data.get("functions", {})
            coverage_map = {
                need: functions.get(need, 0.0)
                for need in profile_ctx["needs"]
            }
            coverage_total = sum(coverage_map.values()) or sum(functions.values()) * 0.3
            compatibility = self._compute_compatibility(record.data, profile_ctx)
            evidence = record.data.get("evidence_level", 0.5)
            total_score = coverage_total * compatibility * (0.6 + evidence * 0.4)
            dominant_need = max(coverage_map, key=lambda k: coverage_map[k]) if coverage_map else None

            scored.append(
                {
                    **entry,
                    "score": round(total_score, 4),
                    "compatibility": round(compatibility, 3),
                    "coverage_map": coverage_map,
                    "dominant_need": dominant_need,
                    "reason": self._build_reason(record, dominant_need, profile_ctx),
                    "source": "detected",
                }
            )
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored

    def _compute_compatibility(self, record: Dict[str, Any], profile_ctx: Dict[str, Any]) -> float:
        compat = 1.0
        risk_flags = [(_normalize_need(flag) or "") for flag in record.get("risk_flags", [])]
        oil_soluble = record.get("compatibilities", {}).get("oil_soluble", False)

        if profile_ctx.get("is_sensitive") and any("irritante" in flag for flag in risk_flags):
            compat -= 0.35
        if profile_ctx.get("skin_type") == "grasa" and oil_soluble:
            compat -= 0.1
        if profile_ctx.get("skin_type") == "seca" and not oil_soluble:
            compat -= 0.05
        if profile_ctx.get("hair_type") == "rizado" and record.get("family") == "botanical":
            compat += 0.05
        return max(0.25, min(1.15, compat))

    def _build_reason(self, record: CatalogEntry, dominant_need: Optional[str], profile_ctx: Dict[str, Any]) -> str:
        label = self._need_label(dominant_need) if dominant_need else "Balance integral"
        family = record.data.get("family", "activo")
        persona = profile_ctx.get("skin_type") or profile_ctx.get("hair_type") or "tu perfil registrado"
        return f"{label} para {persona} con {family.replace('_', ' ')} de Mommyshops."

    def _aggregate_coverage(self, scored_entries: List[Dict[str, Any]], profile_ctx: Dict[str, Any]) -> Dict[str, float]:
        coverage = {need: 0.0 for need in profile_ctx["needs"]}
        for entry in scored_entries:
            for need, score in entry["coverage_map"].items():
                coverage[need] = coverage.get(need, 0.0) + score
        return coverage

    def _find_function_gaps(self, coverage: Dict[str, float], profile_ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
        gaps = []
        for need in profile_ctx["needs"]:
            current = coverage.get(need, 0.0)
            if current < 0.75:
                gaps.append(
                    {
                        "need": need,
                        "required": 0.75,
                        "current": current,
                        "missing": round(0.75 - current, 3),
                        "label": self._need_label(need),
                    }
                )
        return gaps

    def _variant_weight(self, record: CatalogEntry, variant_key: str) -> float:
        family = record.data.get("family", "")
        if variant_key == "botanical":
            return 1.2 if family == "botanical" else 0.8
        if variant_key in {"clinical", "clinico", "clínico"}:
            return 1.2 if family in {"clinical_active", "vitamin", "mineral"} else 0.85
        return 1.0

    def _suggest_additions(
        self,
        gaps: List[Dict[str, Any]],
        profile_ctx: Dict[str, Any],
        variant_key: str,
        used_ids: set[str],
    ) -> List[Dict[str, Any]]:
        additions: List[Dict[str, Any]] = []
        if not gaps:
            return additions

        for gap in gaps:
            candidate = self._best_candidate_for_gap(gap["need"], used_ids, variant_key)
            if not candidate:
                continue
            used_ids.add(candidate.id)
            additions.append(
                {
                    "record": candidate,
                    "score": gap["missing"] * 1.1 + candidate.data.get("evidence_level", 0.5),
                    "dominant_need": gap["need"],
                    "reason": f"Refuerza {gap['label'].lower()} faltante en tu perfil.",
                    "coverage_map": {gap["need"]: candidate.data.get("functions", {}).get(gap["need"], 0.6)},
                    "source": "ai_suggestion",
                    "compatibility": 0.85,
                }
            )
        return additions

    def _best_candidate_for_gap(self, need: str, used_ids: set[str], variant_key: str) -> Optional[CatalogEntry]:
        best_entry = None
        best_score = 0.0
        for entry in self.catalog.values():
            if entry.id in used_ids:
                continue
            func_score = entry.data.get("functions", {}).get(need, 0.0)
            if func_score <= 0:
                continue
            variant_weight = self._variant_weight(entry, variant_key)
            availability = entry.data.get("availability", "stock")
            availability_weight = 0.9 if availability == "stock" else 0.7
            evidence = entry.data.get("evidence_level", 0.5)
            score = func_score * variant_weight * (0.6 + evidence * 0.4) * availability_weight
            if score > best_score:
                best_score = score
                best_entry = entry
        return best_entry

    def _compose_formula(
        self,
        scored_entries: List[Dict[str, Any]],
        additions: List[Dict[str, Any]],
        profile_ctx: Dict[str, Any],
        variant_key: str,
        budget: Optional[float],
    ) -> List[Dict[str, Any]]:
        combined = scored_entries[:3] + additions
        if budget:
            combined = self._respect_budget(combined, budget)

        final_items: List[Dict[str, Any]] = []
        for item in combined:
            record_obj = item.get("record")
            if isinstance(record_obj, CatalogEntry):
                record = record_obj
            elif isinstance(record_obj, dict):
                key = _normalize_text(record_obj.get("inci_name") or record_obj.get("id") or "")
                record = CatalogEntry(key=key or record_obj.get("id", "custom"), data=record_obj)
            else:
                raise ValueError("Invalid record payload for formulation item")
            percent = self._estimate_percentage(record.data, item["score"])
            function_tags = self._top_functions(record.data.get("functions", {}), limit=3)
            final_items.append(
                {
                    **item,
                    "record": record,
                    "percent": percent,
                    "function_tags": function_tags,
                    "reason": item.get("reason") or self._build_reason(record, item.get("dominant_need"), profile_ctx),
                }
            )
        return final_items

    def _respect_budget(self, items: List[Dict[str, Any]], budget: float) -> List[Dict[str, Any]]:
        if not items:
            return items
        estimated = sum(item["record"].data.get("cost", 30.0) for item in items)
        if estimated <= budget:
            return items
        ratio = max(0.4, budget / estimated)
        limited = items[: max(2, int(len(items) * ratio))]
        return limited

    def _estimate_percentage(self, record: Dict[str, Any], score: float) -> float:
        usage = record.get("usage_range") or {}
        minimum = usage.get("min", 0.2)
        maximum = usage.get("max", minimum + 1.0)
        normalized = min(1.0, max(0.2, score))
        percent = minimum + (maximum - minimum) * (normalized / 1.5)
        return round(percent, 2)

    def _top_functions(self, functions: Dict[str, float], limit: int = 3) -> List[str]:
        sorted_funcs = sorted(functions.items(), key=lambda kv: kv[1], reverse=True)
        return [self._need_label(name) for name, _ in sorted_funcs[:limit]]

    def _build_summary(
        self,
        formula_items: List[Dict[str, Any]],
        coverage: Dict[str, float],
        gaps: List[Dict[str, Any]],
        profile_ctx: Dict[str, Any],
        variant_key: str,
        product_name: Optional[str],
    ) -> Dict[str, Any]:
        if formula_items:
            compatibility = sum(item.get("compatibility", 0.85) for item in formula_items) / len(formula_items)
        else:
            compatibility = 0.8
        highlights = [self._need_label(need) for need, score in sorted(coverage.items(), key=lambda kv: kv[1], reverse=True)[:3]]

        profile_hint = "Diseñado para tus necesidades registradas."
        if profile_ctx.get("skin_type") == "grasa":
            profile_hint = "Optimizado para controlar sebo sin irritar."
        elif profile_ctx.get("hair_type") == "rizado":
            profile_hint = "Botánicos inteligentes para rizos definidos y cuero cabelludo sano."

        return {
            "compatibility_score": round(compatibility, 2),
            "highlights": highlights,
            "missing": [gap["label"] for gap in gaps],
            "variant": variant_key,
            "variant_label": self._variant_label(variant_key),
            "profile_hint": profile_hint,
            "product_name": product_name or "Mommyshops Labs Custom Blend",
        }

    def _variant_label(self, variant_key: str) -> str:
        mapping = {
            "botanical": "Botánico",
            "balanced": "Balanceado",
            "clinical": "Clínico suave",
            "clinico": "Clínico suave",
            "clínico": "Clínico suave",
        }
        return mapping.get(variant_key, _title_case(variant_key or "Personalizado"))

    def _describe_originals(self, scored_entries: List[Dict[str, Any]], profile_ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
        described = []
        for entry in scored_entries:
            status = "mantener" if entry["score"] >= 0.5 else "potenciar" if entry["score"] >= 0.3 else "sustituir"
            described.append(
                {
                    "name": entry["input_name"],
                    "status": status,
                    "score": round(entry["score"], 2),
                    "note": entry["reason"],
                }
            )
        return described

    def _build_substitutions(self, additions: List[Dict[str, Any]], gaps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        substitutions = []
        for addition in additions:
            need = addition.get("dominant_need")
            gap = next((g for g in gaps if g["need"] == need), None)
            substitutions.append(
                {
                    "for": gap["label"] if gap else self._need_label(need or "Balance"),
                    "suggested": addition["record"].inci,
                    "reason": addition["reason"],
                }
            )
        return substitutions

    def _build_mockup(self, summary: Dict[str, Any], formula_items: List[Dict[str, Any]], product_name: Optional[str]) -> Dict[str, Any]:
        hero = [item["record"].inci for item in formula_items[:3]]
        return {
            "title": "Mommyshops Labs",
            "variant": summary.get("variant_label") or summary.get("variant", "balanced"),
            "tagline": f"{summary.get('product_name') or product_name or 'Custom Blend'} — {', '.join(hero[:3])}",
            "hero_ingredients": hero,
            "eta_days": "5-7 días hábiles",
        }

    def _seed_from_catalog(self, profile_ctx: Dict[str, Any], variant_key: str) -> List[Dict[str, Any]]:
        seeds = []
        used_ids: set[str] = set()
        for need in profile_ctx["needs"]:
            candidate = self._best_candidate_for_gap(need, used_ids, variant_key)
            if candidate:
                used_ids.add(candidate.id)
                seeds.append(
                    {
                        "record": candidate,
                        "input_name": candidate.inci,
                        "normalized": candidate.key,
                        "score": candidate.data.get("functions", {}).get(need, 0.7),
                        "compatibility": 0.9,
                        "coverage_map": {need: candidate.data.get("functions", {}).get(need, 0.7)},
                        "dominant_need": need,
                        "reason": f"Activo experto de Mommyshops para {self._need_label(need).lower()}.",
                        "source": "catalog_seed",
                    }
                )
        return seeds

    def _build_subtotals(self, formula_items: List[Dict[str, Any]]) -> Dict[str, float]:
        totals: Dict[str, float] = {}
        for item in formula_items:
            for need, score in item.get("coverage_map", {}).items():
                totals[need] = totals.get(need, 0.0) + score
        return totals

    def _fallback_catalog(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "niacinamide",
                "inci_name": "Niacinamide",
                "functions": {"control_grasa": 0.9, "barrera": 0.8},
                "usage_range": {"min": 2.0, "max": 6.0},
                "compatibilities": {"pH": [5.0, 7.0], "oil_soluble": False},
                "risk_flags": [],
                "evidence_level": 0.85,
                "family": "vitamin",
                "synonyms": ["Nicotinamide"],
                "availability": "stock",
            },
            {
                "id": "camellia_sinensis",
                "inci_name": "Camellia Sinensis Leaf Extract",
                "functions": {"antioxidante": 0.8, "antiinflamatorio": 0.7},
                "usage_range": {"min": 0.2, "max": 2.0},
                "compatibilities": {"pH": [4.5, 7.0], "oil_soluble": False},
                "risk_flags": [],
                "evidence_level": 0.7,
                "family": "botanical",
                "synonyms": ["Green Tea Extract"],
                "availability": "stock",
            },
        ]
