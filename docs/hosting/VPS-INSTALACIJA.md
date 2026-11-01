# Instalacija CRM-a na MyCity VPS — nova baza i novi administrator

Ovo je postupak za **novu praznu PostgreSQL bazu i nov administratorski nalog**. Počinje se bez klijenata, porudžbina i starih korisnika. Primeri koriste `/opt/invekta-crm` i `crm.example.rs`: domen zameniti stvarnim.

## 1. Server i pristup

Administrator proverava OS i verziju, SSH/sudo pristup, raspoložive resurse, postojeće sajtove i web panel. Preporučeno je najmanje 2 vCPU, 4 GB RAM i 20 GB slobodnog diska; build zahteva više memorije nego svakodnevni rad. Potrebni su podržani Docker Engine + Compose v2, HTTPS reverse proxy i DNS pristup. Ako nisu instalirani, instalirati ih prema OS-u i zvaničnom Docker uputstvu, uz očuvanje postojećih servisa.

Ako postoji cPanel/DirectAdmin ili drugi panel, poddomen i HTTPS podesiti kroz njega. Ne menjati postojeću konfiguraciju web servera naslepo. Proveriti da port 3000 nije zauzet i da ne postoji projekat/volume `invekta-crm` pre prve instalacije.

U firewall-u omogućiti postojeći SSH pristup, 80 i 443. Ne izlagati PostgreSQL (5432) internetu. Potrebna je odlazna HTTPS veza prema registrima paketa/slika i `generativelanguage.googleapis.com`.

## 2. Raspakivanje i serverske promenljive

Raspakovati sadržaj paketa u `/opt/invekta-crm`; tamo treba direktno da budu `Dockerfile`, `compose.vps.yml`, `frontend` i `backend`, bez dodatnog ugnježdenog foldera. Server administrator bira korisnika koji upravlja ovim folderom i ima pristup Docker-u; primeri su iz tog foldera:

```sh
cd /opt/invekta-crm
umask 077
cp -n docs/hosting/vps.env.example .env.production
chmod 600 .env.production
openssl rand -hex 32
```

Poslednja komanda generiše lozinku za novu bazu. Uneti taj rezultat kao `POSTGRES_PASSWORD` u `.env.production` pomoću serverskog editora. Koristiti baš heksadecimalnu lozinku radi ispravnog URL-a konekcije. Zameniti `CRM_ALLOWED_ORIGINS` tačnim originom, na primer `https://crm.firma.rs`, bez završne kose crte.

`CRM_COOKIE_SECURE=true` ostaje uključen. AI je početno isključen; Gemini ključ se naknadno unosi privatno na serveru. `.env.production` ne slati u repozitorijum ili paket za prosleđivanje. Ne postavljati promenljive/ključeve u frontend. `compose.vps.yml` sam formira `DATABASE_URL` za internu bazu; ne unositi `localhost` kao adresu baze.

## 3. Pokretanje baze i aplikacije

```sh
docker compose version
docker compose --env-file .env.production -f compose.vps.yml config --quiet
docker compose --env-file .env.production -f compose.vps.yml up -d --build
docker compose --env-file .env.production -f compose.vps.yml ps
```

Sačekati da `db` i `crm` budu healthy. Na prvom pokretanju backend primenjuje sve migracije i priprema tri brenda; ne kreira korisnike ili klijente. Poslednja migracija funkcionalnog izdanja je `de50a9b234c6`, uključuje datume ugovora. Frontend se gradi u produkcionom režimu, uključujući naracije. Podaci baze se čuvaju u Docker named volume-u `invekta-crm_crm_postgres`, nezavisno od zamene kontejnera.

```sh
curl --fail http://127.0.0.1:3000/api/health
curl --fail http://127.0.0.1:3000/api/ready
```

Oba zahteva treba da vrate uspeh. Ako ne, pregledati serverske logove privatno:

```sh
docker compose --env-file .env.production -f compose.vps.yml logs --tail=100 crm db
```

Ne pokretati razvojni seed, reset baze ili `build:demo`. **Ne koristiti `down -v` ili `docker volume prune` za restart: time se mogu obrisati poslovni podaci.** Ne menjati sačuvanu lozinku baze nakon kreiranja volume-a bez stvarne promene lozinke u PostgreSQL-u.

## 4. Nov administratorski nalog

Za novu bazu, iz istog foldera, pripremiti administratora:

```sh
docker compose --env-file .env.production -f compose.vps.yml exec crm python -m app.bootstrap_admin --email petar.milosevic@invekta.rs --name 'Petar Milošević'
```

Zatim ga jednokratno aktivirati:

```sh
docker compose --env-file .env.production -f compose.vps.yml exec crm python -m app.bootstrap_admin --email petar.milosevic@invekta.rs --name 'Petar Milošević' --activate
```

Komanda u privatnom terminalu traži novu lozinku i potvrdu (najmanje 12 znakova), bez prikaza unosa. Ne zadavati lozinku u komandnoj liniji. Profil dobija administratorski pristup svim trima brendovima. Aktivacija nije redovan postupak za resetovanje lozinke i ne može se ponavljati nad aktivnim nalogom. Ako email/nalog već postoji, proveriti stanje umesto zaobilaženja zaštite. Lozinku predati vlasniku privatno.

## 5. Domen i HTTPS

