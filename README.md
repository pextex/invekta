# LUU × INVEKTA — AI Sales CRM

Zajednička CRM platforma za LUU i Invektu. **Faza 1: početni frontend sa isključivo demonstracionim podacima.** Nije spremna za stvarne klijente.

## Pokretanje u razvojnom cloud okruženju
Iz korena repozitorijuma:

```bash
cd frontend
npm ci
npm run dev
```

Vite koristi port 5173. U Codespaces-u otvorite karticu **Ports**, pronađite port 5173 i izaberite **Open in Browser**. Zadržite privatnu vidljivost porta. Nije potrebna instalacija na Windows računaru. Ovo je razvojni pregled, ne produkcioni hosting.

## Provera
Iz foldera `frontend`:

```bash
npm test
npm run build
```

Node.js 22 ili 24 LTS. `npm ci` koristi verzije iz zaključanog `package-lock.json`. Na Windows-u koristite `npm.cmd` umesto `npm` ako PowerShell blokira skripte.

## Trenutne mogućnosti
Srpski responzivan interfejs, izbor LUU/Invekta modula, dashboard iz demo zapisa, pretraga kompanija, statički prodajni levak i označavanje demo zadataka tokom sesije.

Nema prijave, backend-a, trajnog čuvanja ili AI integracije. Izbor poslovnog modula nije autorizacija. Ne unositi stvarne poslovne podatke. Katalog, AI i podešavanja jasno prikazuju šta je planirano.

Arhitektura, relacije baze i redosled MVP-a: [plan](docs/architecture/plan.md).
