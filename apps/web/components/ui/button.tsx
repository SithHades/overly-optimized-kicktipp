import { cn } from "@/lib/utils";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary";
};

export function Button({ className, variant = "secondary", ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex h-9 items-center justify-center gap-2 border px-3 text-sm font-medium transition-colors",
        variant === "primary"
          ? "border-terminal-amber bg-terminal-amber text-black hover:bg-terminal-amber/90"
          : "border-terminal-line bg-terminal-panel text-terminal-ink hover:border-terminal-cyan",
        className
      )}
      {...props}
    />
  );
}
