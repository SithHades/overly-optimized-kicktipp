import os

from fastapi import APIRouter, HTTPException, status

from worldcup_api.services.tournament_tips import read_tournament_tips

router = APIRouter(tags=["tournament-tips"])


@router.get("/tournament-tips")
def get_tournament_tips() -> dict:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DATABASE_URL is not configured",
        )
    return read_tournament_tips(database_url)
