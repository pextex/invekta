# CRM u GitHub Codespaces-u

Otvorite granu sa izmenama (`codex/task-calendar`) na GitHub-u → **Code → Codespaces → Create codespace**. Konfiguracija `.devcontainer` priprema Python 3.12, Node 22, Docker/Compose i uv. U postojećem Codespace-u koji nema ove alate upotrebite **Codespaces: Rebuild Container**. Nemojte brisati Codespace u kome čuvate jedinu kopiju razvojne baze.

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

Komanda nikada ne pokreće migracije, seed, reset ili kreiranje korisnika. Ako revizija nedostaje/zaostaje, ispisuje trenutnu reviziju i spisak potrebnih migracija, pa staje **pre pokretanja CRM servera**. Nije dodata nova migracija za Codespaces. Trenutni head je `a797e60f8c86` (kolektivni cilj); prethodni `f686d59e7b75` dodaje mesečne targete i vrste posla. Stvarni spisak zavisi od stanja vaše baze.

Za postojeću bazu prvo pregledajte navedene fajlove u `backend/alembic/versions`, napravite backup i odobrite migraciju. Tek zatim ručno, isključivo nad lokalnim PostgreSQL-om:

```bash
cd backend
uv run --frozen python -m alembic upgrade head
cd ..
python scripts/dev.py
```

Navedeni upgrade nije deo automatskog pokretanja. Ista eksplicitna inicijalizacija potrebna je pri prvom otvaranju potpuno prazne lokalne baze. Ne koristite reset, downgrade ili seed. Za prvi pravi nalog u novoj lokalnoj bazi, nakon odobrenih migracija:

```bash
cd backend
uv run --frozen python -m app.create_user --email vas-email@example.com --name 'Ime Prezime' --unit LUU --unit INVEKTA --unit CENOBOTS --role admin
cd ..
```

Zamenite email i ime; lozinka se unosi skriveno u terminalu. Ovo se ne izvršava automatski i ne dodaje izmišljene klijente. Za platform administratora postoji odvojeni postupak iz README-a.

## Podaci i provera veze

Git čuva kod, **ne bazu**. Postojeći PostgreSQL volume u istom Codespace-u ostaje sačuvan; novi Codespace ne preuzima korisnike/podatke iz Manusa ili drugog Codespace-a. Za prenos postojećih podataka potreban je zaseban dogovoren backup/restore. Ne podešavajte Manus DATABASE_URL u razvoju; ova komanda odbija sve osim lokalnog PostgreSQL-a na portu 5432. Ne prikazuje URL, lozinke ni sesije. AI pozivi su isključeni u ovim razvojnim procesima.

Na istom Live Preview linku otvorite **`/api/ready`**: očekivano je `{"status":"ready"}`. Posle prijave sačuvajte kompaniju ili zadatak, osvežite stranicu i proverite zapis. U browser Network panelu zahtevi `/api/...` moraju ići na isti port 5173; nisu demo podaci. Zatvaranje i ponovno pokretanje komande čuva te zapise i neistekle sesije.

Ne koristite `docker compose down -v` i ne brišite Codespace/volume bez backupa. Portove 8000 i 5432 ne prosleđujte. Ako je 5173 ili 8000 zauzet, zaustavite prethodni razvojni proces; skripta neće gasiti tuđe procese niti birati drugi port. Promene zavisnosti učitavaju se ponovnim pokretanjem iste komande. Manus Dockerfile, managed baza i javni sajt nisu deo ovog postupka.
