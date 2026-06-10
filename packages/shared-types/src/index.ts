export type ScoreProbability = {
  score: string;
  p: number;
};

export type RecommendedTip = {
  score: string;
  expected_points: number;
  explanation: string;
};

export type PredictionResponse = {
  match: {
    id: number;
    date: string;
    stage: string;
    home_team: { id?: number | null; name: string };
    away_team: { id?: number | null; name: string };
  };
  p_home_win: number;
  p_draw: number;
  p_away_win: number;
  lambda_home: number;
  lambda_away: number;
  most_likely_scores: ScoreProbability[];
  recommended_tip: RecommendedTip;
  model_notes: string[];
};
