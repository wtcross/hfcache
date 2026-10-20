export function uncheckedResponse(value: unknown): { allowed: boolean } {
  return value as { allowed: boolean };
}
