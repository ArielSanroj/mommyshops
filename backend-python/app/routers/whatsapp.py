"""
WhatsApp webhook router for WAHA integration.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_database, get_whatsapp_service
from app.schemas.whatsapp import WhatsAppWebhookEvent
from app.services.whatsapp_service import WhatsAppService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
)
async def whatsapp_webhook(
    payload: WhatsAppWebhookEvent,
    db: Session = Depends(get_database),
    whatsapp_service: WhatsAppService = Depends(get_whatsapp_service),
):
    """
    Handle incoming WhatsApp webhook events from WAHA.
    """
    try:
        result = await whatsapp_service.handle_webhook(event=payload, db=db)
    except RuntimeError as exc:
        logger.error("WhatsApp integration misconfiguration: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="WhatsApp integration not configured",
        ) from exc
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Failed to process WhatsApp webhook: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process WhatsApp event",
        ) from exc

    return {"status": "ok", "result": result}
