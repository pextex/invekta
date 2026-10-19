import { organizationAiName } from "../organizations";
export type TourStep = { page: string; target: string; title: string; text: string };
export type TourLesson = { id: string; title: string; steps: TourStep[] };
const nav = (page: string) => `[data-tour-nav="${page}"]`;
export function tourLessons(organization?: string, canViewHistory = false, canManageUsers = false): TourLesson[] {
  const ai = organizationAiName(organization);
  const lessons: TourLesson[] = [
    { id: "companies", title: "Kompanije i kontakti", steps: [
      { page: "Kompanije", target: nav("Kompanije"), title: "Vaše kompanije", text: "U kartici Kompanije nalaze se kompanije kojima imate pristup. Vodič pokazuje elemente aplikacije. Vi birate kada ćete preći na sledeći korak." },
      { page: "Kompanije", target: ".global-search", title: "Pronađite kompaniju", text: "U ovo polje unesite naziv kompanije ili delatnost. Pretraga sužava prikaz. Otvaranjem kompanije možete pregledati njene kontakte i prodajne prilike." },
      { page: "Kompanije", target: ".page-heading .primary-button", title: "Nova kompanija", text: "Dugme za dodavanje kompanije otvara obrazac za naziv, adresu, PIB i kontakt osobe. Podaci se čuvaju tek kada potvrdite obrazac. Vodič neće dodavati kompanije umesto vas." },
    ]},
    { id: "pipeline", title: "Prodajni levak", steps: [
      { page: "Prodajni levak", target: nav("Prodajni levak"), title: "Pratite prodaju", text: "Prodajni levak prikazuje prilike po fazama. Svaka kartica predstavlja jedan posao, njegovu vrednost i trenutno stanje." },
      { page: "Prodajni levak", target: "[data-tour-content] .kanban", title: "Promena statusa", text: "Priliku možete premestiti u drugu fazu pomoću dostupnih kontrola na kartici. Realizovano označava uspešan posao, a Nije realizovano posao koji nije zaključen. Promene utiču na izveštaje i ostvarenje targeta." },
    ]},
    { id: "targets", title: "Lični i kolektivni target", steps: [
      { page: "Targeti", target: ".target-month", title: "Izaberite mesec", text: "Izaberite mesec za koji želite da pratite target. Ciljevi i ostvarenje prikazuju se za taj mesec." },
      { page: "Targeti", target: ".target-person", title: "Ovo je vaš target", text: "Prvo su prikazani pojedinačni targeti po vrstama posla, sa ostvarenim iznosom i procentom napretka. Komercijalista vidi svoj target. Menadžeri i administratori mogu pregledati i postaviti pojedinačne ciljeve." },
      { page: "Targeti", target: ".team-bonus", title: "Kolektivni target", text: "Ispod pojedinačnih targeta nalazi se kolektivni cilj tima. Ovde pratite zajedničko ostvarenje, svoj doprinos i opis zajedničkog bonusa." },
    ]},
    { id: "tasks", title: "Zadaci i kalendar", steps: [
      { page: "Zadaci", target: ".task-calendar-panel", title: "Plan za mesec", text: "U kalendaru izaberite dan da pregledate njegove zadatke. Oznake razlikuju planirane i završene aktivnosti." },
      { page: "Zadaci", target: ".page-heading .primary-button", title: "Dodajte zadatak", text: "Dugme Dodaj novi zadatak otvara unos naziva, datuma, vremena i kompanije. Vodič ne potvrđuje niti čuva zadatak. Sačuvajte ga sami kada proverite unete podatke." },
      { page: "Zadaci", target: ".task-day-panel", title: "Zadaci za izabrani dan", text: "Ovde se nalaze aktivnosti izabranog dana. Kada završite aktivnost, označite je kao završenu. Po potrebi možete izmeniti podatke zadatka." },
    ]},
    { id: "ai", title: ai, steps: [
      { page: "Invekta AI", target: nav("Invekta AI"), title: ai, text: `${ai} priprema poslovni mejl za izabrani brend. Koristi odabranu kompaniju, kontakte i dostupno odobreno znanje o brendu.` },
      { page: "Invekta AI", target: ".ai-grid .panel:first-child", title: "Opišite poruku", text: "Izaberite kompaniju i opišite kome se obraćate i šta želite da postignete. Kontakti se popunjavaju automatski. Klik na dugme za pripremu mejla pokreće generisanje; vodič ga neće pokrenuti umesto vas." },
      { page: "Invekta AI", target: ".ai-grid .panel:last-child", title: "Pregledajte pa kopirajte", text: "Ovde ćete dobiti predlog mejla. Proverite činjenice, primaoce i tekst, pa kopirajte mejl. Asistent ne šalje mejlove. Kopirajte tekst pre napuštanja stranice jer se nacrt ne čuva." },
    ]},
    { id: "reports", title: "Izveštaji", steps: [
      { page: "Izveštaji", target: ".report-toolbar", title: "Dnevni i mesečni pregled", text: "Izaberite dnevni ili mesečni period. Izveštaji prikazuju nove prilike, promene statusa i realizaciju u tom periodu, u okviru vaših ovlašćenja." },
      { page: "Izveštaji", target: ".report-charts", title: "Pratite rezultate", text: "Grafikoni pokazuju kretanje kroz faze prodaje i odnos aktivnosti. Ako nema podataka, izaberite drugi period. Menadžeri imaju i pregled po komercijalistima." },
    ]},
  ];
  if (canViewHistory) lessons.push({ id: "history", title: "Hronologija promena - log", steps: [
    { page: "Hronologija promena - log", target: nav("Hronologija promena - log"), title: "Hronologija promena - log", text: "Ova kartica je dostupna samo menadžerima i administratorima. Prikazuje kreiranje prilika i promene statusa, sa vremenom promene i korisnikom koji ju je izvršio." },
    { page: "Hronologija promena - log", target: ".report-toolbar", title: "Pronađite promenu", text: "Izaberite period i komercijalistu. Promene su poređane od najnovije. Dugmad ispod tabele služe za prelazak na starije zapise." },
  ]});
  if (canManageUsers) lessons.push({ id: "users", title: "Korisnici i pristup", steps: [
    { page: "Podešavanja", target: '[data-tour-nav="Podešavanja"]', title: "Administracija pristupa", text: "Ovde administrator upravlja korisnicima i njihovim pristupom poslovnim jedinicama. Pre promene uloge proverite kom brendu korisnik treba da pristupa. Vodič ne menja ovlašćenja." },
  ]});
  return lessons;
}
