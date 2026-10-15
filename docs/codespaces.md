# CRM u GitHub Codespaces-u

Otvorite granu sa izmenama (`codex/task-calendar`) na GitHub-u → **Code → Codespaces → Create codespace**. Konfiguracija `.devcontainer` priprema Python 3.12, Node 22, Docker/Compose i uv. Ako uv nedostaje ili nije u PATH-u, razvojna komanda ga sama instalira u privatni `.dev-tools` folder; ne instalira pakete u sistemski Python. U postojećem Codespace-u koji nema Node ili Docker upotrebite **Codespaces: Rebuild Container**. Nemojte brisati Codespace u kome čuvate jedinu kopiju razvojne baze.

## Jedna komanda

Iz korena repozitorijuma:

```bash
python scripts/dev.py
```

Komanda čuva postojeći `.env` (kreira privatni lokalni fajl samo ako ne postoji), instalira zaključane backend pakete kroz `uv sync --frozen`, pokreće postojeći PostgreSQL Compose servis i **samo čita** Alembic reviziju baze. Ako šema odgovara kodu, instalira frontend kroz `npm ci`, pokreće FastAPI na `127.0.0.1:8000` sa `--reload` i Vite na `0.0.0.0:5173` sa HMR-om. Pre poruke da je spremna proverava `/api/ready` i direktno i preko Vite proxy-ja. Terminal ostavite otvoren.

U donjem panelu VS Code-a otvorite **Ports**, pronađite **5173 / CRM — Live Preview**, pa kliknite globus **Open in Browser**. Zadržite **Private** vidljivost. Link se ispisuje i u terminalu: `https://<codespace-name>-5173.app.github.dev` (domen može zavisiti od GitHub okruženja). Ako nema Ports kartice, pokrenite **Ports: Focus on Ports View** iz Command Palette-a. Ako port nije dodat, koristite **Forward a Port → 5173**.

Otvara se prava aplikacija. Izaberite firmu i prijavite se postojećim emailom i lozinkom iz **lokalne razvojne baze**. Nemojte birati HTML demo. Frontend koristi relativne `/api` adrese koje Vite prosleđuje FastAPI-ju; PostgreSQL i API se ne objavljuju. Codespaces HTTPS origin, Secure/HttpOnly/SameSite=None cookie i WSS za HMR podešavaju se samo u razvojnim procesima, bez menjanja `.env` ili produkcije. Na lokalnom računaru adresa je `http://localhost:5173`.

Sačuvajte izmenu u `frontend/src` i prikaz će se odmah ažurirati; izmene u `backend/app` automatski ponovo učitavaju API. Nije potreban build. **Ctrl+C** zaustavlja oba razvojna servera, ali ostavlja PostgreSQL i named volume. Ponovno pokretanje koristi istu bazu, naloge i neistekle sesije na istoj adresi. Redovna osmočasovna važnost sesije ostaje nepromenjena.

## Ako komanda prijavi migracije

Komanda nikada ne pokreće migracije, seed, reset ili kreiranje korisnika. Ako revizija nedostaje/zaostaje, ispisuje trenutnu reviziju i spisak potrebnih migracija, pa staje **pre pokretanja CRM servera**. Nije dodata nova migracija za Codespaces. Trenutni head je `b8a6c2d1e409` (prodajni fajlovi); prethodni `a797e60f8c86` dodaje kolektivni cilj, a `f686d59e7b75` mesečne targete i vrste posla. Stvarni spisak zavisi od stanja vaše baze.

Za postojeću bazu prvo pregledajte navedene fajlove u `backend/alembic/versions`, napravite backup i odobrite migraciju. Tek zatim ručno, isključivo nad lokalnim PostgreSQL-om:

```bash
cd backend
.venv/bin/python -m alembic upgrade head
cd ..
python scripts/dev.py
```

Navedeni upgrade nije deo automatskog pokretanja. Za **novu praznu bazu bez Alembic revizije**, iz korena repozitorijuma pokrenite odvojenu jednokratnu inicijalizaciju:

```bash
backend/.venv/bin/python scripts/init_dev_database.py
```

