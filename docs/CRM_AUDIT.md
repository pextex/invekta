# Revizija LUU × INVEKTA × CENOBOTS CRM

Datum: 14. oktobar 2026. Repozitorijum: `pextex/invekta`. Pregledana osnova: commit `15d52a32fcd6bb8cef9f935e3c1ab7eee8585a8f`.

## Zaključak

Projekat već ima React frontend, FastAPI backend, PostgreSQL bazu, migracije, sesije, korisničke uloge i integracione testove. Nije samo HTML demo. Kompanije, kontakti, prodajne prilike, promene statusa, korisnička prava i nacrti poruka imaju stvarnu serversku implementaciju. Zadaci, aktivnosti, podsetnici, ponude, katalog i poslovni objekti još nemaju kompletan model/API/UI.

Najmanje rizičan nastavak je postepeno proširenje postojećeg modularnog sistema. Dizajn, tri brenda, navigaciju i postojeće API ugovore treba sačuvati. Predlog je u [DATABASE_DESIGN.md](DATABASE_DESIGN.md). Ova revizija ne uvodi migracije, ne menja funkcionalnosti i ne menja poslovne zapise.

## Obuhvat i struktura

Pregledani su izvori i konfiguracija svih glavnih delova; repozitorijum sadrži 88 praćenih fajlova:

| Deo | Fajlovi / namena |
|---|---|
| Frontend | `frontend/src/App.tsx` demo; `Workspace.tsx` povezani CRM; `Shell.tsx` zajednički raspored; `components/` prijava i dobrodošlica; `features/crm/` tabla, kontakti, profil kompanije, levak, asistent, korisnici |
| Klijentska infrastruktura | `frontend/src/lib/` API, rute, demo statusi, šabloni, lokalno čuvanje; `organizations.ts`, `styles.css`, `assets/`; Vite, TypeScript, package lock |
| Backend | `backend/app/main.py`, `api/sales.py`, `api/users.py`, `api/ai.py`; modeli, šeme, pristup, bezbednost, konfiguracija, šabloni poruka |
| Baza | `backend/alembic/`, šest uzastopnih migracija; `docker-compose.yml` PostgreSQL 16 sa trajnim volumenom |
| Razvoj i testovi | `backend/tests/`, `app/test_runner.py`, `frontend/src/**/*.test.*`, `scripts/setup_dev.py`, `uv.lock` |
| Demo i dokumentacija | `demo/LUU_Invekta_CRM_Demo.html`, demo README, glavni README, `docs/architecture/`; zajednički `shared/message_catalog.json` |

Nema praćenih `.devcontainer` konfiguracija, GitHub Actions CI, produkcionog reverse proxy/deployment paketa ili konfigurisanog lint procesa. Compose pokreće bazu, ne kompletnu aplikaciju. Nema `AGENTS.md` pronađenog u radnom prostoru.

## Ekrani i stvarna funkcionalnost

| Ekran | Povezani CRM | Anonimni demo / ograničenja |
|---|---|---|
| Izbor organizacije i prijava | Email/lozinka, provera članstva, sesija, odjava; tri odvojene teme i logotipa | Demo ulazak bez prijave; HTML preko `file://` ne podržava stvarnu prijavu |
| Početna tabla | Serverski zbir kompanija, kontakata i prilika koje korisnik sme da vidi | Devet izmišljenih kompanija ukupno, po tri za organizaciju |
| Dobrodošlica | Ime korisnika, datum za `Europe/Belgrade`, preporuke prema broju zapisa i fazama | Nisu stvarni dodeljeni zadaci niti kalendar rokova |
| Novi klijenti | Ista osnova kompanija i ručni unos | Nema zasebnog leada, otkrivanja potencijalnih klijenata ili automatskog bodovanja |
| Kompanije / profil | Lista, pretraga, kreiranje i izmena; više kontakata i prilika po kompaniji | Lista kompanija ograničena na 200, bez pune paginacije; nema brisanja/arhiviranja ili API prenosa vlasništva |
| Kontakti | Čitanje, unos i izmena u kompaniji | Nema verzije za konkurentne izmene; PATCH zahteva ime i može resetovati izostavljena opciona polja |
| Prodajni levak | Sedam faza, kreiranje/izmena prilika, iznos, rok, beleške; prevlačenje i izbor statusa; serverska istorija | Demo čuva statuse u localStorage; nisu poslovni podaci |
| Izveštaji | Postojeći zbirni podaci sa table | Nema prilagodljivih izveštaja, izvoza ili obračuna fakturisanog prihoda; dobijena prilika nije faktura |
| Zadaci | Placeholder | Demo označavanje završetka samo u memoriji, gubi se pri osvežavanju |
| Ponude | Placeholder | Nema stavki, verzija ponuda, PDF-a, proizvoda/usluga ili cenovnika |
| Asistent | Besplatni lokalni šabloni sr/en, novi email, odgovor i follow-up; čuvanje/izmena sopstvenih nacrta u PostgreSQL | Deterministički generator, bez jezičkog modela, razumevanja dolazne poruke ili slanja emailova; demo nacrti lokalno |
| Korisnici i pristup | Globalni administrator kreira korisnike, dodeljuje/ukida pristup firmama, aktivira/deaktivira i postavlja lozinku; izmena poništava sesije | Nema samostalnog oporavka lozinke, MFA, verifikacije emaila ili obavezne prve promene lozinke |

