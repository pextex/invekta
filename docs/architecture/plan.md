# Arhitektura i plan — LUU × INVEKTA × CENOBOTS

## Dogovoreni pravac
Modularni monolit: React + TypeScript + Vite frontend, FastAPI backend, SQLAlchemy 2 + Alembic i PostgreSQL. Razvoj u cloud okruženju, bez instalacija na korisnikovom Windows računaru. Produkcioni hosting bira se kasnije; ovaj korak ne kreira plaćene servise.

## Struktura
- `frontend/src/`: App i zajednički Shell; `features/crm` sadrži profile, kontakte, levak i dashboard, a `lib` API klijent i rute. Demo podaci su izdvojeni.
- `backend/app/`: API, modeli, šeme, autorizacija, konfiguracija, seed i test runner. CRM endpointi su u `api/sales.py`.
- `backend/alembic/` i `backend/tests/`: izvršene migracije i PostgreSQL integracioni testovi.
- `backend/app/seed.py`: eksplicitan seed izmišljenih demo zapisa.
- `docs/architecture/`: odluke i plan. Docker Compose upravlja razvojnom PostgreSQL bazom.

## Model baze — implementirano jezgro i plan proširenja
`business_units` (LUU, INVEKTA, CENOBOTS) ima više `memberships`, koji povezuju `users` sa ulogom po jedinici: komercijalista, menadžer, administrator.
`companies` pripadaju jedinici i odgovornom korisniku; imaju više `contacts`, `locations`, `opportunities`, `activities` i `tasks`.
Prilika pripada kompaniji i nasleđuje njenu odgovornu osobu. Trenutno koristimo sedam unapred definisanih faza; budući `pipeline_stages` omogućiće podešavanje faza po jedinici.
`quotes` imaju `quote_items`; LUU dodaje `products`, `price_lists` i porudžbine; Invekta `services`, `contracts` i tendere.
`lead_sources` čuvaju URL, datum provere i status potvrđenosti podatka; `audit_logs` beleže promene.

Svaki poslovni zapis nosi business_unit_id. Složeni strani ključevi treba da spreče povezivanje kompanije, kontakta i prilike između jedinica. Backend proverava članstvo, ulogu i vlasništvo pri svakom čitanju i pisanju. Menadžerski objedinjeni pregled zahteva izričito pravo. Izbor modula u frontend-u nije sigurnosna granica. Novac: NUMERIC i valuta; vreme: TIMESTAMPTZ; ograničenja i indeksi kroz migracije.

## MVP, po malim proverljivim koracima
1. **Završeno:** responzivan srpski frontend, izbor modula, dashboard, pretraga demo kompanija, prikaz levka i privremeni demo zadaci. Build i testovi filtriranja.
2. **Završeno:** FastAPI i PostgreSQL, Alembic migracije, health/readiness provere i eksplicitni demo seed.
3. **Osnova završena:** Prijava, sesije i backend autorizacija po jedinici, ulozi i vlasniku; testovi neovlašćenog pristupa. Pre stvarnih podataka.
4. **Završeno:** Trajno dodavanje/izmena kompanija i kontakt osoba; pretraga kompanija.
5. **Prilike i KPI završeni:** više prilika po kompaniji, promene faze, istorija i pokazatelji iz baze. Aktivnosti i trajni zadaci slede.
6. Provera korisničkih tokova, izolacije podataka i dokumentacije.

Specijalizovani odeljci za LUU proizvode i Invekta usluge uklonjeni su iz obima na zahtev korisnika. Kasnije: PDF ponude, CSV, napredni izveštaji, AI adapteri sa proverljivim izvorima i nacrtima poruka, backup i produkcija. Bez automatskog masovnog slanja.

## Trenutno stanje — verzija 0.4
Postoje kompanije, kontakti, prilike i istorija faza, uz PostgreSQL, migracije, prijavu i backend autorizaciju po jedinici i kompaniji. Komercijalista nasleđuje pravo na kontakte i prilike svojih kompanija; menadžer i administrator imaju pregled u dozvoljenim jedinicama. Menadžer ne može automatski videti objedinjene podatke drugih jedinica.

Složeni FK na (company_id, business_unit_id) obezbeđuju vezu kontakta i prilike sa kompanijom iste jedinice. Složeni FK istorije vezuju zapis za priliku i korisnikovo članstvo u istoj jedinici. `opportunities.version` i zaključavanje reda štite izmene prilika od prepisivanja zastarele verzije. Datumi promena su sa vremenskom zonom, prikaz vremena u Europe/Belgrade. Očekivani datum zatvaranja je kalendarski DATE.

Migracija verzije 0.3 prenosi stara company.stage/potential_value polja u jednu početnu priliku. Vrednost je NUMERIC(14,2). Stara polja su sačuvana radi kompatibilnosti; nisu izvor za nove KPI. Ne pokretati downgrade na poslovnoj bazi: uklonio bi nove tabele i njihove podatke. Provera downgrade-a rađena je samo nad izolovanom test šemom.

Anonimni demo i njegovi zadaci ostaju izdvojeni. Povezani dashboard koristi podatke razvojne baze, uključujući označene demo zapise. Dodati su UI administracija naloga i AI nacrti poruka. AI čeka povezivanje ključa; produkcioni hosting, puna audit evidencija i trajni zadaci ostaju u planu.

## Izbor kompanije pri prijavi
Početni ekran prikazuje tri organizacije: LUU, Invekta i Cenobots. Izbor prosleđuje kod jedinice backend-u, koji proverava aktivnog korisnika i membership pre nove sesije. Sama kartica kompanije nije pravo pristupa. Registracija jedinica kroz migraciju ne menja korisnička prava; samo eksplicitan razvojni seed daje demo nalogu pristup svim trima.
