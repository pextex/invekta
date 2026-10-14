# Faza 3 — zadaci, aktivnosti i podsetnici

Datum: 14. oktobar 2026. Grana: `feat/crm-phase3-work`, zasnovana na `115e4aa` iz Faza 1–2. Faza 4 nije započeta. Nema merge-a, deployment-a, seed-a ili migracije nad poslovnom bazom.

## PR #1 i GitHub CI

Pre implementacije proverena je javna GitHub stranica, jer CLI/API i dalje vraćaju `Forbidden`:

- [PR #1](https://github.com/pextex/invekta/pull/1) je Draft, što sprečava spajanje. Draft status nije neuspešan test.
- [CRM checks run 38536483665](https://github.com/pextex/invekta/actions/runs/38536483665), [posao checks 115760489102](https://github.com/pextex/invekta/actions/runs/38536483665/job/115760489102): **succeeded**, trajanje 2m26s. Na početku pregleda run je bio In progress; provereno je i završno stanje pre predaje.
- GitHub prikazuje upozorenje o Node20 Actions koracima koji se izvršavaju na Node24 i obaveštenje o budućoj promeni ubuntu-latest slike. To nisu neuspešne provere.
- Ovo je CI Faza 1–2. Provere Faze 3 navedene ispod su lokalne; ne tvrditi da novi remote CI prolazi dok se ne izvrši za novu granu/PR.

PR #1 nije menjan u Ready niti spojen. Nova grana čuva odvojenu reviziju Faze 3. [Pregled samo promena Faze 3](https://github.com/pextex/invekta/compare/feat/crm-metrics-sync...feat/crm-phase3-work).

## Implementirano ponašanje

Postojeći ekran Zadaci sada koristi PostgreSQL preko FastAPI-ja i zajedničkog React Query sloja. Nova aplikacija ili navigacija nisu uvedeni. Vizuelni identitet LUU/Invekte ostaje, a postojeći CENOBOTS podaci i pristup nisu uklonjeni.

### Zadaci

- Kreiranje, izmena, statusi Otvoren/U toku/Završen/Otkazan, prioritet, rok, beleške i opciono vreme podsetnika.
- Kompanija i odgovorna osoba obavezni; prodajna prilika opciona i mora pripadati istoj kompaniji/jedinici.
- Filteri kompanije, odgovorne osobe i statusa; paginacija. Izbor prilika može učitati dodatne stranice.
- Optimistička verzija, zaključavanje reda i 409; neuspešna izmena ne zatvara nesnimljen formular.
- Arhiviranje je soft operacija, sa očuvanom istorijom. Prikaži i arhivirane omogućava vraćanje. Vraćen zapis ostaje Otkazan, dok korisnik izričito ne odluči o aktiviranju; stari podsetnici se ne pokreću automatski.

### Aktivnosti

- Zakazani i izvršeni pozivi, sastanci i beleške; statusi Zakazan/Završen/Otkazan.
- Vreme zakazivanja i izvršenja, beleške i ishod, odgovorna osoba i poslovni kontekst.
- Završavanje bez ručno unetog vremena izvršenja koristi stvarno serversko vreme. Čuvanje je izričita potvrda komercijaliste da je aktivnost izvršena.
- Istorija svake promene prikazuje autora i vreme, status, izmenjena polja i razumljive nazive osoba/kompanija/prilika. Izvorni ID-jevi ostaju u evidenciji; prikaz naziva koristi sadašnji naziv zapisa.

### Podsetnici

- Podsetnici i za zadatke i za zakazane aktivnosti; lični prikaz, pending/delivered/cancelled, oznaka pročitanog.
- In-app isporuka; nema email/SMS integracije ili plaćenog servisa.
- Worker radi nezavisno, zaključava roditeljski zapis pa podsetnik, koristi SKIP LOCKED i atomsku transakciju. Ponovljena obrada ne duplira isporuku.
- Završavanje, otkazivanje ili arhiviranje otkazuje čekajuće podsetnike. Izmena termina/odgovorne osobe usaglašava raspored.
- Pre isporuke ponovo proverava aktivnog korisnika, enabled članstvo i pristup kompaniji. Opozvanom članu se podsetnik ne isporučuje.
- Privremena DB greška vraća transakciju i worker ponavlja obradu. Za rad podsetnika mora biti pokrenut worker — samo frontend nije scheduler.

## Povezanost i prava

Sve liste i agregati primenjuju postojeće server-side članstvo i company ownership. Sales vidi svoje kompanije i dodeljuje obaveze sebi. Manager/admin vidi dozvoljenu jedinicu i može dodeliti samo aktivnom članu koji ima pristup konkretnom klijentu. Globalni platform admin nema automatski tenant bypass.

Profil kompanije dobija tab Zadaci i aktivnosti. Početna tabla prikazuje stvarne današnje/zakasnele obaveze, završene zadatke, izvršene pozive/sastanke i lične nove podsetnike. Izveštaji koriste isti `/work/summary`, sa rezultatima odgovorne osobe i filterima. Preporuke prodaje ostaju jasno označene kao predlozi; konkretne obaveze imaju svoje nazive, kompanije, osobe i rokove.

Uspešan POST/PATCH/archive/restore/read osvežava povezane unit upite. Promene drugih korisnika osvežavaju se na 30 sekundi i pri fokusu, kao u Fazi 2. Podaci ostaju posle browser refresh-a i nove prijave. Prodajni KPI i iznosi prilika nisu kopirani u zadatke/aktivnosti i nema novog obračuna prihoda.

## Pravila vremena i metrika

- Baza koristi timestamptz. API odbija datum/vreme bez zone. Forme koriste lokalnu zonu preglednika, izričito navedenu uz unos; prikaz koristi Europe/Belgrade.
- Task izveštaj period prati due_at. Aktivnosti u statusu Završen prate occurred_at, ostale scheduled_at. Isto vreme koristi i hronološko straničenje aktivnosti.
- Granice perioda su uključivi lokalni dani Europe/Belgrade. Sales period/iznosi ostaju po pravilima Faze 2.
- Dnevne obaveze su nezavisne od sales perioda. Današnji i zakasneli zadaci broje samo otvorene/u toku, ne završene/otkazane/arhivirane.
- Menadžer vidi timski pregled dozvoljene jedinice; redovi izveštaja grupisani su po odgovornoj osobi. Owner filter iz prodajnog pregleda prati vlasnika kompanije, ne nužno izvršioca aktivnosti; to piše u izveštaju.
- Lični nepročitani podsetnici nezavisni su od perioda. U profilu kompanije lista podsetnika dodatno je ograničena na tu kompaniju.
- Dnevni detalji prikazuju do pet zadataka i pet aktivnosti; zbirni brojevi računaju sve dostupne zapise. Nema izmišljenih današnjih zadataka ili automatskog uvoza demo podataka.

## Baza i migracija

Nova migracija `b273e4f50612` sledi `a162bced9031` i dodaje `tasks`, `activities`, `reminders`, `work_events`. Novi composite unique na opportunities omogućava DB proveru iste kompanije/jedinice. Postojeća tabela, ID-jevi, sesije, poslovni iznosi i istorija faza nisu zamenjeni ili prepisani.

Migracija je izvršena samo u izdvojenim test bazama. Read-only pregled poslovne baze potvrđuje stari head `a162bced9031` i **0 novih work tabela**. Nova aplikaciona grana zahteva novu šemu, pa praktičnu proveru sada treba raditi na test serveru ispod, ne pokretati je nad starom poslovnom šemom.

Downgrade uzima DB lock i odbija uklanjanje novih tabela ako sadrže zapise. Test potvrđuje da neuspešan downgrade čuva zadatak i migracioni head. Povratak stare aplikacione verzije uz očuvanje nove šeme je bezbedniji od brisanja novog poslovnog modula. Za kasniju poslovnu migraciju potrebni su pregled, backup/restore plan i odobrena primena; ova faza to nije izvršila.

## Provere

- Backend kompletna provera: **69 passed** u posebnoj `_test` bazi.
- Frontend: **11 passed**, šest Vitest fajlova; uključena provera letnjeg/zimskog vremena Europe/Belgrade.
- Browser: **6 passed** u kompletnoj završnoj proveri, uključujući Faze 1–2, oba brenda i regresiju sporog čuvanja.
- ESLint, Ruff i TypeScript/Vite build prošli. Paralelna lokalna provera je jednom zatekla Playwright pri brisanju test-results direktorijuma i lint je prijavio ENOENT; dodata su standardna isključenja generisanih browser artefakata i lint je ponovo izvršen. Ostaje ranije upozorenje velikog JS paketa zbog inline logotipa, kao i Starlette/httpx deprecation.
- Alembic check nad migriranom test bazom: No new upgrade operations detected. Poslovna baza nije migrirana.

Pokriveni su: autorizacija, zabranjene veze kompanije/prilike/jedinice, dozvoljena dodela, validacija vremena, 409, history i persistencija, task/activity reminders, idempotencija, opoziv članstva, filter kompanije podsetnika, period agregata, archive/restore i guard downgrade-a. Postojeća legacy migration provera i dalje potvrđuje očuvanje originalnih kompanijskih procena.

Završni nezavisni pregled identifikovao je race pri zameni formulara tokom sporog čuvanja. Problem je reprodukovan u browser-u: drugi Edit dugmić bio je aktivan dok prvo čuvanje čeka. Kontrole zamene sada su onemogućene dok formular nije zatvoren. Dodatne regresije proveravaju redosled izvršenih aktivnosti, potpunu archive istoriju i izbegavanje N+1 upita: pre popravke 200 zapisa je koristilo 205 SELECT upita, sada test zahteva najviše 12.

## Izmenjeni fajlovi

Backend:

- `backend/app/work_models.py`, `work_schemas.py`, `work.py`, `work_metrics.py`, `reminders.py`, `api/work.py`.
- `backend/app/models.py`, `main.py` — registracija modela/routera i readiness nove šeme; poslovni auth ugovori ostaju.
- `backend/alembic/versions/b273e4f50612_work_management.py`.
- `backend/tests/test_work.py`, `test_work_migration.py`, `tests/tools/e2e_server.py`.

Frontend:

- `frontend/src/features/crm/WorkSpace.tsx`, `WorkBoard.tsx`, `WorkEditor.tsx`, `WorkOverview.tsx`, `ReminderInbox.tsx`, `workTypes.ts`, `workTypes.test.ts`.
- `frontend/src/Workspace.tsx`, `features/crm/CompanyProfile.tsx`, `Dashboard.tsx`, `styles.css`.
- `frontend/eslint.config.js` — generisani Playwright artefakti izuzeti iz lint-a.
- `frontend/e2e/work.spec.ts`, `helpers.ts`, `crm.spec.ts` — postojeći auth helper je izdvojen radi ponovne upotrebe.

Dokumentacija: `docs/superpowers/plans/2026-10-14-crm-phase3.md`, ovaj dokument. Nema novih plaćenih servisa ili zavisnosti.

## Kako praktično proveriti Fazu 3 bez poslovne baze

U Codespaces-u prebaciti se na `feat/crm-phase3-work`, instalirati locked zavisnosti (`frontend: npm ci`, `backend: uv sync --locked`) i obezbediti postojeći lokalni PostgreSQL. Ne menjati postojeći .env i ne raditi down -v/seed poslovne baze.

Prvi terminal, iz `backend/`:

```bash
PYTHONPATH=. .venv/bin/python tests/tools/e2e_server.py
```

To kreira i migrira novu nasumičnu test bazu, unosi samo sintetičke korisnike/kompanije/prilike i pokreće pravi API i worker za podsetnike. Poslovna baza se ne menja.

Drugi terminal, iz `frontend/`:

```bash
CRM_DEV_API_TARGET=http://127.0.0.1:18000 npm run dev -- --port 5173 --strictPort
```

Otvoriti forwarded port **5173** iz Codespaces Ports taba. Ako tačan spoljašnji HTTPS origin nije dozvoljen, u prvom terminalu postaviti `CRM_ALLOWED_ORIGINS` na taj origin i postojeće localhost origins pre starta servera, kao u [uputstvu Faza 1–2](PHASE_1_2_VALIDATION.md). Ne koristiti wildcard. Restart test servera pravi novu test bazu, pa se njegovi raniji sintetički unosi ne čuvaju posle gašenja.

Sintetički nalozi: `sales@example.com` za LUU, `manager@example.com` za sve jedinice, `outsider@example.com` za INVEKTA. Lozinka samo tih test naloga: `Browser-test-only-123!`.

1. Prijaviti Sales u LUU, otvoriti Zadaci → Novi zadatak. Izabrati Browser Firma A, odgovornu osobu Sales i Browser ponuda.
2. Uneti naslov, današnji rok u budućnosti i vreme podsetnika pre roka. Za brzu proveru može se uneti već proteklo vreme podsetnika; worker ga isporučuje pri narednoj obradi.
3. Sačuvati. Otvoriti početnu tablu i Izveštaje: ista obaveza i tačni brojevi. Kompanije → Browser Firma A → Zadaci i aktivnosti prikazuje isti zapis.
4. Podsetnici: isporučeno obaveštenje; Označi kao pročitan. Menadžer ne vidi tuđi lični podsetnik, ali vidi timske zadatke.
5. Izmeniti status zadatka u Završen. Otvoriti istoriju: autor, vreme i promenjena polja. Osvežiti browser i ponovo se prijaviti: status ostaje sačuvan u test PostgreSQL-u.
6. Aktivnosti → Nova aktivnost: zakazati Poziv ili Sastanak, izabrati klijenta/osobu/priliku i vreme. Posle izvršenja promeniti status u Završen, dopisati ishod. Tabla i izveštaj prikazuju izvršene pozive/sastanke.
7. Arhivirati zapis; uključiti Prikaži i arhivirane; vratiti ga. Istorija ostaje, vraćen zapis je Otkazan i ne aktivira stari podsetnik.
8. U zasebnom privatnom prozoru prijaviti Manager u LUU: isti timski rezultati. Izmene drugih korisnika dolaze na 30s ili pri fokusu.
9. Prijaviti outsider u INVEKTA i napraviti njen zadatak. LUU korisnik ga ne vidi. API odbija LUU pristup outsider-u sa403 i pogrešan company context sa404/422.

Kompletna automatska browser provera iz frontend direktorijuma:

```bash
npx playwright install --with-deps chromium
npm run test:e2e
```

U ovom okruženju korišćen je postojeći Chromium: `CRM_CHROMIUM_PATH=/usr/bin/chromium npm run test:e2e`. Svaki scenario/retry dobija novu bazu i briše je po gašenju. Browser case sporog odgovora koristi stvaran API upis, a odlaže samo mrežni odgovor da proveri očuvanje formulara.

## Worker u budućem povezanom razvoju

Tek posle pregledane primene migracije na odgovarajući razvojni CRM, pored postojećeg API-ja pokrenuti iz backend direktorijuma:

```bash
.venv/bin/python -m app.reminders --interval 20
```

`--once` je jednokratna obrada. Normalan operator pokreće worker nad izabranom privatnom DB konfiguracijom; ne pokretati ovu komandu nad poslovnom bazom kao deo sadašnje revizije/provere. Nema produkcionog service/deployment podešavanja u ovoj fazi.

Faza 4 (ponude, proizvodi/usluge, objekti i ugovori) čeka pregled ovih rezultata. Ranije zabeleženi production rizici — runtime DB superuser, RLS i backup/restore operativna priprema — nisu proglašeni rešenim ovim modulom.