Podesiti DNS A zapis poddomena prema IPv4 VPS-a; ako postoji AAAA, mora pokazivati na njegovu stvarnu IPv6 adresu. Podesiti reverse proxy za taj poddomen ka `http://127.0.0.1:3000`, stvarni važeći TLS sertifikat i automatsko obnavljanje. Za samostalni Nginx primer je `docs/hosting/nginx.example.conf`: zameniti domen i putanje sertifikata; sertifikat prvo izdati kroz panel ili administratorov standardni ACME postupak. Pre učitavanja Nginx konfiguracije izvršiti `nginx -t`.

Proxy mora prosleđivati Host, X-Forwarded-Proto i X-Forwarded-For; timeout najmanje 90 sekundi, dozvoljen upload 11 MB (postojeći primer to sadrži). HTTP treba preusmeriti na HTTPS. Panel i aplikacija ne smeju se takmičiti za portove 80/443. Port aplikacije ostaje vezan samo na 127.0.0.1.

Prijavu testirati na **HTTPS domenu**, ne na HTTP adresi porta 3000: sesijski cookie je namerno Secure. Proveriti da origin domena tačno odgovara `CRM_ALLOWED_ORIGINS`.

## 6. Uključivanje AI asistenta

U `.env.production` privatno uneti `CRM_GEMINI_API_KEY` i postaviti `CRM_AI_ENABLED=true`. Izabrani `CRM_GEMINI_MODEL` mora biti dostupan tom Google projektu, uz raspoloživu kvotu. Ne uključivati plaćene pakete bez odobrenja vlasnika.

```sh
docker compose --env-file .env.production -f compose.vps.yml up -d crm
```

Compose ponovo kreira servis kada se promeni env konfiguracija. Proveriti jedan stvarni zahtev iz AI ekrana sa odobrenim podacima. Uspešan lokalni šablon nije dokaz rada Gemini servisa. AI priprema nacrt mejla, a korisnik ga proverava i šalje iz svog mejl klijenta. Logotipi, naracije, ugrađena pravila i početno znanje brendova su u paketu; odobreno dodatno znanje može uneti administrator/menadžer.

## 7. Backup i obnova

Skripta za ovaj PostgreSQL stack pravi dump u privatni folder i proverava da je arhiva čitljiva:

```sh
sudo bash /opt/invekta-crm/scripts/backup-vps.sh
```

Kopije se podrazumevano čuvaju u `/var/backups/invekta-crm`, sa dozvolama samo za vlasnika. Za dnevnu kopiju napraviti `/etc/cron.d/invekta-crm-backup` sa sadržajem (termin je u vremenskoj zoni servera):

```cron
15 2 * * * root /bin/bash /opt/invekta-crm/scripts/backup-vps.sh >> /var/log/invekta-crm-backup.log 2>&1
```

Pratiti log i prostor na disku. Dogovoriti čuvanje najmanje 30 dnevnih kopija i privatnu kopiju van VPS-a. Skripta ne briše stare kopije automatski. Zasebno sačuvati zaštićenu serversku konfiguraciju i tačnu verziju paketa radi obnove. Poslovni dokumenti čuvaju se u bazi i ulaze u dump. Sam snapshot servera nije zamena za probu obnove.

Probnu obnovu izvršiti na izdvojenoj bazi pre početka rada. U vanrednom slučaju, obnova prave baze **zamenjuje postojeće podatke**: zaustaviti upise, napraviti kopiju trenutnog stanja i uz odluku odgovorne osobe vratiti pregledani dump u kompatibilnu verziju aplikacije. Primer, tek po odabiru stvarnog fajla:

```sh
docker compose --env-file .env.production -f compose.vps.yml stop crm
docker compose --env-file .env.production -f compose.vps.yml exec -T db pg_restore --clean --if-exists --no-owner --exit-on-error -U crm -d crm < /PRIVATE/PATH/SELECTED_BACKUP.dump
docker compose --env-file .env.production -f compose.vps.yml up -d crm
```

Ne izvršavati ovaj primer kao deo prve instalacije. Ako obnova prijavi grešku, ostaviti aplikaciju zaustavljenu i rešiti obnovu pre nastavka rada.

## 8. Završna provera i predaja

- HTTPS i sertifikat rade; `/api/health` i `/api/ready` vraćaju uspeh na domenu.
- Nova administratorska prijava radi u sva tri brenda; nema probnih klijenata ili starih naloga.
- Otvoriti stvarne naloge kroz „Korisnici i pristup” i dodeliti brend/ulogu. Komercijalista vidi samo svoje kompanije i zadatke; marketing koristi svoje porudžbine i nema vodič; menadžer i administrator imaju odgovarajuća prava svog brenda.
- Administrator unosi mesečne targete i kolektivni cilj; korisnici dopunjavaju telefon za AI potpis i menjaju početne lozinke kroz Moj profil. Oporavak lozinke radi administrator; automatsko slanje emaila za oporavak nije deo aplikacije.
- Prva stvarna kompanija/porudžbina, datumi ugovora i zadaci ostaju sačuvani posle restarta. Podsetnik za ugovor pojavljuje se u CRM-u 30 dana pre isteka; nije email ili push kada je aplikacija zatvorena.
- AI proveriti stvarnim zahtevom; PDF/dokumente i vodič proveriti u pregledaču. Testove sa izmišljenim podacima raditi u izdvojenoj bazi, ne ostavljati ih u produkciji.
- Backup je zakazan, proverena je izdvojena obnova i određena odgovorna osoba za održavanje.

Vlasniku predati HTTPS adresu, verziju instaliranog paketa, potvrdu nove baze i admin naloga, rezultate provera i podatak gde/koliko dugo se čuvaju kopije. Lozinke, API ključ i pristup serveru predati odvojeno privatnim putem. Pakovanje koda nije potvrda da je konkretan VPS već podešen ili aplikacija objavljena.
