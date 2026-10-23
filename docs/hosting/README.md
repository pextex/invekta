# Objavljivanje CRM-a na hostingu firme

Ovo izdanje koristi stvarnu prijavu. Produkcioni frontend nema ulaz u demo ni javni pregled izmišljenih klijenata. Vodič sa 26 naracija, lični profil, AI potpisi, redosled targeta i ovlašćenja ostaju uključeni. Odvojeni Gradient + 3D predlog nije primenjen.

Za jednokratno čišćenje i pokretanje stvarnog rada na postojećem Manusu pogledati [poruku za Manus i korake pre početka rada](manus-production-launch.md). Administrator koji ostaje: `petar.milosevic@invekta.rs`; čišćenje prave baze još nije izvršeno.

## MyCity Hosting

Provajder je potvrđen kao MyCity Hosting; konkretan paket i domen još nisu utvrđeni. Njihova [Cloud server stranica](https://mycity-hosting.rs/cloud-server/) navodi SSH pristup i managed Cloud/VPS ponudu (provereno 20.10.2026). Ovaj paket je pripremljen za server sa Docker Compose. Kompatibilnost postojećeg shared paketa mora se zasebno potvrditi sa hostingom.

## Šta je potrebno

Server sa Docker Compose, domen/poddomen za CRM, HTTPS reverse proxy i postojeća ili nova PostgreSQL/MySQL baza. Običan statički/PHP hosting bez Python procesa ili Docker-a nije dovoljan za postojeći FastAPI backend. Konačne vrednosti domena i baze popunjava administrator hostinga.

1. Kopirati `.env.production.example` u `.env.production` **na serveru**. Uneti stvarni `DATABASE_URL`, HTTPS adresu u `CRM_ALLOWED_ORIGINS` i postojeći serverski Gemini ključ. Ne slati taj fajl u GitHub. `localhost` u bazi unutar kontejnera ne označava host servera: koristiti dostupnu adresu/ime baze.
2. Iz korena repozitorijuma pokrenuti:

   ```sh
   docker compose --env-file .env.production -f compose.hosting.yml up -d --build
   ```

   Standardni `npm run build` i eksplicitni `npm run build:hosting` grade produkcioni ulaz; zasebni demo se gradi samo sa `npm run build:demo`. Docker slika koristi `build:hosting`. Na pokretanju se izvršavaju samo Alembic migracije; ne pokreću se demo seed ili reset baze.
3. Podesiti HTTPS reverse proxy sa izabranog domena na `127.0.0.1:3000`. Primer je u `nginx.example.conf`. Sertifikat mora biti stvaran i važeći. Baza ne treba da bude javno dostupna.
4. Proveriti `/api/health` i `/api/ready`, pa prijavu administratora, sva tri brenda, prazan dashboard, dodavanje korisnika/kompanije, profil, AI, dokumente i vodič. `/api/ready` proverava i migraciju telefona i novčana polja marketing porudžbina (`amount`, `business_type`, `realized_at`).

Ako je baza nova i prazna, prvo treba eksplicitno kreirati/aktivirati administratorski nalog standardnim `app.bootstrap_admin` postupkom. To ne radi aplikacija automatski. Ako se čuva postojeći administrator, preneti njegov nalog i pristup iz postojeće baze; ne menjati njegovu lozinku bez zahteva vlasnika.

## Jednokratno čišćenje postojeće baze

**Reset nije izvršen pripremom ovog izdanja.** Neophodni su tačan email administratora i identifikovana ciljna baza. Ne čistiti neku drugu lokalnu, Manus ili produkcionu bazu samo zato što je njena konekcija dostupna.

Reset briše ostale korisnike, kompanije, kontakte, prilike i istoriju, zadatke, targete/bonuse, stare AI nacrte, pokušaje prijave/generisanja i sve otpremljene dokumente sa binarnim sadržajem. Čuva izabranog aktivnog administratora platforme, njegovu lozinku i telefon, pristup svim trima brendovima, konfiguraciju i znanje brendova. Svi uređaji se odjavljuju. Logotipi, naracije i izvorni fajlovi aplikacije nisu otpremljeni poslovni dokumenti i ne brišu se.

1. Napraviti privatnu rezervnu kopiju ciljne baze i proveriti da može da se vrati. Za vreme resetovanja zaustaviti CRM i ostale procese koji upisuju u istu bazu.
2. U okruženju sa pravom konfiguracijom baze, iz `backend` direktorijuma prvo dobiti **pregled bez brisanja**:

   ```sh
   python -m app.reset_workspace --admin-email ADMIN_EMAIL
   ```

3. Proveriti host, ime baze, nalog koji ostaje i broj zapisa. Zatim izvršiti isti pregledani reset:

   ```sh
   python -m app.reset_workspace --admin-email ADMIN_EMAIL --database-host DATABASE_HOST --database-name DATABASE_NAME --apply
   ```

   U Docker okruženju za ova dva koraka koristiti jednokratni `docker compose --env-file .env.production -f compose.hosting.yml run --rm crm python -m app.reset_workspace ...`, uz prethodno zaustavljen `crm` servis.

Sve izmene baze su u jednoj transakciji: greška poništava kompletan reset. Komanda odbija nalog koji nije aktiviran administrator platforme ili nema aktivan administratorski pristup svim trima brendovima. Nikada se ne pokreće pri startovanju aplikacije. Posle uspešnog resetovanja ponovo pokrenuti CRM i proveriti prijavu istom administratorskom lozinkom.

Lokalna provera pripreme pokriva izolovanu test bazu, nepoznat/pogrešan administrator, očuvanje pristupa i lozinke, brisanje dokumenata i vraćanje cele transakcije pri grešci. To nije tvrdnja da je konkretan hosting ili prava baza već očišćena.

## Rezultat provere ovog izdanja

Produkcioni frontend je proveren u Chromium-u na 1440×1000 i 390×844: nema ulaza u demo, stara `#demo` putanja ne zaobilazi prijavu, nema razvojnih napomena, vodič ostaje dostupan. Probni klijenti nisu uključeni u produkcioni JS paket.

Docker slika je izgrađena i pokrenuta kao korisnik UID 10001. Zaseban, privremeni PostgreSQL `hosting_check_test` korišćen je za stvarne startup migracije, `/api/ready`, aktivaciju test administratora, prijavu, profil i unos kompanije. Reset komanda je zatim proverena nad tom test bazom: obrisala je test kompaniju, a sačuvala test administratorsku lozinku i sva tri pristupa. Ove provere nisu pristup pravoj Manus/MyCity bazi niti objava na domenu firme.
