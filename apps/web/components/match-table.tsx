import { Badge } from "@/components/ui/badge";
import { ProbabilityStrip } from "@/components/probability-strip";
import type { PredictionRow } from "@/lib/mock-data";

const confidenceTone = {
  Low: "red",
  Medium: "amber",
  High: "green"
} as const;

export function MatchTable({ rows }: { rows: PredictionRow[] }) {
  return (
    <div className="overflow-x-auto border border-terminal-line">
      <table className="min-w-full border-collapse text-sm">
        <thead className="bg-terminal-panel text-left font-mono text-xs uppercase text-terminal-muted">
          <tr>
            <th className="border-b border-terminal-line px-3 py-2">Date</th>
            <th className="border-b border-terminal-line px-3 py-2">Match</th>
            <th className="border-b border-terminal-line px-3 py-2">Model 1X2</th>
            <th className="border-b border-terminal-line px-3 py-2">Best Tipp</th>
            <th className="border-b border-terminal-line px-3 py-2">Most Likely</th>
            <th className="border-b border-terminal-line px-3 py-2">Confidence</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} className="bg-terminal-bg odd:bg-terminal-panel/45">
              <td className="whitespace-nowrap border-b border-terminal-line px-3 py-3 font-mono text-xs text-terminal-muted">
                {row.date}
              </td>
              <td className="border-b border-terminal-line px-3 py-3">
                <div className="font-medium text-terminal-ink">{row.match}</div>
                <div className="font-mono text-xs text-terminal-muted">{row.stage}</div>
              </td>
              <td className="border-b border-terminal-line px-3 py-3">
                <ProbabilityStrip probabilities={row.model} />
              </td>
              <td className="border-b border-terminal-line px-3 py-3 font-mono text-terminal-amber">{row.bestTip}</td>
              <td className="border-b border-terminal-line px-3 py-3 font-mono text-terminal-muted">
                {row.mostLikelyScore}
              </td>
              <td className="border-b border-terminal-line px-3 py-3">
                <Badge tone={confidenceTone[row.confidence]}>{row.confidence}</Badge>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
