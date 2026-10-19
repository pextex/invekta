export type EmailPart = { text: string; bold: boolean };
export type EmailBlock = { kind: "paragraph" | "list"; lines: EmailPart[][] };
export function inlineParts(text: string): EmailPart[] {
  const parts: EmailPart[] = [];
  const pattern = /\*\*([^*\n]+)\*\*/g;
  let start = 0;
  for (const match of text.matchAll(pattern)) {
    if (match.index! > start) parts.push({ text: text.slice(start, match.index), bold: false });
    parts.push({ text: match[1], bold: true });
    start = match.index! + match[0].length;
  }
  if (start < text.length) parts.push({ text: text.slice(start), bold: false });
  return parts;
}
export function emailBlocks(body: string): EmailBlock[] {
  const blocks: EmailBlock[] = [];
  for (const paragraph of body.replace(/\r\n?/g, "\n").split(/\n\s*\n/)) {
    if (!paragraph.trim()) continue;
    let kind: EmailBlock["kind"] | null = null;
    for (const line of paragraph.split("\n")) {
      const list = /^\s*[-•]\s+/.test(line);
      const nextKind = list ? "list" : "paragraph";
      if (kind !== nextKind) { blocks.push({ kind: nextKind, lines: [] }); kind = nextKind; }
      blocks[blocks.length - 1].lines.push(inlineParts(list ? line.replace(/^\s*[-•]\s+/, "") : line));
    }
  }
  return blocks;
}
const escapeHtml = (text: string) => text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
export function emailPlainText(body: string): string {
  return body.replace(/\r\n?/g, "\n").split("\n").map(line => inlineParts(line).map(part => part.text).join("")).join("\n");
}
export function emailHtml(body: string): string {
  return emailBlocks(body).map(block => {
    const lines = block.lines.map(line => line.map(part => part.bold ? `<strong>${escapeHtml(part.text)}</strong>` : escapeHtml(part.text)).join(""));
    return block.kind === "list" ? `<ul style="margin:0 0 16px;padding-left:22px">${lines.map(line => `<li>${line}</li>`).join("")}</ul>` : `<p style="margin:0 0 16px;line-height:1.6">${lines.join("<br>")}</p>`;
  }).join("");
}
export function emailClipboard(draft: { recipient?: string | null; subject: string; body: string }) {
  const header = `${draft.recipient?.trim() ? `Za: ${draft.recipient.trim()}\n` : ""}Predmet: ${draft.subject}`;
  return {
    plain: `${header}\n\n${emailPlainText(draft.body)}`,
    html: `<div style="font-family:Arial,sans-serif;font-size:14px;color:#202936">${emailHtml(header)}${emailHtml(draft.body)}</div>`,
  };
}
