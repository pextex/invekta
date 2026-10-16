# LUU × INVEKTA × CENOBOTS — AI Sales CRM

Zajednička CRM platforma za LUU, Invektu i Cenobots. Ciljani trajni Manus deployment koristi managed MySQL; CRM podaci su dostupni samo posle prijave. Javno objavljivanje je pod kontrolom vlasnika; automatsko objavljivanje nije uključeno.

## Izgled interfejsa

Odeljak „Specijalizovani moduli“ i posebne stavke za proizvode/usluge uklonjeni su iz menija. Izbor poslovne jedinice LUU/Invekta/Cenobots ostaje u zaglavlju.

Interfejs prati dostavljeni HTML prototip: tamnoplava navigacija, plava dugmad, svetla pozadina, plavo-tirkizni baner i kartice. Demo i povezani CRM dele isti raspored. Globalna pretraga je u zaglavlju. CRM je vezan za izabranu firmu; nema menija za prebacivanje. Za promenu firme odjavite se, izaberite drugu i ponovo se prijavite. Stavke koje još nisu povezane jasno prikazuju da su u pripremi.

## Vizuelna dubina i vraćanje prethodnog izgleda

Dodat je suptilan efekat dubine na kartice, banere, dugmad, polja i grafikone: višeslojne senke, osvetljene ivice i blagi pritisak/podizanje dugmeta. Postojeće LUU žuto-sive, Invekta plavo-narandžaste i Cenobots crno-bele boje, logotipi, raspored i funkcije ostaju isti. Podizanje pri hover-u važi samo za uređaje sa mišem; `prefers-reduced-motion` isključuje pokrete i prelaze.

