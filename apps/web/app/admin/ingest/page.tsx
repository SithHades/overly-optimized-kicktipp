"use client";

import { DatabaseZap } from "lucide-react";
import { useState } from "react";

import { DashboardShell } from "@/components/dashboard-shell";
import { Button } from "@/components/ui/button";

type IngestResponse = {
  provider: string;
  fixture_count: number;
  postgres_upserts: number;
  tournament_tip_count: number;
  warnings: string[];
};

export default function AdminIngestPage() {
  const [token, setToken] = useState("");
  const [provider, setProvider] = useState("football-data");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<IngestResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function runIngest() {
    setLoading(true);
    setError(null);
    setResult(null);

    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
    const baseUrl = apiBaseUrl ? apiBaseUrl.replace(/\/$/, "") : "";

    try {
      const response = await fetch(`${baseUrl}/api/admin/ingest-fixtures?provider=${provider}`, {
        method: "POST",
        headers: {
          "X-Admin-Token": token
        }
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail ?? "Ingest failed");
      }
      setResult(payload);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Ingest failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <DashboardShell>
      <section className="max-w-2xl border border-terminal-line bg-terminal-panel p-4">
        <div className="mb-4 flex items-center gap-2">
          <DatabaseZap className="h-4 w-4 text-terminal-cyan" />
          <h2 className="text-xl font-semibold text-terminal-ink">Fixture Ingest</h2>
        </div>

        <div className="space-y-4">
          <label className="block">
            <span className="mb-1 block text-sm text-terminal-muted">Provider</span>
            <select
              className="h-10 w-full border border-terminal-line bg-terminal-bg px-3 font-mono text-terminal-ink"
              value={provider}
              onChange={(event) => setProvider(event.target.value)}
            >
              <option value="openfootball">openfootball</option>
              <option value="football-data">football-data</option>
            </select>
          </label>

          <label className="block">
            <span className="mb-1 block text-sm text-terminal-muted">Admin token</span>
            <input
              className="h-10 w-full border border-terminal-line bg-terminal-bg px-3 font-mono text-terminal-ink"
              type="password"
              value={token}
              onChange={(event) => setToken(event.target.value)}
            />
          </label>

          <Button disabled={loading || !token} onClick={runIngest} variant="primary">
            <DatabaseZap className="h-4 w-4" />
            {loading ? "Running..." : "Run ingest"}
          </Button>
        </div>

        {result ? (
          <div className="mt-4 border border-terminal-line bg-terminal-bg p-3 font-mono text-sm text-terminal-green">
            {result.provider}: {result.postgres_upserts} match upserts, {result.tournament_tip_count} tournament Tipps
          </div>
        ) : null}

        {error ? (
          <div className="mt-4 border border-terminal-red bg-terminal-bg p-3 font-mono text-sm text-terminal-red">
            {error}
          </div>
        ) : null}
      </section>
    </DashboardShell>
  );
}
