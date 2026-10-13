export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}
export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  if (window.location.protocol === "file:")
    throw new Error(
      "Povezani CRM zahteva pokrenut backend. Ovaj HTML fajl služi za demo pregled.",
    );
  const response = await fetch("/api" + path, {
    credentials: "same-origin",
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.headers.get("content-type")?.includes("application/json"))
    throw new Error(
      "Backend trenutno nije dostupan. Pokušajte ponovo kada bude pokrenut.",
    );
  const data = await response.json();
  if (!response.ok)
    throw new ApiError(
      response.status,
      typeof data.detail === "string"
        ? data.detail
        : "Proverite uneta polja i pokušajte ponovo.",
    );
  return data as T;
}
export const errorText = (error: unknown) =>
  error instanceof Error
    ? error.message
    : "Zahtev nije uspeo. Pokušajte ponovo.";
