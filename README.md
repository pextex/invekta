# LUU × INVEKTA × CENOBOTS — AI Sales CRM

Zajednička CRM platforma za LUU, Invektu i Cenobots. **Razvojna verzija 0.4**, samo za testne podatke. Produkcioni hosting još nije postavljen.

## Izgled interfejsa

Odeljak „Specijalizovani moduli“ i posebne stavke za proizvode/usluge uklonjeni su iz menija. Izbor poslovne jedinice LUU/Invekta/Cenobots ostaje u zaglavlju.

Interfejs prati dostavljeni HTML prototip: tamnoplava navigacija, plava dugmad, svetla pozadina, plavo-tirkizni baner i kartice. Demo i povezani CRM dele isti raspored. Globalna pretraga je u zaglavlju. CRM je vezan za izabranu firmu; nema menija za prebacivanje. Za promenu firme odjavite se, izaberite drugu i ponovo se prijavite. Stavke koje još nisu povezane jasno prikazuju da su u pripremi.

## Šta sada radi
- Unos, izmena i pretraga kompanija, uz odvojene poslovne jedinice.
- Profil kompanije: više kontakt osoba, e-mail, telefon i pozicija; trajni unos i izmena.
- Više prodajnih prilika po kompaniji: naslov, vrednost u RSD, faza, očekivani datum zatvaranja i beleška.
- Kanban sa fazama Novi lead, Kontaktiran, Sastanak, Ponuda, Pregovori, Dobijeno i Izgubljeno. Faza se menja prevlačenjem kartice ili izborom na kartici; promene ostaju u bazi.
- Istorija kreiranja i promena faze sa korisnikom i vremenom. Zastarela izmena prilike vraća konflikt umesto prepisivanja novijih podataka.
- Povezani dashboard i osnovni izveštaj računaju kompanije, kontakte, otvorene prilike, potencijalnu vrednost i dobijene poslove iz baze, prema pravima korisnika.
- Prijava, serverske sesije, hash lozinki, odjava i osnovno ograničenje pokušaja prijave.
- Backend i baza sprečavaju povezivanje kontakata/prilika sa kompanijom iz druge jedinice. Komercijalista vidi podatke svojih kompanija; menadžer i administrator vide podatke u svojim jedinicama.
- Eksplicitan demo seed čuva postojeće zapise i lozinke. Demo kontakti i prilike su označeni; svi razvojni podaci služe samo testiranju.

Ponude, trajni zadaci, aktivnosti, raspodela kompanija, upravljanje nalozima kroz UI, potpuna audit evidencija i AI još nisu implementirani. Istorija faza je trenutno jedina poslovna istorija promena. Dobijeni poslovi predstavljaju vrednost prilika označenih kao dobijene, ne fakturisan prihod.

## Kako koristiti povezani CRM
1. Na početnom ekranu izaberite **LUU**, **Invekta** ili **Cenobots**, pa unesite korisničko ime i lozinku. Server proverava pristup izabranoj jedinici pre kreiranja nove sesije.
2. U **Kompanije** dodajte kompaniju ili kliknite **Otvori profil →**.
3. U profilu, kroz **Kontakt osobe**, unesite kontakt i sačuvajte ga.
4. Otvorite karticu **Prodajne prilike** i kreirajte jednu ili više prilika.
5. U meniju **Prodajni levak** prevucite karticu u drugu kolonu ili promenite fazu izborom na kartici. Na telefonu koristite izbor faze. Dugme **Istorija** prikazuje promene. Ako se pojavi konflikt, osvežite levak pre nove izmene.
6. **Početna tabla** prikazuje aktuelne pokazatelje iz baze. Refresh zadržava otvorenu stranicu, profil i poslovnu jedinicu.

## Interaktivni demo levak
Preuzeti demo HTML sada podržava sedam statusa, prevlačenje i izbor statusa na kartici. Statusi su sačuvani lokalno kada browser dozvoljava localStorage, uz pamćenje otvorene demo stranice. Otvarajte isti fajl u istom browseru da biste videli prethodne izmene. Demo ne šalje ove promene backend-u. Kada lokalno čuvanje nije dostupno, prikazuje se poruka da promena važi samo tokom tog prikaza.

