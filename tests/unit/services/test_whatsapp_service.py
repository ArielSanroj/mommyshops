"""
Unit tests for WhatsApp service helpers.
"""

from core.config import Settings
from app.services.whatsapp_service import WhatsAppService


def make_service() -> WhatsAppService:
    """Helper to create a WhatsAppService with minimal configuration."""
    settings = Settings(WAHA_BASE_URL="http://localhost:3000")
    return WhatsAppService(settings=settings)


def test_extract_ingredients_parses_unique_tokens():
    service = make_service()
    text = "Ingredientes: Aqua, Glycerin; Parfum - Sodium Chloride"

    ingredients = service._extract_ingredients(text)  # pylint: disable=protected-access

    assert "Aqua" in ingredients
    assert "Glycerin" in ingredients
    assert "Parfum" in ingredients
    assert len(ingredients) == len(set(ingredient.lower() for ingredient in ingredients))


def test_build_reply_message_success():
    service = make_service()
    analysis = {
        "success": True,
        "overall_score": 82.3,
        "ingredients_analysis": [
            {"name": "Aqua", "score": 90, "safety_level": "seguro"},
            {"name": "Glycerin", "score": 85, "safety_level": "seguro"},
        ],
        "recommendations": ["Adecuado para piel normal."],
    }

    message = service._build_reply_message(  # pylint: disable=protected-access
        analysis=analysis,
        extracted_text="Aqua, Glycerin",
    )

    assert message is not None
    assert "Aqua" in message
    assert "82.3" in message
    assert "Recomendaciones" in message


def test_build_error_message_no_ingredients():
    service = make_service()
    analysis = {"success": False, "error": "no_ingredients"}

    response = service._build_reply_message(  # pylint: disable=protected-access
        analysis=analysis,
        extracted_text=None,
    )

    assert "No encontré ingredientes" in response
