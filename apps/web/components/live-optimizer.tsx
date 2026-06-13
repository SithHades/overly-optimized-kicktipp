"use client";

import Link from "next/link";
import { ArrowUpRight, BrainCircuit, Calculator, GitCompareArrows, Radar, Shield, Target } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { ProbabilityStrip } from "@/components/probability-strip";
import { Badge } from "@/components/ui/badge";
import {
  apiBaseUrl,
  candidateByScore,
  conservativePriorPick,
  favoriteLabel,
  formatKickoff,
  formatPercent,
  type PredictionResponse
} from "@/lib/predictions";

type MatchPreview = {
  fixture: string;
  tactical_preview: string;
  key_factors: string[];
  upset_scenario: string;
  injury_watch: string[];
  source_urls: string[];
  confidence: number;
};

const previewProgressPhases = [
  { delay: 0, message: "Checking Redis cache for this match and model..." },
  { delay: 1800, message: "No cached preview yet. Preparing the OpenRouter request..." },
  { delay: 6000, message: "Running web search for recent tactics, squad news, and availability..." },
  { delay: 25000, message: "The model is drafting the tactical preview from the gathered context..." },
  { delay: 60000, message: "Validating the response shape and repairing JSON if needed..." },
  { delay: 105000, message: "Still waiting on OpenRouter web search. First runs can take close to two minutes..." }
];

type LiveOptimizerProps = {
  initialMatchId?: number;
  lockMatch?: boolean;
};

