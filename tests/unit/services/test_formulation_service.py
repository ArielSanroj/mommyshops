import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[3] / "backend-python" / "app" / "services" / "formulation_service.py"
spec = importlib.util.spec_from_file_location("mommyshops_formulation_service", MODULE_PATH)
assert spec and spec.loader
formulation_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = formulation_module
spec.loader.exec_module(formulation_module)  # type: ignore[attr-defined]
FormulationService = formulation_module.FormulationService


def test_generate_formula_without_detected_ingredients_uses_catalog_seed():
    service = FormulationService()

    result = service.generate_formula(
        profile={"hair_type": "rizado", "concerns": ["Hidratación profunda"]},
        detected_ingredients=[],
    )

    assert result["new_formula"], "Expected fallback formula when no ingredients are provided"
    assert result["summary"]["variant"] == "botanical"
    assert result["summary"]["compatibility_score"] > 0


def test_generate_formula_supports_new_function_labels():
    service = FormulationService()

    profile = {"concerns": ["Termoprotección"], "hair_type": "lacio"}
    result = service.generate_formula(profile=profile, detected_ingredients=[])

    all_tags = [tag for item in result["new_formula"] for tag in item.get("function_tags", [])]
    assert any("Termoprotección" in tag for tag in all_tags), "Expected formula to cover heat protection"
