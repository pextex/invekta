# Faze 1–2: povezane metrike i proverljiva razvojna osnova

Datum: 14. oktobar 2026. Grana: `feat/crm-metrics-sync`. Osnova: `6904d16`.

## Šta je implementirano

Postojeći CRM je proširen, bez nove aplikacije i bez poslovne migracije. FastAPI računa KPI i izveštaje iz postojećeg PostgreSQL modela. Dashboard i Izveštaji koriste isti `/api/units/{unit}/summary` odgovor; levak koristi iste period/owner filtere i isti autorizovani skup prilika. Profil kompanije koristi iste prilike, uz prikaz kompletnog konteksta kompanije.

React Query centralizuje server state: kompanije, kontakte, profile, paginirani levak i agregate. Uspešna mutacija osvežava povezane upite poslovne jedinice; 409 osvežava server prikaz, prijavljuje konflikt i čuva nesnimljen formular. Drag/drop i select pozivaju postojeći isti `/stage` endpoint sa verzijom. Nema prividnog čuvanja pri API grešci ili prebacivanja na demo podatke.

Promene u istoj sesiji postaju vidljive posle potvrde backend-a. Prikazi drugih korisnika osvežavaju se na 30 sekundi dok je prozor aktivan i pri povratku fokusa; nema WebSocket obećanja niti trenutnog push-a između preglednika. Cache se prazni na prijavi/odjavi. Poslovne jedinice se filtriraju kroz kontrolu u pregledu, sa samo dozvoljenim članstvima; nije vraćen meni za prebacivanje CRM-a.

Novi KPI: broj kompanija/kontakata, otvorenih prilika i vrednost, dobijene/izgubljene prilike i njihove vrednosti, raspodela faza i rezultati komercijalista. Izveštaji dodaju rezultate kompanija, direktne evidentirane konverzije i mesečne događaje promena faza. Zadaci, podsetnici, ponude, opšti audit i druge poslovne migracije ostaju naredne faze; postojeći placeholder ekrani jasno ostaju u pripremi.

## Tačna pravila metrika

- Iznosi su RSD i server-side Decimal. Dobijeni poslovi nisu fakturisani prihod.
- Aktivne/otvorene prilike su sve faze osim Dobijeno/Izgubljeno.
- Period bira prilike po `created_at`, od početka do kraja izabranih lokalnih dana u Europe/Belgrade, uključivo. Sadašnja faza i iznos izabrane kohorte su osnova KPI; ovo nisu istorijski snapshot-i.
- Kompanije i kontakti su ukupan vidljiv broj za izabranu jedinicu/komercijalistu, nezavisno od perioda kreiranja prilika. To piše uz filtere.
- Komercijalista rezultata je vlasnik kompanije, ne korisnik koji je poslednji menjao priliku.
- Konverzija je broj različitih prilika sa zabeleženim direktnim prelazom source→target tokom perioda, podeljen brojem različitih prilika zabeleženih u source fazi (from ili to događaj). Važi za izabranu kohortu. Ponovljeni isti prelaz iste prilike računa se jednom; prikaz uključuje i kretanje unazad, što nije prodajni uspeh.
- Mesečni pregled broji događaje ulaska u fazu, uključujući kreiranje i ponovljene prelaze, za isti autorizovani skup i period. Ne prikazuje istorijske vrednosti jer istorija statusa ne čuva tadašnji iznos.
- Legacy prilike bez istorije ulaze u sadašnje KPI, ali ne dobijaju izmišljene prelaze.
- Agregati uključuju sve dostupne prilike, ne samo prvih 100/200 učitanih kartica. Brojevi u kolonama levka i dalje označavaju učitane kartice.
- Prodavac ne može owner filterom proširiti pristup; tuđi owner u istoj jedinici je 404, nedozvoljena jedinica 403, neprijavljen korisnik 401.

## Rezultati lokalnih provera

