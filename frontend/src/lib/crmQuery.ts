import { QueryClient, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError } from "./api";

export const crmQueryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 0,
      retry: false,
      refetchOnWindowFocus: true,
      refetchInterval: 30_000,
      refetchIntervalInBackground: false,
    },
  },
});
export const crmKey = (unit: number, path: string) =>
  ["crm", unit, path] as const;
export function useCrmQuery<T>(unit: number, path: string, enabled = true) {
  return useQuery({
    queryKey: crmKey(unit, path),
    queryFn: ({ signal }) => api<T>(`/units/${unit}${path}`, { signal }),
    enabled: enabled && unit > 0,
  });
}
export async function crmRequest<T>(
  client: QueryClient,
  unit: number,
  path: string,
  init: RequestInit,
): Promise<T> {
  try {
    const result = await api<T>(`/units/${unit}${path}`, init);
    await client.invalidateQueries({ queryKey: ["crm", unit] });
    return result;
  } catch (error) {
    if (error instanceof ApiError && error.status === 409)
      await client.invalidateQueries({ queryKey: ["crm", unit] });
    throw error;
  }
}
export function useCrmRequest(unit: number) {
  const client = useQueryClient();
  return <T>(path: string, init: RequestInit) =>
    crmRequest<T>(client, unit, path, init);
}
