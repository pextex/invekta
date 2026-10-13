# Provera verzije 0.3

## Izvršene provere
- 27 PostgreSQL backend testova: postojeća autentifikacija, novi kontakti i prilike, validacija, CSRF, vlasništvo, izolacija jedinica, FK ograničenja, istorija faza, paginacija, tačni decimalni zbirni iznosi i konflikt verzije.
- Migracija proverena u izdvojenoj test šemi: očuvanje legacy procene, ponovljiv upgrade, kompanija sa nazivom od 200 znakova i downgrade bez gubitka prvobitne kompanije. Test šema se uklanja; razvojna baza se ne briše.
- 2 postojeća frontend testa i TypeScript/Vite produkcioni build.
- Browser tok: kreirana privremena kompanija, unet i izmenjen kontakt, kreirane dve prilike za istu kompaniju, promenjena i izmenjena faza/vrednost, potvrđena istorija i čuvanje posle refresh-a.
- Provereno pamćenje profila, stranice levka i odabrane poslovne jedinice u URL-u; promena jedinice skriva kartice druge jedinice.
- Provereni povezani dashboard, mobilni levak na 390 × 844 bez prelivanja cele stranice i odjava. Široki levak ima sopstveni horizontalni skrol.
- Privremeni browser zapisi uklonjeni po tačnom ID-u i nazivu, zajedno sa svojim kontaktima/prilikama/istorijom. Seed demo podaci nisu brisani.

## Ograničenja
Istorija faza nije potpuna audit evidencija. Odgovorna osoba prilike se nasleđuje iz kompanije; samostalna raspodela prilika nije uvedena. Paginacija kompanija, pretraga kontakata preko cele baze, trajni zadaci i dokumenti ostaju za naredne faze. Kanban koristi izbor faze na kartici, bez drag-and-drop operacije. MVP je razvojni; nije javno objavljen niti spreman za stvarne poslovne podatke.