Prethodni izgled je sačuvan Git oznakom **`ui-before-3d-2026-10-15`**, na commitu **`4e56b80`**. Za poređenje preuzmite [prethodni HTML pregled](https://github.com/pextex/invekta/blob/ui-before-3d-2026-10-15/demo/LUU_Invekta_CRM_Demo.html). Izgled se primenjuje kroz odvojeni `frontend/src/depth.css`, jednim importom u `frontend/src/main.tsx`.

Za vraćanje prethodnog izgleda uz očuvanje svih naknadnih funkcionalnih izmena, uklonite samo `import "./depth.css";`, ponovite frontend build i izvoz demo HTML-a, pa sačuvajte normalan commit. Alternativno, dok je vizuelni commit poslednji, može se koristiti običan `git revert` tog commita. Ne vraćati ceo projekat reset-om i ne menjati bazu. Ovo ne zahteva migraciju, promenu prava pristupa ili novo produkciono okruženje. Manus objava je zaseban korak.

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

Automatsko kreiranje ponuda i obračun stavki, aktivnosti, raspodela kompanija i potpuna audit evidencija još nisu implementirani. Upravljanje nalozima i priprema AI nacrta su dodati; AI zahteva povezivanje servisa. Istorija prodajnih prilika beleži kreiranje, promene statusa i izmene podataka; potpuna audit evidencija ostalih modula još nije implementirana. Dobijeni poslovi predstavljaju vrednost prilika označenih kao dobijene, ne fakturisan prihod.

## Kako koristiti povezani CRM
1. Na početnom ekranu izaberite **LUU**, **Invekta** ili **Cenobots**, pa unesite email i lozinku. Server proverava pristup izabranoj jedinici pre kreiranja nove sesije.
2. U **Kompanije** dodajte kompaniju ili kliknite **Otvori profil →**.
3. U profilu, kroz **Kontakt osobe**, unesite kontakt i sačuvajte ga.
4. Otvorite karticu **Prodajne prilike** i kreirajte jednu ili više prilika.
5. U meniju **Prodajni levak** prevucite karticu u drugu kolonu ili promenite fazu izborom na kartici. Na telefonu koristite izbor faze. Dugme **Istorija** prikazuje promene. Ako se pojavi konflikt, osvežite levak pre nove izmene.
6. **Početna tabla** prikazuje aktuelne pokazatelje iz baze. Refresh zadržava otvorenu stranicu, profil i poslovnu jedinicu.

## Interaktivni demo levak
Preuzeti demo HTML sada podržava sedam statusa, prevlačenje i izbor statusa na kartici. Statusi su sačuvani lokalno kada browser dozvoljava localStorage, uz pamćenje otvorene demo stranice. Otvarajte isti fajl u istom browseru da biste videli prethodne izmene. Demo ne šalje ove promene backend-u. Kada lokalno čuvanje nije dostupno, prikazuje se poruka da promena važi samo tokom tog prikaza.

Pokazatelji demo dashboard-a odmah prate promene: Dobijeno i Izgubljeno ne ulaze u otvorene prilike i njihovu potencijalnu vrednost. Zadaci iz demo kalendara čuvaju se lokalno u browseru, odvojeno od CRM baze.

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

U Codespaces-u otvorite postojeći projekat sa `.devcontainer` konfiguracijom, pa iz korena pokrenite:

```bash
python scripts/dev.py
```

Otvorite **Ports → 5173 → Open in Browser**, uz **Private** vidljivost. Komanda pokreće PostgreSQL, FastAPI sa reload-om i Vite sa HMR-om/proxy-jem. Čuva postojeći `.env`, korisnike, sesije i podatke u lokalnom volume-u. Ako šema baze zaostaje, prijavljuje potrebne migracije i staje; **ne izvršava migracije, seed ili reset**. Novi Codespace ne preuzima Manus bazu preko Git-a.

[Uputstvo za Codespaces, recovery režim, prvu praznu bazu i postojeće migracije](docs/codespaces.md). Lokalno su potrebni Node 22/24, Python 3.12+ i Docker Compose; uv se po potrebi instalira u privatni `.dev-tools` folder. Ista komanda otvara CRM na `http://localhost:5173`. Produkcioni Manus deployment ostaje odvojen.

Za opciono pokretanje istog koda na jednom Vercel projektu sa dva servisa dodat je root `vercel.json`: `/api/...` ide FastAPI backend-u, ostalo statičkom Vite frontend-u. [Vercel podešavanje, baza, lokalni `vercel dev -L` i ograničenje većih fajlova](docs/vercel.md). Manus Docker/startup nije izmenjen; ova konfiguracija sama ne objavljuje sajt niti migrira podatke.

Za nastavak sa **novom praznom PostgreSQL bazom**, bez prenosa sa Manus-a, pogledati [jednokratne migracije i početni administratorski nalog](docs/vercel.md#nova-prazna-baza-umesto-manus-podataka). Standardni Neon/provider URI koristi postojeći psycopg drajver automatski. Kreiranje online baze zahteva povezan nalog kod njenog pružaoca; aplikacija je ne kreira pri build-u ili prvom HTTP zahtevu.

Neon projekat `invekta-crm` je kreiran sa zasebnim production/preview bazama i postojećom CRM šemom. [Podaci o projektu i skriveni unos za aktivaciju prvog administratora](docs/vercel.md#kreiran-neon-projekat); netajni identifikatori su u `deployment/neon.json`. Objavljivanje i povezivanje Vercel projekta su zaseban korak.

## Provere

Provera bezbednosnih pravila razvojne komande (iz korena, bez pristupa bazi):

```bash
backend/.venv/bin/python scripts/test_dev.py
```

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
`.env`, lozinke, sesije, `node_modules`, virtuelno okruženje i build izlazi nisu u Git-u. `.env.example` opisuje imena promenljivih. Docker named volume `crm_data` čuva lokalnu razvojnu bazu pri restartu u istom okruženju. `docker compose down -v` briše podatke — ne koristite ga za redovan restart. Obnova baze u novom cloud okruženju zahteva sačuvan volume ili backup. Canonical kod za ovaj Manus sajt čuva se kroz Manus-managed checkpoint-e; poslovni CRM podaci se čuvaju samo u bazi.

Pre šire poslovne upotrebe i dalje su potrebni dogovoreni backup/restore postupak, poslovni audit i periodična provera korisničkih tokova. Produkcioni hosting koristi trajni Manus/MySQL servis; automatsko objavljivanje novih checkpoint-a nije uključeno, a vlasnik upravlja objavama.

[Arhitektura i plan MVP-a](docs/architecture/plan.md) · [Proverena verzija 0.4](docs/architecture/validation-0.4.md)

## Prijava emailom i lozinkom

Prava prijava zahteva server i bazu: Manus deployment koristi managed MySQL, a lokalni razvoj PostgreSQL. HTML demo ne autentifikuje korisnike. Email je jedinstven, lozinka se čuva kao PBKDF2 hash, a sesija koristi HttpOnly cookie. Prijava proverava i članstvo u izabranoj firmi. Postojećim korisnicima nije izmišljena email adresa.

Posle `alembic upgrade head`, administrator kreira nalog iz direktorijuma `backend`:

```bash
.venv/bin/python -m app.create_user --email osoba@example.com --name 'Ime Prezime' --unit LUU --role manager
```

Unesite i potvrdite lozinku u skrivenom terminalskom unosu. Za pristup dodatnoj firmi eksplicitno ponovite argument `--unit`. Postojeći email se odbija bez menjanja naloga. Za automatizaciju koristite sigurnu procesnu promenljivu `CRM_ACCOUNT_PASSWORD`, nikad argument komandne linije ili lozinku u repozitorijumu. Kreiranje naloga ne šalje email i ne dodaje izmišljene klijente.

## Administrator platforme i korisnici

Administrator platforme vidi **Korisnici i pristup** u bočnom meniju svakog CRM-a. Može kreirati naloge sa emailom, početnom lozinkom i izabranim firmama/ulogama, izmeniti prava, deaktivirati nalog ili zadati novu lozinku. Izmena profila opoziva postojeće sesije; korisnik se ponovo prijavljuje. Isključeno članstvo blokira prijavu i sve CRM API pozive, uz očuvanje klijenata koje je korisnik ranije vodio. Zastarela izmena profila vraća konflikt. Glavni administrator je zaštićen od deaktivacije kroz ovaj ekran.

Uloga **Administrator firme** ne daje upravljanje nalozima cele platforme. Globalno pravo se dodeljuje samo eksplicitnom administratorskom komandom. Nema samostalne registracije, slanja pozivnica ili automatskog slanja emaila.

Posle migracija, bootstrap komanda može da pripremi **samo prvog** administratora platforme, i to dok još ne postoji nijedan platform admin. Profil se pravi neaktivan, sa administratorskim članstvom u sve tri poslovne jedinice i trajnim markerom `bootstrap_pending`.

```bash
.venv/bin/python -m app.bootstrap_admin --email osoba@example.com --name 'Ime Prezime'
```

Ponovno pokretanje pripreme za isti pending nalog je no-op. Drugi administratorski nalog se odbija. Aktivacija kroz skriven unos:

```bash
.venv/bin/python -m app.bootstrap_admin --email osoba@example.com --name 'Ime Prezime' --activate
```

Aktivacija prihvata samo postojeći, neaktivan nalog sa `bootstrap_pending=true`; posle uspeha trajno troši marker. Ponovljeni poziv `--activate` ne može resetovati lozinku, aktivirati drugi nalog ili kreirati novog administratora. Za automatizaciju unesite `CRM_ACCOUNT_PASSWORD` kroz zaštićeni unos okruženja i koristite ga samo za ovu komandu; ne postavljajte lozinku kao argument, u chat ili u Git. Komanda je eksplicitna i ne izvršava se tokom pokretanja servera. Manus deployment zadržava managed MySQL bazu; odvojeni Vercel deployment može koristiti novu PostgreSQL bazu. Lozinku drugih korisnika kasnije menjajte kroz ovlašćeni interfejs, ne bootstrap komandom.

## Invekta AI — prodajni mejlovi uz GroqCloud

U odeljku **Invekta AI** postoje samo dva polja za pripremu: **Šta želite da napišete?** i pretraga **Kompanija kojoj šaljete mejl**. Nema izbora tona, jezika, cilja, kontakta, prilike niti dodatnog potpisa. Napišite sve što želite u zahtevu (npr. „odgovori na engleskom“ ili nalepite upit klijenta); Groq određuje stil i vrstu poruke iz zahteva, a podrazumevano piše profesionalno na srpskoj latinici. Ime prijavljenog komercijaliste i brend koriste se u potpisu.

Posle izbora kompanije automatski se prikažu njeni kontakti sa ispravnim emailom, redom unosa. Sve različite adrese popunjavaju **Primaoci** uz generisani mejl; iste adrese sa razlikom u veličini slova se ne ponavljaju, a prazni/neispravni istorijski emailovi se preskaču. Ako nema adrese, prikazuje se obaveštenje i polje ostaje prazno — ne izmišlja se kontakt. Primaoce, predmet i tekst možete izmeniti. **Kopiraj mejl** kopira i red „Za:“; **Kopiraj adrese** kopira samo adrese za polje primaoca u email programu. Promena kompanije odmah uklanja prethodni tekst/To i učitava samo nove kontakte; zastareli odgovor pretrage se ignoriše.

Mejl i uputstva ostaju samo u memoriji otvorenog ekrana: nema automatskog čuvanja u bazi/browser storage-u, dugmeta Sačuvaj niti spiska ranijih poruka. Osvežavanje ili napuštanje ekrana uklanja trenutni tekst; kopirajte ga pre toga. Asistent ne šalje mejlove i nema pristup sandučetu. Podešavanje znanja je iza dugmeta **Znanje brenda**, dostupnog samo administratoru; ne zauzima osnovnu formu komercijaliste.

Početno znanje o LUU, Invekti i Cenobots-u je sažeto iz zvaničnih sajtova koje je vlasnik naveo; izvori i datum provere su u `backend/app/brand_knowledge.json`. To je početna baza informacija, ne kompletan katalog niti pretraživanje interneta uživo. Ne uključuje cenovnik ili garantovane uslove. **Znanje brenda** administrator firme/platforme sa aktivnim članstvom uređuje zasebno za svaku firmu (do 12.000 znakova). Ostali članovi ga koriste pri generisanju; API za čitanje zadržava ista prava članstva. Izmena ima proveru verzije, a prazan sačuvan tekst namerno isključuje početno znanje. Čitanje/pokretanje ne seed-uje bazu. U model ulazi samo znanje aktivnog brenda; podaci klijenata iz drugih brendova ili tuđih kompanija ostaju nedostupni.

### Podešavanje za Manus/server

1. Otvoriti GroqCloud nalog na besplatnom paketu i napraviti API ključ: https://console.groq.com/keys . Ostati na Free plan-u; aplikacija ne može utvrditi plan ili billing podešavanja Groq naloga.
2. Ključ dodati kao serverski secret **`CRM_GROQ_API_KEY`**, dozvoljen samo za **`api.groq.com`**. Ne slati ključ u chat, ne dodavati ga u Git i ne koristiti `VITE_` promenljivu. Postojeći `CRM_AI_API_KEY` se ne koristi za Groq i nikada mu se ne prosleđuje.
3. Podesiti **`CRM_AI_ENABLED=true`** i običnu serversku promenljivu **`CRM_GROQ_MODEL=openai/gpt-oss-120b`**, pa restartovati backend. Model je proveren u aktuelnoj Groq listi Free limita; dostupnost i limit potvrditi za konkretni nalog. Prefiks `openai/` ovde označava otvoreni model hostovan na Groq-u, ne poziv OpenAI API-ju.
4. Pre objave pregledati novu aditivnu migraciju **`c9d7a4e8f201`** preko `b8a6c2d1e409` i backup baze. Dodaje samo `ai_brand_knowledge`, sa prenosivim TEXT/INTEGER/FK tipovima za MySQL i PostgreSQL, bez seed-a i promena postojećih zapisa. Managed baza nije migrirana tokom ove izmene. Postojeći Docker startup ostaje `python -m app.run_migrations`, pa uvicorn na jednom portu; Publish ostaje zaseban vlasnikov korak.

Podrazumevano `CRM_AI_ENABLED=false`: tada ostaju lokalni šabloni bez spoljnog poziva, jasno označeni kao šabloni koji ne tumače slobodno uputstvo. Ako je AI uključen bez Groq ključa, UI traži podešavanje i backend vraća 503 bez trošenja pokušaja. Ne postoji automatski prelazak na OpenAI ili drugi provider, nadogradnja paketa ili skriveno ponavljanje poziva. Groq Free ima zajedničke limite naloga; 429 daje jasnu poruku za kasniji pokušaj. Besplatnost zavisi od odabranog Groq paketa, ne od CRM-a. Referenca: https://console.groq.com/docs/rate-limits .

Server poziva isključivo `https://api.groq.com/openai/v1/chat/completions` preko postojećeg HTTP mehanizma bez nove SDK zavisnosti. JSON odgovor se validira pre prikazivanja; nepotpun ili neispravan tekst se odbija. Timeout je 45 sekundi, najviše 20 pokušaja po korisniku za 15 minuta kroz njegove firme; neuspešni spoljašnji pozivi troše pokušaj. Za GPT-OSS model koristi se nizak reasoning effort i ograničen izlaz. Samo eksplicitna priprema šalje uputstvo, odabranu kompaniju, imena/funkcije njenih primalaca, ime pošiljaoca i znanje aktivnog brenda Groq servisu. Email adrese kontakata ne šalju se automatski, ali korisnik može uneti lične podatke u slobodna polja. Ne šalju se svi klijenti ili fajlovi iz Ponuda. Nema automatskog čitanja prodajnih PDF-ova. Pravila zadržavanja podataka zavise od Groq naloga: https://console.groq.com/docs/your-data .

Serverska provera sesije, članstva i vidljivosti kompanije radi pre poziva i ponovo pre vraćanja teksta. Generisani tekst i ručne izmene se ne upisuju u `ai_drafts`. U bazi ostaje samo evidencija vremena pokušaja za ograničavanje korišćenja, bez teksta mejla ili uputstva. Autorizacija i Origin zaštita ostaju. Raniji zapisi se ne brišu niti menjaju; nisu prikazani u UI-ju. AI nema alate za menjanje CRM-a; beleške i dolazna poruka tretiraju se kao nepouzdani sadržaj. Pregled činjenica i zamena `[dopuniti]` ostaju obavezni pre slanja.

API: `POST /api/units/{unit_id}/ai/generate` prihvata samo `{company_id, instructions}` iz jednostavne forme i vraća `{subject, body, recipient, recipients, model}` (recipient je spoj adresa, recipients su stvarni kontakti) bez upisa poruke; `GET /api/units/{unit_id}/ai/companies/{company_id}/recipients` vraća dozvoljene primaoce bez AI poziva, `GET /api/units/{unit_id}/ai/status` prikazuje konfiguraciju, a `GET/PUT /api/units/{unit_id}/ai/knowledge` (PUT samo admin, telo `{content, version}`). Stari `POST /ai/drafts` i `PATCH /ai/drafts/{id}` su penzionisani (410 nakon provere pristupa), bez upisa ili poziva AI-ja. Privatni `GET /ai/drafts` ostaje samo za čitanje ranijih zapisa radi kompatibilnosti; frontend ga ne poziva. Serverski API i dalje prihvata prethodna opciona polja za kompatibilnost, uključujući eksplicitni contact_id koji sužava primaoce. Za pojednostavljenje forme i automatske kontakte nije potrebna dodatna migracija; prethodna migracija znanja i dalje je deo postojećeg head-a. Ruta interfejsa ostaje `#crm/ai?unit=...`, naziv u meniju je Invekta AI. Samostalni HTML prikazuje novi ekran i koristi lokalne šablone; pravi Groq zahteva prijavljen CRM, backend i serverski ključ.

Testovi koriste izolovanu PostgreSQL `_test` bazu i simuliran Groq transport: proveravaju JSON protokol, greške/limit, privatnost i autorizaciju, verzije znanja i odvajanje brendova. Ne potvrđuju stvarni Groq ključ ili kvalitet modela. Posle serverskog podešavanja potreban je jedan probni mejl sa neosetljivim podacima.

### Provera Groq veze / HTTP 403

U **objavljenom produkcionom kontejneru**, iz `/app/backend`, pokrenuti jednom:

```bash
python -m app.check_ai_connection
```

Komanda koristi postojeću runtime konfiguraciju i isti HTTP klijent, model i validaciju kao CRM. Šalje **jedan generički zahtev bez CRM podataka**, bez ponavljanja ili dodatnog model-list poziva. Ne otvara bazu, ne pokreće migracije i ne upisuje nacrte/pokušaje. Ako AI nije uključen ili zaseban Groq ključ nedostaje, nema mrežnog poziva. Troši samo običan Groq inference zahtev u okviru postojećeg paketa; ne menja billing. Izlaz je kratak JSON bez ključa, zaglavlja, sirovog odgovora ili generisanog teksta. Exit kod: 0 potvrđeno generisanje, 1 neuspešan poziv/odgovor, 2 nepotpuna konfiguracija.

- `generation_validated`: odgovor je primljen i prošao istu validaciju subject/body kao pravi CRM. Proveru treba pokrenuti u published runtime-u; uspeh u preview-u ne potvrđuje produkcionu konfiguraciju.
- `model_permission_blocked_org` / `model_permission_blocked_project`: proveriti odgovarajući Organization/Project Limits u Groq Console. Organizacione zabrane imaju prednost. [Groq model permissions](https://console.groq.com/docs/model-permissions).
- `edge_block`: prepoznat zaštitni odgovor, uz `cloudflare_1010` samo kada telo sadrži taj konkretan potpis. Proveriti podržan izlazni pristup sa Manus servera sa platformom/Groq podrškom. Ne menjati ključ na osnovu same ove oznake. [Cloudflare 1010](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1010/).
- `forbidden_unknown`: 403 bez potvrđenog uzroka. `response_format` razlikuje JSON, HTML, tekst i nečitljiv/prevelik odgovor, bez objave njihovog sadržaja. DNS/TLS uspeh i odbijen model-list sami ne dokazuju da je ključ neispravan.
- `authentication`: HTTP 401; proveriti ključ i njegov projekat. `rate_limit`: sačekati, bez prelaska na plaćeni paket. `connection_or_response_invalid` / `timeout`: proveriti vezu ili ispravnost odgovora.

Klijent se sada predstavlja kao `InvektaCRM/0.4` i traži `application/json`; ne imitira browser, ne menja TLS/proxy pravila i ne zaobilazi zabrane. To je poboljšanje kompatibilnosti, **ne potvrda da je produkcioni 403 rešen**. Serverska obrada greške čita najviše 8 KiB i propušta samo unapred dozvoljene dijagnostičke oznake. Za ovu izmenu nema nove migracije, paketa ili rute. Integracija GitHub commita i Manus objava ostaju odvojeni koraci.

## Unos kompanije i pristup podacima

Komercijalista vidi i menja samo svoje kompanije, njihove kontakte i prodajne prilike. Menadžer i administrator firme vide sve kompanije unutar firme kojoj imaju pristup; prava ne prelaze u druge firme. Nova kompanija automatski pripada korisniku koji je unosi.

Unos nove kompanije sadrži naziv, adresu, PIB (9 cifara), grad i delatnost, kao i jednu ili više kontakt osoba sa imenom, funkcijom, telefonom i emailom. Kompanija i kontakti se čuvaju zajedno. Adresa i PIB postojećih kompanija ostaju prazni do dopune. Kontakte naknadno dodajete i menjate u profilu kompanije.

Posle preuzimanja ove izmene pokrenite iz `backend` direktorijuma `uv run python -m alembic upgrade head`, pa restartujte backend. GitHub ne migrira pokrenutu bazu automatski.

## Dnevni i mesečni izveštaji promena

Odeljak **Izveštaji** prikazuje kreiranje prilika i promene statusa u prodajnom levku tokom izabranog dana ili meseca, prema vremenskoj zoni Europe/Belgrade. Podrazumevano se otvara današnji dnevni pregled. Period se odnosi na vreme promene, ne na datum kreiranja prilike.

Hronologija prikazuje kompaniju, priliku, prethodni i novi status, korisnika i vreme promene. Izveštaj ima četiri pokazatelja: Nove prilike, Promene statusa, Realizovano i Nije realizovano. Kartice „Sve promene“ i „Izmene podataka“ su uklonjene, kao i detalji izmena polja iz prikaza. Izmene naslova, vrednosti, očekivanog datuma, vrste posla i beleške bez promene statusa ne ulaze u zbirne brojeve, grafikone, pregled po komercijalisti ili paginaciju izveštaja. Istorija tih izmena ostaje sačuvana u bazi i postojeća evidencija se ne briše. Vrednost pri promeni statusa ostaje istorijski podatak. Demo računa izveštaj istim pravilima.

Pokazatelji broje događaje (jedna prilika može imati više promena) i različite prilike u periodu. Menadžer vidi dostupne događaje cele firme, komercijalista događaje na prilikama svojih kompanija. Demo događaji iz baze podrazumevano su isključeni i mogu se uključiti filterom. Sve promene dostupne su kroz stranice od 50 zapisa; zbirni brojevi obuhvataju ceo period.

Samostalni HTML demo prikazuje lokalnu istoriju promena statusa od ove verzije, sa dnevnim/mesečnim filterom. Demo istorija se čuva samo u istom browseru kada je localStorage dostupan, ne šalje se serveru i nema izmišljenu prethodnu istoriju.

Posle preuzimanja pokrenite `uv run python -m alembic upgrade head` iz `backend`, zatim restartujte backend.

## Kalendar zadataka

„Novi klijenti“ je uklonjen iz menija; kompanije se dodaju kroz **Kompanije**. Stare `#crm/leads` i `#demo/leads` putanje i dalje otvaraju kompanije.

U **Zadaci** izaberite mesec i dan, pa **Dodaj novi zadatak**. Unesite naziv, datum, opciono vreme u Beogradu, belešku i kompaniju. Kompanija se bira pretragom dok kucate naziv, grad ili PIB, kao kod prilika. CRM pretražuje dozvoljene kompanije na serveru, uključujući one van početnih 200 rezultata; demo pretražuje lokalne kompanije izabranog brenda. Podržani su miš i tastatura (strelice, Enter, Escape). Kompanija ostaje opciona: ostavite polje prazno ili izaberite **Bez kompanije**. Ako je naziv upisan, potrebno je izabrati rezultat ili obrisati tekst pre čuvanja. Pri izmeni se čuva već povezana kompanija i kada nije u početnoj listi. Moguće je izmeniti zadatak, označiti ga kao završenog i ponovo otvoriti. Nova kompanijska veza proverava se na serveru; nije moguće izabrati kompaniju iz druge firme ili tuđu kompaniju bez ovlašćenja. Zadaci automatski pripadaju korisniku koji ih unosi. Komercijalista vidi samo svoje zadatke i dozvoljene povezane kompanije; menadžer i administrator vide zadatke svoje firme. Promene imaju verziju radi zaštite od prepisivanja novijih podataka.

API: `GET/POST /api/units/{unit_id}/tasks`, `PATCH /api/units/{unit_id}/tasks/{task_id}` i `PATCH /api/units/{unit_id}/tasks/{task_id}/status`. Lista zahteva `date_from` i `date_to`; kalendar učitava sve stranice kako bi broj zadataka ostao tačan i preko 200 zapisa. UI putanja je `#crm/tasks?unit=...`, demo `#demo/tasks?organization=...`.

Nova migracija `d264b37c5f53` dodaje samo tabelu i indeks zadataka, bez seed-a ili promene postojećih podataka. Koristi prenosive SQLAlchemy Date/Time/String tipove i strane ključeve za PostgreSQL i MySQL. Demo ima zaseban kalendar u localStorage po firmi; podaci se ne šalju managed bazi.

**Integracija sa Manus projektom:** kalendar grana je spojena sa export granom `manus/hosted-deployment-77e0ede`. Revizija `e575c48d6a64` spaja migracione grane bez izmene postojećih revizija. Route manifest uključuje kalendar i uklanja redundantni ekran novih klijenata; stare hash putanje ostaju kompatibilne. Sačuvani su Manus Docker runtime, oba COPY koraka za shared katalog, MySQL podrška, HTTPS session/Origin zaštita i readiness bez prijave. GitHub grana je priprema za Manus canonical checkpoint; git push ne objavljuje sajt. Ne pokretati seed, testove, reset ili downgrade nad managed bazom.

Provere integrisanog kalendara: frontend `npm ci`, 9 testova i build; 63 backend regresiona testa isključivo nad lokalnom PostgreSQL `_test` bazom; Pyright bez grešaka; Alembic jedan head `e575c48d6a64`. Clean Docker build i privremeni kontejner provereni su sa lokalnom test bazom: startup migracije, port 3000, `/api/ready` bez prijave, statički assets i `/app/shared/message_catalog.json`. Ove provere nisu Publish niti test Manus managed baze.

Docker build u okruženju sa TLS proxy-jem opciono prihvata BuildKit secret `proxy_ca` (CA bundle), npr. `docker build --secret id=proxy_ca,src=/etc/ssl/certs/ca-certificates.crt -t invekta-review .`. CA se montira samo tokom instalacije zaključanih paketa, TLS provera ostaje uključena i sertifikat se ne kopira u image. Manus build bez tog secret-a koristi standardni trust store. `.dockerignore` isključuje lokalne tajne i zavisnosti iz build konteksta.

## Mesečni targeti po komercijalisti

**Targeti** prikazuju cilj u RSD, ostvarenu vrednost, broj realizovanih poslova, procenat napretka i preostali iznos. Menadžer i administrator firme postavljaju mesečne ciljeve aktivnim komercijalistima iz svoje firme; komercijalista vidi samo svoje ciljeve i ne može ih menjati. Za LUU postoji **Prodaja**, za Invektu **Ugovoren posao**, a za Cenobots odvojeno **Prodaja**, **Lizing** i **Najam**. Nema automatski upisanih ciljnih iznosa; nula znači da cilj nije postavljen. Konflikt pri upisu zahteva osvežavanje, a više kategorija čuva se zajedno.

Vrsta posla bira se pri unosu/izmeni prilike, uz serversku proveru vrste za konkretnu firmu. Cenobots prilika mora imati vrstu posla pre realizacije; ranije Cenobots prilike ostaju nekategorisane dok se ručno ne dopune. Za LUU i Invektu postojeće prilike dobijaju jedinu dozvoljenu vrstu posla. Novi UI i dalje koristi **Realizovano / Nije realizovano**; stabilne interne oznake sačuvane su radi kompatibilnosti baze i starih klijenata.

Ostvarenje se računa iz trenutno realizovanih prilika kompanija konkretnog komercijaliste. Datum je poslednji stvarni prelazak u Realizovano po beogradskom vremenu; svaka prilika se broji jednom. Koriste se istorijski sačuvani vrednost i vrsta posla tog događaja. Kod ranije nekategorisanih Cenobots prilika koristi se naknadno ručno izabrana vrsta posla, dok istorijska vrednost i dalje mora biti zabeležena. Ponovno otvaranje izuzima priliku iz ostvarenja, a nova realizacija pripada novom mesecu. Samo izmene beleške/vrednosti na već realizovanoj prilici ne dodaju novu realizaciju. Ovo je vrednost poslova, ne fakturisan prihod. Demo zapisi i ranije prilike bez istorijskog iznosa/događaja realizacije ne ulaze u ostvarenje; prazno ostvarenje nije dokaz da ranije nije bilo prodaje.

API: `GET/PUT /api/units/{unit_id}/targets`; izbor meseca koristi `YYYY-MM`. UI `#crm/targets?unit=...`, demo `#demo/targets?organization=...`. Demo ciljevi se čuvaju lokalno po firmi/mesecu i prate promene demo levka; nisu stvarni targeti niti se šalju managed bazi. Migracija `f686d59e7b75` dodaje targete i vrste posla preko postojećeg merge head-a. Objavljivanje kroz Manus ostaje odvojen korak, bez seed-a, resetovanja baze ili testova nad managed podacima.

## Današnji zadaci, pretraga kompanija i timski bonus

Početni baner sada prikazuje stvarne zadatke za današnji datum u Beogradu: vreme, kompaniju, vlasnika i status. Prikazano je do pet zadataka, uz pune brojače i vezu ka kalendaru; učitavaju se sve stranice dnevne liste. Osvežavanje se vrši povratkom na prozor i periodično tokom otvorenog prikaza. Važe ista serverska prava kao u kalendaru. Demo baner prati lokalne zadatke izabrane firme.

Pri unosu prilike u polje kompanije može da se kuca naziv, grad ili PIB. Pretraga ide ka serveru, pa radi i za kompanije van početnih 200 rezultata. Iz rezultata je obavezno izabrati kompaniju; podržani su tastatura (strelice, Enter, Escape) i pokazivač. Server i dalje proverava pristup izabranoj kompaniji.

Menadžer i administrator u **Izveštajima** imaju pregled po komercijalisti i filter `owner_id`. Dnevni/mesečni brojači i grafikoni obuhvataju ceo filtrirani period, nezavisno od paginacije istorije. Učinak se pripisuje trenutnom vlasniku kompanije; korisnik koji je napravio promenu ostaje zasebno prikazan. Komercijalista ne može filtriranjem pristupiti tuđim podacima.

U **Targetima** svi članovi firme vide **Kolektivni bonus za tim**: zajednički mesečni cilj, zbir pojedinačnih targeta aktivnih komercijalista, njihovo zbirno ostvarenje i sopstveni doprinos. Administrator firme ili administrator platforme sa članstvom u firmi postavlja cilj i opcioni opis zajedničke nagrade. Menadžer bez tih prava i komercijalista imaju samo pregled. Kolektivni izveštaj izlaže zbirne podatke bez spiska tuđih kompanija ili pojedinačnih iznosa kolega. Realizacija se računa istim pravilima kao pojedinačni targeti i prati poslovne vrste konkretnog brenda. Dostizanje cilja označava ispunjen uslov; ne računa niti potvrđuje isplatu bonusa. Nula ili nepostavljen cilj ne otključava bonus.

API `GET/PUT /api/units/{unit_id}/team-bonus?month=YYYY-MM` (za PUT mesec je u JSON telu). PUT koristi `version`, zahteva postojeću Origin/session zaštitu i ne dopušta prepisivanje zastarelih podataka. Migracija `a797e60f8c86` dodaje samo tabelu mesečnog kolektivnog cilja preko prethodnog head-a, bez seed-a ili promene postojećih poslovnih zapisa. Readiness proverava i ovu tabelu. Demo zajednički cilj i opis čuvaju se lokalno po firmi i mesecu; nisu produkcioni bonus planovi.


## Ponude i prodajni fajlovi

U **Ponude** administrator firme ili platform administrator sa aktivnim članstvom u firmi može izabrati **Dodaj fajl**, uneti opcioni naziv i sačuvati dokument. Podržani su PDF, DOC/DOCX, XLS/XLSX, PNG i JPG/JPEG, do 10 MB po fajlu. Dokumenti se dodaju pojedinačno; isto ime fajla ne prepisuje prethodni zapis.

Svi prijavljeni korisnici sa aktivnim pristupom istom brendu mogu videti spisak, pretraživati naziv/ime fajla i preuzeti dokument. Menadžer i komercijalista nemaju pravo dodavanja, čak ni direktnim API zahtevom. Ovo je zajednička biblioteka dokumentacije koju administrator objavljuje timu; ne menja vidljivost kompanija i njihovih privatnih podataka. LUU, Invekta i Cenobots dokumenti ostaju međusobno odvojeni. Deaktivacija naloga ili članstva odmah blokira sledeći zahtev za preuzimanje. Fajlovi nisu javni statički resursi i ne postoje javni linkovi za deljenje.

Sadržaj fajla i metapodaci čuvaju se zajedno u trajnoj bazi (PostgreSQL BYTEA lokalno, MySQL MEDIUMBLOB u Manus okruženju), bez čuvanja u prolaznom kontejner fajl-sistemu ili dodavanja plaćenog storage servisa. Backup baze zato mora obuhvatiti i tabelu `sales_documents`. Server proverava ekstenziju, osnovni potpis i stvarnu veličinu tokom prijema, uključujući zahteve bez Content-Length. Sadržaj se preuzima kao attachment uz nosniff; nije ugrađen u HTML i ne prikazuje se inline. Lista vraća samo metapodatke, bez binarnog sadržaja; pretraga i paginacija ne preuzimaju fajlove.

API: `GET /api/units/{unit_id}/sales-documents?search=&limit=20&offset=0`, `POST /api/units/{unit_id}/sales-documents?filename=...&title=...` (sirovi binarni sadržaj, `application/octet-stream`, postojeća session/Origin zaštita), i `GET /api/units/{unit_id}/sales-documents/{document_id}/download`. Ruta interfejsa ostaje `#crm/quotes?unit=...`. Demo prikazuje ekran bez stvarnog upload-a ili izmišljenih dokumenata; za rad sa fajlovima potrebna je prijava u CRM.

Migracija **`b8a6c2d1e409`**, preko `a797e60f8c86`, dodaje samo novu tabelu i indeks. Ne menja postojeće korisnike, sesije ili poslovne zapise. Podržava PostgreSQL i MySQL preko eksplicitne MySQL varijante binarnog tipa. Pre Manus objave pregledati migraciju i napraviti backup managed baze; testovi/seed/reset se tamo ne pokreću. Izmena na GitHub grani sama po sebi ne objavljuje sajt. Testovi koriste samo lokalnu izolovanu PostgreSQL `_test` bazu.
