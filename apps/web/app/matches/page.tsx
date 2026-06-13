import { DashboardShell } from "@/components/dashboard-shell";
import { PredictionBoard } from "@/components/prediction-board";

export default function MatchesPage() {
  return (
    <DashboardShell>
      <div className="mb-3">
        <h2 className="text-xl font-semibold text-terminal-ink">Matches</h2>
        <p className="text-sm text-terminal-muted">
          One combined board for fixtures, venues, results, model probabilities, expected points, and drill-down analysis.
        </p>
      </div>
      <PredictionBoard limit={null} showControls />
    </DashboardShell>
  );
}
