"""
Substitute Service
Provides ingredient substitute suggestions tailored by product type
"""

import json
from pathlib import Path
from typing import List, Dict, DefaultDict
from collections import defaultdict

SUBSTITUTE_PATH = Path(__file__).resolve().parent.parent / "data" / "substitute_catalog.json"


class SubstituteService:
    """Suggest substitutes based on product category and ingredient name."""

    def __init__(self) -> None:
        self.catalog = self._load_catalog()

    def get_substitutes(self, product_type: str, ingredient_name: str) -> List[Dict[str, str]]:
        product_key = (product_type or "").lower()
        name = (ingredient_name or "").upper()
        return self.catalog.get(product_key, {}).get(name, [])

    def _load_catalog(self) -> Dict[str, Dict[str, List[Dict[str, str]]]]:
        """Load substitute options from JSON with sensible defaults."""
        catalog: Dict[str, Dict[str, List[Dict[str, str]]]] = self._default_catalog()

        if not SUBSTITUTE_PATH.exists():
            return catalog

        try:
            raw = json.loads(SUBSTITUTE_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return catalog

        processed: DefaultDict[str, Dict[str, List[Dict[str, str]]]] = defaultdict(dict)
        for product_type, substitutions in raw.items():
            normalized_type = (product_type or "").lower()
            processed.setdefault(normalized_type, {})
            for ingredient_name, options in substitutions.items():
                processed[normalized_type][ingredient_name.upper()] = options

        # Merge defaults with file (file overrides defaults)
        for product_type, substitutions in processed.items():
            if product_type not in catalog:
                catalog[product_type] = {}
            catalog[product_type].update(substitutions)

        return catalog

    @staticmethod
    def _default_catalog() -> Dict[str, Dict[str, List[Dict[str, str]]]]:
        """Fallback substitutions used if catalog file is missing."""
        return {
            "hair_conditioner": {
                "DIMETHICONE": [
                    {
                        "name": "Amodimethicone",
                        "reason": "Silicona funcional con depósito selectivo; deja menos residuo.",
                    }
                ],
                "PARFUM": [
                    {
                        "name": "Fragrance-Free",
                        "reason": "Versión sin fragancia para minimizar alérgenos.",
                    }
                ],
            }
        }
