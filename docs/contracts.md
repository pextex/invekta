# Datumi ugovora i podsetnici

Kompanija ima opcione datume `contract_signed_on` (potpisivanje) i `contract_expires_on` (istek), unose se kroz Nova kompanija / Izmeni. Datumi se prikazuju u profilu kompanije, a istek i na listi. Datum isteka ne može biti pre potpisivanja; prazni datumi su dozvoljeni. Stari klijenti ostaju bez izmišljenih datuma.

U prijavljenom CRM-u, iznad sadržaja stranice, pojavljuje se odeljak **Ugovori koji ističu ili su istekli (broj)**. Otvaranjem odeljka vidi se kompanija, datum i broj preostalih dana, uz dugme za profil. Rok podsetnika je uključivo 30 kalendarskih dana unapred, po Europe/Belgrade; datum isteka označen je „Ističe danas”, prethodni datumi kao istekli. Podsetnik ostaje do promene/brisanja datuma, a produženje preko 30 dana uklanja ga. Ne kreiraju se dupli zadaci. Podsetnik je u aplikaciji, ne šalje email, SMS ili sistemsku push notifikaciju dok je aplikacija zatvorena.

Podaci se osvežavaju pri promeni kompanije, vraćanju fokusa i svakog minuta dok je tab vidljiv. Prikazuje se pet po stranici uz paginaciju, nezavisno od pretrage i ograničenja 200 na listi kompanija. Ugovori su sortirani od najranijeg isteka. Prava prate kompanije: komercijalista samo svoje, menadžer/admin kompanije dozvoljenog brenda; marketing ne vidi podsetnik niti podatke kompanija. Označeni demo klijenti se ne računaju.

API: `GET /api/units/{unit_id}/contract-reminders?limit=5&offset=0`, vraća `today`, `reminder_days`, `total`, `items`. Filter i broj zapisa obračunavaju se na serveru, nakon provere pristupa. Čitanje ništa ne menja u bazi.

## Objavljivanje ove izmene

Preuzeti najnoviji commit grane `codex/task-calendar`, napraviti standardnu rezervnu kopiju, pokrenuti `python -m app.run_migrations` iz `backend` i objaviti novi backend i frontend (`npm run build:hosting`). Nova migracija `de50a9b234c6`, iza `cd49f8a123b5`, dodaje dva nullable DATE polja, proveru redosleda datuma i indeks. `/api/ready` proverava i nova polja.

Ovo je nadogradnja postojeće aplikacije: **ne pokretati reset_workspace, seed, brisanje naloga ili downgrade** radi ove izmene. Raniji jednokratni plan čišćenja nije postupak za redovno ažuriranje. Ovom izmenom nije pristupano pravoj Manus bazi i sajt nije objavljen.

## Provera

API testovi pokrivaju unos, čitanje, izmenu i brisanje datuma, neispravne datume i redosled, provere postojećeg datuma pri parcijalnoj izmeni, Origin zaštitu, vlasništvo, brendove, menadžera/admina, marketing, 30 dana, istek danas, istekle ugovore, paginaciju i produženje. Izolovani PostgreSQL testovi proveravaju migraciju nove i postojeće šeme. Produkcioni frontend u Chromium-u na 1440×1000 i 390×844 proveren je kroz stvarni API i izdvojenu PostgreSQL bazu: prijava, podsetnik, profil, izmena datuma, čuvanje u bazi i uklanjanje podsetnika nakon produženja.
