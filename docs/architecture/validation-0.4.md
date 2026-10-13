# Provera verzije 0.4 — tri kompanije i ekran prijave

- 30 PostgreSQL backend testova prolaze, uključujući odabir kompanije pri prijavi, odbijanje korisnika bez Cenobots članstva bez kreiranja sesije, validaciju kodova i izolaciju kompanija/kontakata/prilika/KPI podataka.
- Migracija registruje nedostajuće LUU, Invekta i Cenobots jedinice bez promene postojećih zapisa ili članstava. Seed je ponovljiv i daje treću jedinicu samo razvojnom demo nalogu.
- Dva frontend testa prolaze; filtriranje provereno i za Cenobots. TypeScript/Vite build prolazi.
- Browser: izbor sve tri kompanije, ulaz u Cenobots demo, stvarna prijava u Cenobots, njegov dashboard, odvojene tabele pri prebacivanju na LUU/Invektu, odjava i mobilni ekran 390 × 844 bez horizontalnog prelivanja.
- Samostalni HTML prikazuje novi portal i eksplicitan ulaz u demo bez autentifikacije; pravi login zahteva API.

Cenobots demo partneri i iznosi su neutralni izmišljeni primeri, ne podaci preuzeti sa sajta. Administracija članstava kroz UI i produkcioni hosting ostaju za naredne faze.