Prilike koriste faze `Novi lead`, `Kontaktiran`, `Sastanak`, `Ponuda`, `Pregovori`, `Dobijeno`, `Izgubljeno`. Serverske izmene prilika i nacrta imaju verziju i zaključavanje reda; zastarela izmena vraća 409. Levak pomera karticu nakon uspešnog API odgovora, uz alternativni izbor statusa.

Izbor firme je na ulazu, bez menija za prebacivanje unutar CRM-a. Sesija važi za korisnika, a pristup svakoj firmi proverava backend; sesija nije zaključana samo na firmu izabranu pri prijavi. Globalni administrator ne dobija automatski pristup poslovnim podacima bez članstva.

## Gde se čuvaju podaci

Stvarni CRM koristi PostgreSQL preko SQLAlchemy i Alembic. Postojeća razvojna baza `crm` je na `127.0.0.1:5432`, sa Docker volumenom `crm_data`; sadržaj nije u Git-u. Šest migracija završava na `a162bced9031`.

| Postojeća tabela | Sadržaj |
|---|---|
| `business_units` | LUU, INVEKTA, CENOBOTS |
| `users`, `memberships` | Identitet, hash lozinke, aktivnost, globalni admin, verzija; uloga i omogućen pristup po firmi |
| `login_sessions`, `login_attempts` | Hash tokena/istek sesije i pokušaji prijave |
| `companies` | Firma, poslovna jedinica, vlasnik, grad/sektor, demo oznaka; zadržana stara polja stage/potential_value |
| `contacts` | Kontakt povezan sa kompanijom i poslovnom jedinicom |
| `opportunities` | Više prilika po kompaniji, sedam faza, iznos, rok, beleške, verzija |
| `opportunity_stage_changes` | Autor i vreme kreiranja/promene faze |
| `ai_drafts`, `ai_attempts` | Sopstveni nacrti poruka po korisniku/firmi i ograničenje generisanja |

Napomena: `ai_drafts` čuva konačan tekst i primaoca, ne ceo kontekst sastavljanja niti FK izabranog kontakta/prilike. Stara kompanijska procena nije novi izvor istine za levak: postojeće prilike to preuzimaju.

Anonimni demo koristi React stanje i localStorage: `luu_invekta_demo_stages_v1` za faze i `crm_assistant_v1_<organizacija>` za nacrte, sastavljanje i potpise, do 30 sačuvanih nacrta po organizaciji. Podaci su običan tekst u pregledniku, razdvojeni po organizaciji, ne po prijavljenom korisniku. To nije višekorisničko poslovno skladište. Demo i poslovne zapise ne treba automatski spajati.

`seed.py` je eksplicitna razvojna komanda, ne startup rutina. Kreira korisnika `demo` bez email adrese, dok aktuelni GUI zahteva email: README uputstvo za prijavu sa username `demo` ne odgovara sadašnjem formularu. Postoje CLI alati za kreiranje korisnika i početnog administratora; nisu pokretani tokom revizije. Lični administratorski nalog i njegova lozinka nisu proveravani.

## API, autentifikacija i izolacija

OpenAPI trenutno sadrži 25 kombinacija metode i putanje:

