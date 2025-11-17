"""
Leads router
Handles lead/signup form submissions
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
import logging

from app.dependencies import get_database, require_admin
from app.database.models import Lead, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/leads", tags=["leads"])


class LeadCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    email: EmailStr = Field(..., description="Email address")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")
    country: str = Field(..., min_length=2, max_length=10, description="Country code")


class LeadResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    phone: Optional[str]
    country: str
    created_at: str

    class Config:
        from_attributes = True


@router.post("/", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead_data: LeadCreate,
    db: Session = Depends(get_database)
):
    """Create a new lead from signup form"""
    try:
        # Check if lead with this email already exists
        existing_lead = db.query(Lead).filter(Lead.email == lead_data.email).first()
        
        if existing_lead:
            logger.info(f"Lead already exists with email: {lead_data.email}")
            # Return existing lead instead of raising error
            return LeadResponse(
                id=existing_lead.id,
                first_name=existing_lead.first_name,
                last_name=existing_lead.last_name,
                email=existing_lead.email,
                phone=existing_lead.phone,
                country=existing_lead.country,
                created_at=existing_lead.created_at.isoformat()
            )
        
        # Create new lead
        lead = Lead(
            first_name=lead_data.first_name,
            last_name=lead_data.last_name,
            email=lead_data.email,
            phone=lead_data.phone,
            country=lead_data.country
        )
        
        db.add(lead)
        db.commit()
        db.refresh(lead)
        
        logger.info(f"Lead created: {lead.email} ({lead.first_name} {lead.last_name})")
        
        return LeadResponse(
            id=lead.id,
            first_name=lead.first_name,
            last_name=lead.last_name,
            email=lead.email,
            phone=lead.phone,
            country=lead.country,
            created_at=lead.created_at.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Lead creation failed: {e}", exc_info=True)
        db.rollback()
        error_detail = str(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create lead: {error_detail}"
        )


@router.get("/", response_model=List[LeadResponse])
async def list_leads(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of leads to return"),
    offset: int = Query(0, ge=0, description="Number of leads to skip"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_database)
):
    """List all leads (admin only)"""
    try:
        leads = (
            db.query(Lead)
            .order_by(Lead.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        
        total = db.query(Lead).count()
        
        return [
            LeadResponse(
                id=lead.id,
                first_name=lead.first_name,
                last_name=lead.last_name,
                email=lead.email,
                phone=lead.phone,
                country=lead.country,
                created_at=lead.created_at.isoformat()
            )
            for lead in leads
        ]
        
    except Exception as e:
        logger.error(f"Failed to list leads: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list leads"
        )


@router.get("/stats")
async def get_leads_stats(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_database)
):
    """Get leads statistics (admin only)"""
    try:
        total_leads = db.query(Lead).count()
        
        # Count by country
        from sqlalchemy import func
        country_counts = (
            db.query(Lead.country, func.count(Lead.id).label('count'))
            .group_by(Lead.country)
            .all()
        )
        
        return {
            "total": total_leads,
            "by_country": {country: count for country, count in country_counts}
        }
        
    except Exception as e:
        logger.error(f"Failed to get leads stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get leads statistics"
        )

