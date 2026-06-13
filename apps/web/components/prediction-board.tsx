"use client";

import { useEffect, useMemo, useState } from "react";

import { MatchTable } from "@/components/match-table";
import type { PredictionRow } from "@/lib/mock-data";
import { apiBaseUrl, formatKickoff, type PredictionResponse } from "@/lib/predictions";

type PredictionBoardProps = {
  limit?: number | null;
  showControls?: boolean;
};

export function PredictionBoard({ limit = 12, showControls = false }: PredictionBoardProps) {
  const [rows, setRows] = useState<PredictionRow[]>([]);
  const [stageFilter, setStageFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadPredictions() {
      setLoading(true);
      setError(null);

      const baseUrl = apiBaseUrl();
      try {
        const predictionsResponse = await fetch(`${baseUrl}/api/predictions`, { cache: "no-store" });
        if (!predictionsResponse.ok) {
          throw new Error("Prediction feed unavailable");
        }

        const predictionsPayload = (await predictionsResponse.json()) as { predictions: PredictionResponse[] };
        const predictionPayloads = limit === null
          ? predictionsPayload.predictions
          : predictionsPayload.predictions.slice(0, limit);

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

  const stageOptions = useMemo(
    () => ["all", ...Array.from(new Set(rows.map((row) => row.stage))).filter(Boolean)],
    [rows]
  );
  const visibleRows = useMemo(
    () => rows.filter((row) => stageFilter === "all" || row.stage === stageFilter),
    [rows, stageFilter]
  );

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

    return (
      <div className="space-y-3">
        {showControls ? (
          <div className="flex flex-wrap items-center justify-between gap-2 border border-terminal-line bg-terminal-panel p-3">
            <div className="text-sm text-terminal-muted">
              Showing {visibleRows.length} of {rows.length} predicted matches.
            </div>
            <label className="flex items-center gap-2 text-sm text-terminal-muted">
              Stage
              <select
                className="h-9 border border-terminal-line bg-terminal-bg px-2 font-mono text-terminal-ink"
                value={stageFilter}
                onChange={(event) => setStageFilter(event.target.value)}
              >
                {stageOptions.map((stage) => (
                  <option key={stage} value={stage}>
                    {stage === "all" ? "All stages" : stage}
                  </option>
                ))}
              </select>
            </label>
          </div>
        ) : null}
        <MatchTable rows={visibleRows} />
      </div>
    );
  }, [error, loading, rows, showControls, stageFilter, stageOptions, visibleRows]);

  return content;
}

function toPredictionRow(prediction: PredictionResponse): PredictionRow {
  const match = prediction.match;
  const model: [number, number, number] = [
    prediction.p_home_win,
    prediction.p_draw,
    prediction.p_away_win
  ];

  return {
    id: match.id,
    date: formatKickoff(match.date),
    stage: match.group_name ?? match.stage,
    match: `${match.home_team.name} vs ${match.away_team.name}`,
    actualScore: prediction.recommended_tip.actual_score,
    status: match.status,
    model,
    market: model,
    bestTip: `${prediction.recommended_tip.score} (${prediction.recommended_tip.expected_points.toFixed(2)} EV)`,
    actualPoints: prediction.recommended_tip.actual_points,
    mostLikelyScore: prediction.most_likely_scores[0]?.score ?? "-",
    confidence: prediction.confidence.label,
    confidenceScore: prediction.confidence.score,
    confidenceReason: prediction.confidence.reason,
    homeElo: prediction.home_rating.model_elo,
    awayElo: prediction.away_rating.model_elo,
    homeRatingKnown: prediction.home_rating.known_rating,
    awayRatingKnown: prediction.away_rating.known_rating,
    ratingDelta: prediction.rating_delta,
    expectedGoals: `${prediction.lambda_home.toFixed(2)}-${prediction.lambda_away.toFixed(2)}`,
    modelVersion: prediction.model_context.model_version,
    explanation: prediction.model_context.explanation,
    disagreement: 0
  };
}
