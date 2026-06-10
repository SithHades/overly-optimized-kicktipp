import { cn } from "@/lib/utils";

type BadgeProps = {
  children: React.ReactNode;
  tone?: "neutral" | "green" | "amber" | "red" | "cyan";
};

const tones = {
  neutral: "border-terminal-line bg-terminal-panel text-terminal-muted",
  green: "border-terminal-green/40 bg-terminal-green/10 text-terminal-green",
  amber: "border-terminal-amber/40 bg-terminal-amber/10 text-terminal-amber",
  red: "border-terminal-red/40 bg-terminal-red/10 text-terminal-red",
  cyan: "border-terminal-cyan/40 bg-terminal-cyan/10 text-terminal-cyan"
};

export function Badge({ children, tone = "neutral" }: BadgeProps) {
  return (
    <span className={cn("inline-flex items-center border px-2 py-0.5 text-xs font-medium", tones[tone])}>
      {children}
    </span>
  );
}
