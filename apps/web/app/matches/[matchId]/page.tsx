import Link from "next/link";

import { DashboardShell } from "@/components/dashboard-shell";
import { LiveOptimizer } from "@/components/live-optimizer";

type MatchDetailPageProps = {
  params: Promise<{ matchId: string }>;
};

export default async function MatchDetailPage({ params }: MatchDetailPageProps) {
  const { matchId } = await params;
  const parsedMatchId = Number(matchId);

  return (
    <DashboardShell>
      <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-terminal-ink">Match Detail Terminal</h2>
          <p className="text-sm text-terminal-muted">
            Single-match optimizer view with scenario EV, model lenses, AI preview, and scoring-rule recompute.
          </p>
        </div>
        <Link
          href="/matches"
          className="inline-flex h-9 items-center justify-center border border-terminal-line bg-terminal-panel px-3 text-sm text-terminal-ink hover:border-terminal-cyan"
        >
          Back to matches
        </Link>
      </div>
      <LiveOptimizer initialMatchId={Number.isFinite(parsedMatchId) ? parsedMatchId : undefined} lockMatch />
    </DashboardShell>
  );
}
