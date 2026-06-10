"use client";

import { Calculator, Shield, TrendingUp, Zap } from "lucide-react";
import { useMemo, useState } from "react";

import { DashboardShell } from "@/components/dashboard-shell";
import { Button } from "@/components/ui/button";

const strategies = [
  { label: "Safe", pick: "1-0", note: "Lower variance, protects a lead", icon: Shield },
  { label: "Max EV", pick: "2-1", note: "Best expected points under rules", icon: Calculator },
  { label: "Catch-up", pick: "1-1", note: "Contrarian without going pure chaos", icon: TrendingUp },
  { label: "Chaos", pick: "0-1", note: "High leverage upset profile", icon: Zap }
];

export default function LeaderboardOptimizerPage() {
  const [exactScore, setExactScore] = useState(4);
  const [goalDiff, setGoalDiff] = useState(3);
  const [result, setResult] = useState(2);

  const scoringSummary = useMemo(
    () => `Exact ${exactScore} / Diff ${goalDiff} / Result ${result}`,
    [exactScore, goalDiff, result]
  );

  return (
    <DashboardShell>
      <div className="grid gap-4 lg:grid-cols-[0.9fr_1.4fr]">
        <section className="border border-terminal-line bg-terminal-panel p-4">
          <h2 className="text-xl font-semibold text-terminal-ink">Scoring Rules</h2>
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
          <Button className="mt-4 w-full" variant="primary">
            <Calculator className="h-4 w-4" />
            Recompute
          </Button>
          <div className="mt-3 font-mono text-xs text-terminal-amber">{scoringSummary}</div>
        </section>

        <section className="border border-terminal-line bg-terminal-panel p-4">
          <h2 className="text-xl font-semibold text-terminal-ink">Germany vs Japan</h2>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            {strategies.map((strategy) => {
              const Icon = strategy.icon;
              return (
                <div key={strategy.label} className="border border-terminal-line bg-terminal-bg p-4">
                  <div className="mb-3 flex items-center justify-between">
                    <span className="font-mono text-xs uppercase text-terminal-muted">{strategy.label}</span>
                    <Icon className="h-4 w-4 text-terminal-cyan" />
                  </div>
                  <div className="font-mono text-3xl text-terminal-amber">{strategy.pick}</div>
                  <p className="mt-2 text-sm text-terminal-muted">{strategy.note}</p>
                </div>
              );
            })}
          </div>
        </section>
      </div>
    </DashboardShell>
  );
}