Pokazatelji demo dashboard-a odmah prate promene: Dobijeno i Izgubljeno ne ulaze u otvorene prilike i njihovu potencijalnu vrednost. Zadaci u demo prikazu i dalje nisu trajni.

U povezanom levku kartica menja kolonu tek posle uspešnog API čuvanja. Kod greške ili konflikta ostaje u prethodnoj koloni. Tokom čuvanja ili otvorene forme blokirane su dodatne promene faze. Istorija i serverska kontrola pristupa važe i za prevlačenje.

## Tri poslovne jedinice i prijava
Cenobots je registrovan kao zasebna jedinica `CENOBOTS`, uz LUU i Invektu. Migracija dodaje nedostajuće jedinice, čuva postojeća imena i podatke i **ne dodeljuje pristup postojećim korisnicima**. Prava se vode u `memberships`; za sada ih priprema administrator van korisničkog interfejsa. Korisnik vidi samo dozvoljene jedinice u povezanom CRM-u.

Razvojni `seed` daje isključivo nalogu `demo` pristup sve tri jedinice i kreira označene izmišljene Cenobots partnere, kontakte i prilike. Cenobots demo podaci ne predstavljaju klijente ili katalog sa sajta. Za pristup Cenobots-u na već pripremljenoj razvojnoj bazi ponovo pokrenite eksplicitni seed uz postojeću demo lozinku, bez `--reset-password`.

Početni URL bez CRM putanje prikazuje novi ekran prijave. `#crm/...` putanja vraća postojeću sesiju i ovlašćenu jedinicu posle refresh-a. U preuzetom HTML-u izaberite kompaniju, pa **Pogledaj demo bez prijave**. Taj ulaz daje samo izmišljene podatke, ne autentifikaciju ili pristup backend-u. Za pravu prijavu potreban je pokrenut backend; u fajlu otvorenom preko `file:` dugme za pravu prijavu je onemogućeno.

Novi frontend šalje `business_unit_code` pri prijavi. API zadržava kompatibilnost sa starim klijentima koji ne šalju izbor; svaki pristup podacima i dalje proverava članstvo i vlasništvo.

## Prelazak sa verzije 0.2
Pokrenite `alembic upgrade head` iz foldera `backend`. Migracija prenosi raniju vrednost i fazu kompanije u jednu početnu prodajnu priliku. Stara polja kompanije nisu uklonjena ni resetovana, ali se više ne koriste za novi levak i KPI. Kontakt postaje zaseban zapis. Početnim prenetim prilikama se ne izmišlja korisnik ili istorija promena; istorija počinje novim eksplicitnim promenama.

API lista prilika koristi paginaciju (100 po strani u UI, najviše 200 po API zahtevu). Dashboard računa sve ovlašćene zapise, nezavisno od stranice. Tabela kompanija i izbor kompanije pri kreiranju prilike i dalje prikazuju najviše 200 pogodaka. Pretragom pronađite kompaniju i otvorite njen profil za unos prilike ako je nema u početnom izboru.

## Pokretanje u privatnom cloud / Codespaces razvoju
Potrebni: Node.js 22/24 LTS, Python 3.12+, `uv` i Docker sa Compose-om. Koristite postojeći checkout; ne kreirajte dodatni projekat.

Iz korena repozitorijuma:

```bash
python scripts/setup_dev.py
docker compose up -d --wait db
cd backend
uv sync --frozen
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m app.seed
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Seed traži lozinku demo naloga, bez prikaza unosa. Izaberite najmanje 12 znakova. Korisničko ime je **demo**; ovaj razvojni menadžer ima pristup svim trima jedinicama. Za neinteraktivno pokretanje postavite `CRM_DEMO_PASSWORD` u proces kroz siguran kanal. Ponovni seed ne menja postojeću lozinku. Za izričiti reset samo demo naloga:

```bash
.venv/bin/python -m app.seed --reset-password
```

U drugom terminalu, iz korena repozitorijuma:

```bash
cd frontend
npm ci
npm run dev
```

Vite prosleđuje `/api` lokalnom backend-u na portu 8000. U Codespaces kartici **Ports** otvorite port 5173 u browseru i zadržite **Private** vidljivost. Portove 8000 i 5432 ne objavljujte.

Za Codespaces u korenskom `.env` podesite `CRM_ALLOWED_ORIGINS` na tačnu HTTPS adresu pregleda sa kartice Ports (bez završne kose crte), i `CRM_COOKIE_SECURE=true`, pa ponovo pokrenite backend. Za lokalni privatni HTTP test generator postavlja `false`. Ne koristite ovo podešavanje na javnom HTTP serveru. Koristimo isti origin i Vite proxy; nema potrebe za širokim CORS pravilima.

Na Windows-u koristite `npm.cmd` i `backend\.venv\Scripts\python.exe` umesto aktivacije PowerShell skripti. Cloud razvoj ne zahteva lokalnu Windows instalaciju.

## Provere
Iz `backend`:

```bash
.venv/bin/python -m app.test_runner
.venv/bin/python -m alembic check
```

Test runner kreira i migrira **izdvojenu** bazu `crm_test`; testovi koriste transakcije i ne menjaju razvojnu bazu. Za prilagođenu infrastrukturu postavite `CRM_TEST_DATABASE_URL` koji završava sa `_test`. Nalog mora imati dozvolu za kreiranje test baze ili ona mora već postojati. Ne pokretati razvojne skripte nad produkcijom.

Iz `frontend`:

```bash
npm test
npm run build
```

Health: `/api/health`. Readiness proverava bazu i nove tabele iz migracije: `/api/ready`.

## Podaci i konfiguracija
`.env`, lozinke, sesije, `node_modules`, virtuelno okruženje i build izlazi nisu u Git-u. `.env.example` opisuje imena promenljivih. Docker named volume `crm_data` čuva bazu pri restartu u istom okruženju. `docker compose down -v` briše podatke — ne koristite ga za redovan restart. Obnova baze u novom cloud okruženju zahteva sačuvan volume ili backup; GitHub ne čuva bazu.

Pre stvarne poslovne upotrebe ostaju produkcioni deployment, HTTPS, backup/restore provera, audit, upravljanje nalozima, dodatna zaštita prijave i testovi svih korisničkih tokova. GitHub čuva kod, ne hostuje ovu aplikaciju automatski.

[Arhitektura i plan MVP-a](docs/architecture/plan.md) · [Proverena verzija 0.4](docs/architecture/validation-0.4.md)

## Prijava emailom i lozinkom

Prava prijava zahteva server i PostgreSQL; HTML demo ne autentifikuje korisnike. Email je jedinstven, lozinka se čuva kao PBKDF2 hash, a sesija koristi HttpOnly cookie. Prijava proverava i članstvo u izabranoj firmi. Postojeći nalozi i lozinke ostaju sačuvani; stari API unos `username` ostaje podržan radi kompatibilnosti. Postojećim korisnicima nije izmišljena email adresa.

Posle `alembic upgrade head`, administrator kreira nalog iz direktorijuma `backend`:

```bash
.venv/bin/python -m app.create_user --email osoba@example.com --name 'Ime Prezime' --unit LUU --role manager
```

Unesite i potvrdite lozinku u skrivenom terminalskom unosu. Za pristup dodatnoj firmi eksplicitno ponovite argument `--unit`. Postojeći email se odbija bez menjanja naloga. Za automatizaciju koristite sigurnu procesnu promenljivu `CRM_ACCOUNT_PASSWORD`, nikad argument komandne linije ili lozinku u repozitorijumu. Kreiranje naloga ne šalje email i ne dodaje izmišljene klijente.