- Health/readiness i login/logout/me.
- Kompanije: lista, unos, izmena i pojedinačan profil.
- Kontakti u kompaniji: lista, unos, izmena.
- Prilike: paginirana lista, unos, izmena, promena faze, istorija; zbirna statistika jedinice.
- Administracija korisnika: lista, unos, izmena.
- Asistent: status, lista nacrta, kreiranje i izmena nacrta.

Klijent koristi `/api` i same-origin cookie. Vite razvojni proxy prosleđuje backend-u na 8000; Vite build/preview sam po sebi ne obezbeđuje produkcioni API proxy.

Postoje sledeće zaštite:

- PBKDF2-SHA256, 600.000 iteracija, slučajna so i poređenje hash vrednosti; lozinke nisu sačuvane kao tekst.
- Nasumičan token sesije, samo SHA256 hash u bazi; HttpOnly, SameSite Strict, putanja `/api`, trajanje osam sati. Secure je konfigurabilan i isključen za lokalni HTTP razvoj.
- Aktivnost korisnika, istek sesije i omogućeno članstvo proveravaju se na backend-u. `sales` vidi sopstvene kompanije; `manager`/`admin` kompanije svoje jedinice. Nacrti dodatno pripadaju autoru.
- Kompozitni strani ključevi sprečavaju povezivanje kompanije/prilike/istorije/nacrta sa pogrešnom jedinicom ili vlasnikom bez članstva.
- Mutacije zahtevaju dozvoljen Origin; ulazi koriste Pydantic validaciju, zabranu dodatnih polja, granice i email validaciju. Greške validacije ne vraćaju poslatu lozinku.
- SQLAlchemy parametrizovani upiti, escaped pretraga, `no-store` i `nosniff` odgovori.

**Nema PostgreSQL RLS politika na poslovnim tabelama.** Izolacija čitanja zavisi od ispravnog backend filtriranja; kompozitni FK ne štiti nefiltriran SELECT. Postojeća razvojna DB uloga ima superuser i createdb privilegije. To omogućava test runner, ali nije prihvatljiva produkciona aplikaciona uloga.

Asistent trenutno poziva `message_templates.generate`. Stari `ai_provider.py` ostaje u kodu, ali ga aktuelni endpoint za nacrte ne poziva; plaćeni provider je podrazumevano isključen. Nije bilo stvarnog poziva komercijalnom modelu u ovoj proveri. Ograničenje nacrta je 20 generisanja po korisniku u 15 minuta, čak i za besplatne šablone. Nema povezivanja sa mailbox-om niti slanja poruka.

## Provere izvršene u dostupnom okruženju

| Provera | Rezultat |
|---|---|
| `cd frontend && npm run build` | Prošao TypeScript i Vite build |
| `cd frontend && npm test` | 5 prošlih testova, 3 fajla |
| Backend `app.test_runner` | 45 prošlih testova u novoj, nasumično imenovanoj `_test` bazi; 1 upozorenje |
| `cd backend && .venv/bin/python -m alembic check` | Nema novih upgrade operacija: modeli odgovaraju postojećoj šemi |
| `alembic heads` i read-only DB metadata | Jedan head `a162bced9031`, ista verzija u bazi; PostgreSQL 16.15; sva tri koda organizacija prisutna |
| TestClient GET `/api/health`, `/api/ready` | 200 / 200 |
| Neprijavljen GET kompanija i admin korisnika | 401 / 401 |
| Lint | Nije konfigurisan: nema npm lint skripte, ESLint konfiguracije ili backend lint alata u zavisnostima; nije označen kao uspešan |
| Praćeni HTML demo prema svežem buildu | Ugrađeni JS i CSS odgovaraju svežem buildu |

Backend komanda je pozvala `app.test_runner.main()` kroz `.venv/bin/python` uz `CRM_TEST_DATABASE_URL` postavljen samo u procesu na novu `crm_audit_20261014_<random>_test` bazu. URL i lozinka nisu ispisivani. Migracije i test upisi izvršeni su samo u toj test bazi, ne u poslovnoj bazi. Test baza ostaje razvojni artefakt.

Postojeći DB kontejner je bio zaustavljen; pokrenut je sa `docker compose start db`, uz očuvan volumen. Prvi pokušaj `start --wait` nije podržan ovom Compose instalacijom i završen je bez pokretanja; korišćena je podržana komanda. Nisu pokretani seed, bootstrap admin, reset naloga, migracije nad poslovnom bazom, reset volumena ili produkcioni deployment.

