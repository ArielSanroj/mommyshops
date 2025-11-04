"""
Endpoints for creating personalized cosmetic products based on analysis results.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.models import CustomProduct, User
from app.dependencies import get_database, optional_auth, require_auth
from app.schemas.builder import CustomProductCreate, CustomProductResponse

router = APIRouter(prefix="/builder", tags=["builder"])


def _estimate_price(substitution_count: int, safe_count: int) -> float:
    base_price = 28.0
    return round(base_price + substitution_count * 5 + safe_count * 1.5, 2)


@router.post("/products", response_model=CustomProductResponse, status_code=status.HTTP_201_CREATED)
async def create_custom_product(
    payload: CustomProductCreate,
    current_user: User = Depends(optional_auth),
    db: Session = Depends(get_database),
) -> CustomProductResponse:
    """
    Store a personalized product configuration so the user can request or purchase it later.
    """
    substitution_count = len(payload.substitutions)
    safe_count = len(payload.safe_ingredients)
    price = _estimate_price(substitution_count, safe_count)

    custom_product = CustomProduct(
        user_id=current_user.id if current_user else None,
        base_product_name=payload.base_product_name,
        safe_ingredients=payload.safe_ingredients,
        substitutions=[selection.dict() for selection in payload.substitutions],
        profile_snapshot=payload.profile or {},
        labs_formula=payload.labs_formula or [],
        labs_summary=payload.labs_summary or {},
        labs_mockup=payload.labs_mockup or {},
        price=price,
        status="pending" if current_user else "draft",
    )

    try:
        db.add(custom_product)
        db.commit()
        db.refresh(custom_product)
        
        # Convert to response model manually to ensure proper serialization
        return CustomProductResponse(
            id=custom_product.id,
            base_product_name=custom_product.base_product_name,
            safe_ingredients=custom_product.safe_ingredients or [],
            substitutions=custom_product.substitutions or [],
            profile_snapshot=custom_product.profile_snapshot or {},
            labs_formula=custom_product.labs_formula or [],
            labs_summary=custom_product.labs_summary or {},
            labs_mockup=custom_product.labs_mockup or {},
            price=custom_product.price,
            status=custom_product.status,
            created_at=custom_product.created_at
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating custom product: {str(e)}"
        )


@router.get("/products", response_model=List[CustomProductResponse])
async def list_custom_products(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_database),
) -> List[CustomProductResponse]:
    """
    List personalized products created by the authenticated user.
    """
    products = (
        db.query(CustomProduct)
        .filter(CustomProduct.user_id == current_user.id)
        .order_by(CustomProduct.created_at.desc())
        .all()
    )
    return [
        CustomProductResponse(
            id=p.id,
            base_product_name=p.base_product_name,
            safe_ingredients=p.safe_ingredients or [],
            substitutions=p.substitutions or [],
            profile_snapshot=p.profile_snapshot or {},
            labs_formula=p.labs_formula or [],
            labs_summary=p.labs_summary or {},
            labs_mockup=p.labs_mockup or {},
            price=p.price,
            status=p.status,
            created_at=p.created_at
        )
        for p in products
    ]


@router.get("/products/{product_id}", response_model=CustomProductResponse)
async def get_custom_product(
    product_id: int,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_database),
) -> CustomProductResponse:
    """
    Retrieve a specific personalized product.
    """
    product = db.query(CustomProduct).filter(CustomProduct.id == product_id).first()
    if not product or product.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return CustomProductResponse(
        id=product.id,
        base_product_name=product.base_product_name,
        safe_ingredients=product.safe_ingredients or [],
        substitutions=product.substitutions or [],
        profile_snapshot=product.profile_snapshot or {},
        labs_formula=product.labs_formula or [],
        labs_summary=product.labs_summary or {},
        labs_mockup=product.labs_mockup or {},
        price=product.price,
        status=product.status,
        created_at=product.created_at
    )
