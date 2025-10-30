# Ingredient Catalog & Substitute Data

To keep ingredient scoring reliable and easy to update, the backend loads
structured data files from `backend-python/app/data/`:

| File | Purpose |
|------|---------|
| `ingredient_catalog.json` | Scores, risk, eco flag, description, aliases and categories for each ingredient. |
| `substitute_catalog.json` | Recommended alternatives grouped by product type and ingredient. |

## Adding or Updating Ingredients

1. Edit `backend-python/app/data/ingredient_catalog.json`.
2. Use the exact casing you prefer for display; the service normalises keys automatically.
3. Recommended fields per entry:

```jsonc
"Dimethicone": {
  "score": 60,              // 0–100
  "ewg": 5,                 // 0–10
  "risk": "moderate",       // free text, kept for reporting
  "eco": false,             // eco-friendly flag
  "description": "Silicona no volátil para desliz.",
  "categories": ["hair_conditioner", "styling"],
  "aliases": ["Dimeticona"] // optional
}
```

4. Save the file using UTF-8 and valid JSON syntax.
5. No restart logic is needed—the backend reads the file on startup.

## Adding or Updating Substitutes

1. Edit `backend-python/app/data/substitute_catalog.json`.
2. Structure data by product type:

```jsonc
"hair_conditioner": {
  "DIMETHICONE": [
    {
      "name": "Amodimethicone",
      "reason": "Silicona funcional con depósito selectivo."
    }
  ]
}
```

3. Ingredient keys are normalised to uppercase, and product types to lowercase.
4. Multiple product types can coexist (e.g., `shampoo`, `skincare`).

## Best Practices

- Prefer authoritative sources (EWG, CIR, SCCS, PubChem) when assigning scores.
- For aliases, include language variations or INCI synonyms (e.g., "Fragrance", "Perfume").
- Keep descriptions short and user-friendly; detailed references belong in extended reports.
- When adding new product types, update the detection heuristics if necessary (e.g., in `AnalysisService`).

## Validation

- Run `pytest tests/unit/services/test_ingredient_catalog.py` (added with this change) after edits.
- If JSON parsing fails, the backend falls back to the minimal built-in catalog and logs a warning.