| Provera | Rezultat |
|---|---|
| Backend celokupan pytest preko test runner-a | 53 passed; samo prethodno Starlette/httpx deprecation upozorenje |
| Frontend Vitest | 9 passed, 5 test fajlova |
| Browser Playwright/Chromium | 3 passed: kompletan prodajni tok, novi zapisi/iznosi/409, druga menadžerska sesija |
| Frontend ESLint | Prošao |
| Backend Ruff | Prošao; greške/undefined/unused provere, bez masovnog preformatiranja starog koda |
| TypeScript + Vite build | Prošao; zadržano upozorenje velikog paketa, sada približno 4 MB zbog postojećih inline logotipa |
| Alembic check | Nema razlike modela/šeme; head ostaje a162bced9031 |

Poslovni PostgreSQL zapisi nisu menjani. Pytest koristi zasebnu `crm_phases12_20261014_test` bazu, fixtures rollback; svaki browser test/retry kreira novu nasumičnu `_test` bazu, migrira i unosi samo sintetičke podatke, pa je briše po gašenju. Kredencijali poslovne baze nisu ispisivani. Ne pokretati seed nad poslovnom bazom radi ove provere.

CI workflow instalira locked npm/uv zavisnosti, pokreće PG16, lint/build/pytest/Vitest/Playwright i čuva browser failure artefakte. Lokalni prolaz ne znači da je GitHub Actions run već izvršen; proveriti status na PR-u. Ovo nije produkcioni deployment niti produkciona bezbednosna sertifikacija.

## Izmenjeni fajlovi

- Razvoj: `.github/workflows/ci.yml`, `.gitignore`, `frontend/package.json`, `package-lock.json`, `eslint.config.js`, `vitest.config.ts`, `playwright.config.ts`, `vite.config.ts`, `backend/pyproject.toml`, `uv.lock`.
- Backend: `app/metrics.py`, `app/api/sales.py`, `app/schemas.py`; kompatibilni import za postojeće provider testove u `app/api/ai.py`; testovi `tests/test_metrics.py`, `tests/tools/e2e_server.py`, uklonjen neiskorišćen test import u `test_user_management.py`.
- Frontend: `src/lib/crmQuery.ts`, `crmQuery.test.ts`, `crmQueryAuthorization.test.tsx`, `main.tsx`, `Workspace.tsx`, `features/crm/Dashboard.tsx`, `Reports.tsx`, `MetricsFilters.tsx`, `Pipeline.tsx`, `CompanyProfile.tsx`, `Contacts.tsx`, `types.ts`, mali CSS dodatak i uklonjeni neiskorišćeni importi iz `App.tsx`.
- Browser dokaz: `frontend/e2e/crm.spec.ts`, `fixtures.ts`.
- Plan i zapis: `docs/superpowers/plans/2026-10-14-crm-metrics-sync.md`, ovaj dokument.

## Kako praktično proveriti bez poslovnih podataka

Prebaciti se na granu u Codespaces-u i instalirati zavisnosti: `cd frontend && npm ci`, a u backend-u `uv sync --locked`. PostgreSQL mora biti dostupan prema postojećoj privatnoj `.env` konfiguraciji. Postojeću konfiguraciju/volumen sačuvati; ne raditi `down -v`. Ako kontejner postoji ali je ugašen, iz korena repoa `docker compose start db`. Nov razvojni workspace zahteva početni setup iz README-a.

Automatska provera iz `frontend/`:

```bash
npx playwright install --with-deps chromium
npm run test:e2e
```

Ako je Chromium već instaliran i preuzimanje browser-a nije dozvoljeno:

```bash
CRM_CHROMIUM_PATH=/usr/bin/chromium npm run test:e2e
```

Za ručno otvaranje sintetičkog CRM-a, prvi terminal iz `backend/`:

```bash
PYTHONPATH=. .venv/bin/python tests/tools/e2e_server.py
```

Drugi terminal iz `frontend/`:

