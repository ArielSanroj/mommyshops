"""
Service layer for handling WhatsApp (WAHA) webhooks and responses.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import httpx
from sqlalchemy.orm import Session
from waha import AsyncWahaClient
from waha.exceptions import WahaException

from app.schemas.whatsapp import WhatsAppMessagePayload, WhatsAppWebhookEvent
from app.services.ingredient_service import IngredientService
from app.services.ocr_service import OCRService
from core.config import Settings
from pydantic import ValidationError


logger = logging.getLogger(__name__)


class WhatsAppService:
    """Business logic for WhatsApp webhook handling."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.ocr_service = OCRService()
        self.logger = logger

    async def handle_webhook(
        self,
        event: WhatsAppWebhookEvent,
        db: Session,
    ) -> Dict[str, Any]:
        """Process an incoming WAHA webhook event."""
        if event.event != "message":
            return {"status": "ignored", "reason": f"unsupported_event:{event.event}"}

        try:
            message = WhatsAppMessagePayload.model_validate(event.payload)
        except ValidationError as exc:
            self.logger.warning("Invalid WhatsApp webhook payload: %s", exc)
            return {"status": "ignored", "reason": "invalid_payload"}

        if message.fromMe:
            return {"status": "ignored", "reason": "outgoing_message"}

        session_name = event.session or self.settings.WAHA_DEFAULT_SESSION
        chat_id = message.from_ or message.chatId
        if not chat_id:
            return {"status": "ignored", "reason": "missing_chat_id"}

        analysis_result: Dict[str, Any]
        extracted_text: Optional[str] = None

        async with self._create_client() as client:
            if self._is_image_message(message):
                analysis_result, extracted_text = await self._handle_image_message(
                    client=client,
                    session=session_name,
                    message=message,
                    db=db,
                    user_id=chat_id,
                )
            else:
                analysis_result = await self._analyze_text_message(
                    message=message,
                    db=db,
                    user_id=chat_id,
                )

            reply_text = self._build_reply_message(
                analysis=analysis_result,
                extracted_text=extracted_text,
            )

            if reply_text:
                await self._send_text_reply(
                    client=client,
                    session=session_name,
                    chat_id=chat_id,
                    text=reply_text,
                    reply_to=message.id,
                )

        return {
            "status": "processed",
            "analysis": analysis_result,
            "extracted_text": extracted_text,
        }

    async def _handle_image_message(
        self,
        client: AsyncWahaClient,
        session: str,
        message: WhatsAppMessagePayload,
        db: Session,
        user_id: str,
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """Download image, run OCR, and analyze extracted text."""
        media_bytes = await self._download_media(client, session=session, message=message)
        if not media_bytes:
            return {"success": False, "error": "media_download_failed"}, None

        extracted_text = await self.ocr_service.extract_text_from_image(media_bytes)
        if not extracted_text:
            return {"success": False, "error": "ocr_failed"}, None

        analysis_result = await self._analyze_text(
            text=extracted_text,
            db=db,
            user_id=user_id,
        )
        return analysis_result, extracted_text

    async def _analyze_text_message(
        self,
        message: WhatsAppMessagePayload,
        db: Session,
        user_id: str,
    ) -> Dict[str, Any]:
        """Analyze a plain text WhatsApp message."""
        text = (message.body or "").strip()
        return await self._analyze_text(text=text, db=db, user_id=user_id)

    async def _analyze_text(
        self,
        text: str,
        db: Session,
        user_id: str,
    ) -> Dict[str, Any]:
        """Analyze text for ingredient safety."""
        if not text or len(text.strip()) < 5:
            return {"success": False, "error": "insufficient_text", "source_text": text}

        ingredients = self._extract_ingredients(text)
        if not ingredients:
            return {"success": False, "error": "no_ingredients", "source_text": text}

        ingredient_service = IngredientService(db)
        try:
            analysis = await ingredient_service.analyze_ingredients(
                ingredients=ingredients,
                user_id=user_id,
                user_concerns=None,
            )
        except Exception as exc:  # pylint: disable=broad-except
            self.logger.error("Ingredient analysis failed: %s", exc)
            return {"success": False, "error": "analysis_failed", "source_text": text}

        analysis["ingredients"] = ingredients
        analysis["source_text"] = text
        return analysis

    async def _download_media(
        self,
        client: AsyncWahaClient,
        session: str,
        message: WhatsAppMessagePayload,
    ) -> Optional[bytes]:
        """Download media bytes for a WhatsApp message."""
        try:
            result = await client.media.download(message_id=message.id, session=session)
        except WahaException as exc:
            self.logger.error("WAHA media download failed: %s", exc)
            result = {}

        if not result:
            result = {}

        content = result.get("content")
        if isinstance(content, (bytes, bytearray)):
            return bytes(content)

        media_info = result.get("media") or {}
        url = media_info.get("url") or result.get("url")
        if not url and message.media and isinstance(message.media, dict):
            media_url = message.media.get("url")
            if isinstance(media_url, str):
                url = media_url

        if not url:
            return None

        headers = {}
        if self.settings.WAHA_API_KEY:
            headers["X-Api-Key"] = self.settings.WAHA_API_KEY

        try:
            async with httpx.AsyncClient(timeout=30) as http_client:
                response = await http_client.get(url, headers=headers)
                response.raise_for_status()
                return response.content
        except httpx.HTTPError as exc:
            self.logger.error("Failed to download media bytes: %s", exc)
            return None

    async def _send_text_reply(
        self,
        client: AsyncWahaClient,
        session: str,
        chat_id: str,
        text: str,
        reply_to: Optional[str] = None,
    ) -> None:
        """Send a text reply via WAHA."""
        sanitized = text.strip()
        if len(sanitized) > 3500:
            sanitized = sanitized[:3497] + "..."

        try:
            await client.messages.send_text(
                chat_id=chat_id,
                text=sanitized,
                session=session or self.settings.WAHA_DEFAULT_SESSION,
                reply_to=reply_to,
            )
        except WahaException as exc:
            self.logger.error("Failed to send WhatsApp reply: %s", exc)

    def _build_reply_message(
        self,
        analysis: Dict[str, Any],
        extracted_text: Optional[str] = None,
    ) -> Optional[str]:
        """Build a WhatsApp-friendly reply message."""
        if not analysis or not analysis.get("success"):
            return self._build_error_message(analysis)

        overall_score = analysis.get("overall_score")
        ingredients_analysis = analysis.get("ingredients_analysis") or []
        recommendations = analysis.get("recommendations") or []

        lines = ["🔍 Análisis de ingredientes"]
        if isinstance(overall_score, (int, float)):
            lines.append(f"Puntaje promedio: {overall_score:.1f}/100")

        if ingredients_analysis:
            lines.append("")
            lines.append("Ingredientes evaluados:")
            for ingredient in ingredients_analysis[:5]:
                name = ingredient.get("name", "Desconocido")
                score = ingredient.get("score")
                safety = ingredient.get("safety_level", "desconocido")
                score_text = f"{score:.0f}" if isinstance(score, (int, float)) else "?"
                lines.append(f"- {name}: {safety} ({score_text}/100)")
            if len(ingredients_analysis) > 5:
                remaining = len(ingredients_analysis) - 5
                lines.append(f"... y {remaining} ingredientes más.")

        if recommendations:
            lines.append("")
            lines.append("Recomendaciones:")
            for recommendation in recommendations[:3]:
                lines.append(f"- {recommendation}")

        if extracted_text:
            snippet = extracted_text.strip()
            if len(snippet) > 180:
                snippet = snippet[:177].rstrip() + "..."
            if snippet:
                lines.append("")
                lines.append(f"Texto detectado: {snippet}")

        lines.append("")
        lines.append("Envía otra foto o lista de ingredientes cuando quieras. 😊")

        return "\n".join(lines)

    def _build_error_message(self, analysis: Optional[Dict[str, Any]]) -> Optional[str]:
        """Create a user-friendly error message."""
        if not analysis:
            return "No pude procesar tu mensaje. Intenta nuevamente o envía una lista de ingredientes."

        error = analysis.get("error")
        if error == "insufficient_text":
            return (
                "Necesito más detalles para ayudarte. "
                "Envía la lista completa de ingredientes o comparte una foto clara de la etiqueta."
            )
        if error == "no_ingredients":
            return (
                "No encontré ingredientes en el mensaje. "
                "Asegúrate de separarlos por comas o envía una imagen nítida de la etiqueta."
            )
        if error == "media_download_failed":
            return (
                "No pude descargar la imagen. Por favor, reenvíala o intenta con una foto diferente."
            )
        if error == "ocr_failed":
            return (
                "No logré leer el texto en la imagen. Intenta tomar la foto con mejor iluminación."
            )
        if error == "analysis_failed":
            return "Ocurrió un error al analizar los ingredientes. Intenta nuevamente en unos minutos."

        return (
            "No pude analizar el mensaje. Envía la lista de ingredientes o una foto clara de la etiqueta."
        )

    def _extract_ingredients(self, text: str) -> List[str]:
        """Extract potential ingredient names from free text."""
        cleaned = text.replace("\r", " ").replace("\n", " ")
        cleaned = re.sub(r"\b(ingredientes?|contains?|lista)\b[:\-]?", " ", cleaned, flags=re.IGNORECASE)

        candidates = re.split(r"[;,•\-\|]+", cleaned)
        ingredients: List[str] = []
        seen = set()

        for candidate in candidates:
            name = candidate.strip()
            if not name or len(name) < 3:
                continue

            name = re.sub(r"[^A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ\s\-/]", "", name).strip()
            lowered = name.lower()

            if lowered in {"y", "and", "con", "de", "the", "para"}:
                continue

            if lowered not in seen:
                seen.add(lowered)
                ingredients.append(name)

        return ingredients

    def _is_image_message(self, message: WhatsAppMessagePayload) -> bool:
        """Determine if message contains an analyzable image."""
        if not message.hasMedia:
            return False

        mimetype = ""
        if message.media and isinstance(message.media, dict):
            mimetype = (message.media.get("mimetype") or "").lower()

        if not mimetype and message.type:
            mimetype = message.type.lower()

        return mimetype.startswith("image") or message.type == "image"

    def _create_client(self) -> AsyncWahaClient:
        """Create a configured WAHA async client."""
        if not self.settings.WAHA_BASE_URL:
            raise RuntimeError("WAHA_BASE_URL is not configured")
        return AsyncWahaClient(
            base_url=self.settings.WAHA_BASE_URL,
            api_key=self.settings.WAHA_API_KEY,
            timeout=30.0,
        )
