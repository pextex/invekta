# Invekta CRM — paket za MyCity VPS

Ovaj paket proslediti osobi koja administrira VPS. Kompletno uputstvo je u **[docs/hosting/VPS-INSTALACIJA.md](docs/hosting/VPS-INSTALACIJA.md)**.

## Poruka za menadžera / administratora servera

Molim te instaliraj ovaj CRM na naš MyCity VPS prema priloženom uputstvu. Imaš pristup kontrolnom panelu pa proveri OS, SSH/sudo, postojeći web server i odaberi odgovarajući poddomen i HTTPS. Kod je pripremljen za Docker Compose; `compose.vps.yml` uključuje privatni PostgreSQL za novu instalaciju. Nemoj menjati postojeće sajtove ili njihovu bazu.

Želimo čist početak sa administratorskim nalogom **petar.milosevic@invekta.rs**. Kreiraj ga i aktiviraj prema uputstvu, a novu lozinku predaj vlasniku privatno. Ne pokreći seed ili reset; nova baza nema stare klijente.

Podesi Gemini ključ na serveru, proveri jedan AI zahtev, HTTPS prijavu, ovlašćenja, čuvanje podataka i backup. Na kraju nam pošalji HTTPS adresu aplikacije, rezultat provera i potvrdu podešenih rezervnih kopija. Ne šalji lozinke i ključeve u grupne poruke.

## Šta je uključeno

- Frontend i Python backend, Dockerfile, zaključane zavisnosti i migracije baze.
- Sve CRM funkcije, uključujući marketing porudžbine i targete, datume ugovora i podsetnike.
- Logotipi, vodič i 26 Kore naracija, ugrađena AI pravila i početno znanje brendova.
- Konfiguracija za novi VPS sa PostgreSQL, primer promenljivih i skripta za backup.

## Šta nije uključeno

Postojeća baza, nalozi, lozinke, poslovni dokumenti i podaci, serverski ključevi i HTTPS sertifikat. Instalacija koristi novu praznu bazu i kreira nov administratorski nalog sa novom lozinkom. Paket nije već instaliran na VPS.

Ne koristiti razvojne `docker-compose.yml`, seed ili `build:demo` za ovu instalaciju. Ne pokretati komandu za reset baze.
