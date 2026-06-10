import { Activity, BarChart3, GitBranch, LineChart } from "lucide-react";

import { DashboardShell } from "@/components/dashboard-shell";
import { Badge } from "@/components/ui/badge";

const rows = [
  ["Elo baseline", "0.621", "0.214", "active"],
  ["Poisson score", "0.608", "0.207", "active"],
  ["Market blend", "pending", "pending", "planned"],
  ["Bayesian hierarchy", "pending", "pending", "later"]
];

export default function ModelLabPage() {
  return (
    <DashboardShell>
      <div className="grid gap-4 lg:grid-cols-[1.1fr_1fr]">
        <section className="border border-terminal-line bg-terminal-panel p-4">
          <div className="mb-4 flex items-center gap-2">
            <GitBranch className="h-4 w-4 text-terminal-cyan" />
            <h2 className="text-xl font-semibold text-terminal-ink">Model Runs</h2>
          </div>
          <table className="w-full border-collapse text-sm">
            <thead className="font-mono text-xs uppercase text-terminal-muted">
              <tr>
                <th className="border-b border-terminal-line py-2 text-left">Model</th>
                <th className="border-b border-terminal-line py-2 text-left">Log loss</th>
                <th className="border-b border-terminal-line py-2 text-left">Brier</th>
                <th className="border-b border-terminal-line py-2 text-left">State</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(([name, logLoss, brier, state]) => (
                <tr key={name}>
                  <td className="border-b border-terminal-line py-3">{name}</td>
                  <td className="border-b border-terminal-line py-3 font-mono">{logLoss}</td>
                  <td className="border-b border-terminal-line py-3 font-mono">{brier}</td>
                  <td className="border-b border-terminal-line py-3">
                    <Badge tone={state === "active" ? "green" : "amber"}>{state}</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="grid gap-4">
          <div className="border border-terminal-line bg-terminal-panel p-4">
            <div className="mb-3 flex items-center gap-2">
              <LineChart className="h-4 w-4 text-terminal-cyan" />
              <h2 className="text-lg font-semibold">Calibration</h2>
            </div>
            <div className="grid h-48 place-items-center border border-dashed border-terminal-line font-mono text-xs text-terminal-muted">
              Recharts calibration chart placeholder
            </div>
          </div>
          <div className="border border-terminal-line bg-terminal-panel p-4">
            <div className="mb-3 flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-terminal-cyan" />
              <h2 className="text-lg font-semibold">Feature Importance</h2>
            </div>
            <div className="grid h-32 place-items-center border border-dashed border-terminal-line font-mono text-xs text-terminal-muted">
              Elo diff, market implied p, rest days, squad strength
            </div>
          </div>
          <div className="border border-terminal-line bg-terminal-panel p-4">
            <div className="mb-3 flex items-center gap-2">
              <Activity className="h-4 w-4 text-terminal-cyan" />
              <h2 className="text-lg font-semibold">Data Audit</h2>
            </div>
            <p className="text-sm text-terminal-muted">No anomalies in sample data.</p>
          </div>
        </section>
      </div>
    </DashboardShell>
  );
}
