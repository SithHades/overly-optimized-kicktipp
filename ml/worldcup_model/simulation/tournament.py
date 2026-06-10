from dataclasses import dataclass


@dataclass(frozen=True)
class TeamStageProbability:
    team: str
    group_winner: float = 0.0
    advance_group: float = 0.0
    round_of_16: float = 0.0
    quarter_final: float = 0.0
    semi_final: float = 0.0
    final: float = 0.0
    winner: float = 0.0


def empty_tournament_projection(teams: list[str]) -> dict[str, TeamStageProbability]:
    return {team: TeamStageProbability(team=team) for team in teams}
