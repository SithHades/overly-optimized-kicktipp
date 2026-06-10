import { formatPercent } from "@/lib/utils";

type ProbabilityStripProps = {
  probabilities: [number, number, number];
};

export function ProbabilityStrip({ probabilities }: ProbabilityStripProps) {
  const [home, draw, away] = probabilities;
  return (
    <div className="w-full min-w-40">
      <div className="flex h-2 overflow-hidden border border-terminal-line bg-terminal-bg">
        <div className="bg-terminal-green" style={{ width: `${home * 100}%` }} />
        <div className="bg-terminal-amber" style={{ width: `${draw * 100}%` }} />
        <div className="bg-terminal-red" style={{ width: `${away * 100}%` }} />
      </div>
      <div className="mt-1 grid grid-cols-3 gap-2 font-mono text-xs text-terminal-muted">
        <span>{formatPercent(home)}</span>
        <span>{formatPercent(draw)}</span>
        <span>{formatPercent(away)}</span>
      </div>
    </div>
  );
}
