# Preuzimanje CRM demo prikaza

Otvorite `LUU_Invekta_CRM_Demo.html` na GitHub-u i kliknite **Download raw file** (strelica za preuzimanje u zaglavlju fajla). Preuzeti HTML otvorite u Chrome-u ili Edge-u.

Fajl je samostalan pregled frontenda verzije 0.4, sa izmišljenim demo podacima. Ne zahteva instalaciju. Prijava, kontakti i trajne prodajne prilike zahtevaju pokrenut backend i PostgreSQL; ne rade samostalno iz preuzetog fajla. Ovo nije javni hosting CRM-a.

Demo je izvezen iz proverenog Vite build-a; pri promenama aplikacije potrebno je ponovo izvesti ovaj pregled.

Aktuelni pregled ima suptilne 3D senke i ivice, uz iste brend boje i raspored. [Prethodni izgled za poređenje](https://github.com/pextex/invekta/blob/ui-before-3d-2026-10-15/demo/LUU_Invekta_CRM_Demo.html) trajno je sačuvan oznakom `ui-before-3d-2026-10-15`. Na obe stranice koristite **Download raw file**. Vizuelni sloj može se ukloniti bez promene funkcija ili baze; postupak je u glavnom README-u.

U **Prodajni levak** prevucite karticu u drugu kolonu ili izaberite status na njoj. Na telefonu koristite izbor statusa. Promene ostaju u istom fajlu/browseru kada je lokalno čuvanje dostupno, i nisu prenete u CRM bazu. Demo dashboard odmah računa nove otvorene prilike.

Po otvaranju izaberite LUU, Invekta ili Cenobots, pa kliknite **Pogledaj demo bez prijave**. Stvarna prijava ne radi iz samostalnog HTML fajla. Cenobots partneri su izmišljeni i jasno označeni, kao i podaci ostalih jedinica.


Besplatni šabloni rade i u samostalnom HTML-u bez servera i interneta. U odeljku Invekta AI izaberite klijenta i cilj poruke, pa Pripremi nacrt iz šablona. Tekst se može urediti i kopirati dugmetom **Kopiraj mejl**. Ako browser blokira clipboard, tekst se označi za ručno kopiranje. Mejl, potpis i sadržaj pripreme ne čuvaju se u browser storage-u; osvežavanje ili napuštanje ekrana ih uklanja. Nema dugmeta za čuvanje, istorije ni spiska ranijih poruka. Stari lokalni zapisi se ne učitavaju i ne brišu automatski.

Invekta AI u samostalnom HTML-u prikazuje novi prozor za zahtev i primere, ali radi samo sa lokalnim šablonima. Slobodno uputstvo tumači pravi Groq model tek u povezanom CRM-u sa serverskim ključem. Znanje brenda administrator uređuje u prijavljenoj aplikaciji.
