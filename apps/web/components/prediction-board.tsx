"use client";

import { useEffect, useMemo, useState } from "react";

import { MatchTable } from "@/components/match-table";
import type { PredictionRow } from "@/lib/mock-data";

type ApiMatch = {
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
};

type MatchListResponse = {
  matches: ApiMatch[];
};

type PredictionResponse = {
  match: ApiMatch;
  p_home_win: number;
  p_draw: number;
  p_away_win: number;
  most_likely_scores: { score: string; p: number }[];
  recommended_tip: { score: string; expected_points: number; explanation: string };
};

type PredictionBoardProps = {
  limit?: number;
};

export function PredictionBoard({ limit = 12 }: PredictionBoardProps) {
  const [rows, setRows] = useState<PredictionRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadPredictions() {
      setLoading(true);
      setError(null);

      const baseUrl = apiBaseUrl();
      try {
        const matchesResponse = await fetch(`${baseUrl}/api/matches`, { cache: "no-store" });
        if (!matchesResponse.ok) {
          throw new Error("Match feed unavailable");
        }

        const matchesPayload = (await matchesResponse.json()) as MatchListResponse;
        const candidates = matchesPayload.matches
          .filter((match) => match.home_team.name !== "TBD" && match.away_team.name !== "TBD")
          .slice(0, limit);

        const predictionPayloads = await Promise.all(
          candidates.map(async (match) => {
            const response = await fetch(`${baseUrl}/api/matches/${match.id}/prediction`, {
              cache: "no-store"
            });
            if (!response.ok) {
              throw new Error(`Prediction unavailable for match ${match.id}`);
            }
            return (await response.json()) as PredictionResponse;
          })
        );

        if (!cancelled) {
          setRows(predictionPayloads.map(toPredictionRow));
        }
      } catch (caught) {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "Failed to load predictions");
          setRows([]);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadPredictions();
    return () => {
      cancelled = true;
    };
  }, [limit]);

  const content = useMemo(() => {
    if (loading) {
      return (
        <div className="border border-terminal-line bg-terminal-panel p-4 text-sm text-terminal-muted">
          Loading live predictions...
        </div>
      );
    }

    if (error) {
      return (
        <div className="border border-terminal-red bg-terminal-panel p-4 text-sm text-terminal-red">
          {error}
        </div>
      );
    }

    if (rows.length === 0) {
      return (
        <div className="border border-terminal-line bg-terminal-panel p-4 text-sm text-terminal-muted">
          No prediction rows are available yet.
        </div>
      );
    }

    return <MatchTable rows={rows} />;
  }, [error, loading, rows]);

  return content;
}

function toPredictionRow(prediction: PredictionResponse): PredictionRow {
  const match = prediction.match;
  const model: [number, number, number] = [
    prediction.p_home_win,
    prediction.p_draw,
    prediction.p_away_win
  ];
  const strongestOutcome = Math.max(...model);

  return {
    id: match.id,
    date: new Date(match.date).toLocaleString(),
    stage: match.group_name ?? match.stage,
    match: `${match.home_team.name} vs ${match.away_team.name}`,
    model,
    market: model,
    bestTip: `${prediction.recommended_tip.score} (${prediction.recommended_tip.expected_points.toFixed(2)} EV)`,
    mostLikelyScore: prediction.most_likely_scores[0]?.score ?? "-",
    confidence: strongestOutcome >= 0.5 ? "High" : strongestOutcome >= 0.4 ? "Medium" : "Low",
    disagreement: 0
  };
}

function apiBaseUrl() {
  return (process.env.NEXT_PUBLIC_API_BASE_URL ?? "").replace(/\/$/, "");
}
