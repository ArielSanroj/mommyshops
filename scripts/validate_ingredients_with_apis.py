#!/usr/bin/env python3
"""
Script para validar ingredientes del catálogo contra APIs externas
Compara los valores actuales con datos de EWG, PubChem y otras fuentes
"""

import json
import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import httpx
from datetime import datetime

# Add backend-python to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend-python"))

CATALOG_PATH = Path(__file__).parent.parent / "backend-python" / "app" / "data" / "ingredient_catalog.json"

# Test ingredients from user's sample
TEST_INGREDIENTS = [
    "Cocamidopropyl Betaine",
    "Sodium Myreth Sulfate",
    "Coco-Glucoside",
    "Glyceryl Caprylate",
    "PEG-150 Distearate",
    "Fragrance (Parfum)",
    "Polyquaternium-10",
    "Caramel",
    "Panthenol",
    "Glycerin",
    "Chamomilla Recutita",
    "Persea Gratissima"
]


class ExternalAPIValidator:
    """Validates ingredients against external APIs"""
    
    def __init__(self):
        self.timeout = 30.0
        self.results: List[Dict[str, Any]] = []
    
    async def validate_ingredient(self, ingredient_name: str) -> Dict[str, Any]:
        """Validate a single ingredient against multiple sources"""
        print(f"\n🔍 Validando: {ingredient_name}")
        
        result = {
            "ingredient": ingredient_name,
            "catalog_data": self._get_catalog_data(ingredient_name),
            "external_data": {},
            "validation": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Try multiple sources in parallel
        tasks = [
            self._check_ewg_scrape(ingredient_name),
            self._check_pubchem(ingredient_name),
            self._check_cosing_estimate(ingredient_name)
        ]
        
        external_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Parse results
        for source_name, source_data in zip(["ewg", "pubchem", "cosing"], external_results):
            if isinstance(source_data, Exception):
                result["external_data"][source_name] = {"error": str(source_data)}
            else:
                result["external_data"][source_name] = source_data
        
        # Compare and validate
        result["validation"] = self._compare_data(result["catalog_data"], result["external_data"])
        
        return result
    
    def _get_catalog_data(self, ingredient_name: str) -> Optional[Dict[str, Any]]:
        """Get data from local catalog"""
        try:
            with open(CATALOG_PATH, 'r', encoding='utf-8') as f:
                catalog = json.load(f)
            
            # Normalize name for lookup
            key = ingredient_name.strip()
            
            # Try exact match
            if key in catalog:
                return catalog[key]
            
            # Try case-insensitive
            for cat_key, cat_data in catalog.items():
                if cat_key.lower() == key.lower():
                    return cat_data
                
                # Check aliases
                aliases = cat_data.get("aliases", [])
                if any(alias.lower() == key.lower() for alias in aliases):
                    return cat_data
            
            return None
            
        except Exception as e:
            print(f"  ❌ Error reading catalog: {e}")
            return None
    
    async def _check_ewg_scrape(self, ingredient_name: str) -> Dict[str, Any]:
        """
        Check EWG Skin Deep database (simplified scrape)
        Note: EWG doesn't have a public API, this is educational/research use only
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # EWG search URL
                search_url = f"https://www.ewg.org/skindeep/search/?query={ingredient_name.replace(' ', '+')}"
                
                headers = {
                    "User-Agent": "Mozilla/5.0 (Educational Research)",
                    "Accept": "text/html,application/xhtml+xml"
                }
                
                response = await client.get(search_url, headers=headers, follow_redirects=True)
                
                if response.status_code == 200:
                    html = response.text
                    
                    # Simple pattern matching for score (this is a simplified version)
                    import re
                    
                    # Look for hazard score patterns
                    score_patterns = [
                        r'hazard-score["\']?\s*[:=]\s*["\']?(\d+)',
                        r'score["\']?\s*[:=]\s*["\']?(\d+)',
                        r'data-score["\']?\s*[:=]\s*["\']?(\d+)'
                    ]
                    
                    extracted_score = None
                    for pattern in score_patterns:
                        match = re.search(pattern, html, re.IGNORECASE)
                        if match:
                            extracted_score = int(match.group(1))
                            break
                    
                    print(f"  📊 EWG: score estimado = {extracted_score if extracted_score else 'N/A'}")
                    
                    return {
                        "available": extracted_score is not None,
                        "hazard_score": extracted_score,
                        "note": "Scraped from EWG Skin Deep (educational use)",
                        "url": search_url
                    }
                
                return {"available": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"  ⚠️  EWG no disponible: {str(e)[:50]}")
            return {"available": False, "error": str(e)}
    
    async def _check_pubchem(self, ingredient_name: str) -> Dict[str, Any]:
        """Check PubChem database"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # PubChem REST API
                search_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{}/property/MolecularFormula,MolecularWeight/JSON"
                
                response = await client.get(
                    search_url.format(ingredient_name.replace(" ", "%20")),
                    headers={"Accept": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    properties = data.get("PropertyTable", {}).get("Properties", [])
                    
                    if properties:
                        prop = properties[0]
                        print(f"  🧪 PubChem: CID={prop.get('CID')}, Formula={prop.get('MolecularFormula')}")
                        return {
                            "available": True,
                            "cid": prop.get("CID"),
                            "formula": prop.get("MolecularFormula"),
                            "molecular_weight": prop.get("MolecularWeight"),
                            "source": "PubChem"
                        }
                
                return {"available": False, "note": "Not found in PubChem"}
                
        except Exception as e:
            print(f"  ⚠️  PubChem no disponible: {str(e)[:50]}")
            return {"available": False, "error": str(e)}
    
    async def _check_cosing_estimate(self, ingredient_name: str) -> Dict[str, Any]:
        """
        Estimate safety based on ingredient characteristics
        (COSING database is not publicly available via API)
        """
        name_lower = ingredient_name.lower()
        
        # Heuristic classification
        is_natural = any(keyword in name_lower for keyword in [
            "extract", "oil", "juice", "flower", "fruit", "root", "seed", "plant", "herb"
        ])
        
        is_chemical = any(keyword in name_lower for keyword in [
            "sulfate", "peg", "paraben", "fragrance", "parfum", "propyl", "phenoxy"
        ])
        
        is_preservative = any(keyword in name_lower for keyword in [
            "paraben", "sorbate", "benzoate", "phenoxyethanol"
        ])
        
        estimated_risk = "low"
        if is_chemical and not is_preservative:
            estimated_risk = "moderate"
        if "sulfate" in name_lower or "fragrance" in name_lower:
            estimated_risk = "high"
        
        print(f"  🌿 Clasificación: {'natural' if is_natural else 'sintético'}, riesgo={estimated_risk}")
        
        return {
            "available": True,
            "is_natural": is_natural,
            "is_chemical": is_chemical,
            "is_preservative": is_preservative,
            "estimated_risk": estimated_risk,
            "note": "Estimated classification (no direct COSING API)"
        }
    
    def _compare_data(self, catalog: Optional[Dict], external: Dict[str, Any]) -> Dict[str, Any]:
        """Compare catalog data with external sources"""
        if not catalog:
            return {
                "status": "not_in_catalog",
                "recommendation": "Add to catalog with external data"
            }
        
        validation = {
            "status": "validated",
            "discrepancies": [],
            "confidence": "high"
        }
        
        # Compare EWG score if available
        ewg_external = external.get("ewg", {}).get("hazard_score")
        ewg_catalog = catalog.get("ewg")
        
        if ewg_external and ewg_catalog:
            diff = abs(ewg_external - ewg_catalog)
            if diff > 2:
                validation["discrepancies"].append({
                    "field": "ewg_score",
                    "catalog": ewg_catalog,
                    "external": ewg_external,
                    "difference": diff
                })
                validation["confidence"] = "medium"
        
        # Compare risk classification
        cosing_risk = external.get("cosing", {}).get("estimated_risk")
        catalog_risk = catalog.get("risk")
        
        if cosing_risk and catalog_risk and cosing_risk != catalog_risk:
            validation["discrepancies"].append({
                "field": "risk_level",
                "catalog": catalog_risk,
                "external": cosing_risk
            })
        
        if validation["discrepancies"]:
            validation["status"] = "needs_review"
        
        return validation
    
    async def validate_all(self, ingredients: List[str]) -> List[Dict[str, Any]]:
        """Validate all ingredients"""
        print("=" * 70)
        print("🔬 VALIDACIÓN DE INGREDIENTES CONTRA APIs EXTERNAS")
        print("=" * 70)
        
        results = []
        for ingredient in ingredients:
            result = await self.validate_ingredient(ingredient)
            results.append(result)
            
            # Be respectful with rate limiting
            await asyncio.sleep(2)
        
        return results
    
    def generate_report(self, results: List[Dict[str, Any]]) -> str:
        """Generate validation report"""
        report = ["\n" + "=" * 70]
        report.append("📋 REPORTE DE VALIDACIÓN")
        report.append("=" * 70)
        
        total = len(results)
        in_catalog = sum(1 for r in results if r["catalog_data"] is not None)
        needs_review = sum(1 for r in results if r["validation"].get("status") == "needs_review")
        validated = sum(1 for r in results if r["validation"].get("status") == "validated")
        
        report.append(f"\n📊 RESUMEN:")
        report.append(f"  • Total ingredientes analizados: {total}")
        report.append(f"  • En catálogo: {in_catalog}/{total}")
        report.append(f"  • Validados correctamente: {validated}/{in_catalog}")
        report.append(f"  • Necesitan revisión: {needs_review}/{in_catalog}")
        
        if needs_review > 0:
            report.append(f"\n⚠️  INGREDIENTES QUE NECESITAN REVISIÓN:")
            for r in results:
                if r["validation"].get("status") == "needs_review":
                    report.append(f"\n  🔸 {r['ingredient']}")
                    for disc in r["validation"].get("discrepancies", []):
                        report.append(f"     • {disc['field']}: catálogo={disc['catalog']}, externo={disc.get('external', 'N/A')}")
        
        report.append("\n" + "=" * 70)
        return "\n".join(report)


async def main():
    """Main validation function"""
    validator = ExternalAPIValidator()
    
    print("\n🚀 Iniciando validación de ingredientes...")
    print(f"📁 Catálogo: {CATALOG_PATH}")
    print(f"🧪 Ingredientes a validar: {len(TEST_INGREDIENTS)}\n")
    
    results = await validator.validate_all(TEST_INGREDIENTS)
    
    # Generate and print report
    report = validator.generate_report(results)
    print(report)
    
    # Save detailed results to JSON
    output_path = Path(__file__).parent / "validation_results.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Resultados detallados guardados en: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