Pre toga bar jednom pokrenite `python scripts/dev.py` da pripremi pakete i PostgreSQL. Inicijalizacija prihvata samo lokalni PostgreSQL i pre migracija proverava da nijedna korisnička šema nema tabele, poglede, materijalizovane poglede ili sekvence. Ako postoji bilo koji takav objekat, komanda staje bez migracije, čak i kada Alembic revizija nedostaje. Za potvrđenu praznu bazu pravi CRM šemu i registruje tri poslovne jedinice kroz postojeće migracije; ne pokreće seed i ne dodaje naloge, klijente ili demo podatke. Ponovljeno pokretanje odbija već inicijalizovanu bazu. Ovo je izričita komanda koju vi pokrećete, a ne automatski korak redovnog startovanja.

Ne koristite reset, downgrade ili seed. Za prvi pravi nalog u novoj lokalnoj bazi, nakon inicijalizacije:

```bash
cd backend
.venv/bin/python -m app.create_user --email vas-email@example.com --name 'Ime Prezime' --unit LUU --unit INVEKTA --unit CENOBOTS --role admin
cd ..
```

Zamenite email i ime; lozinka se unosi skriveno u terminalu. Ovo se ne izvršava automatski i ne dodaje izmišljene klijente. Za platform administratora postoji odvojeni postupak iz README-a.

## Podaci i provera veze

Git čuva kod, **ne bazu**. Postojeći PostgreSQL volume u istom Codespace-u ostaje sačuvan; novi Codespace ne preuzima korisnike/podatke iz Manusa ili drugog Codespace-a. Za prenos postojećih podataka potreban je zaseban dogovoren backup/restore. Ne podešavajte Manus DATABASE_URL u razvoju; ova komanda odbija sve osim lokalnog PostgreSQL-a na portu 5432. Ne prikazuje URL, lozinke ni sesije. AI pozivi su isključeni u ovim razvojnim procesima.

Na istom Live Preview linku otvorite **`/api/ready`**: očekivano je `{"status":"ready"}`. Posle prijave sačuvajte kompaniju ili zadatak, osvežite stranicu i proverite zapis. U browser Network panelu zahtevi `/api/...` moraju ići na isti port 5173; nisu demo podaci. Zatvaranje i ponovno pokretanje komande čuva te zapise i neistekle sesije.

Ne koristite `docker compose down -v` i ne brišite Codespace/volume bez backupa. Portove 8000 i 5432 ne prosleđujte. Ako je 5173 ili 8000 zauzet, zaustavite prethodni razvojni proces; skripta neće gasiti tuđe procese niti birati drugi port. Promene zavisnosti učitavaju se ponovnim pokretanjem iste komande. Manus Dockerfile, managed baza i javni sajt nisu deo ovog postupka.

## Recovery režim / nedostaje uv

Creation log od 15.10.2026. pokazao je konkretan uzrok: nasleđeni Yarn APT repozitorijum vraća `NO_PUBKEY 62D54FD4003F6525`, pa instalacija Docker feature-a pada pre pripreme uv. Razvojni `.devcontainer/Dockerfile` uklanja samo taj nepotrebni Yarn source **pre** instaliranja Features; Node koristi npm/Corepack, bez Yarn APT-a. Provera potpisa ostalih paketa ostaje uključena. Korenski produkcioni Dockerfile nije izmenjen.

U postojećem terminalu preuzmite samo normalne, usklađene izmene:

```bash
git pull --ff-only origin codex/task-calendar
python scripts/dev.py
```

Ako Git prijavi lokalne izmene ili razilaženje grana, stanite i sačuvajte ih; ne koristite reset ili force. Komanda proverava Node, Docker daemon i Compose pre menjanja lokalne konfiguracije ili pokretanja baze. Kada su dostupni, nedostajući uv priprema automatski i ne zahteva uspešan `postCreateCommand`.

Ako Codespaces i dalje prijavljuje **recovery mode**, otvorite **Cmd/Ctrl+Shift+P → Codespaces: View Creation Log**. Potrebna je konkretna `ERROR`/`failed` poruka, ne početno obaveštenje o recovery režimu. Proverite poslednje redove i lokalno u terminalu:

```bash
tail -n 80 /workspaces/.codespaces/.persistedshare/creation.log
```

Ako taj fajl nije dostupan, koristite View Creation Log. Ne delite lozinke, tokene ili DATABASE_URL iz loga. Nakon preuzimanja ispravke upotrebite **Codespaces: Rebuild Container**. Sama instalacija uv ne popravlja Docker ili neuspešno kreiranje razvojnog kontejnera; bez creation log-a uzrok takvog pada nije potvrđen. Nijedan od ovih koraka ne radi seed, reset ili automatsku migraciju CRM baze.
