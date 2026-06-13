import { DashboardShell } from "@/components/dashboard-shell";
import { LiveDashboardSummary } from "@/components/live-dashboard-summary";
import { PredictionBoard } from "@/components/prediction-board";
import { Badge } from "@/components/ui/badge";

export default function Home() {
  return (
    <DashboardShell>
      <LiveDashboardSummary />

      <div className="mt-4">
        <section>
          <div className="mb-2 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-terminal-ink">Live Match Board</h2>
            <Badge tone="cyan">Tipp EV: expected points</Badge>
          </div>
          <PredictionBoard limit={8} scope="upcoming" />
        </section>
      </div>
    </DashboardShell>
  );
}
