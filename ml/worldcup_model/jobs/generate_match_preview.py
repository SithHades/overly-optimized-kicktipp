from worldcup_model.ai.match_preview_agent import generate_match_preview


def main(home_team: str, away_team: str) -> dict:
    preview = generate_match_preview(home_team, away_team)
    return preview.model_dump()