```bash
CRM_DEV_API_TARGET=http://127.0.0.1:18000 npm run dev -- --port 5173 --strictPort
```

Otvoriti forwarded port **5173** iz Codespaces Ports taba. API se proxy-uje iz istog origin-a. Ako koristeći spoljašnji forwarded URL server odbije Origin pri prijavi, podesiti `CRM_ALLOWED_ORIGINS` u prvom terminalu na tačan HTTPS URL koji Ports tab prikazuje, uz postojeće lokalne origins; ne koristiti wildcard. Restartovati test server, koji pravi novu sintetičku bazu. Lozinke/nalozi ispod postoje samo u tom izdvojenom test serveru, nisu administracija poslovnog CRM-a.

| Korisnik | Email | Firma |
|---|---|---|
| Komercijalista | sales@example.com | LUU |
| Menadžer | manager@example.com | Sve tri |
| Druga jedinica | outsider@example.com | INVEKTA |

Lozinka sintetičkih naloga: `Browser-test-only-123!`. Nikada je ne koristiti za stvarne naloge.

1. Izabrati LUU i prijaviti sales nalog. Otvoriti Prodajni levak.
2. Prevuci Browser ponuda iz Ponuda u Dobijeno ili upotrebi Faza select na kartici.
3. Početna tabla: otvorene prilike 0, dobijene 1, vrednost 12.500,55 RSD.
4. Izveštaji: iste vrednosti po fazama, Sales rezultat i Browser Firma A, evidentiran Ponuda→Dobijeno prelaz.
5. Kompanije → Browser Firma A → Prodajne prilike: Dobijeno; Istorija prikazuje autora i vreme.
6. Osvežiti stranicu; odjaviti se i ponovo prijaviti. Status i iznos ostaju sačuvani u test PostgreSQL-u.
7. U zasebnom privatnom prozoru prijaviti manager nalog za LUU: ista dobijena vrednost, plus druga otvorena prilika drugog prodavca od 200,20 RSD.
8. Promeniti iznos sales prilike; menadžer u aktivnom prozoru dobija novi zbir najkasnije sledećom 30-sekundnom proverom ili pri povratku fokusa.
9. Prijaviti outsider u INVEKTA: vidi samo Browser Firma C / 300,30 RSD. Autorizovani GET za LUU `/api/units/1/summary` odbija 403; INVEKTA pokušaj čitanja LUU kompanije odbija 404. Nemoj očekivati zabranu samo u meniju — to potvrđuju backend testovi.

Test server po gašenju briše isključivo svoju novu nasumičnu bazu. Ne koristiti ovaj server kao trajni CRM server. Za postojeći poslovni CRM ostaju standardne README komande, backend port8000 i frontend port5173, sa postojećim privatnim nalozima i podacima.

## Granice i naredni korak

Faze 3–5 nisu pokrenute: nisu dodate tabele aktivnosti/zadataka/podsetnika/ponuda. Postojeća istorija faza je dokaz promene prilike, ne potpuni opšti audit. Company/contact konkurentne izmene, najmanje privilegovana runtime DB uloga, RLS i backup/restore ostaju zabeleženi rizici iz revizije. Offline HTML demo nije izvoz nove povezane verzije; za ovu proveru treba pokrenut backend/frontend.

Nakon pregleda PR-a korisnik odlučuje o nastavku sledećih faza; nema automatskog merge-a ili produkcionog deployment-a.

## Završni pregled

Nezavisni pregled koda nije našao kritične ili važne greške. Dva dodatna nalaza su tretirana kao potrebna za pouzdanost i ispravljena: prikazi sada skrivaju zadržane podatke posle neuspešne autorizovane provere; browser testovi imaju sopstvenu bazu i preduslove, pa ne zavise od redosleda. Regresioni test za prikaz opozvanih prava prvo je pao, zatim prošao. Samostalan browser scenario novih zapisa prvo je pokazao zavisnost od prethodnog testa; sada se proverava izdvojeno.
