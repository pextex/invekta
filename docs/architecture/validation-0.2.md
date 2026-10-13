# Provera verzije 0.2

## Izvršeno u cloud razvojnom okruženju
- PostgreSQL 16 preko Docker Compose, healthcheck uspešan.
- Alembic početna migracija izvršena na razvojnoj i izdvojenoj test bazi.
- `alembic check`: nema razlike između ORM modela i migracije.
- 13 backend testova: readiness, anonimni pristup, prijava/odjava, sesije, jedinice, vlasništvo, unos/izmena, validacija, CSRF i ograničenje prijave, hash sesije, Secure cookie, FK izolacija i ponovljiv seed/reset.
- 2 frontend testa: demo filtriranje po modulu i pretraga.
- TypeScript i Vite produkcioni build.

- Chromium browser tok: prijava, unos, osvežavanje, izmena faze, promena jedinice i odjava — prošlo.
- Mobilni viewport 390 × 844: nema horizontalnog prelivanja cele stranice; široka tabela ima sopstveni skrol.
- Browser provera otkrila povratak na demo pri refresh-u; povezani prikaz sada ostaje otvoren preko `#crm`.

## Granice
Ovo nije produkciona sertifikacija. Osnovno ograničenje prijave po korisničkom imenu nije potpuna zaštita od distribuiranog napada; pri deployment-u dodati ograničenje na reverse proxy-ju, bezbedne HTTPS cookie-je i operativni monitoring. Javna registracija ne postoji. Nalozi i prava se za sada pripremaju administratorskim skriptama; `seed` kreira samo razvojni demo nalog.

Anonimni demo frontend i povezani CRM su različiti prikazi. Demo zadaci ne koriste bazu. Izbor jedinice u demo prikazu nije autorizacija. Povezani API proverava sesiju i prava.

## Prilagođavanje dostavljenom HTML prototipu
- Zajednička React komponenta Shell za navigaciju i zaglavlje demo prikaza i povezanog CRM-a.
- Vizuelno upoređen desktop prikaz sa dostavljenim prototipom; mobilni prikaz proveren na 390 × 844.
- Browser provere: globalna pretraga, odabir demo modula, prikaz svih demo kompanija, tabela, planirane stavke menija i odsustvo horizontalnog prelivanja stranice.
- Ponovo proveren povezani tok: prijava, unos, refresh, izmena, promena jedinice i odjava. Backend model i pravila pristupa nisu menjani.
- Produkcioni build i postojeći frontend testovi prolaze.
- Preuzeti HTML demo prikazuje frontend; trajni CRM zahteva pokrenut API i bazu. Ponude, AI i specijalizovani moduli nisu implementirani preuzimanjem njihovog izgleda.
