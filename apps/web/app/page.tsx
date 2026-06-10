import { AlertTriangle, BrainCircuit, Database, Trophy } from "lucide-react";

import { DashboardShell } from "@/components/dashboard-shell";
import { MatchTable } from "@/components/match-table";
import { Badge } from "@/components/ui/badge";
import { predictionRows, stageProbabilities } from "@/lib/mock-data";
import { formatPercent } from "@/lib/utils";

const metrics = [
  { label: "Predicted winner", value: "Brazil", subvalue: "17.4%", icon: Trophy },
  { label: "Model run", value: "v0.1.0", subvalue: "sample mode", icon: BrainCircuit },
  { label: "Biggest disagreement", value: "Uruguay v Mexico", subvalue: "6.0 pts", icon: AlertTriangle },
  { label: "Data source", value: "Local sample", subvalue: "3 fixtures", icon: Database }
];

export default function Home() {
  return (
    <DashboardShell>
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

      <div className="mt-4 grid gap-4 lg:grid-cols-[1.8fr_1fr]">
        <section>
          <div className="mb-2 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-terminal-ink">Live Match Board</h2>
            <Badge tone="cyan">Tipp EV enabled</Badge>
          </div>
          <MatchTable rows={predictionRows} />
        </section>

        <section className="border border-terminal-line bg-terminal-panel p-4">
          <h2 className="text-lg font-semibold text-terminal-ink">Title Probabilities</h2>
          <div className="mt-4 space-y-4">
            {stageProbabilities.map((team) => (
              <div key={team.team}>
                <div className="mb-1 flex justify-between text-sm">
                  <span>{team.team}</span>
                  <span className="font-mono text-terminal-amber">{formatPercent(team.winner)}</span>
                </div>
                <div className="h-2 border border-terminal-line bg-terminal-bg">
                  <div className="h-full bg-terminal-green" style={{ width: `${team.winner * 100 * 4}%` }} />
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </DashboardShell>
  );
}
