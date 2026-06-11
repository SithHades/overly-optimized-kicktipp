MODEL_VERSION = "baseline-strength-v2"
MODEL_TRAINING_STATUS = "Not trained yet; deterministic baseline using public fixtures and model ratings."
RATING_SOURCE = "Seeded team-strength prior, not a learned Elo history."

TEAM_STRENGTH: dict[str, float] = {
    "Argentina": 97,
    "France": 96,
    "Brazil": 95,
    "England": 94,
    "Spain": 93,
    "Portugal": 92,
    "Netherlands": 90,
    "Germany": 89,
    "Belgium": 87,
    "Uruguay": 86,
    "Croatia": 85,
    "Italy": 84,
    "Morocco": 83,
    "Colombia": 82,
    "Japan": 81,
    "Mexico": 80,
    "Switzerland": 79,
    "United States": 78,
    "Denmark": 78,
    "Senegal": 77,
    "Austria": 76,
    "South Korea": 75,
    "Ecuador": 75,
    "Australia": 73,
    "Czechia": 73,
    "Turkey": 73,
    "Canada": 72,
    "Scotland": 72,
    "South Africa": 70,
    "Ghana": 70,
    "Algeria": 70,
    "Tunisia": 69,
    "Egypt": 69,
    "Qatar": 68,
    "Saudi Arabia": 68,
    "Iran": 68,
    "Norway": 68,
    "Bosnia-Herzegovina": 67,
    "Paraguay": 67,
    "Ivory Coast": 67,
    "Uzbekistan": 66,
    "Sweden": 66,
    "New Zealand": 63,
    "Panama": 62,
    "Haiti": 60,
    "Cape Verde Islands": 60,
    "Congo DR": 59,
    "Curaçao": 58,
    "Jordan": 58,
    "Iraq": 58,
    "TBD": 50,
}

TEAM_ALIASES = {
    "USA": "United States",
    "United States of America": "United States",
    "Bosnia & Herzegovina": "Bosnia-Herzegovina",
    "Bosnia and Herzegovina": "Bosnia-Herzegovina",
    "Cape Verde": "Cape Verde Islands",
    "Côte d'Ivoire": "Ivory Coast",
    "Cote d'Ivoire": "Ivory Coast",
    "DR Congo": "Congo DR",
    "Czech Republic": "Czechia",
    "Curacao": "Curaçao",
}


def canonical_team_name(team: str) -> str:
    return TEAM_ALIASES.get(team, team)


def strength_score(team: str) -> float:
    return TEAM_STRENGTH.get(canonical_team_name(team), 64.0)


def model_elo(team: str) -> int:
    return round(1200 + strength_score(team) * 8)


def rating_tier(team: str) -> str:
    score = strength_score(team)
    if score >= 92:
        return "favorite"
    if score >= 84:
        return "contender"
    if score >= 74:
        return "solid"
    if score >= 64:
        return "outsider"
    return "long shot"


def rating_known(team: str) -> bool:
    return canonical_team_name(team) in TEAM_STRENGTH


def estimate_lambdas(home_team: str, away_team: str) -> tuple[float, float]:
    home_strength = strength_score(home_team)
    away_strength = strength_score(away_team)
    rating_delta = (home_strength - away_strength) / 25.0
    lambda_home = 1.24 + rating_delta * 0.28
    lambda_away = 1.12 - rating_delta * 0.22
    return max(0.45, min(2.7, lambda_home)), max(0.35, min(2.5, lambda_away))


def rating_source_note(home_team: str, away_team: str) -> str:
    unknown = [team for team in [home_team, away_team] if not rating_known(team)]
    if unknown:
        return f"{RATING_SOURCE} Neutral fallback used for: {', '.join(unknown)}."
    return RATING_SOURCE
