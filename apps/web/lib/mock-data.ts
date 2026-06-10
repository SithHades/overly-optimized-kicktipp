export type PredictionRow = {
  id: number;
  date: string;
  stage: string;
  match: string;
  model: [number, number, number];
  market: [number, number, number];
  bestTip: string;
  mostLikelyScore: string;
  confidence: "Low" | "Medium" | "High";
  disagreement: number;
};

export const predictionRows: PredictionRow[] = [
  {
    id: 1,
    date: "2026-06-11 21:00",
    stage: "Group A",
    match: "Germany vs Japan",
    model: [0.48, 0.27, 0.25],
    market: [0.52, 0.25, 0.23],
    bestTip: "2-1",
    mostLikelyScore: "1-1",
    confidence: "Medium",
    disagreement: 0.04
  },
  {
    id: 2,
    date: "2026-06-12 18:00",
    stage: "Group B",
    match: "Brazil vs Denmark",
    model: [0.57, 0.24, 0.19],
    market: [0.61, 0.23, 0.16],
    bestTip: "2-0",
    mostLikelyScore: "1-0",
    confidence: "High",
    disagreement: 0.04
  },
  {
    id: 3,
    date: "2026-06-12 23:00",
    stage: "Group C",
    match: "Uruguay vs Mexico",
    model: [0.41, 0.29, 0.3],
    market: [0.35, 0.31, 0.34],
    bestTip: "1-1",
    mostLikelyScore: "1-1",
    confidence: "Low",
    disagreement: 0.06
  }
];

export const stageProbabilities = [
  { team: "Brazil", winner: 0.174, final: 0.302, semifinal: 0.471 },
  { team: "Argentina", winner: 0.141, final: 0.266, semifinal: 0.43 },
  { team: "France", winner: 0.126, final: 0.244, semifinal: 0.401 },
  { team: "Spain", winner: 0.097, final: 0.197, semifinal: 0.342 },
  { team: "Germany", winner: 0.045, final: 0.1, semifinal: 0.2 }
];
