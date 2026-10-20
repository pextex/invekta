# Naracija vodiča glasom Kore

Svih 26 jedinstvenih koraka vodiča sada ima snimak sa izabranim ženskim glasom Kore na srpskom. Izgovoreni uvodi odgovaraju nazivima kartica, uključujući Početnu tablu, Zadatke, Izveštaje i AI uvode za sve brendove.

Tačna evidencija je u `frontend/src/components/tourVoiceManifest.json`: 20 snimaka je napravljeno modelom `gemini-3.8-flash-lite-tts`, a poslednjih šest modelom `gemini-3.8-flash-tts`, uz isti izbor glasa Kore. Drugi model je korišćen nakon što je Lite model vratio HTTP 429 za dnevni besplatni limit. Ne predstavljati ovaj set kao generisan jednim modelom; identitet izabranog glasa je zajednički.

Snimci su u `frontend/src/assets/tour-narration/uniform/`. Vodič koristi jednu mapu snimaka, bez ranijih posebnih uvoda. U HTML demo snimci su ugrađeni i ne zahtevaju poziv servisu tokom reprodukcije. Automatski prelazak i minimizovani vodič zadržani su. Vizuelni predlog Gradient + 3D ostaje odvojen.
