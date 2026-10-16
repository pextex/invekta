# CRM na Vercel Services

Opciono odvojeno okruženje za postojeći React/Vite i FastAPI kod. Root `Dockerfile`, Manus port/startup, migracije i managed baza ostaju isti. Vercel konfiguracija ne objavljuje sajt i ne prenosi podatke sama po sebi.

## Servisi i javne putanje

| Servis | Izvor | Javni ulaz | Pozivi drugih servisa / bindings |
| --- | --- | --- | --- |
| `backend` | `backend`, FastAPI `app.main:app`, Python 3.12 | `/api/...` | Nema |
| `frontend` | `frontend`, Vite statički `dist` | Sve ostalo, uključujući `/` i `/assets/...` | Nema serverskih funkcija ni internih poziva |

Browser koristi postojeće relativne `/api` URL-ove. Vercel rutira te zahteve direktno backend-u i zadržava `/api` prefiks; ne dodaje se drugi `/api`, `root_path`, javni backend hostname ili CORS. Autentifikacija, sesije, Origin provera i prava ostaju na backend-u. Backend nije javan preko drugih putanja: `/docs`, `/openapi.json` i `/redoc` nisu izloženi ovom konfiguracijom. `GET /api/ready` ostaje dostupan bez prijave. Aplikacija koristi postojeće `#crm/...` putanje, tako da refresh ne traži poseban SPA rewrite.

