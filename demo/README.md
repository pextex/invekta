# Preuzimanje CRM demo prikaza

Otvorite `LUU_Invekta_CRM_Demo.html` na GitHub-u i kliknite **Download raw file** (strelica za preuzimanje u zaglavlju fajla). Preuzeti HTML otvorite u Chrome-u ili Edge-u.

Fajl je samostalan pregled frontenda verzije 0.4, sa izmišljenim demo podacima. Ne zahteva instalaciju. Prijava, kontakti i trajne prodajne prilike zahtevaju pokrenut backend i PostgreSQL; ne rade samostalno iz preuzetog fajla. Ovo nije javni hosting CRM-a.

Demo je izvezen iz proverenog Vite build-a; pri promenama aplikacije potrebno je ponovo izvesti ovaj pregled.

Aktuelni pregled ima suptilne 3D senke i ivice, uz iste brend boje i raspored. [Prethodni izgled za poređenje](https://github.com/pextex/invekta/blob/ui-before-3d-2026-10-15/demo/LUU_Invekta_CRM_Demo.html) trajno je sačuvan oznakom `ui-before-3d-2026-10-15`. Na obe stranice koristite **Download raw file**. Vizuelni sloj može se ukloniti bez promene funkcija ili baze; postupak je u glavnom README-u.

U **Prodajni levak** prevucite karticu u drugu kolonu ili izaberite status na njoj. Na telefonu koristite izbor statusa. Promene ostaju u istom fajlu/browseru kada je lokalno čuvanje dostupno, i nisu prenete u CRM bazu. Demo dashboard odmah računa nove otvorene prilike.

Po otvaranju izaberite LUU, Invekta ili Cenobots, pa kliknite **Pogledaj demo bez prijave**. Stvarna prijava ne radi iz samostalnog HTML fajla. Cenobots partneri su izmišljeni i jasno označeni, kao i podaci ostalih jedinica.


Besplatni šabloni rade i u samostalnom HTML-u bez servera i interneta. U odeljku AI asistenta izabranog brenda opišite mejl, izaberite kompaniju pretragom i kliknite **Pripremi mejl iz šablona**. Tekst se može urediti i kopirati dugmetom **Kopiraj mejl**. Ako browser blokira clipboard, tekst se označi za ručno kopiranje. Mejl, potpis i sadržaj pripreme ne čuvaju se u browser storage-u; osvežavanje ili napuštanje ekrana ih uklanja. Nema dugmeta za čuvanje, istorije ni spiska ranijih poruka. Stari lokalni zapisi se ne učitavaju i ne brišu automatski.

AI asistent u samostalnom HTML-u prikazuje novi prozor za zahtev i primere, ali radi samo sa lokalnim šablonima. Slobodno uputstvo tumači Gemini model tek u povezanom CRM-u sa serverskim ključem. Znanje brenda administrator uređuje u prijavljenoj aplikaciji.

Forma ima samo zahtev i kompaniju. Stvarni kontakti se automatski popunjavaju samo u prijavljenom CRM-u; demo ne izmišlja email adrese klijenata. U pripremljenom mejlu primaoci, predmet i tekst su izmenjivi.

## Vodič sa naracijom

Dugme **Vodič kroz aplikaciju** otvara lekcije sa pokazivačem, isticanjem elemenata i unapred pripremljenom AI naracijom ženskim glasom na srpskom. Svih 26 jedinstvenih koraka ima snimak izabranim ženskim glasom Kore, uključujući uvode za INVEKTA AI i CENOBOTS AI. Snimci su uključeni u HTML i pri reprodukciji ne zahtevaju nalog ili serverski ključ.

**Pokreni vodič od početka** počinje lekcijom **Početna tabla**: današnji zadaci, pokazatelji prodaje i pregled levka. Posle nje automatski slede Kompanije i ostale dostupne lekcije. Naslovi odgovaraju nazivima kartica, a na početku snimljene lekcije izgovara se njen naziv. Uvodi za Zadaci i Izveštaji su celi snimci sa jasno odvojenim naslovom.

Tokom lekcije vodič se minimizuje. Dugme **Proširi vodič** prikazuje tekst i podešavanja. Pauza zadržava mesto u snimku i zaustavlja automatski prelazak. **Ponovi korak** pušta snimak od početka. Dostupni su isključivanje naracije i ručno preskakanje. Ako browser blokira zvuk, pritisnite Ponovi korak.

Vodič otvara ekrane, ali ne unosi podatke, ne čuva zapise i ne pokreće AI generisanje. Pre početka sačuvajte otvoren unos ili kopirajte pripremljeni mejl. U povezanom CRM-u hronologija i administrativne lekcije prate korisnička ovlašćenja. ElevenLabs se ne koristi.

## Pregledni prodajni mejlovi

Mejlovi imaju odvojene pasuse, umereno podebljane ključne fraze i direktan poziv na sledeći korak. **Uredi tekst** otvara izmenu, a **Prikaži mejl** formatirani pregled. **Kopiraj mejl** prenosi i HTML formatiranje u programe koji ga podržavaju; rezervno kopiranje daje čist tekst bez oznaka za bold.

Povezani Gemini dobija prodajna pravila na serveru i referentni sadržaj zvaničnog sajta izabranog brenda. Serverska provera javnih stranica kešira se 15 minuta. Ako provera ne uspe, koristi se jasno označen sačuvani sažetak. Izvori su prikazani ispod mejla. Provera sajta ne šalje podatke klijenata tim sajtovima. Promena zahteva novu verziju frontenda i backenda na Manusu; samostalni demo i dalje koristi lokalne šablone.

## Moj profil

Dugme **Moj profil** nalazi se gore desno, pored imena korisnika. U prijavljenom CRM-u korisnik može sačuvati ili ukloniti telefon i promeniti šifru uz trenutnu šifru i potvrdu nove (najmanje 12 znakova). Nova šifra odjavljuje ostale uređaje, dok trenutna sesija ostaje aktivna. Telefon se koristi u potpisu AI mejlova. Samostalni demo prikazuje profil bez čuvanja podataka i promene šifre.

Za ovu izmenu Manus treba da objavi frontend i backend i izvrši standardne Alembic migracije (`python -m app.run_migrations` iz backend direktorijuma); nova migracija dodaje opciono polje `users.phone`.

Potpis prodajnih mejlova sada sadrži ime i prezime sa korisničkog naloga, naziv aktivnog brenda, telefon iz profila, njegov zvanični sajt i adresu. Potpis za Gemini dodaje server iz CRM podataka, a lokalni šabloni koriste iste kontakt podatke. Bez unetog telefona stoji podsetnik da se dopuni u „Moj profil“; broj se ne izmišlja. Adrese su proverene prema kontakt stranicama [LUU](https://luu.rs/kontakt/), [INVEKTA](https://invekta.rs/kontakt/) i [CENOBOTS](https://cenobots.rs/kontakt/) 19.10.2026. U samostalnom demo fajlu ime i telefon ostaju za dopunu jer nema prijavljenog korisnika.

Lični podaci potpisa (ime, telefon i ostala sender_* polja) izuzeti su iz konteksta koji se šalje Gemini modelu; potpis se sastavlja na serveru nakon generisanja.

Pristup „Znanje brenda“: administratori i menadžeri imaju pregled, a izmenu zadržavaju administratori. Komercijalistima je skriveno dugme i server odbija direktan zahtev za sadržaj; AI i dalje koristi odobreno znanje za pripremu mejlova. Pristup uvek zahteva aktivno članstvo u odgovarajućem brendu.
