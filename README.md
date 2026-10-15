# LUU × INVEKTA × CENOBOTS — AI Sales CRM

Zajednička CRM platforma za LUU, Invektu i Cenobots. Ciljani trajni Manus deployment koristi managed MySQL; CRM podaci su dostupni samo posle prijave. Javno objavljivanje je pod kontrolom vlasnika; automatsko objavljivanje nije uključeno.

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

Ponude, aktivnosti, raspodela kompanija i potpuna audit evidencija još nisu implementirani. Upravljanje nalozima i priprema AI nacrta su dodati; AI zahteva povezivanje servisa. Istorija prodajnih prilika beleži kreiranje, promene statusa i izmene podataka; potpuna audit evidencija ostalih modula još nije implementirana. Dobijeni poslovi predstavljaju vrednost prilika označenih kao dobijene, ne fakturisan prihod.

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

Aktivacija prihvata samo postojeći, neaktivan nalog sa `bootstrap_pending=true`; posle uspeha trajno troši marker. Ponovljeni poziv `--activate` ne može resetovati lozinku, aktivirati drugi nalog ili kreirati novog administratora. Za automatizaciju unesite `CRM_ACCOUNT_PASSWORD` kroz zaštićeni unos okruženja i koristite ga samo za ovu komandu; ne postavljajte lozinku kao argument, u chat ili u Git. Komanda je eksplicitna i ne izvršava se tokom pokretanja servera. U Manus deployment-u podaci naloga ostaju u managed MySQL bazi; PostgreSQL je samo za lokalni razvoj. Lozinku drugih korisnika kasnije menjajte kroz ovlašćeni interfejs, ne bootstrap komandom.

## AI asistent za nacrte poruka

U svakom povezanom CRM-u otvorite **AI asistent**, izaberite klijenta i opciono kontakt/prodajnu priliku. Izaberite novi email, odgovor ili follow-up, ton i srpski/engleski jezik. Za odgovor nalepite primljenu poruku. Navedite cilj poruke i kliknite **Pripremi AI nacrt**. Nacrt se čuva u bazi; predmet, primalac i tekst su izmenjivi. **Kopiraj nacrt** kopira tekst za ručno slanje iz email programa. Ova funkcija ne šalje poruke i nema vezu sa vašim email sandučetom.

Server koristi OpenAI Responses API na `https://api.openai.com/v1/responses`, podrazumevani model `gpt-4.1-mini` i strukturirani JSON odgovor. Podatke čine samo izabrana kompanija, ime/pozicija izabranog kontakta, izabrana prilika, instrukcije i dolazna poruka. Adresa kontakta služi za polje primaoca i ne šalje se modelu. API zahtev koristi `store=false`; to samo po sebi nije obećanje o potpunom odsustvu zadržavanja podataka kod pružaoca usluge. Pristup se proverava pre poziva i ponovo pre čuvanja nakon poziva. Nacrt ostaje privatni zapis autora u firmi, uz pravila vidljivosti klijenta.

Podesite `CRM_AI_API_KEY` kroz bezbedna podešavanja okruženja/servera i dozvolite `api.openai.com`. U ovom cloud okruženju ključ može da se isporuči kroz proxy binding namenjen isključivo tom domenu. Ne koristiti rezervisano ime `OPENAI_API_KEY` za ovu deklaraciju. `CRM_AI_MODEL` je opciona obična promenljiva. Restartujte backend posle izmene konfiguracije. Bez ključa prikazuje se stanje da servis nije povezan; nema lažnog generisanja ili zamenskih tekstova.

Najviše 20 pokušaja generisanja po korisniku u 15 minuta, ukupno kroz njegove firme; neuspešan poziv servisu takođe troši pokušaj. Zahtev ima timeout 45 sekundi. Neispravan, odbijen ili nepotpun AI odgovor ne čuva nacrt. Čuvanje ručnih izmena koristi verziju i vraća konflikt ako je drugi prozor već izmenio zapis. Proverite činjenice i mesta `[dopuniti]` pre slanja. Za izbor kompanije učitava se najviše 200 zapisa i za izabranu kompaniju najviše 100 prilika.

Samostalni HTML sada lokalno priprema šablonske nacrte i ispisuje tekst za kopiranje; bez backend-a ne čuva ih u bazi. Testovi pokrivaju protokol sa simuliranim AI odgovorima, granice pristupa, kontekst, rate limit, greške i upis/izmenu nacrta; poziv stvarnom OpenAI servisu zahteva podešen ključ i proveru nakon povezivanja.

AI generisanje je isključeno na zahtev korisnika. `CRM_AI_ENABLED` podrazumevano je `false`; prisustvo ključa ne omogućava pozive. Sačuvani nacrti ostaju dostupni. Za uklanjanje binding-a izbrišite `CRM_AI_API_KEY` u podešavanjima okruženja, a za opoziv samog ključa obrišite ga i na OpenAI API Keys stranici. Ponovno uključivanje naplatnog servisa zahteva izričit zahtev korisnika.

## Besplatni asistent sa šablonima

