const NON_ACTIONABLE_MESSAGES = [
  "failed to fetch",
  "network error",
  "network request failed",
  "load failed",
  "fetch failed",
  "internal server error",
  "bad gateway",
  "service unavailable",
  "err_connection_refused",
  "unexpected end of json input",
  "syntaxerror",
  "[object object]",
  "undefined",
  "null",
];

function isNonActionableMessage(message: string) {
  const normalized = message.trim().toLowerCase();
  return !normalized
    || NON_ACTIONABLE_MESSAGES.some((item) => normalized === item || normalized.startsWith(`${item}:`))
    || /^\d{3}(\s|$)/.test(normalized)
    || normalized.includes("traceback");
}

export function userFacingError(reason: unknown, fallback: string) {
  const message = typeof reason === "string" ? reason.trim() : reason instanceof Error ? reason.message.trim() : "";
  return isNonActionableMessage(message) ? fallback : message;
}
