import { expect, it } from "vitest";
import { maxDocumentSize, validateDocument } from "./salesDocuments";

it("accepts common sales documents and rejects empty, unsupported or oversized files before upload", () => {
  for (const name of ["Ponuda.PDF", "Cenovnik.xlsx", "Ugovor.docx", "Slika.jpg"]) {
    expect(validateDocument({ name, size: 100 })).toBeNull();
  }
  expect(validateDocument({ name: "Ponuda.pdf", size: maxDocumentSize })).toBeNull();
  expect(validateDocument({ name: "Ponuda.pdf", size: maxDocumentSize + 1 })).toContain("10 MB");
  expect(validateDocument({ name: "Ponuda.pdf", size: 0 })).toContain("prazan");
  expect(validateDocument({ name: "Ponuda.pdf.html", size: 100 })).toContain("Dozvoljeni");
  expect(validateDocument({ name: "a".repeat(252) + ".pdf", size: 100 })).toContain("255");
});