**Bindings nisu dodati:** statički React se izvršava u browser-u, ne u frontend serverskoj funkciji. Binding promenljiva ne bi bila dostupna tom kodu, a nije dostupna ni tokom Vite build-a. Backend ne poziva frontend; Groq i spoljašnja baza nisu Vercel servisi ovog projekta. Ne izlagati interne URL-ove kroz `VITE_` promenljive. Ako se kasnije doda pravi serverski poziv između servisa, binding se deklarše na njegovom pozivaocu, sa sva četiri polja `type`, `service`, `format`, `env`, a URL se čita u funkciji tokom izvršavanja. [Vercel bindings](https://vercel.com/docs/services/bindings).

## Podešavanje projekta

1. Uvesti ovaj repozitorijum u **jedan** Vercel projekat, sa Root Directory na korenu repozitorijuma, gde je `vercel.json`. Potrebna je podrška za aktuelni `services` režim. Ne postavljati jedan servis kao root celog projekta. Omogućiti pristup zajedničkim izvorima van pojedinačnog service root-a ako ga postavke projekta ograničavaju: oba build-a koriste `shared/message_catalog.json`.
2. Frontend koristi `npm ci` i postojeći `frontend/package-lock.json`. Backend koristi `backend/uv.lock`; njegov build eksplicitno pokreće `uv run --frozen --no-dev python build_vercel.py`, bez importovanja aplikacije ili baze. Skripta kopira samo javni katalog poruka u generisani `backend/app/_vercel_data/`, kako bi bio dostupan u zasebnom Python runtime paketu. Manus i lokalni razvoj nastavljaju da čitaju originalni `shared/` fajl. Python je izabran preko `backend/.python-version`.
3. **Serverske tajne uneti direktno u Vercel podešavanjima**, nikad u chat/Git: `DATABASE_URL` za dostupnu PostgreSQL ili MySQL/PyMySQL bazu. Standardni PostgreSQL URI prefiksi `postgres://` i `postgresql://` automatski koriste zaključani drajver psycopg 3, kao i eksplicitni `postgresql+psycopg://`; TLS parametri ostaju sačuvani. Opciono `CRM_GROQ_API_KEY` samo ako se AI uključuje. `CRM_AI_ENABLED=false` ostaje početna vrednost. Ako se uključi, koristi postojeći Groq Free nalog i `CRM_GROQ_MODEL`, bez plaćenog fallback-a. Ne kopirati vrednosti iz Manus Secrets. Podatke za pristup bazi obezbeđuje njen vlasnik preko podržanog načina povezivanja.
4. Na HTTPS-u zadržati `CRM_COOKIE_SECURE=true` (podrazumevano). `CRM_ALLOWED_ORIGINS` može sadržati tačne dozvoljene HTTPS domene, odvojene zarezom. Postojeća provera browser `Sec-Fetch-Site: same-origin` podržava preview domene bez `*` liste. Ne izvoditi javne adrese iz internog Host header-a.
5. **Ne koristiti postojeću Manus managed bazu kao pretpostavku.** Ona možda nema podržan spoljašnji pristup. Za Vercel Preview koristiti zasebnu neprodukcijsku bazu; izbor produkcione baze/podataka treba posebno navesti. Git ne prenosi korisnike, sesije ili klijente. Za postojeće naloge potrebna je dostupna ista baza ili odobren prenos koji čuva podatke; nova prazna baza ih nema. Na novom domenu potrebna je ponovna prijava jer browser ne prenosi Manus cookie na Vercel; postojeći zapisi sesija se ne menjaju. Nijedna nova baza, kopija ili prenos nije napravljen ovim podešavanjem.
6. Vercel build i import aplikacije **ne pokreću Alembic, seed ili reset**. Zaostalu šemu prijavljuje `/api/ready` sa 503. Migracije sprovoditi odvojeno iz okruženja koje ima pristup izabranoj bazi, uz backup i proveru postojeće revizije; ne paralelno pri startu serverless instanci. Ne pokretati test runner nad managed/produkcijskom bazom. Za ovu konfiguraciju nema nove migracije.

## Nova prazna baza umesto Manus podataka

Vlasnik je izabrao novu bazu. Predloženi servis je Neon PostgreSQL, projekat `invekta-crm`, uz Free paket bez automatskog prelaska na naplatu. Kreiranje online projekta zahteva povezan vlasnikov Neon nalog ili Vercel Marketplace integraciju. Priprema koda i lokalna provera nisu dokaz da je online baza napravljena. [Neon paketi](https://neon.com/pricing) · [Postgres na Vercel-u](https://vercel.com/docs/postgres).

1. Napraviti nov, prazan PostgreSQL projekat/bazu, bez kloniranja Manus podataka i bez uključivanja Neon Auth-a: CRM zadržava svoju postojeću prijavu i sesije. Sačuvati TLS u vezi. Tajni connection URL uneti direktno kroz zaštićenu konfiguraciju, nikad u chat ili argument komandne linije.
2. U privatnom terminalu checkout-a pripremiti `DATABASE_URL` **isključivo za novu bazu**. Za jednokratne migracije koristiti direktnu/unpooled vezu, ne PgBouncer adresu koja sadrži `-pooler`. Ne koristiti stari Manus URL. Iz `backend/`, posle `uv sync --frozen`, pokrenuti:

   ```bash
   uv run --frozen python -m app.run_migrations
   ```

   Postojeće Alembic migracije prave CRM šemu i registruju LUU, INVEKTA i CENOBOTS; ne dodaju korisnike, klijente, dokumente ili demo sadržaj. Nema nove migracije, seed-a, reset-a ili izmišljene početne lozinke.
3. Pripremiti, pa aktivirati prvi administratorski nalog postojećim komandama, sa **svojim stvarnim emailom i imenom** umesto primera:

   ```bash
   uv run --frozen python -m app.bootstrap_admin --email osoba@example.com --name 'Ime Prezime'
   uv run --frozen python -m app.bootstrap_admin --email osoba@example.com --name 'Ime Prezime' --activate
   ```

   Aktivacija traži novu lozinku u skrivenom unosu ako `CRM_ACCOUNT_PASSWORD` nije postavljen. Ne koristiti nasleđenu promenljivu sa nepoznatom lozinkom. Komanda ne šalje email. Administrator dobija aktivan pristup sva tri brenda, zatim korisnike kreira kroz „Korisnici i pristup“; prodajna ovlašćenja ostaju ista.
4. U Vercel projektu podesiti `DATABASE_URL` nove baze (runtime može koristiti Neon pooled vezu), `CRM_COOKIE_SECURE=true`, a AI ostaviti isključenim dok se posebno ne podesi. Zatim objaviti i proveriti `/api/ready`, prijavu i prazne kompanije sva tri brenda. Preview povezati na zasebnu praznu test granu/bazu, ne na produkcione podatke. Ne pokretati backend testove na Neon produkciji.

Stara Manus baza se ne menja. Njeni korisnici, kompanije, istorija, zadaci i fajlovi neće se pojaviti u novoj bazi. Eventualni kasniji uvoz zahteva zaseban plan za povezane zapise i sprečavanje duplikata. Ograničenje većih fajlova na Vercel-u opisano ispod i dalje važi.

### Kreiran Neon projekat

Dana 2026-10-16 kreiran je namenski projekat **invekta-crm**, PostgreSQL 16 u Frankfurtu, na potvrđenom Free nalogu. [Otvori projekat](https://console.neon.tech/app/projects/falling-glitter-57126600). Baza je `crm`, vlasnička DB uloga `crm_owner`. Netajni identifikatori i direktni/pooled host su u `deployment/neon.json`; connection URL i lozinke nisu u repozitorijumu. Postojeći lokalni `.env` nije preusmeren na online bazu.

Grane **production** i **preview** inicijalizovane su do revizije `c9d7a4e8f201` postojećim Alembic migracijama: 17 tabela sa Alembic metapodacima, tri poslovne jedinice, bez klijenata i demo sadržaja. Najpre je proverena preview grana; ista transakcija je potom primenjena na praznu production bazu. Prvi administratorski profil pripremljen je samo na production grani kao **neaktivan / bootstrap_pending**, sa pristupom sva tri brenda. Stvarna lozinka se postavlja odvojeno i nije generisana, prikazana ili poslata kroz chat. Preview nema taj nalog. Vercel projekat još nije povezan niti objavljen.

Za aktivaciju iz privatnog interaktivnog terminala checkout-a, uz instaliran uv/Python 3.12, iz korena repozitorijuma pokrenuti (zameniti email i ime svojim):

```bash
uv run --frozen --project backend python scripts/activate_neon_admin.py --email osoba@example.com --name 'Ime Prezime'
```

U Neon projektu izabrati **production → Connect**, bazu `crm`, ulogu `crm_owner` i direktnu vezu (isključeno pooling). Connection URL nalepiti u skriveni terminalski unos, zatim uneti i potvrditi svoju novu lozinku. Skripta proverava da je cilj baš nova production baza i da TLS ostaje uključen; zatim poziva postojeći `app.bootstrap_admin --activate`. Ne preuzima tajne kroz chat, ne menja `.env`, ne koristi nasleđenu `CRM_ACCOUNT_PASSWORD`, ne pokreće migracije/seed i ne može ponovljenom aktivacijom resetovati aktivan nalog. Ne pokretati je u chat poruci, javnom logu ili neinteraktivnom CI job-u.

Za primenu migracija preko odobrene veze koja prihvata SQL, Alembic sada podržava standardni **offline izvoz** `alembic upgrade head --sql`: on generiše SQL iz postojećih migracija bez povezivanja na bazu i bez URL-a/lozinke u izlazu. Taj puni izvoz je namenjen isključivo praznoj bazi, uz proveru cilja; ne izvršavati ga ponovo nad postojećim CRM-om. Uobičajeni online Alembic tok i Manus startup ostaju isti. Nisu dodavane nove migracije.

Ako aktivacija odbije vezu pre zahteva za lozinku, ažurirati checkout sa `git pull --ff-only`. Skripta sada razlikuje pogrešan endpoint, bazu, port i TLS bez ispisivanja unetih vrednosti. U Connect prozoru baza mora biti **crm**, ne podrazumevana `neondb`, a grana **production** u projektu **invekta-crm**. Može se nalepiti sam URL, URL u navodnicima ili Neon komanda `psql 'URL'`; komanda se samo parsira, nikad ne izvršava kroz shell. Pooled URL se prihvata samo za unapred zabeleženi production endpoint i pretvara u njegovu direktnu vezu uz očuvanje lozinke i TLS parametara. Preview i svi drugi endpoint-i se odbijaju. Ako uv nije u PATH-u, prvo pokrenuti `python scripts/dev_tools.py`, a zatim koristiti `.dev-tools/bin/uv` umesto `uv` u komandi za aktivaciju. Nijedna od ovih komandi ne pokreće razvojni CRM, migracije ili seed.

## Lokalna provera svih servisa

Postojeće `python scripts/dev.py` ostaje dostupno. Za proveru baš Vercel rutiranja koristiti aktuelni Vercel CLI iz korena:

```bash
vercel dev -L
```

`-L` pokreće servise lokalno bez prijave na Vercel Cloud; može se koristiti i povezani `vercel dev`. Pre toga obezbediti Node 22/24, Python 3.12, uv, zaključane zavisnosti (`npm ci` u `frontend`, `uv sync --frozen` u `backend`) i lokalnu PostgreSQL bazu sa postojećom šemom. Za lokalni HTTP podesiti `CRM_COOKIE_SECURE=false` samo u lokalnom, ignorisanom `.env`. CLI ispisuje zajedničku adresu; otvoriti nju, ne pojedinačan servisni port. `/api/health` treba da vrati JSON, `/api/ready` status baze, a `/api/auth/me` bez prijave 401. Zatim proveriti pravu prijavu, kompanije i generisanje ako je AI izričito konfigurisan. Ne pokretati seed da bi pregled izgledao popunjen.

Postojeći `frontend/vite.config.ts` proxy `127.0.0.1:8000` služi za običan lokalni/Codespaces razvoj. Nije produkcijska veza između Vercel servisa: zajednički Vercel ulaz prvo rutira `/api/...` backend-u, pre nego što zahtev stigne do Vite-a. Nema server-to-server poziva koji bi zahtevao bound URL.

## Ograničenja pre produkcijske upotrebe

- Vercel Functions imaju limit tela zahteva/odgovora od **4,5 MB**. CRM trenutno dozvoljava prodajne dokumente do **10 MiB**; veći upload/download može zato biti odbijen na Vercel-u pre aplikacije. Ta funkcija zahteva dodatno rešenje za velike fajlove ili izbor odgovarajućeg runtime-a pre pune zamene Manus-a. Nisu uvedeni novi storage servisi niti promenjen postojeći limit/podaci. [Vercel Functions limits](https://vercel.com/docs/functions/limitations).
- FastAPI funkcija ima konfigurisanih 60 sekundi za postojeći Groq timeout od 45 sekundi. Dostupnost servisa, limita i spoljašnjeg pristupa bazi proveriti za konkretan Vercel projekat/paket; ne nadograđivati paket automatski.
- Lokalni build/test nije dokaz javnog deployment-a niti potvrda Groq ključa. Posle objave proveriti `/api/ready`, sesiju i jedan neosetljiv AI zahtev u stvarnom runtime-u.

Reference: [Services](https://vercel.com/docs/services), [rutiranje koje zadržava originalnu putanju](https://vercel.com/docs/services/routing), [FastAPI](https://vercel.com/docs/frameworks/backend/fastapi).

## Provera ove konfiguracije

Lokalno je proverena sa Vercel CLI 64.3.1 kroz `vercel dev -L`: oba servisa, React stranica, `/api/health`, `/api/ready`, 401 bez sesije, prava prijava/refresh, čitanje lokalne PostgreSQL `_test` baze, izolacija kompanija komercijaliste i generisanje lokalnog šablona bez Groq poziva. Prošlo je 130 backend testova (uključujući online/offline migracije prazne šeme, aktivaciju/prijavu prvog administratora i zaštitu unosa nove aktivacione komande), 11 frontend testova, frontend build, Pyright i Manus Docker build/runtime provera na `_test` bazi. Neon šema primenjena je i proverena na preview i production grani; produkcioni početni nalog ostaje pending do privatnog postavljanja lozinke. Cloud Vercel build/deployment i povezivanje Vercel projekta još nisu izvršeni. Manus produkcija nije menjana.
