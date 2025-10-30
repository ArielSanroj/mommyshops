"""
Pydantic schemas for WhatsApp (WAHA) integration.
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class WhatsAppMessagePayload(BaseModel):
    """Schema for incoming WhatsApp message payload."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: str
    timestamp: int
    from_: str = Field(alias="from")
    fromMe: bool
    to: Optional[str] = None
    chatId: Optional[str] = None
    body: Optional[str] = None
    type: Optional[str] = None
    hasMedia: Optional[bool] = False
    media: Optional[Dict[str, Any]] = None
    mediaUrl: Optional[str] = None
    ack: Optional[int] = None


class WhatsAppWebhookEvent(BaseModel):
    """Schema for WAHA webhook event."""

    model_config = ConfigDict(extra="allow")

    id: str
    timestamp: int
    session: str
    event: str
    payload: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    engine: Optional[str] = None
    me: Optional[Dict[str, Any]] = None
    environment: Optional[Dict[str, Any]] = None
