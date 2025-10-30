import pytest

from app.services.ingredient_service import IngredientService


@pytest.mark.asyncio
async def test_catalog_loads_dimethicone_entry():
    service = IngredientService(db=None)

    result = await service.analyze_ingredients(
        ["Dimethicone"], user_id="test-user", product_type="hair_conditioner"
    )

    assert result["success"] is True
    entry = result["ingredients_analysis"][0]
    assert entry["name"] == "Dimethicone"
    assert entry["ewg_score"] == 5
    assert entry["substitute"] in {"Amodimethicone", "Dimethicone PEG-7 Phosphate"}


@pytest.mark.asyncio
async def test_alias_mapping_for_fragrance():
    service = IngredientService(db=None)

    result = await service.analyze_ingredients(
        ["Fragrance"], user_id="test-user", product_type="hair_conditioner"
    )

    entry = result["ingredients_analysis"][0]
    assert entry["name"] == "Parfum"
    assert entry["risk"] == "high"
    assert entry["substitute"] == "Fragrance-Free"


@pytest.mark.asyncio
async def test_unknown_ingredient_returns_neutral_defaults():
    service = IngredientService(db=None)

    result = await service.analyze_ingredients(
        ["Totally Unknown Ingredient"], user_id="test-user", product_type="hair_conditioner"
    )

    entry = result["ingredients_analysis"][0]
    assert entry["name"] == "Totally Unknown Ingredient"
    assert entry["score"] == 80
    assert entry["substitute"] is None
