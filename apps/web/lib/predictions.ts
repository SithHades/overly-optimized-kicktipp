export type ApiMatch = {
  id: number;
  source: string | null;
  source_match_id: string | null;
  date: string;
  stage: string;
  group_name: string | null;
  home_team: { id: number | null; name: string };
  away_team: { id: number | null; name: string };
  venue: string | null;
  status: string;
  home_score: number | null;
  away_score: number | null;
};

export type TipCandidate = {
  score: string;
  expected_points: number;
  exact_probability: number;
  label: string;
  rationale: string;
  actual_points: number | null;
};

export type PredictionResponse = {
  match: ApiMatch;
  p_home_win: number;
  p_draw: number;
  p_away_win: number;
  lambda_home: number;
  lambda_away: number;
  most_likely_scores: { score: string; p: number }[];
  recommended_tip: {
    score: string;
    expected_points: number;
    explanation: string;
    actual_points: number | null;
    actual_score: string | null;
  };
  tip_candidates: TipCandidate[];
  home_rating: { model_elo: number; strength_score: number; tier: string; known_rating: boolean };
  away_rating: { model_elo: number; strength_score: number; tier: string; known_rating: boolean };
  rating_delta: number;
  confidence: { label: "Low" | "Medium" | "High"; score: number; reason: string };
  model_context: {
    model_version: string;
    data_source: string;
    training_status: string;
    rating_source: string;
    explanation: string[];
  };
  model_notes: string[];
};

export type ScoringRules = {
  exactScore: number;
  goalDiff: number;
  result: number;
};

export function apiBaseUrl() {
  return (process.env.NEXT_PUBLIC_API_BASE_URL ?? "").replace(/\/$/, "");
}

export function formatPercent(value: number) {
  return `${Math.round(value * 100)}%`;
}

export function formatKickoff(value: string) {
  return new Date(value).toLocaleString();
}

export function favoriteLabel(prediction: PredictionResponse) {
  const outcomes = [
    { label: prediction.match.home_team.name, value: prediction.p_home_win },
    { label: "Draw", value: prediction.p_draw },
    { label: prediction.match.away_team.name, value: prediction.p_away_win }
  ];
  return outcomes.sort((a, b) => b.value - a.value)[0];
}

export function conservativePriorPick(prediction: PredictionResponse) {
  const delta = prediction.rating_delta;
  if (Math.abs(delta) < 75) {
    return "1-1";
  }
  return delta > 0 ? "1-0" : "0-1";
}

export function candidateByScore(prediction: PredictionResponse, score: string) {
  return prediction.tip_candidates.find((candidate) => candidate.score === score) ?? null;
}
