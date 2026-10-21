# Marketing i porudžbine

Administrator platforme sada može dodeliti ulogu **Marketing** u svakom od tri brenda. Nalog se kreira kroz **Korisnici i pristup** sa stvarnim imenom, emailom i početnom lozinkom; ova izmena ne kreira izmišljene naloge ili podatke.

Marketing ima Porudžbine umesto Kompanija. Unos: ime, prezime, telefon, opcion email i izvor Sajt/Telefon. Levak ima četiri faze: Porudžbine, Ponuda poslata, Realizovano i Nije realizovano. Kartice se mogu prevlačiti ili menjati status kroz izbor na kartici, uključujući mobilni prikaz. Svaka kolona ima sopstvenu paginaciju. Status se čuva uz proveru verzije, tako da se paralelne izmene ne pregaze.

Marketing vidi samo svoje porudžbine aktivnog brenda; menadžeri i administratori mogu pregledati porudžbine u brendu kojem imaju pristup. Komercijalisti nemaju pristup porudžbinama. Marketing nema pravo čitanja tuđih kompanija, upravljanja nalozima, čitanja znanja brenda ili hronologije. Zadaci ostaju lični, bez birača kompanija za marketing. Ponude i profil koriste postojeća prava pristupa.

Marketing dashboard i izveštaji koriste porudžbine, ne komercijalističke prilike. Izveštaj prikazuje **trenutni status porudžbina unetih u izabranom periodu**, sa datumima po Europe/Belgrade; ne predstavlja istoriju kretanja statusa. Porudžbine nemaju novčani iznos i zato se njihov broj ne pretvara u RSD ostvarenje targeta. Targeti i kolektivni cilj zadržavaju postojeću novčanu logiku.

Marketing AI bira porudžbinu umesto kompanije, preuzima njen email i koristi postojeća pravila brenda i potpis. Nacrt nije poslat niti trajno sačuvan. Ograničenje je 20 priprema za 15 minuta po korisniku, zajedno sa postojećim AI zahtevima. Kada je Gemini isključen, prikazuje se lokalni šablon uz odgovarajuću napomenu.

Marketing prikaz nema dugme za vodič i ne otvara vodič. Dodavanje marketing naracije je otkazano. Postojeći vodič i 26 Kore naracija za ostale uloge ostaju dostupni.

Za objavu primeniti Alembic migraciju `bc38e7f012a4` standardnom komandom `python -m app.run_migrations`, zatim objaviti novi frontend i backend. Migracija je dodata iza `ab27d6e901f3`; ne briše postojeće naloge ili poslovne podatke. Ranije pripremljena komanda za reset automatski čisti i marketing porudžbine jer prati redosled stranih ključeva u šemi. Reset prave baze i dalje nije izvršen ovom izmenom.

Provereno: migracija primenjena na izolovanoj PostgreSQL `marketing_test` bazi, validan marketing nalog/porudžbina prošli stvarna DB ograničenja; 34 backend provere (uloge, prava, zadaci, targeti, znanje brenda, reset i porudžbine) i 23 frontend provere prošle su uspešno. Produkcioni build i Chromium prikaz na 1440×1000 i 390×844 potvrđuju unos emaila, četiri faze i promenu statusa. Nijedan pravi nalog ili produkciona baza nisu menjani.