Aktivni CRM sada koristi lokalne šablone, ne OpenAI. Izaberite firmu klijenta, kontakt/priliku, novi email/odgovor/follow-up, cilj (sastanak, predstavljanje, dodatne informacije), ton i srpski/engleski jezik. Nacrt se priprema i čuva u CRM bazi bez API ključa i bez naplate po poruci (managed MySQL na hostingu, PostgreSQL lokalno). Primalac, predmet i telo mogu se uređivati i kopirati. Napomene i pitanja iz dolazne poruke morate ručno uneti u odgovor: šabloni nemaju razumevanje slobodnog teksta. Plaćeni provider je odvojen i isključen; nijedan korisnički endpoint ga više ne poziva. Prethodna uputstva za povezivanje OpenAI opisuju raniju opciju, ne aktivni način rada.

Samostalni demo podržava lokalnu pripremu besplatnih nacrta i kopiranje teksta. Za to nisu potrebni backend ili API ključ. U demou se poslednjih 30 nacrta, izmene i potpis pamte u lokalnom browseru po firmi. Čuvanje u bazi i kontakti iz baze rade samo u prijavljenom CRM-u.

Profesionalni nacrti: unesite temu, šta nudite, fokus/potrebe klijenta, opcioni termin i potpis. Dodatne informacije ulaze u poruku. Za odgovore unesite konkretan odgovor klijentu; prazno polje ostavlja vidljivo mesto za dopunu. Novi cilj „Predstavljanje predloga saradnje“ ne dodaje izmišljene cene ili uslove. Formulacije sr/en su zajedničke za demo i backend u shared/message_catalog.json.

Dobrodošlica na početnoj tabli prikazuje ime korisnika i datum u vremenskoj zoni Europe/Belgrade. Predlog za danas računa se iz trenutnih faza prilika i broja kompanija; to nisu zadaci sa dodeljenim rokovima. Svaki predlog vodi na odgovarajući ekran. Demo pamti nacrte, kompoziciju poruke i potpis lokalno po firmi; nesačuvane izmene mogu se vratiti nakon navigacije ili refresh-a. Ako localStorage nije dostupan, poruka traži ručno kopiranje. Pretraga nacrta filtrira prikazane zapise; stvarni CRM zadržava paginaciju.

## Unos kompanije i pristup podacima

Komercijalista vidi i menja samo svoje kompanije, njihove kontakte i prodajne prilike. Menadžer i administrator firme vide sve kompanije unutar firme kojoj imaju pristup; prava ne prelaze u druge firme. Nova kompanija automatski pripada korisniku koji je unosi.

Unos nove kompanije sadrži naziv, adresu, PIB (9 cifara), grad i delatnost, kao i jednu ili više kontakt osoba sa imenom, funkcijom, telefonom i emailom. Kompanija i kontakti se čuvaju zajedno. Adresa i PIB postojećih kompanija ostaju prazni do dopune. Kontakte naknadno dodajete i menjate u profilu kompanije.

Posle preuzimanja ove izmene pokrenite iz `backend` direktorijuma `uv run python -m alembic upgrade head`, pa restartujte backend. GitHub ne migrira pokrenutu bazu automatski.

## Dnevni i mesečni izveštaji promena

Odeljak **Izveštaji** prikazuje sve zabeležene događaje u prodajnom levku tokom izabranog dana ili meseca, prema vremenskoj zoni Europe/Belgrade. Podrazumevano se otvara današnji dnevni pregled. Period se odnosi na vreme promene, ne na datum kreiranja prilike.

Hronologija prikazuje kompaniju, priliku, prethodni i novi status, korisnika i vreme promene. Beleže se i kreiranje prilike i izmene naslova, vrednosti, očekivanog datuma zatvaranja i beleške. Vrednost pri promeni čuva se kao istorijski podatak; ponovljeno čuvanje bez stvarne izmene ne pravi događaj. Stariji zapisi sadrže samo istoriju statusa, bez naknadnog izmišljanja ranijih izmena ili vrednosti.

Pokazatelji broje događaje (jedna prilika može imati više promena) i različite prilike u periodu. Menadžer vidi dostupne događaje cele firme, komercijalista događaje na prilikama svojih kompanija. Demo događaji iz baze podrazumevano su isključeni i mogu se uključiti filterom. Sve promene dostupne su kroz stranice od 50 zapisa; zbirni brojevi obuhvataju ceo period.

Samostalni HTML demo prikazuje lokalnu istoriju promena statusa od ove verzije, sa dnevnim/mesečnim filterom. Demo istorija se čuva samo u istom browseru kada je localStorage dostupan, ne šalje se serveru i nema izmišljenu prethodnu istoriju.

Posle preuzimanja pokrenite `uv run python -m alembic upgrade head` iz `backend`, zatim restartujte backend.

## Kalendar zadataka

„Novi klijenti“ je uklonjen iz menija; kompanije se dodaju kroz **Kompanije**. Stare `#crm/leads` i `#demo/leads` putanje i dalje otvaraju kompanije.

U **Zadaci** izaberite mesec i dan, pa **Dodaj novi zadatak**. Unesite naziv, datum, opciono vreme u Beogradu, belešku i kompaniju. Moguće je izmeniti zadatak, označiti ga kao završenog i ponovo otvoriti. Nova kompanijska veza proverava se na serveru; nije moguće izabrati kompaniju iz druge firme ili tuđu kompaniju bez ovlašćenja. Zadaci automatski pripadaju korisniku koji ih unosi. Komercijalista vidi samo svoje zadatke i dozvoljene povezane kompanije; menadžer i administrator vide zadatke svoje firme. Promene imaju verziju radi zaštite od prepisivanja novijih podataka.

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
