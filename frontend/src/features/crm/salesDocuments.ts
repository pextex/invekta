import { api, ApiError } from "../../lib/api";

export const documentAccept = ".pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg";
export const maxDocumentSize = 10 * 1024 * 1024;
export type SalesDocument = {
  id: number; business_unit_id: number; title: string; filename: string;
  content_type: string; size_bytes: number; created_at: string; uploaded_by_name: string;
};
export type DocumentPage = { items: SalesDocument[]; total: number };

export function validateDocument(file: Pick<File, "name" | "size">): string | null {
  const extension = "." + file.name.split(".").pop()?.toLowerCase();
  if (!documentAccept.split(",").includes(extension)) return "Dozvoljeni su PDF, Word, Excel, PNG i JPG fajlovi.";
  if (!file.size) return "Izabrani fajl je prazan.";
  if (file.size > maxDocumentSize) return "Fajl može imati najviše 10 MB.";
  if (file.name.length > 255) return "Naziv fajla može imati najviše 255 znakova.";
  return null;
}

export function documentSize(bytes: number) {
  return bytes < 1024 * 1024 ? `${Math.max(1, Math.ceil(bytes / 1024))} KB` : `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function uploadDocument(unit: number, file: File, title: string) {
  const params = new URLSearchParams({ filename: file.name, title: title.trim() });
  return api<SalesDocument>(`/units/${unit}/sales-documents?${params}`, {
    method: "POST", headers: { "Content-Type": "application/octet-stream" }, body: file,
  });
}

export async function downloadDocument(unit: number, document: SalesDocument) {
  const response = await fetch(`/api/units/${unit}/sales-documents/${document.id}/download`, { credentials: "same-origin" });
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new ApiError(response.status, typeof data?.detail === "string" ? data.detail : "Preuzimanje nije uspelo. Pokušajte ponovo.");
  }
  if (!response.headers.get("content-type")?.includes("application/octet-stream")) {
    throw new Error("Backend trenutno nije dostupan. Fajl nije preuzet.");
  }
  return response.blob();
}
