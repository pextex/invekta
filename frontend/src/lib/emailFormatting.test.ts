import { expect, it } from "vitest";
import { emailBlocks, emailClipboard, emailHtml, emailPlainText } from "./emailFormatting";
it("preserves paragraphs, a signature's line breaks and modest bold emphasis", () => {
  const body = "Poštovani,\n\nPredlažem **kratak razgovor**.\n\nSrdačno,\nAna\nINVEKTA";
  expect(emailBlocks(body)).toHaveLength(3);
  expect(emailHtml(body)).toContain("<strong>kratak razgovor</strong>");
  expect(emailHtml(body)).toContain("Srdačno,<br>Ana<br>INVEKTA");
  expect(emailPlainText(body)).toBe("Poštovani,\n\nPredlažem kratak razgovor.\n\nSrdačno,\nAna\nINVEKTA");
});
it("treats generated HTML and unsafe markup as text, including in bold and copied HTML", () => {
  const body = '**<img src=x onerror="alert(1)">**\n\n<script>alert(2)</script>';
  const html = emailHtml(body);
  expect(html).not.toContain("<img"); expect(html).not.toContain("<script");
  expect(html).toContain("&lt;img"); expect(html).toContain("&lt;script&gt;");
});
it("keeps a genuine list and escapes clipboard subject/recipients while omitting bold markers in plain text", () => {
  const content = emailClipboard({ recipient: 'a@example.test', subject: '<img src=x>', body: '- **Prva korist**\n- Druga korist\n\nSledeći korak.' });
  expect(content.html).toContain("<ul"); expect(content.html).toContain("<li><strong>Prva korist</strong></li>");
  expect(content.html).toContain("&lt;img src=x&gt;");
  expect(content.plain).toContain("Za: a@example.test\nPredmet: <img src=x>");
  expect(content.plain).not.toContain("**");
});
