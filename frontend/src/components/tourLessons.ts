import { organizationAiName } from "../organizations";
export type TourStep = { page: string; target: string; title: string; text: string };
export type TourLesson = { id: string; title: string; steps: TourStep[] };
const nav = (page: string) => `[data-tour-nav="${page}"]`;
export function tourLessons(organization?: string, canViewHistory = false, canManageUsers = false, marketing = false): TourLesson[] {
  const ai = organizationAiName(organization);
  if (marketing) return [
    { id: "marketing-dashboard", title: "Početna tabla", steps: [{ page: "Početna tabla", target: ".metrics", title: "Marketing pregled", text: "Ovde pratite broj svojih porudžbina po četiri faze. Podaci pripadaju aktivnom brendu." }] },
    { id: "marketing-orders", title: "Porudžbine", steps: [
      { page: "Porudžbine", target: nav("Porudžbine"), title: "Porudžbine", text: "Ovde unosite ime, prezime, telefon, email i izvor porudžbine: sajt ili telefon. Email je opcion. Marketing vidi samo svoje porudžbine." },
      { page: "Porudžbine", target: ".page-heading .primary-button", title: "Nova porudžbina", text: "Otvorite obrazac, unesite podatke i sačuvajte porudžbinu. Vodič ne unosi niti čuva podatke umesto vas." },
    ] },
    { id: "marketing-pipeline", title: "Prodajni levak", steps: [{ page: "Prodajni levak", target: ".order-board", title: "Četiri faze porudžbine", text: "Porudžbine, Ponuda poslata, Realizovano i Nije realizovano. Karticu prevucite u drugu kolonu ili promenite status izborom na kartici. Kolone imaju zasebne stranice za starije porudžbine." }] },
    { id: "marketing-reports", title: "Izveštaji", steps: [{ page: "Izveštaji", target: ".report-toolbar", title: "Period porudžbina", text: "Izaberite period unosa porudžbina. Pokazatelji prikazuju njihov trenutni status, a ne istoriju promena statusa." }] },
    { id: "marketing-ai", title: ai, steps: [{ page: "Invekta AI", target: ".ai-grid", title: ai, text: "Pronađite porudžbinu, izaberite je i opišite mejl. Pregledajte nacrt, pa ga kopirajte. Asistent ne šalje mejl." }] },
  ];
  const lessons: TourLesson[] = [
    { id: "dashboard", title: "Početna tabla", steps: [
      { page: "Početna tabla", target: nav("Početna tabla"), title: "Početna tabla", text: "Početna tabla je polazni ekran za vaš radni dan. Ovde su pregled prodaje, današnji zadaci i prečice ka ostalim karticama. Podaci koje vidite zavise od izabranog brenda i vaših ovlašćenja." },
      { page: "Početna tabla", target: ".daily-welcome", title: "Vaš plan za danas", text: "U ovom delu nalaze se zadaci za danas. Dugme Otvori kalendar vodi na karticu Zadaci, gde možete pregledati druge dane i planirati sledeće aktivnosti." },
      { page: "Početna tabla", target: ".metrics", title: "Pokazatelji prodaje", text: "Ove kartice pokazuju ključne podatke o kompanijama i prodajnim prilikama. Vrednost otvorenih prilika predstavlja potencijal prodaje, a ne ostvaren prihod. Prikazane vrednosti pripadaju trenutno izabranom brendu." },
      { page: "Početna tabla", target: ".bars", title: "Pregled prodajnog levka", text: "Ovaj pregled pokazuje koliko je prilika u svakoj fazi prodaje. Dugme Otvori prodajni levak vodi na detaljne kartice prilika. Vodič sada nastavlja na karticu Kompanije." },
    ]},
    { id: "companies", title: "Kompanije", steps: [
      { page: "Kompanije", target: nav("Kompanije"), title: "Vaše kompanije", text: "U kartici Kompanije nalaze se kompanije kojima imate pristup. Vodič pokazuje elemente aplikacije. Vi birate kada ćete preći na sledeći korak." },
      { page: "Kompanije", target: ".global-search", title: "Pronađite kompaniju", text: "U ovo polje unesite naziv kompanije ili delatnost. Pretraga sužava prikaz. Otvaranjem kompanije možete pregledati njene kontakte i prodajne prilike." },
      { page: "Kompanije", target: ".page-heading .primary-button", title: "Nova kompanija", text: "Dugme za dodavanje kompanije otvara obrazac za naziv, adresu, PIB i kontakt osobe. Podaci se čuvaju tek kada potvrdite obrazac. Vodič neće dodavati kompanije umesto vas." },
    ]},
    { id: "pipeline", title: "Prodajni levak", steps: [
      { page: "Prodajni levak", target: nav("Prodajni levak"), title: "Pratite prodaju", text: "Prodajni levak prikazuje prilike po fazama. Svaka kartica predstavlja jedan posao, njegovu vrednost i trenutno stanje." },
      { page: "Prodajni levak", target: "[data-tour-content] .kanban", title: "Promena statusa", text: "Priliku možete premestiti u drugu fazu pomoću dostupnih kontrola na kartici. Realizovano označava uspešan posao, a Nije realizovano posao koji nije zaključen. Promene utiču na izveštaje i ostvarenje targeta." },
    ]},
    { id: "targets", title: "Targeti", steps: [
      { page: "Targeti", target: ".target-month", title: "Izaberite mesec", text: "Izaberite mesec za koji želite da pratite target. Ciljevi i ostvarenje prikazuju se za taj mesec." },
      { page: "Targeti", target: ".target-person", title: "Ovo je vaš target", text: "Prvo su prikazani pojedinačni targeti po vrstama posla, sa ostvarenim iznosom i procentom napretka. Komercijalista vidi svoj target. Menadžeri i administratori mogu pregledati i postaviti pojedinačne ciljeve." },
      { page: "Targeti", target: ".team-bonus", title: "Kolektivni target", text: "Ispod pojedinačnih targeta nalazi se kolektivni cilj tima. Ovde pratite zajedničko ostvarenje, svoj doprinos i opis zajedničkog bonusa." },
    ]},
    { id: "tasks", title: "Zadaci", steps: [
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

export function nextTourPosition(lessons: TourLesson[], lessonId: string | null, index: number) {
  const current = lessons.findIndex(lesson => lesson.id === lessonId);
  if (current < 0) return null;
  if (index + 1 < lessons[current].steps.length) return { lessonId: lessons[current].id, index: index + 1 };
  const next = lessons[current + 1];
  return next ? { lessonId: next.id, index: 0 } : null;
}
export function previousTourPosition(lessons: TourLesson[], lessonId: string | null, index: number) {
  const current = lessons.findIndex(lesson => lesson.id === lessonId);
  if (current < 0) return null;
  if (index > 0) return { lessonId: lessons[current].id, index: index - 1 };
  const previous = lessons[current - 1];
  return previous ? { lessonId: previous.id, index: previous.steps.length - 1 } : null;
}
