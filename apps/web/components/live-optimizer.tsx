"use client";

import { BrainCircuit, Calculator, Shield, Target } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { ProbabilityStrip } from "@/components/probability-strip";

type Prediction = {
  match: {
    id: number;
    date: string;
    stage: string;
    group_name: string | null;
    home_team: { id: number | null; name: string };
    away_team: { id: number | null; name: string };
  };
  p_home_win: number;
  p_draw: number;
  p_away_win: number;
  recommended_tip: { score: string; expected_points: number; explanation: string };
  most_likely_scores: { score: string; p: number }[];
  home_rating: { model_elo: number; tier: string };
  away_rating: { model_elo: number; tier: string };
  confidence: { label: string; score: number; reason: string };
  model_context: { model_version: string; training_status: string; explanation: string[] };
};

type MatchPreview = {
  fixture: string;
  tactical_preview: string;
  key_factors: string[];
  upset_scenario: string;
  injury_watch: string[];
  source_urls: string[];
  confidence: number;
};

export function LiveOptimizer() {
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [selectedMatchId, setSelectedMatchId] = useState<number | null>(null);
  const [exactScore, setExactScore] = useState(4);
  const [goalDiff, setGoalDiff] = useState(3);
  const [result, setResult] = useState(2);
  const [optimized, setOptimized] = useState<Prediction | null>(null);
  const [preview, setPreview] = useState<MatchPreview | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
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
        const payload = (await response.json()) as { predictions: Prediction[] };
        if (!cancelled) {
          setPredictions(payload.predictions);
          setSelectedMatchId(payload.predictions[0]?.match.id ?? null);
          setOptimized(payload.predictions[0] ?? null);
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
  }, []);

  async function recompute() {
    if (selectedMatchId === null) {
      return;
    }
    setLoading(true);
    setError(null);
    setPreview(null);
    setPreviewError(null);
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
      setOptimized((await response.json()) as Prediction);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to recompute");
    } finally {
      setLoading(false);
    }
  }

  async function loadAiPreview() {
    if (selectedMatchId === null) {
      return;
    }
    const previewUrl = `${apiBaseUrl()}/api/matches/${selectedMatchId}/preview`;
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 35000);

    setPreviewLoading(true);
    setPreviewError(null);
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
    } catch (caught) {
      if (caught instanceof DOMException && caught.name === "AbortError") {
        setPreviewError("AI preview timed out after 35 seconds. Check the API container logs and OpenRouter settings.");
      } else {
        setPreviewError(caught instanceof Error ? caught.message : "AI preview failed");
      }
    } finally {
      window.clearTimeout(timeout);
      setPreviewLoading(false);
    }
  }

  const selectedLabel = useMemo(() => {
    const match = predictions.find((item) => item.match.id === selectedMatchId)?.match;
    return match ? `${match.home_team.name} vs ${match.away_team.name}` : "No match selected";
  }, [predictions, selectedMatchId]);

  return (
    <div className="grid gap-4 lg:grid-cols-[0.9fr_1.4fr]">
      <section className="border border-terminal-line bg-terminal-panel p-4">
        <h2 className="text-xl font-semibold text-terminal-ink">Scoring Rules</h2>
        <label className="mt-4 block">
          <span className="mb-1 block text-sm text-terminal-muted">Match</span>
          <select
            className="h-10 w-full border border-terminal-line bg-terminal-bg px-3 font-mono text-terminal-ink"
            value={selectedMatchId ?? ""}
            onChange={(event) => setSelectedMatchId(Number(event.target.value))}
          >
            {predictions.map((prediction) => (
              <option key={prediction.match.id} value={prediction.match.id}>
                {prediction.match.home_team.name} vs {prediction.match.away_team.name}
              </option>
            ))}
          </select>
        </label>
        <div className="mt-4 space-y-4">
          {[
            ["Exact score", exactScore, setExactScore],
            ["Correct goal difference", goalDiff, setGoalDiff],
            ["Correct result", result, setResult]
          ].map(([label, value, setter]) => (
            <label key={label as string} className="block">
              <span className="mb-1 block text-sm text-terminal-muted">{label as string}</span>
              <input
                className="h-10 w-full border border-terminal-line bg-terminal-bg px-3 font-mono text-terminal-ink"
                min={0}
                max={20}
                type="number"
                value={value as number}
                onChange={(event) => (setter as (value: number) => void)(Number(event.target.value))}
              />
            </label>
          ))}
        </div>
        <Button className="mt-4 w-full" disabled={loading || selectedMatchId === null} onClick={recompute} variant="primary">
          <Calculator className="h-4 w-4" />
          Recompute Tipp
        </Button>
        {error ? <div className="mt-3 text-sm text-terminal-red">{error}</div> : null}
      </section>

      <section className="border border-terminal-line bg-terminal-panel p-4">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold text-terminal-ink">{selectedLabel}</h2>
            <p className="text-sm text-terminal-muted">
              Live model probabilities and Tipp-Spiel EV: average expected points under the scoring rules.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button disabled={previewLoading || selectedMatchId === null} onClick={loadAiPreview}>
              <BrainCircuit className="h-4 w-4" />
              AI Preview
            </Button>
            <Target className="h-5 w-5 text-terminal-cyan" />
          </div>
        </div>

        {optimized ? (
          <div className="grid gap-4 md:grid-cols-2">
            <div className="border border-terminal-line bg-terminal-bg p-4">
              <div className="mb-2 font-mono text-xs uppercase text-terminal-muted">Model 1X2</div>
              <ProbabilityStrip probabilities={[optimized.p_home_win, optimized.p_draw, optimized.p_away_win]} />
              <div className="mt-3 font-mono text-xs text-terminal-muted">
                Elo {optimized.home_rating.model_elo} - {optimized.away_rating.model_elo}
              </div>
            </div>
            <div className="border border-terminal-line bg-terminal-bg p-4">
              <div className="mb-2 flex items-center gap-2 font-mono text-xs uppercase text-terminal-muted">
                <Shield className="h-4 w-4 text-terminal-cyan" />
                Recommended Tipp
              </div>
              <div className="font-mono text-3xl text-terminal-amber">{optimized.recommended_tip.score}</div>
              <p className="mt-2 text-sm text-terminal-muted">
                EV {optimized.recommended_tip.expected_points.toFixed(2)} means this pick averages that many
                scoring-rule points across the model&apos;s full score distribution. {optimized.recommended_tip.explanation}
              </p>
            </div>
            <div className="border border-terminal-line bg-terminal-bg p-4 md:col-span-2">
              <div className="font-mono text-xs uppercase text-terminal-muted">Interpretation</div>
              <p className="mt-2 text-sm text-terminal-muted">{optimized.confidence.reason}</p>
              <ul className="mt-3 grid gap-2 text-sm text-terminal-muted md:grid-cols-2">
                {optimized.model_context.explanation.map((item) => (
                  <li key={item} className="border-l border-terminal-line pl-3">
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            {preview || previewError || previewLoading ? (
              <div className="border border-terminal-line bg-terminal-bg p-4 md:col-span-2">
                <div className="mb-2 flex items-center gap-2 font-mono text-xs uppercase text-terminal-muted">
                  <BrainCircuit className="h-4 w-4 text-terminal-cyan" />
                  AI Preview
                </div>
                {previewLoading ? <p className="text-sm text-terminal-muted">Generating preview...</p> : null}
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
              </div>
            ) : null}
          </div>
        ) : (
          <div className="text-sm text-terminal-muted">Loading optimizer...</div>
        )}
      </section>
    </div>
  );
}

function apiBaseUrl() {
  return (process.env.NEXT_PUBLIC_API_BASE_URL ?? "").replace(/\/$/, "");
}

async function readErrorDetail(response: Response) {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    return typeof payload.detail === "string" ? payload.detail : null;
  } catch {
    return null;
  }
}