export function LiveOptimizer({ initialMatchId, lockMatch = false }: LiveOptimizerProps) {
  const [predictions, setPredictions] = useState<PredictionResponse[]>([]);
  const [selectedMatchId, setSelectedMatchId] = useState<number | null>(null);
  const [exactScore, setExactScore] = useState(4);
  const [goalDiff, setGoalDiff] = useState(3);
  const [result, setResult] = useState(2);
  const [optimized, setOptimized] = useState<PredictionResponse | null>(null);
  const [preview, setPreview] = useState<MatchPreview | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewStatus, setPreviewStatus] = useState<string | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadMatches() {
      try {
        const response = await fetch(`${apiBaseUrl()}/api/predictions`, { cache: "no-store" });
        if (!response.ok) {
          throw new Error("Prediction feed unavailable");
        }
        const payload = (await response.json()) as { predictions: PredictionResponse[] };
        if (!cancelled) {
          const initialPrediction =
            payload.predictions.find((prediction) => prediction.match.id === initialMatchId) ?? payload.predictions[0] ?? null;
          setPredictions(payload.predictions);
          setSelectedMatchId(initialPrediction?.match.id ?? null);
          setOptimized(initialPrediction);
          setError(null);
        }
      } catch (caught) {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "Failed to load optimizer");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadMatches();
    return () => {
      cancelled = true;
    };
  }, [initialMatchId]);

  async function recompute() {
    if (selectedMatchId === null) {
      return;
    }
    setLoading(true);
    setError(null);
    setPreview(null);
    setPreviewError(null);
    setPreviewStatus(null);
    try {
      const params = new URLSearchParams({
        exact_score: String(exactScore),
        goal_difference: String(goalDiff),
        correct_result: String(result)
      });
      const response = await fetch(`${apiBaseUrl()}/api/matches/${selectedMatchId}/prediction?${params}`, {
        cache: "no-store"
      });
      if (!response.ok) {
        throw new Error("Could not recompute this match");
      }
      setOptimized((await response.json()) as PredictionResponse);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to recompute");
    } finally {
      setLoading(false);
    }
  }

  function selectMatch(matchId: number) {
    setSelectedMatchId(matchId);
    setOptimized(predictions.find((prediction) => prediction.match.id === matchId) ?? null);
    setPreview(null);
    setPreviewError(null);
    setPreviewStatus(null);
  }

  async function loadAiPreview() {
    if (selectedMatchId === null) {
      return;
    }
    const previewUrl = `${apiBaseUrl()}/api/matches/${selectedMatchId}/preview`;
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 180000);
    const progressTimers = previewProgressPhases.map((phase) =>
      window.setTimeout(() => setPreviewStatus(phase.message), phase.delay)
    );

    setPreviewLoading(true);
    setPreviewError(null);
    setPreviewStatus(previewProgressPhases[0].message);
    try {
      const response = await fetch(previewUrl, {
        cache: "no-store",
        signal: controller.signal
      });
      if (!response.ok) {
        const detail = await readErrorDetail(response);
        throw new Error(detail ? `AI preview unavailable: ${detail}` : `AI preview unavailable (${response.status})`);
      }
      setPreview((await response.json()) as MatchPreview);
      setPreviewStatus("Preview ready. Future clicks for this match/model should use the Redis cache.");
    } catch (caught) {
      if (caught instanceof DOMException && caught.name === "AbortError") {
        setPreviewError("AI preview timed out after 180 seconds. Check the API container logs and OpenRouter settings.");
      } else {
        setPreviewError(caught instanceof Error ? caught.message : "AI preview failed");
      }
    } finally {
      window.clearTimeout(timeout);
      progressTimers.forEach((timer) => window.clearTimeout(timer));
      setPreviewLoading(false);
    }
  }

  const selectedLabel = useMemo(() => {
    const match = predictions.find((item) => item.match.id === selectedMatchId)?.match;
    return match ? `${match.home_team.name} vs ${match.away_team.name}` : "No match selected";
  }, [predictions, selectedMatchId]);

  const priorScore = optimized ? conservativePriorPick(optimized) : null;
  const priorCandidate = optimized && priorScore ? candidateByScore(optimized, priorScore) : null;
  const modalScore = optimized?.most_likely_scores[0]?.score ?? null;
  const modalCandidate = optimized && modalScore ? candidateByScore(optimized, modalScore) : null;
  const favorite = optimized ? favoriteLabel(optimized) : null;

  return (
    <div className="space-y-4">
      <section className="border border-terminal-line bg-terminal-panel">
        <div className="flex flex-col gap-3 border-b border-terminal-line p-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="font-mono text-xs uppercase text-terminal-amber">Leaderboard Optimizer</div>
            <h2 className="text-2xl font-semibold text-terminal-ink">{selectedLabel}</h2>
            <div className="mt-2 flex flex-wrap gap-2">
              {optimized ? <Badge tone="cyan">{optimized.model_context.model_version}</Badge> : null}
              {optimized ? <Badge tone="green">Confidence {optimized.confidence.label}</Badge> : null}
              {optimized?.match.status ? <Badge>{optimized.match.status}</Badge> : null}
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {optimized ? (
              <Link
                href={`/matches/${optimized.match.id}`}
                className="inline-flex h-9 items-center gap-2 border border-terminal-line bg-terminal-bg px-3 text-sm text-terminal-ink hover:border-terminal-cyan"
              >
                Match detail
                <ArrowUpRight className="h-4 w-4" />
              </Link>
            ) : null}
            <Button disabled={previewLoading || selectedMatchId === null} onClick={loadAiPreview}>
              <BrainCircuit className="h-4 w-4" />
              AI Preview
            </Button>
          </div>
        </div>

        <div className="grid gap-4 p-4 lg:grid-cols-[0.85fr_1.15fr]">
          <div className="space-y-4">
            <div className="border border-terminal-line bg-terminal-bg p-4">
              <div className="mb-3 flex items-center gap-2 font-mono text-xs uppercase text-terminal-muted">
                <Target className="h-4 w-4 text-terminal-cyan" />
                Command Inputs
              </div>
              <label className="block">
                <span className="mb-1 block text-sm text-terminal-muted">Match</span>
                <select
                  className="h-10 w-full border border-terminal-line bg-terminal-panel px-3 font-mono text-terminal-ink disabled:opacity-70"
                  disabled={lockMatch}
                  value={selectedMatchId ?? ""}
                  onChange={(event) => selectMatch(Number(event.target.value))}
                >
                  {predictions.map((prediction) => (
                    <option key={prediction.match.id} value={prediction.match.id}>
                      {prediction.match.home_team.name} vs {prediction.match.away_team.name}
                    </option>
                  ))}
                </select>
              </label>
              <div className="mt-4 grid gap-3 sm:grid-cols-3">
                {[
                  ["Exact score", exactScore, setExactScore],
                  ["Goal diff", goalDiff, setGoalDiff],
                  ["Result", result, setResult]
                ].map(([label, value, setter]) => (
                  <label key={label as string} className="block">
                    <span className="mb-1 block text-xs text-terminal-muted">{label as string}</span>
                    <input
                      className="h-10 w-full border border-terminal-line bg-terminal-panel px-3 font-mono text-terminal-ink"
                      min={0}
                      max={20}
                      type="number"
                      value={value as number}
                      onChange={(event) => (setter as (value: number) => void)(Number(event.target.value))}
                    />
                  </label>
                ))}
              </div>
              <Button
                className="mt-4 w-full"
                disabled={loading || selectedMatchId === null}
                onClick={recompute}
                variant="primary"
              >
                <Calculator className="h-4 w-4" />
                Recompute Terminal
              </Button>
              {error ? <div className="mt-3 text-sm text-terminal-red">{error}</div> : null}
            </div>

            {optimized ? (
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="border border-terminal-line bg-terminal-bg p-4">
                  <div className="font-mono text-xs uppercase text-terminal-muted">Kickoff</div>
                  <div className="mt-1 text-sm text-terminal-ink">{formatKickoff(optimized.match.date)}</div>
                  <div className="mt-2 text-xs text-terminal-muted">
                    {optimized.match.group_name ?? optimized.match.stage}
                    {optimized.match.venue ? ` / ${optimized.match.venue}` : ""}
                  </div>
                </div>
                <div className="border border-terminal-line bg-terminal-bg p-4">
                  <div className="font-mono text-xs uppercase text-terminal-muted">Elo Gap</div>
                  <div className="mt-1 font-mono text-lg text-terminal-ink">
                    {optimized.home_rating.model_elo} - {optimized.away_rating.model_elo}
                  </div>
                  <div className="text-xs text-terminal-amber">
                    {optimized.rating_delta > 0 ? "+" : ""}
                    {optimized.rating_delta} home delta
                  </div>
                </div>
              </div>
            ) : null}
          </div>

          <div className="space-y-4">
            {optimized ? (
              <>
                <div className="grid gap-4 md:grid-cols-[1fr_0.85fr]">
                  <div className="border border-terminal-line bg-terminal-bg p-4">
                    <div className="mb-2 flex items-center gap-2 font-mono text-xs uppercase text-terminal-muted">
                      <Radar className="h-4 w-4 text-terminal-cyan" />
                      Match Chances
                    </div>
                    <ProbabilityStrip probabilities={[optimized.p_home_win, optimized.p_draw, optimized.p_away_win]} />
                    <div className="mt-3 grid grid-cols-3 gap-2 font-mono text-xs">
                      <div>
                        <div className="text-terminal-muted">{optimized.match.home_team.name}</div>
                        <div className="text-terminal-ink">{formatPercent(optimized.p_home_win)}</div>
                      </div>
                      <div>
                        <div className="text-terminal-muted">Draw</div>
                        <div className="text-terminal-ink">{formatPercent(optimized.p_draw)}</div>
                      </div>
                      <div>
                        <div className="text-terminal-muted">{optimized.match.away_team.name}</div>
                        <div className="text-terminal-ink">{formatPercent(optimized.p_away_win)}</div>
                      </div>
                    </div>
                  </div>
                  <div className="border border-terminal-line bg-terminal-bg p-4">
                    <div className="mb-2 flex items-center gap-2 font-mono text-xs uppercase text-terminal-muted">
                      <Shield className="h-4 w-4 text-terminal-cyan" />
                      Best Terminal Tipp
                    </div>
                    <div className="font-mono text-4xl text-terminal-amber">{optimized.recommended_tip.score}</div>
                    <div className="mt-2 font-mono text-sm text-terminal-green">
                      {optimized.recommended_tip.expected_points.toFixed(2)} EV
                    </div>
                    <p className="mt-2 text-xs text-terminal-muted">{optimized.recommended_tip.explanation}</p>
                  </div>
                </div>

                <div className="border border-terminal-line bg-terminal-bg p-4">
                  <div className="mb-3 flex items-center gap-2 font-mono text-xs uppercase text-terminal-muted">
                    <GitCompareArrows className="h-4 w-4 text-terminal-cyan" />
                    Model Lenses
                  </div>
                  <div className="grid gap-3 md:grid-cols-3">
                    <ModelLens
                      label="Current model"
                      score={optimized.recommended_tip.score}
                      meta={`${formatPercent(favorite?.value ?? 0)} ${favorite?.label ?? "top outcome"}`}
                      note={optimized.model_context.training_status}
                    />
                    <ModelLens
                      label="Legacy prior lens"
                      score={priorScore ?? "-"}
                      meta={priorCandidate ? `${priorCandidate.expected_points.toFixed(2)} EV` : "not a top candidate"}
                      note="A conservative old-style lens: draw if Elo is close, otherwise 1-goal favorite win."
                    />
                    <ModelLens
                      label="Modal exact score"
                      score={modalScore ?? "-"}
                      meta={modalCandidate ? `${formatPercent(modalCandidate.exact_probability)} exact` : "from top scores"}
                      note="The single most likely scoreline, which can differ from the highest-EV Tipp."
                    />
                  </div>
                </div>

                <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
                  <div className="border border-terminal-line bg-terminal-bg p-4">
                    <div className="mb-3 font-mono text-xs uppercase text-terminal-muted">Scenario EV Table</div>
                    <div className="overflow-x-auto">
                      <table className="min-w-full border-collapse text-sm">
                        <thead className="text-left font-mono text-xs uppercase text-terminal-muted">
                          <tr>
                            <th className="border-b border-terminal-line px-2 py-2">Scenario</th>
                            <th className="border-b border-terminal-line px-2 py-2">Tipp</th>
                            <th className="border-b border-terminal-line px-2 py-2">Exact</th>
                            <th className="border-b border-terminal-line px-2 py-2">EV</th>
                            <th className="border-b border-terminal-line px-2 py-2">Actual</th>
                          </tr>
                        </thead>
                        <tbody>
                          {optimized.tip_candidates.map((candidate) => (
                            <tr key={`${candidate.label}-${candidate.score}`}>
                              <td className="border-b border-terminal-line px-2 py-2 text-terminal-muted">
                                <div className="text-terminal-ink">{candidate.label}</div>
                                <div className="max-w-72 text-xs">{candidate.rationale}</div>
                              </td>
                              <td className="border-b border-terminal-line px-2 py-2 font-mono text-terminal-amber">
                                {candidate.score}
                              </td>
                              <td className="border-b border-terminal-line px-2 py-2 font-mono text-terminal-muted">
                                {formatPercent(candidate.exact_probability)}
                              </td>
                              <td className="border-b border-terminal-line px-2 py-2 font-mono text-terminal-green">
                                {candidate.expected_points.toFixed(2)}
                              </td>
                              <td className="border-b border-terminal-line px-2 py-2 font-mono text-terminal-muted">
                                {candidate.actual_points === null ? "-" : `${candidate.actual_points} pts`}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                  <div className="border border-terminal-line bg-terminal-bg p-4">
                    <div className="mb-3 font-mono text-xs uppercase text-terminal-muted">Most Likely Scores</div>
                    <div className="space-y-2">
                      {optimized.most_likely_scores.map((score) => (
                        <div key={score.score}>
                          <div className="mb-1 flex items-center justify-between font-mono text-xs">
                            <span className="text-terminal-ink">{score.score}</span>
                            <span className="text-terminal-muted">{formatPercent(score.p)}</span>
                          </div>
                          <div className="h-1.5 bg-terminal-line">
                            <div className="h-full bg-terminal-cyan" style={{ width: `${Math.max(2, score.p * 100)}%` }} />
                          </div>
                        </div>
                      ))}
                    </div>
                    <p className="mt-4 text-xs text-terminal-muted">{optimized.confidence.reason}</p>
                  </div>
                </div>

                <div className="border border-terminal-line bg-terminal-bg p-4">
                  <div className="font-mono text-xs uppercase text-terminal-muted">Model Notes</div>
                  <ul className="mt-3 grid gap-2 text-sm text-terminal-muted md:grid-cols-2">
                    {optimized.model_context.explanation.map((item) => (
                      <li key={item} className="border-l border-terminal-line pl-3">
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </>
            ) : (
              <div className="border border-terminal-line bg-terminal-bg p-4 text-sm text-terminal-muted">
                Loading optimizer...
              </div>
            )}
          </div>
        </div>
      </section>

      {preview || previewError || previewLoading ? (
        <section className="border border-terminal-line bg-terminal-panel p-4">
          <div className="mb-2 flex items-center gap-2 font-mono text-xs uppercase text-terminal-muted">
            <BrainCircuit className="h-4 w-4 text-terminal-cyan" />
            AI Preview
          </div>
          {previewStatus ? (
            <div className="mb-3 border border-terminal-line bg-terminal-bg p-3">
              <div className="flex items-center gap-2 text-sm text-terminal-muted">
                {previewLoading ? (
                  <span className="h-2 w-2 animate-pulse bg-terminal-cyan" aria-hidden="true" />
                ) : (
                  <span className="h-2 w-2 bg-terminal-green" aria-hidden="true" />
                )}
                <span>{previewStatus}</span>
              </div>
              {previewLoading ? (
                <div className="mt-2 h-1 overflow-hidden bg-terminal-line">
                  <div className="h-full w-1/3 animate-[pulse_1.5s_ease-in-out_infinite] bg-terminal-cyan" />
                </div>
              ) : null}
            </div>
          ) : null}
          {previewError ? <p className="text-sm text-terminal-red">{previewError}</p> : null}
          {preview ? (
            <div className="space-y-3 text-sm text-terminal-muted">
              <p>{preview.tactical_preview}</p>
              <ul className="grid gap-2 md:grid-cols-2">
                {preview.key_factors.map((factor) => (
                  <li key={factor} className="border-l border-terminal-line pl-3">
                    {factor}
                  </li>
                ))}
              </ul>
              <p>
                <span className="text-terminal-ink">Upset scenario:</span> {preview.upset_scenario}
              </p>
              {preview.injury_watch.length > 0 ? (
                <ul className="space-y-2">
                  {preview.injury_watch.map((item) => (
                    <li key={item} className="border-l border-terminal-line pl-3">
                      {item}
                    </li>
                  ))}
                </ul>
              ) : null}
              <div className="font-mono text-xs text-terminal-muted">
                AI confidence {Math.round(preview.confidence * 100)}%
              </div>
            </div>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}

function ModelLens({
  label,
  score,
  meta,
  note
}: {
  label: string;
  score: string;
  meta: string;
  note: string;
}) {
  return (
    <div className="border border-terminal-line bg-terminal-panel/60 p-3">
      <div className="font-mono text-xs uppercase text-terminal-muted">{label}</div>
      <div className="mt-1 font-mono text-2xl text-terminal-amber">{score}</div>
      <div className="mt-1 font-mono text-xs text-terminal-green">{meta}</div>
      <p className="mt-2 text-xs text-terminal-muted">{note}</p>
    </div>
  );
}

async function readErrorDetail(response: Response) {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    return typeof payload.detail === "string" ? payload.detail : null;
  } catch {
    return null;
  }
}
