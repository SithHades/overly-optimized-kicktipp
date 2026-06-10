import { DashboardShell } from "@/components/dashboard-shell";
import { LiveFixtureTable } from "@/components/live-fixture-table";
import { MatchTable } from "@/components/match-table";
import { predictionRows } from "@/lib/mock-data";

export default function MatchesPage() {
  return (
    <DashboardShell>
      <div className="mb-3">
        <h2 className="text-xl font-semibold text-terminal-ink">Matches</h2>
        <p className="text-sm text-terminal-muted">Model probabilities, market comparison, and EV-optimal picks.</p>
      </div>
      <div className="space-y-6">
        <LiveFixtureTable />
        <section>
          <h2 className="mb-2 text-lg font-semibold text-terminal-ink">Prediction Preview</h2>
          <MatchTable rows={predictionRows} />
        </section>
      </div>
    </DashboardShell>
  );
}
