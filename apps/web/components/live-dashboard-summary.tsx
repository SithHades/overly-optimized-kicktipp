"use client";

import { AlertTriangle, BrainCircuit, Database, Info, Trophy } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { formatPercent } from "@/lib/utils";

type TournamentTip = {
  question_key: string;
  question_label: string;
  answer: Record<string, unknown>;
  confidence: number;
  generated_at: string;
  model_version: string;
  source_state: Record<string, unknown>;
};

type TournamentTipsResponse = {
  phases: {
    current?: TournamentTip[];
    pre_tournament?: TournamentTip[];
  };
};

type MatchListResponse = {
  matches: {
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
  }[];
};

export function LiveDashboardSummary() {
  const [tips, setTips] = useState<TournamentTipsResponse | null>(null);
  const [matchCount, setMatchCount] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadSummary() {
      const baseUrl = apiBaseUrl();
      try {
        const [tipsResponse, matchesResponse] = await Promise.all([
          fetch(`${baseUrl}/api/tournament-tips`, { cache: "no-store" }),
          fetch(`${baseUrl}/api/matches`, { cache: "no-store" })
        ]);
        if (!tipsResponse.ok || !matchesResponse.ok) {
          throw new Error("Live model summary unavailable");
        }

        const tipsPayload = (await tipsResponse.json()) as TournamentTipsResponse;
        const matchesPayload = (await matchesResponse.json()) as MatchListResponse;
        if (!cancelled) {
          setTips(tipsPayload);
          setMatchCount(matchesPayload.matches.length);
          setError(null);
        }
      } catch (caught) {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "Failed to load live summary");
        }
      }
    }

    loadSummary();
    return () => {
      cancelled = true;
    };
  }, []);

  const currentTips = tips?.phases.current ?? [];
  const winnerTip = currentTips.find((tip) => tip.question_key === "tournament_winner");
  const semifinalistsTip = currentTips.find((tip) => tip.question_key === "semifinalists");
  const topScorerTip = currentTips.find((tip) => tip.question_key === "top_scorer");
  const titleRows = useMemo(() => teamRows(semifinalistsTip), [semifinalistsTip]);

  const metrics = [
    {
      label: "Predicted winner",
      value: stringField(winnerTip?.answer.team) ?? "-",
      subvalue: winnerTip ? formatPercent(winnerTip.confidence) : "waiting for ingest",
      icon: Trophy
    },
    {
      label: "Model run",
      value: winnerTip?.model_version ?? "historical-world-cup-elo-v1",
      subvalue: winnerTip ? new Date(winnerTip.generated_at).toLocaleString() : "not generated",
      icon: BrainCircuit
    },
    {
      label: "Top scorer",
      value: scorerLabel(topScorerTip),
      subvalue: topScorerTip ? formatPercent(topScorerTip.confidence) : "waiting for ingest",
      icon: AlertTriangle
    },
    {
      label: "Data source",
      value: "Football-Data",
      subvalue: matchCount === null ? "loading fixtures" : `${matchCount} fixtures`,
      icon: Database
    }
  ];

  return (
    <>
      <div className="mb-4 flex flex-wrap gap-2">
        <Badge tone={error ? "red" : "green"}>{error ? "Live API unavailable" : "Live API connected"}</Badge>
        <Badge tone="cyan">{matchCount === null ? "Fixtures loading" : `${matchCount} fixtures`}</Badge>
        <Badge tone="amber">{winnerTip ? `Last model run: ${new Date(winnerTip.generated_at).toLocaleString()}` : "No tips yet"}</Badge>
      </div>

      <div className="grid gap-4 lg:grid-cols-4">
        {metrics.map((metric) => {
          const Icon = metric.icon;
          return (
            <section key={metric.label} className="border border-terminal-line bg-terminal-panel p-4">
              <div className="mb-4 flex items-center justify-between">
                <span className="font-mono text-xs uppercase text-terminal-muted">{metric.label}</span>
                <Icon className="h-4 w-4 text-terminal-cyan" />
              </div>
              <div className="text-2xl font-semibold text-terminal-ink">{metric.value}</div>
              <div className="mt-1 font-mono text-xs text-terminal-amber">{metric.subvalue}</div>
            </section>
          );
        })}
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_1.15fr]">
        <section className="border border-terminal-line bg-terminal-panel p-4">
          <h2 className="text-lg font-semibold text-terminal-ink">Title Contenders</h2>
          <div className="mt-4 space-y-4">
            {titleRows.length === 0 ? (
              <div className="text-sm text-terminal-muted">Run fixture ingest to generate contender projections.</div>
            ) : null}
            {titleRows.map((team) => (
              <div key={team.team}>
                <div className="mb-1 flex justify-between text-sm">
                  <span>{team.team}</span>
                  <span className="font-mono text-terminal-amber">{team.score.toFixed(1)}</span>
                </div>
                <div className="h-2 border border-terminal-line bg-terminal-bg">
                  <div className="h-full bg-terminal-green" style={{ width: `${team.width}%` }} />
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="border border-terminal-line bg-terminal-panel p-4">
          <div className="mb-3 flex items-center gap-2">
            <Info className="h-4 w-4 text-terminal-cyan" />
            <h2 className="text-lg font-semibold text-terminal-ink">Why This Output?</h2>
          </div>
          <div className="space-y-3 text-sm text-terminal-muted">
            <p>
              This is a transparent model, not a black box. It fetches completed historical World Cup matches,
              fits Elo ratings chronologically, converts the rating gap into expected goals, then runs a Poisson
              score model.
            </p>
            <p>
              {winnerTip
                ? `${stringField(winnerTip.answer.team) ?? "The leader"} is on top because its historical World Cup Elo and projected bracket score currently rank first. This is still a model estimate, not a guarantee.`
                : "The tournament winner card appears after fixture ingest creates tournament projections."}
            </p>
            <p>
              Low confidence on individual games is normal: football has high draw/upset probability, and a
              40% favorite is still more likely not to win than to win.
            </p>
          </div>
        </section>
      </div>
    </>
  );
}

function teamRows(tip: TournamentTip | undefined) {
  const teams = tip?.answer.teams;
  if (!Array.isArray(teams)) {
    return [];
  }

  const rows = teams
    .map((item) => {
      if (typeof item !== "object" || item === null || !("team" in item)) {
        return null;
      }
      const score = "projection_score" in item ? Number(item.projection_score) : 0;
      return { team: String(item.team), score };
    })
    .filter((item): item is { team: string; score: number } => item !== null);

  const maxScore = Math.max(...rows.map((row) => row.score), 1);
  return rows.map((row) => ({ ...row, width: Math.max(8, (row.score / maxScore) * 100) }));
}

function scorerLabel(tip: TournamentTip | undefined) {
  if (!tip) {
    return "-";
  }
  const player = stringField(tip.answer.player);
  const team = stringField(tip.answer.team);
  if (player && team) {
    return `${player} (${team})`;
  }
  return player ?? team ?? "-";
}

function stringField(value: unknown) {
  return typeof value === "string" ? value : null;
}

function apiBaseUrl() {
  return (process.env.NEXT_PUBLIC_API_BASE_URL ?? "").replace(/\/$/, "");
}
