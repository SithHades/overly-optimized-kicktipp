"use client";

import { RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ApiMatchListResponse, LiveFixtureExport, LiveFixtureExportRow } from "@/lib/live-fixtures";

export function LiveFixtureTable() {
  const [fixtures, setFixtures] = useState<LiveFixtureExportRow[]>([]);
  const [exportedAt, setExportedAt] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
    const matchesUrl = apiBaseUrl ? `${apiBaseUrl.replace(/\/$/, "")}/api/matches` : "/api/matches";

    fetch(matchesUrl, { cache: "no-store" })
      .then((response) => {
        if (!response.ok) {
          throw new Error("API match feed unavailable");
        }
        return response.json();
      })
      .then((payload: ApiMatchListResponse) => {
        setFixtures(
          payload.matches.map((match) => ({
            id: match.id,
            source: match.source ?? "api",
            source_match_id: match.source_match_id ?? String(match.id),
            date: match.date,
            stage: match.stage,
            group_name: match.group_name,
            home_team: match.home_team.name,
            away_team: match.away_team.name,
            venue: match.venue,
            status: match.status,
            home_score: null,
            away_score: null
          }))
        );
        setExportedAt(null);
      })
      .catch(() =>
        fetch("/live-fixtures.json", { cache: "no-store" })
          .then((response) => response.json())
          .then((payload: LiveFixtureExport) => {
            setFixtures(payload.fixtures);
            setExportedAt(payload.exported_at);
          })
      )
      .finally(() => setLoading(false));
  }, []);

  return (
    <section>
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold text-terminal-ink">Live Fixture Feed</h2>
          <p className="text-sm text-terminal-muted">
            {exportedAt ? `Last ingest export: ${exportedAt}` : `Loaded ${fixtures.length} matches from API match feed`}
          </p>
        </div>
        <Button onClick={() => window.location.reload()}>
          <RefreshCw className="h-4 w-4" />
          Reload
        </Button>
      </div>
      <div className="overflow-x-auto border border-terminal-line">
        <table className="min-w-full border-collapse text-sm">
          <thead className="bg-terminal-panel text-left font-mono text-xs uppercase text-terminal-muted">
            <tr>
              <th className="border-b border-terminal-line px-3 py-2">Date</th>
              <th className="border-b border-terminal-line px-3 py-2">Match</th>
              <th className="border-b border-terminal-line px-3 py-2">Stage</th>
              <th className="border-b border-terminal-line px-3 py-2">Venue</th>
              <th className="border-b border-terminal-line px-3 py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td className="px-3 py-4 text-terminal-muted" colSpan={5}>
                  Loading fixtures...
                </td>
              </tr>
            ) : null}
            {!loading && fixtures.length === 0 ? (
              <tr>
                <td className="px-3 py-4 text-terminal-muted" colSpan={5}>
                  No live fixture export is available.
                </td>
              </tr>
            ) : null}
            {fixtures.map((fixture) => (
              <tr key={`${fixture.source}-${fixture.source_match_id}`} className="bg-terminal-bg odd:bg-terminal-panel/45">
                <td className="whitespace-nowrap border-b border-terminal-line px-3 py-3 font-mono text-xs text-terminal-muted">
                  {new Date(fixture.date).toLocaleString()}
                </td>
                <td className="border-b border-terminal-line px-3 py-3">
                  <div className="font-medium text-terminal-ink">
                    {fixture.home_team} vs {fixture.away_team}
                  </div>
                  <div className="font-mono text-xs text-terminal-muted">{fixture.source}</div>
                </td>
                <td className="border-b border-terminal-line px-3 py-3 text-terminal-muted">
                  {fixture.group_name ?? fixture.stage}
                </td>
                <td className="border-b border-terminal-line px-3 py-3 text-terminal-muted">{fixture.venue ?? "-"}</td>
                <td className="border-b border-terminal-line px-3 py-3">
                  <Badge tone={fixture.status === "finished" ? "green" : "cyan"}>{fixture.status}</Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
