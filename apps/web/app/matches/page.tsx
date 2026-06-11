import { DashboardShell } from "@/components/dashboard-shell";
import { LiveFixtureTable } from "@/components/live-fixture-table";
import { PredictionBoard } from "@/components/prediction-board";

export default function MatchesPage() {
  return (
    <DashboardShell>
      <div className="mb-3">
        <h2 className="text-xl font-semibold text-terminal-ink">Matches</h2>
        <p className="text-sm text-terminal-muted">
          Model probabilities, expected points, and the Tipp with the best average payoff under your scoring rules.
        </p>
      </div>
      <div className="space-y-6">
        <LiveFixtureTable />
        <section>
          <h2 className="mb-2 text-lg font-semibold text-terminal-ink">Live Prediction Preview</h2>
          <PredictionBoard limit={null} showControls />
        </section>
      </div>
    </DashboardShell>
  );
}
