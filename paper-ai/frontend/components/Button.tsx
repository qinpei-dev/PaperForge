import type { ButtonHTMLAttributes } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "danger" };

export function Button({ className = "", variant = "primary", type = "button", ...props }: ButtonProps) {
  return <button type={type} className={`pf-button pf-button--${variant} ${className}`.trim()} {...props} />;
}
