import Link from "next/link";
import { Activity, Braces, ChartNoAxesCombined, Crown, Trophy } from "lucide-react";

import { Badge } from "@/components/ui/badge";

const navItems = [
  { href: "/", label: "Dashboard", icon: Activity },
  { href: "/matches", label: "Matches", icon: ChartNoAxesCombined },
  { href: "/tournament-tips", label: "Tournament", icon: Crown },
  { href: "/leaderboard-optimizer", label: "Optimizer", icon: Trophy },
  { href: "/model-lab", label: "Model Lab", icon: Braces }
];

export function DashboardShell({ children }: { children: React.ReactNode }) {
  return (
    <main className="min-h-screen bg-terminal-bg">
      <header className="border-b border-terminal-line">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-4 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="font-mono text-xs uppercase tracking-[0.2em] text-terminal-amber">WorldCupQuant</div>
            <h1 className="text-2xl font-semibold text-terminal-ink">Prediction Terminal</h1>
          </div>
          <nav className="flex flex-wrap gap-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className="inline-flex h-9 items-center gap-2 border border-terminal-line bg-terminal-panel px-3 text-sm text-terminal-muted hover:border-terminal-cyan hover:text-terminal-ink"
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
      </header>
      <section className="mx-auto max-w-7xl px-4 py-4">
        <div className="mb-4 flex flex-wrap gap-2">
          <Badge tone="cyan">Model: historical Elo + Poisson</Badge>
          <Badge tone="green">Fixtures: live API</Badge>
          <Badge tone="amber">Ratings: international history</Badge>
        </div>
        {children}
      </section>
    </main>
  );
}
