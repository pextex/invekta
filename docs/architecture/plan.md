# Arhitektura i plan — LUU × INVEKTA

## Dogovoreni pravac
Modularni monolit: React + TypeScript + Vite frontend, FastAPI backend, SQLAlchemy 2 + Alembic i PostgreSQL. Razvoj u cloud okruženju, bez instalacija na korisnikovom Windows računaru. Produkcioni hosting bira se kasnije; ovaj korak ne kreira plaćene servise.

## Struktura
- `frontend/src/`: početni UI i izdvojeni demonstracioni podaci; kasnije `app`, `components`, `features`, `lib` i `types`.
- `backend/app/`: budući API, core, db, models, schemas, services i integrations.
- `backend/alembic/` i `backend/tests/`: migracije i testovi backend-a u narednim koracima.
- `database/seed/`: eksplicitno označeni demo podaci kada uvedemo bazu.
- `docs/architecture/`: odluke i plan. Docker Compose dolazi sa backend-om i bazom.

## Osnovni model baze (plan, još nije implementiran)
`business_units` (LUU, INVEKTA) ima više `memberships`, koji povezuju `users` sa ulogom po jedinici: komercijalista, menadžer, administrator.
`companies` pripadaju jedinici i odgovornom korisniku; imaju više `contacts`, `locations`, `opportunities`, `activities` i `tasks`.
`pipeline_stages` pripadaju jedinici; prilika pripada kompaniji, fazi i odgovornom korisniku.
`quotes` imaju `quote_items`; LUU dodaje `products`, `price_lists` i porudžbine; Invekta `services`, `contracts` i tendere.
`lead_sources` čuvaju URL, datum provere i status potvrđenosti podatka; `audit_logs` beleže promene.

Svaki poslovni zapis nosi business_unit_id. Složeni strani ključevi treba da spreče povezivanje kompanije, kontakta i prilike između jedinica. Backend proverava članstvo, ulogu i vlasništvo pri svakom čitanju i pisanju. Menadžerski objedinjeni pregled zahteva izričito pravo. Izbor modula u frontend-u nije sigurnosna granica. Novac: NUMERIC i valuta; vreme: TIMESTAMPTZ; ograničenja i indeksi kroz migracije.

## MVP, po malim proverljivim koracima
1. **Završeno:** responzivan srpski frontend, izbor modula, dashboard, pretraga demo kompanija, prikaz levka i privremeni demo zadaci. Build i testovi filtriranja.
2. **Završeno:** FastAPI i PostgreSQL, Alembic migracije, health/readiness provere i eksplicitni demo seed.
3. **Osnova završena:** Prijava, sesije i backend autorizacija po jedinici, ulozi i vlasniku; testovi neovlašćenog pristupa. Pre stvarnih podataka.
4. **Kompanije završene; kontakti slede:** Trajno dodavanje/izmena, validacija i pretraga.
5. Prodajne prilike, promene faze, aktivnosti i zadaci. Dashboard računa KPI iz baze.
6. Provera korisničkih tokova, izolacije podataka i dokumentacije.

Kasnije: LUU katalog i potrošnja, Invekta ugovori, PDF ponude, CSV, napredni izveštaji, AI adapteri sa proverljivim izvorima i nacrtima poruka, backup i produkcija. Bez automatskog masovnog slanja.

## Trenutno stanje — verzija 0.2
Postoje PostgreSQL, migracije, prijava, serverske sesije i backend kontrola kompanija po jedinici/ulozi/vlasniku. Povezani ekran omogućava trajni unos i izmenu kompanija. Seed kreira samo jasno označene demo kompanije i demo menadžera; nove ručno unete kompanije nisu označene kao seed demo, ali je čitavo okruženje razvojno.

Demo dashboard i privremeni zadaci i dalje koriste izdvojene izmišljene podatke. Nema kontakata, zasebnog modela prilika, produkcionog hostinga, UI administracije korisnika, audit-a, AI ili backup rešenja. Pre stvarnih podataka završiti produkcionu pripremu. Trenutne faza i vrednost kompanije su prelazna osnova; zasebni opportunities dolaze u narednoj fazi.