Okruženje: Python 3.12.14, Node 24.19.0, npm 11.9.0, uv 0.12.23, Compose 2.40.3. Instalirani FastAPI 0.143.0, SQLAlchemy 2.1.4, Alembic 1.20.0; frontend lock koristi React 19.3.0, TypeScript 5.8.3 i Vite 6.4.4.

Build upozorava na JS paket od 3.954,61 kB (gzip 2.458,81 kB), preko praga 500 kB. Ugrađeni PNG logotipi i odsustvo podele paketa doprinose veličini. Backend upozorenje: Starlette TestClient deprecira korišćeni httpx adapter. Nisu zabeleženi neuspešni aplikacioni testovi.

Testovi pokrivaju backend pristup, sesije, korisnike, prodaju, nacrte i migracije, kao i ograničene frontend slučajeve. Ova provera nije kompletan browser E2E, penetracioni test, dependency audit, test opterećenja ili dokaz spremnosti za produkciju. Backup/restore nije testiran.

## Rizici, dug i nedovršene funkcije

| Prioritet | Nalaz i posledica | Preporuka |
|---|---|---|
| Pre produkcije | Runtime DB superuser, bez RLS | Odvojiti migracionu i aplikacionu ulogu; zadržati API autorizaciju, zatim testirano uvesti RLS |
| Visok | Nema opšte istorije promene podataka i administratorskih prava | Transakciona audit evidencija, bez lozinki/tokena i nepotrebnog sadržaja emaila |
| Visok | Kompanije/kontakti bez verzionisanja; različita PATCH semantika | Dodati verziju i dosledan partial update pre intenzivnog višekorisničkog rada |
| Visok | Nema dokumentovanog i proverenog backup/restore procesa | Lokalna proba obnove pre produkcione migracije |
| Srednji | Login limit po identifikatoru, bez globalne/IP kontrole; count/insert nije serijalizovan | Proveriti paralelne pokušaje, ograničiti zloupotrebu bez omogućavanja lakog zaključavanja tuđeg naloga |
| Srednji | Nema MFA, reset linka, verifikacije emaila i prve obavezne promene lozinke | Faze razvoja prema potrebi; ne slati lozinke u chat |
| Srednji | Nema prenosa vlasništva; deaktivirani vlasnik ostavlja zapise dostupne menadžeru | Kontrolisan prenos sa auditom i pravilima dodele |
| Srednji | Nedostaju zadaci/aktivnosti/podsetnici, objekti, leadovi, ponude i katalog | Dodavati pojedinačne module u postojeće ekrane/API |
| Srednji | Nema CI, lint, devcontainer i širokih frontend testova | Ponovljivi izolovani checks i smoke/E2E ugovori pre proširenja |
| Srednji | Veliki paket i ručno ugrađen offline demo | Optimizovati slike i izvoz, bez promene vizuelnog identiteta |
| Niži | `App`/`Workspace` po preko 500 linija, asistent oko 790; duplirani enum-i i rute | Postepeno izdvojiti logiku, bez prepisivanja aplikacije |
| Niži | README i ranije validation beleške protivreče aktuelnom kodu | Usaglasiti uputstva nakon odobrenog narednog koraka |

Logotipi su rekonstrukcije iz dostavljenih slika, ne originalni vektorski fajlovi. Browser lokalni demo sadržaj nije za poverljive zajedničke poslovne zapise. Nema poslovnog jedinstvenog identiteta kao PIB, arhiviranja, potpune paginacije kompanija ili kontrole duplih kontakata. Pretraga arhive nacrta odnosi se na prikazanu stranicu, ne sve zapise na serveru.

## Prvi bezbedan implementacioni korak

Posle odobrenja: prvo uspostaviti ponovljivu CI/Codespaces proveru sadašnjeg ponašanja, sa izolovanom test bazom i smoke testom prijave, prava po firmi, vlasništva i zabrane pristupa tuđim podacima; dogovoriti i konfiguraciju lint-a. Ne menjati poslovnu šemu tim korakom. Zatim rešiti konkurentne izmene i audit, pa povezati postojeći ekran Zadaci sa malim modulom zadataka/aktivnosti. Ne implementirati ceo predloženi model odjednom.

Revizija je završena dokumentacijom. Implementacija novih modula, šeme i produkcionih promena čeka odobrenje korisnika.
