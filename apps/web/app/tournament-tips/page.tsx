"use client";

import { Crown, Sigma, Trophy, UsersRound } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { DashboardShell } from "@/components/dashboard-shell";
import { Badge } from "@/components/ui/badge";

type TournamentTip = {
  question_key: string;
  question_label: string;
  answer: Record<string, unknown>;
  confidence: number;
  generated_at: string;
  model_version: string;
};

type TournamentTipsResponse = {
  phases: {
    pre_tournament?: TournamentTip[];
    current?: TournamentTip[];
  };
};

const iconByQuestion = {
  top_scorer: Sigma,
  semifinalists: UsersRound,
  tournament_winner: Crown
};

export default function TournamentTipsPage() {
  const [data, setData] = useState<TournamentTipsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
    const baseUrl = apiBaseUrl ? apiBaseUrl.replace(/\/$/, "") : "";

    fetch(`${baseUrl}/api/tournament-tips`, { cache: "no-store" })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Tournament Tipps are not available yet");
        }
        return response.json();
      })
      .then((payload: TournamentTipsResponse) => setData(payload))
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Failed to load Tipps"));
  }, []);

  const rows = useMemo(() => {
    const current = data?.phases.current ?? [];
    const preTournament = new Map((data?.phases.pre_tournament ?? []).map((tip) => [tip.question_key, tip]));
    return current.map((tip) => ({
      current: tip,
      baseline: preTournament.get(tip.question_key)
    }));
  }, [data]);

  return (
    <DashboardShell>
      <div className="mb-3 flex items-center gap-2">
        <Trophy className="h-5 w-5 text-terminal-cyan" />
        <h2 className="text-xl font-semibold text-terminal-ink">Tournament Tipps</h2>
      </div>

      {error ? (
        <section className="border border-terminal-red bg-terminal-panel p-4 text-sm text-terminal-red">
          {error}
        </section>
      ) : null}

      {!error && rows.length === 0 ? (
        <section className="border border-terminal-line bg-terminal-panel p-4 text-sm text-terminal-muted">
          Run fixture ingest to create the pre-tournament and current Tipps.
        </section>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-2">
        {rows.map(({ current, baseline }) => {
          const Icon = iconByQuestion[current.question_key as keyof typeof iconByQuestion] ?? Trophy;
          const changed = baseline ? answerLabel(current.answer) !== answerLabel(baseline.answer) : false;

          return (
            <section key={current.question_key} className="border border-terminal-line bg-terminal-panel p-4">
              <div className="mb-3 flex items-start justify-between gap-3">
                <div className="flex items-center gap-2">
                  <Icon className="h-4 w-4 text-terminal-cyan" />
                  <h3 className="font-semibold text-terminal-ink">{current.question_label}</h3>
                </div>
                <Badge tone={changed ? "amber" : "green"}>{changed ? "changed" : "same"}</Badge>
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                <div className="border border-terminal-line bg-terminal-bg p-3">
                  <div className="font-mono text-xs uppercase text-terminal-muted">Pre-start</div>
                  <div className="mt-2 text-lg font-semibold text-terminal-ink">
                    {baseline ? answerLabel(baseline.answer) : "-"}
                  </div>
                </div>
                <div className="border border-terminal-line bg-terminal-bg p-3">
                  <div className="font-mono text-xs uppercase text-terminal-muted">Current</div>
                  <div className="mt-2 text-lg font-semibold text-terminal-amber">
                    {answerLabel(current.answer)}
                  </div>
                </div>
              </div>

              <div className="mt-3 font-mono text-xs text-terminal-muted">
                Confidence {(current.confidence * 100).toFixed(0)}% · {current.model_version}
              </div>
            </section>
          );
        })}
      </div>
    </DashboardShell>
  );
}

function answerLabel(answer: Record<string, unknown>): string {
  if (Array.isArray(answer.teams)) {
    return answer.teams
      .map((item) => (typeof item === "object" && item !== null && "team" in item ? String(item.team) : ""))
      .filter(Boolean)
      .join(", ");
  }
  if (typeof answer.player === "string" && typeof answer.team === "string") {
    return `${answer.player} (${answer.team})`;
  }
  if (typeof answer.team === "string") {
    return answer.team;
  }
  return JSON.stringify(answer);
}
