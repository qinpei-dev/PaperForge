import type { HTMLAttributes } from "react";

type BadgeVariant = "default" | "success" | "warning" | "danger" | "neutral" | "primary";

type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  variant?: BadgeVariant;
};

export function Badge({ className = "", variant = "default", ...props }: BadgeProps) {
  const variantClass = variant !== "default" ? `pf-badge--${variant}` : "";
  return <span className={`pf-badge ${variantClass} ${className}`.trim()} {...props} />;
}
