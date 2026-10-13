# LUU × INVEKTA — AI Sales CRM

Zajednička CRM platforma za LUU i Invektu. **Razvojna verzija 0.2**, samo za testne podatke. Produkcioni hosting još nije postavljen.

## Izgled interfejsa

Interfejs prati dostavljeni HTML prototip: tamnoplava navigacija, plava dugmad, svetla pozadina, plavo-tirkizni baner i kartice. Demo i povezani CRM dele isti raspored. Globalna pretraga i izbor jedinice su u zaglavlju. „Sve demo kompanije“ objedinjeno prikazuje isključivo izmišljene demo zapise; povezani CRM nudi samo jedinice iz korisnikovih ovlašćenja. Stavke koje još nisu povezane jasno prikazuju da su u pripremi.

## Šta sada radi
- Srpski responzivan demo pregled, odvojeni LUU/Invekta primeri, levak i privremeni zadaci.
- Dugme **Otvori povezani CRM** vodi na prijavu i kompanije iz PostgreSQL baze.
- Unos, izmena i pretraga kompanija; podaci ostaju posle osvežavanja i odjave.
- Serverske sesije, hash lozinki, odjava i ograničenje pokušaja prijave.
- Backend proverava članstvo u jedinici. Komercijalista vidi i menja svoje kompanije; menadžer i administrator imaju pregled kompanija u svojim jedinicama.
- Demo seed je eksplicitan i idempotentan; postojeće podatke i lozinke ne menja bez zahteva za reset.

Kontakti, zasebne prodajne prilike, dodeljivanje kompanija, trajni zadaci, upravljanje korisnicima kroz UI, audit evidencija i AI još nisu implementirani. Trenutna vrednost i faza na kompaniji su privremena osnova za budući model prodajnih prilika.

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

Seed traži lozinku demo naloga, bez prikaza unosa. Izaberite najmanje 12 znakova. Korisničko ime je **demo**; ovaj razvojni menadžer ima pristup obema jedinicama. Za neinteraktivno pokretanje postavite `CRM_DEMO_PASSWORD` u proces kroz siguran kanal. Ponovni seed ne menja postojeću lozinku. Za izričiti reset samo demo naloga:

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

Health: `/api/health`. Readiness proverava bazu i tabelu iz migracije: `/api/ready`.

## Podaci i konfiguracija
`.env`, lozinke, sesije, `node_modules`, virtuelno okruženje i build izlazi nisu u Git-u. `.env.example` opisuje imena promenljivih. Docker named volume `crm_data` čuva bazu pri restartu u istom okruženju. `docker compose down -v` briše podatke — ne koristite ga za redovan restart. Obnova baze u novom cloud okruženju zahteva sačuvan volume ili backup; GitHub ne čuva bazu.

Pre stvarne poslovne upotrebe ostaju produkcioni deployment, HTTPS, backup/restore provera, audit, upravljanje nalozima, dodatna zaštita prijave i testovi svih korisničkih tokova. GitHub čuva kod, ne hostuje ovu aplikaciju automatski.

[Arhitektura i plan MVP-a](docs/architecture/plan.md) · [Proverena verzija 0.2](docs/architecture/validation-0.2.md)
