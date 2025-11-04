"""
Mommyshops Labs formulation endpoints.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import optional_auth
from app.database.models import User
from app.schemas.formulation import FormulateRequest, FormulateResponse
from app.services.formulation_service import FormulationService

router = APIRouter(tags=["formulation"])
formulation_service = FormulationService()


def _user_profile_snapshot(user: Optional[User]) -> Optional[dict]:
    if not user:
        return None
    return {
        "skin_type": getattr(user, "skin_face", None),
        "hair_type": getattr(user, "hair_type", None),
        "concerns": (user.goals_face or []) + (user.goals_hair or []),
        "goals": user.conditions or [],
    }


@router.post("/formulate", response_model=FormulateResponse, status_code=status.HTTP_200_OK)
async def formulate_formula(
    payload: FormulateRequest,
    current_user: Optional[User] = Depends(optional_auth),
) -> FormulateResponse:
    """
    Generate a personalized Mommyshops Labs formula from detected ingredients + profile context.
    """
    try:
        incoming_profile = payload.profile.dict(exclude_unset=True) if payload.profile else None
        if not incoming_profile:
            incoming_profile = _user_profile_snapshot(current_user)

        result = formulation_service.generate_formula(
            profile=incoming_profile,
            detected_ingredients=payload.ingredients_detected,
            variant=payload.variant,
            product_name=payload.product_name,
            budget=payload.budget,
        )
        return FormulateResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:  # pragma: no cover - safeguard
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


# Compatibility alias: /api/formulate
router.add_api_route(
    "/api/formulate",
    formulate_formula,
    methods=["POST"],
    response_model=FormulateResponse,
    include_in_schema=False,
)
