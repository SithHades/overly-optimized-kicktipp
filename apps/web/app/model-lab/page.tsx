import { Activity, BarChart3, Database, GitBranch, LineChart, RefreshCw } from "lucide-react";

import { DashboardShell } from "@/components/dashboard-shell";
import { Badge } from "@/components/ui/badge";

const modelRows = [
  {
    name: "Historical World Cup Elo",
    status: "active",
    role: "Ranks team strength before kickoff",
    caveat: "Fitted from completed World Cup results fetched from openfootball"
  },
  {
    name: "Poisson score model",
    status: "active",
    role: "Turns expected goals into scoreline probabilities",
    caveat: "Uses expected goals derived from historical Elo gaps"
  },
  {
    name: "Tipp EV optimizer",
    status: "active",
    role: "Chooses the score with best expected scoring-rule points",
    caveat: "Optimizes game rules, not emotional plausibility"
  },
  {
    name: "Historical calibration",
    status: "planned",
    role: "Backtests log loss, Brier score, and calibration buckets",
    caveat: "Needs historical international fixture dataset"
  }
];

const dataLineage = [
  "Fixtures and match status come from football-data.org via the ingest endpoint.",
  "Teams are upserted into Postgres and predictions are generated on request.",
  "Tournament tips are regenerated after ingest and stored as pre_tournament/current phases.",
  "No scheduled retraining exists yet; ratings refresh when fixture ingest or the Elo admin endpoint runs."
];

export default function ModelLabPage() {
  return (
    <DashboardShell>
      <div className="grid gap-4 lg:grid-cols-[1.1fr_1fr]">
        <section className="border border-terminal-line bg-terminal-panel p-4">
          <div className="mb-4 flex items-center gap-2">
            <GitBranch className="h-4 w-4 text-terminal-cyan" />
            <h2 className="text-xl font-semibold text-terminal-ink">Model Stack</h2>
          </div>
          <table className="w-full border-collapse text-sm">
            <thead className="font-mono text-xs uppercase text-terminal-muted">
              <tr>
                <th className="border-b border-terminal-line py-2 text-left">Component</th>
                <th className="border-b border-terminal-line py-2 text-left">Role</th>
                <th className="border-b border-terminal-line py-2 text-left">State</th>
              </tr>
            </thead>
            <tbody>
              {modelRows.map((row) => (
                <tr key={row.name}>
                  <td className="border-b border-terminal-line py-3">
                    <div className="font-medium text-terminal-ink">{row.name}</div>
                    <div className="text-xs text-terminal-muted">{row.caveat}</div>
                  </td>
                  <td className="border-b border-terminal-line py-3 text-terminal-muted">{row.role}</td>
                  <td className="border-b border-terminal-line py-3">
                    <Badge tone={row.status === "active" ? "green" : "amber"}>{row.status}</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="grid gap-4">
          <div className="border border-terminal-line bg-terminal-panel p-4">
            <div className="mb-3 flex items-center gap-2">
              <Database className="h-4 w-4 text-terminal-cyan" />
              <h2 className="text-lg font-semibold">Data Lineage</h2>
            </div>
            <ul className="space-y-2 text-sm text-terminal-muted">
              {dataLineage.map((item) => (
                <li key={item} className="border-l border-terminal-line pl-3">
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <div className="border border-terminal-line bg-terminal-panel p-4">
            <div className="mb-3 flex items-center gap-2">
              <LineChart className="h-4 w-4 text-terminal-cyan" />
              <h2 className="text-lg font-semibold">Calibration Status</h2>
            </div>
            <p className="text-sm text-terminal-muted">
              Elo fitting is now data-driven, but calibration is not fully proven yet. Confidence labels should
              still be treated as probability-spread diagnostics until backtests are published.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="border border-terminal-line bg-terminal-panel p-4">
              <div className="mb-3 flex items-center gap-2">
                <RefreshCw className="h-4 w-4 text-terminal-cyan" />
                <h2 className="text-lg font-semibold">Retraining</h2>
              </div>
              <p className="text-sm text-terminal-muted">
                Fixture ingest ensures historical Elo ratings exist, then refreshes tournament tips. Use the
                Elo admin endpoint with force=true to refit ratings from source history.
              </p>
            </div>
            <div className="border border-terminal-line bg-terminal-panel p-4">
              <div className="mb-3 flex items-center gap-2">
                <BarChart3 className="h-4 w-4 text-terminal-cyan" />
                <h2 className="text-lg font-semibold">Next Upgrade</h2>
              </div>
              <p className="text-sm text-terminal-muted">
                Publish backtested log loss, Brier score, and calibration curves per model version.
              </p>
            </div>
          </div>

          <div className="border border-terminal-line bg-terminal-panel p-4">
            <div className="mb-3 flex items-center gap-2">
              <Activity className="h-4 w-4 text-terminal-cyan" />
              <h2 className="text-lg font-semibold">Interpretation</h2>
            </div>
            <p className="text-sm text-terminal-muted">
              A “Low” confidence label does not mean the model is broken. It means the top 1X2 outcome is close
              to the alternatives, which is common in football.
            </p>
          </div>
        </section>
      </div>
    </DashboardShell>
  );
}
