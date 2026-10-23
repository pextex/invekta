# Pokretanje stvarnog rada na Manusu

## Stanje pripreme, 23.10.2026.

Kod je pripremljen na grani `codex/task-calendar`. Git push nije objava sajta. Ciljna Manus baza nije dostupna iz ovog radnog okruženja; lokalna konfiguracija pokazuje na razvojni PostgreSQL `127.0.0.1/crm`. Ta baza nije zamena za Manus managed bazu i nije očišćena.

Nalog koji vlasnik želi da sačuva: **petar.milosevic@invekta.rs**. Brisanje stvarnih podataka i potvrda njegove prijave tek treba da se izvrše u okruženju aktuelnog Manus CRM projekta. Za taj jednokratni reset postoji izričit zahtev vlasnika; ne dodavati automatsko brisanje pri pokretanju.

## Poruka za Manus

Preuzmi najnoviji commit sa grane `codex/task-calendar` repozitorijuma `pextex/invekta` i pokreni tu verziju u postojećem Manus CRM projektu za stvarno korišćenje. Koristi postojeći hosting i njegovu managed bazu. Sačuvaj postojeću infrastrukturu i tajne; ne kreiraj drugi CRM ili zamensku bazu.

Vlasnik je odobrio jednokratno čišćenje: obriši sve kompanije i povezane poslovne podatke, porudžbine, fajlove i sve naloge osim **petar.milosevic@invekta.rs**. Sačuvaj njegovu lozinku, telefon, aktivan administratorski pristup svim trima brendovima, brendove i odobreno znanje brendova.

Uradi sledeće bez redizajna i dodatnih funkcionalnosti:

1. Identifikuj bazu koju koristi aktuelni Manus CRM. Napravi privatnu rezervnu kopiju i proveri postupak vraćanja. Sačuvaj prethodni checkpoint aplikacije. Zaustavi sve procese koji upisuju podatke dok traju migracija i čišćenje. Ako nema pristupa bazi, mogućnosti pravljenja kopije ili nije jasno koja je baza aktuelnog projekta, stani i prijavi konkretno šta nedostaje.
2. Primeni pregledane migracije novog koda komandom `python -m app.run_migrations` iz `backend`. Očekivani head ovog izdanja je `cd49f8a123b5` (ili njegov novi potomak iz preuzete grane). Ne pokreći razvojni seed, downgrade ili testove nad pravom bazom.
3. U tom istom serverskom okruženju pokreni pregled bez brisanja:

   ```sh
   python -m app.reset_workspace --admin-email petar.milosevic@invekta.rs
   ```

   Proveri da host i ime baze odgovaraju aktuelnom Manus projektu i da administrator postoji, aktiviran je i ima sva tri administratorska pristupa. Ako komanda odbije administratora, ne kreiraj zamenski nalog, ne menjaj lozinku i ne zaobilazi proveru; prijavi problem.
4. Na osnovu potvrđenog hosta i imena baze iz pregleda izvrši odobreni reset, zamenjujući oznake stvarnim vrednostima:

   ```sh
   python -m app.reset_workspace --admin-email petar.milosevic@invekta.rs --database-host ACTUAL_HOST --database-name ACTUAL_DATABASE --apply
   ```

   Ne stavljaj lozinke, ključeve ili rezervnu kopiju u chat, Git ili javni folder. Proveri rezultat: jedan preostali korisnik, nula kompanija, porudžbina, poslovnih fajlova i ostalih podataka koje reset briše. Svi uređaji biće odjavljeni.
5. Izgradi frontend sa `npm run build:hosting` i objavi zajedno sa novim backendom kroz Manus checkpoint/deployment. Koristi stvarni HTTPS domen, `CRM_COOKIE_SECURE=true` i tačan HTTPS origin u `CRM_ALLOWED_ORIGINS`. Sačuvaj serverski Gemini ključ. Nemoj koristiti `build:demo` ili vraćati demo podatke.
6. Proveri `/api/health` i `/api/ready`, pristup preko HTTPS-a i prijavu sa sačuvanim administratorskim nalogom kroz privatni pristup. Ako nemaš njegovu lozinku, ne menjaj je; jasno navedi da vlasnik mora da proveri prijavu. Proveri sva tri brenda i prazan CRM. Potvrdi da objavljena verzija odgovara preuzetom commitu i da stari `#demo` URL ne zaobilazi prijavu.
7. Proveri postojeću konfiguraciju automatskih rezervnih kopija: učestalost, zadržavanje i način obnove. Ako nije podešena, podesi je u okviru postojećeg hosting paketa ili prijavi tačno ograničenje. Ne uvodi plaćene usluge bez odobrenja.

Sačuvaj: vodič i 26 Kore naracija za ostale uloge; marketing nema vodič. Marketing koristi porudžbine sa imenom, prezimenom, telefonom, emailom, izvorom i iznosom u RSD. Realizovane porudžbine ulaze u lični i kolektivni target prema mesecu realizacije; Cenobots ima prodaju/lizing/najam. Lični target je prvi. Profil i AI potpis ostaju; znanje brenda i „Hronologija promena - log” dostupni su samo menadžerima i administratorima.

Na kraju vrati HTTPS link, commit/checkpoint, rezultat migracija i čišćenja, status rezervnih kopija i rezultate provera. Ne navodi da je nešto testirano ako nije. Ako stvarni AI poziv nije izvršen, navedi to; lokalni šablon nije dokaz rada Gemini servisa.

## Pre prvog radnog dana

- Vlasnik proverava administratorsku prijavu i otvara stvarne naloge kroz „Korisnici i pristup”, sa odgovarajućim brendom i ulogom. Nalozi za komercijaliste imaju ulogu Komercijalista; Marketing samo za obradu porudžbina. Svako dobija sopstvenu početnu lozinku privatnim putem i menja je kroz „Moj profil”. Administrator rešava zaboravljene lozinke; automatski email za oporavak nije implementiran.
- Uneti lične targete, kolektivni cilj i bonus za tekući mesec: reset ih namerno briše. Dopuniti telefone korisnika i proveriti sajt/adresu svakog brenda radi AI potpisa.
- Proveriti pristup komercijaliste samo njegovim kompanijama i zadacima, menadžera podacima njegovog brenda i zabranu pristupa znanju/logu za komercijalistu i marketing. Funkcionalne testove sa izmišljenim podacima raditi na izdvojenoj bazi, ne ostavljati probne naloge u praznoj produkciji.
- Proveriti jedan stvarni Gemini zahtev i raspoloživu kvotu na objavljenom serveru. AI priprema nacrt, ne šalje email. Za svaku ponudu korisnik proverava cenu, tvrdnje i primaoca, pa šalje kroz svoj email klijent. Pre slanja stvarnih podataka povezanom AI servisu dogovoriti koje podatke firma dozvoljava da se koriste.
- Potvrditi ko održava aplikaciju, prati greške, proverava backup i vraća pristup kada administrator nije dostupan. Povratak koda posle migracije mora biti kompatibilan sa novom šemom; ne vraćati obrisane probne podatke preko novog poslovnog rada.

## Provereno u radnom okruženju

Izmena `/api/ready` proverava i `amount`, `business_type`, `realized_at`; baza bez poslednje migracije vraća 503. Test resetovanja uključuje realizovanu porudžbinu sa iznosom, čuva administratora i konfiguraciju, briše poslovne zapise i proverava vraćanje transakcije pri grešci. To nije tvrdnja da je prava Manus baza očišćena ili da je sajt objavljen.
