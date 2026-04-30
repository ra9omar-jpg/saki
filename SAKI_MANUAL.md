# Saki – Komplet Manual
**AI-assistent for Sakeena | WhatsApp + Microsoft Teams**

---

## Hvad er Saki?

Saki er en AI-assistent der hjælper med at koordinere frivillige i Sakeena. Saki kører på WhatsApp-nummeret **+45 55 22 80 34** og sender beskeder til teams, rykker for svar, holder styr på opgaver og giver Rani et ugentligt overblik — automatisk, uden Rani behøver at gøre noget manuelt.

Saki identificerer sig altid som en AI-assistent og udgiver sig aldrig for at være et menneske.

**Saki kommunikerer:**
- Kort og direkte (2-3 sætninger max)
- Altid på dansk
- Aldrig med emojis
- Afslutter altid med "Saki"
- Lejlighedsvis med en islamisk påmindelse fra Koranen eller Sahih Hadith (kun verificerede citater)

---

## De tre tilstande

Saki har tre tilstande. **Start altid i test.**

### Tilstand 1: Test
- Saki sender KUN til testgrupper Rani selv har oprettet
- Rigtige Sakeena-grupper ignoreres fuldstændigt
- Ingen risiko — prøv alt frit

### Tilstand 2: Shadow
- Saki overvåger de rigtige grupper
- I stedet for at sende direkte sender Saki en kladde til Ranis personlige WhatsApp
- Rani læser kladden og sender den manuelt fra sin gamle telefon (der stadig har Sakis SIM)
- Teamet ser beskeder fra Sakis nummer og tror Saki kører — men Rani har fuld kontrol

### Tilstand 3: Live
- Saki sender automatisk til de rigtige grupper
- Når man skifter til live, kan den gamle telefon ikke længere bruge nummeret i normal WhatsApp
- Dette er en envejsændring — gå til shadow-tilstand FØR man registrerer nummeret hos Meta

**Skift tilstand:** Skriv til Saki med din hemmelige kode, og skriv derefter:
```
set_mode test
set_mode shadow
set_mode live
```

---

## Kontrol-menu (kun Rani)

Rani har en hemmelig kode. Når han skriver den til Saki på WhatsApp, viser Saki en menu med alle kommandoer.

Herefter kan Rani skrive kommandoerne direkte (i 10 minutter efter koden er sendt):

### Tilstand
| Kommando | Hvad den gør |
|----------|-------------|
| `set_mode test` | Skift til test-tilstand |
| `set_mode shadow` | Skift til shadow-tilstand |
| `set_mode live` | Skift til live-tilstand |
| `current_mode` | Vis nuværende tilstand |

### Grupper
| Kommando | Hvad den gør |
|----------|-------------|
| `pause [gruppenavn]` | Stop alle beskeder til en gruppe |
| `resume [gruppenavn]` | Start beskeder igen |
| `broadcast rd [besked]` | Send en akut besked til R&D nu |
| `broadcast marketing [besked]` | Send en akut besked til Marketing nu |

### System
| Kommando | Hvad den gør |
|----------|-------------|
| `status` | Vis hvem der mangler at svare og hvad der er stuck |
| `settings` | Vis alle nuværende indstillinger |
| `shutdown` | Nødstop — Saki er stille indtil du genaktiverer |
| `wake_up` | Genaktiver Saki efter shutdown |
| `check_now` | Synkroniser Microsoft Planner med det samme |
| `stop_islamic_reminders` | Sluk islamiske påmindelser globalt |
| `start_islamic_reminders` | Tænd islamiske påmindelser igen |
| `change_time [gruppe] [HH:MM]` | Ændr planlagt tidspunkt for en besked |
| `help` | Vis menuen igen |

### Test-kommandoer (kun i test- og shadow-tilstand)
| Kommando | Hvad den gør |
|----------|-------------|
| `test_status_update` | Trigger mandagsopdatering med det samme |
| `test_poll` | Trigger ugentlig poll med det samme |
| `test_review_request` | Trigger artikel-reviewanmodning med det samme |
| `force_draft` | Send næste kladde til Rani nu (shadow-tilstand) |

### Hurtig pause
Skriv **`Saki!!!`** (tre udråbstegn) til Saki for at sætte alt på pause i 5 timer.
Saki svarer: *"Forstået, Rani. Jeg er stille i 5 timer. Jeg vågner kl. XX:XX. Saki"*
Efter 5 timer genoptager Saki automatisk.

---

## Alle Sakis funktioner

### Funktion 1 — Pre-send bekræftelse
Inden Saki sender en planlagt gruppebesked, spørger den Rani privat:
*"Hey Rani, hvornår passer det dig at sende [beskrivelse] ud denne uge?"*
Rani svarer med et tidspunkt. Saki sender på det tidspunkt.
Ingen gruppebesked sendes nogensinde uden Ranis godkendelse.

---

### Funktion 2 — Ugentlig workshop-poll
**Hvornår:** Ugentligt, efter Rani bekræfter tidspunkt

Saki sender en poll til Marketing og R&D med spørgsmål om hvornår folk kan til den kommende workshop.
- Rykker ikke-svarende 24 timer efter
- Sender en sidste rykker 12 timer inden afstemningen lukker
- Sender en opsummering af svar til Rani
- Skriver workshop-tid ind i Microsoft Planner

---

### Funktion 3 — Mandags-statusopdatering (R&D)
**Hvornår:** Hver mandag aften

Saki tjekker Microsoft Planner, ser hvem der har hvilke opgaver, og sender en besked til R&D-gruppen:
*"Ahmed – [opgave]. Fatima – [opgave]. Skriv venligst i én linje: Færdig / Halvvejs / Ikke startet / Blokeret af X."*

- Rykker ikke-svarende tirsdag aften
- Sender en sidste rykker onsdag morgen
- Giver Rani en opsummering onsdag morgen med hvem der ikke har svaret
- Opdaterer Planner med status

Marketing-teamet modtager IKKE mandagsopdateringer — de følges via workshops (Funktion 4).

---

### Funktion 4 — Marketing-workshop tracking
**Åbningsmøde:** Saki registrerer hvem der er tildelt hvad + tidsstempel

**Afslutningsmøde (1,5 time senere):** Saki sammenligner hvad der blev lovet med hvad der faktisk blev leveret og rapporterer afvigelser til Rani.

**Mønstre:** Saki tracker hvem der konsekvent lover men ikke leverer, og hvem der kun arbejder under workshops versus selvstændigt — og giver Rani et ugentligt mønstersummary.

---

### Funktion 5 — Ubesvaret spørgsmål-overvågning
Saki overvåger alle gruppe-chats kontinuerligt.

Hvis et spørgsmål er gået ubesvaret i **4+ timer** og der ikke er en aktiv samtale i gang:
1. Saki sender **ét** venligt reminder i gruppen: *"Der blev stillet et spørgsmål tidligere. Kan nogen hjælpe? Saki"*
2. Saki sender **aldrig** mere end ét reminder for samme spørgsmål
3. Hvis spørgsmålet stadig er ubesvaret 24 timer efter, notificerer Saki Rani privat

---

### Funktion 6 — Engagement-tracking og ugentlige indsigter
**Hvornår:** Hver fredag

Saki tracker løbende for hvert teammedlem:
- Har de svaret på polls?
- Har de sendt statusopdatering?
- Har de deltaget i workshops?
- Hvor aktive er de i grupperne?

Fredag sender Saki Rani et privat overblik:
- Hvem er pålidelige og aktive
- Hvem har været stille eller inaktive
- Hvem viser tegn på frafald (lav engagement de seneste 4 uger)

Disse data deles ALDRIG med teamet — kun Rani kan se dem.

---

### Funktion 7 — Workshop-opsummering og næste skridt
**Hvornår:** Efter hvert workshop

Saki laver en kladde med:
- Hvad blev fuldført
- Hvad blev ikke fuldført
- Hvem lovede hvad inden næste møde
- Næste skridt og deadlines

Opsummeringen sendes til Rani FØR den sendes til gruppen. Rani skriver "godkendt" og så sender Saki den.

---

### Funktion 8 — Artikel-review workflow
Hele pipeline for review af artikler fra R&D-teamet:

1. Når en artikel flyttes til "Ready for Review" i Planner → Saki tilføjer den til review-køen
2. **Ugentligt:** Saki sender en besked til Ekspertise Review-gruppen med alle artikler der venter: *"Disse artikler venter på review. Hvem kan tage hvilken?"*
3. Teammedlemmer svarer med artikelnummer de vil tage
4. Saki sender en **privat besked** til revieweren med link, deadline (1 uge) og islamisk påmindelse
5. Saki rykker revieweren 2 dage inden deadline
6. Hvis deadline passeres → Saki notificerer Rani

Hvis en artikel ikke er taget inden 3 dage → Saki sender et venligt ping. Efter yderligere 3 dage → eskalerer til Rani.

---

### Funktion 9 — Microsoft Planner integration
Saki læser og opdaterer Planner automatisk:

| Bucket | Hvad Saki gør |
|--------|--------------|
| To Do | Inkluderer i mandagsopdatering |
| In Progress | Tracker i ugentlig opsummering |
| Ready for Review | Trigger artikel-review workflow |
| Approved | Informerer Rani — klar til publicering |
| Done | Ingen handling |

Planner synkroniseres hvert 15. minut.

---

### Funktion 10 — Kontrol-menu (hemmelig kode)
Se afsnittet "Kontrol-menu" ovenfor.

---

### Funktion 11 — Hurtig pause (Saki!!!)
Se afsnittet "Kontrol-menu" ovenfor.

---

### Funktion 12 — Workshop-opsummering fra optagelser og billeder
Rani kan sende Saki råmateriale fra et workshop:
- **Tekst:** noter eller referat
- **Lydfil:** optagelse af mødet (Saki transskriberer via Whisper)
- **Billede:** foto af whiteboard eller håndskrevne noter (Saki læser via AI Vision)

Saki laver et rent tekstreferat og sender det til Rani:
*"Her er mit referat: [...] Hvilken gruppe skal dette sendes til? (Marketing, R&D, Eksperter, Lærere — eller flere)"*

Rani svarer med gruppenavn(e), og Saki sender til de valgte grupper.
Billeder og lyd videresendes **aldrig** — kun tekst-opsummeringen sendes.

---

### Funktion 13 — Smart spørgsmål-eskalering
Se Funktion 5. Saki er intelligent nok til at skelne:
- Aktiv diskussion i gang → Saki tier stille
- Spørgsmål henligger uden svar → Saki sender ét reminder

---

### Funktion 14 — "Saki, lav en to do"
**Hvem kan bruge den:** Alle i alle grupper

Hvis nogen skriver *"Saki, lav en to do"* (eller lignende) i en gruppe-chat, læser Saki de seneste 2 timers beskeder og laver en liste over:
- Konkrete opgaver (med ansvarlig person hvis nævnt)
- Beslutninger der er truffet
- Åbne spørgsmål der mangler svar

Listen postes direkte i gruppen.

---

### Funktion 15 — Manuel broadcast
Via kontrol-menuen kan Rani sende en akut besked til en gruppe:
```
broadcast rd Website skal være færdig fredag, vi skal bruge alle hænder.
```
Saki sender beskeden til R&D-gruppen med Sakis afsender og signatur, og bekræfter til Rani at den er sendt.

---

### Funktion 16 — Fejlnotifikationer til Rani
Hvis noget fejler (besked kan ikke sendes, API nede, planlagt job crasher) sender Saki øjeblikkeligt en privat besked til Rani:

*"FEJL: mandagsopdatering fejlede kl. 20:03. ConnectionError. Forsøger igen næste kørsel. Saki"*

Kritiske fejl sætter Saki på pause og kræver at Rani skriver "wake_up" for at bekræfte.

---

### Funktion 17 — Mønster-eskalering (gentagne forsømmere)
Saki tracker mønstre stille og privat og eskalerer til Rani:

| Antal missede opdateringer i træk | Hvad Saki gør |
|----------------------------------|--------------|
| 1 | Nævnes i den ugentlige rapport |
| 2 | Saki notificerer Rani privat: "Ahmed har misset 2 mandagsopdateringer i træk." |
| 3 | Stærkere advarsel: "Ahmed har misset 3 mandagsopdateringer i træk. Måske en samtale er nødvendig." |

For artikel-reviews: Hvis nogen tager artikler men ikke leverer 2 gange → udelukkes automatisk fra nye reviewanmodninger indtil de leverer.

---

### Funktion 18 — 1-til-1 beskeder fra teammedlemmer
Hvis et teammedlem skriver direkte til Sakis nummer, svarer Saki som en hjælpsom assistent:

- Besvarer faktuelle spørgsmål (deadlines, hvem har hvilken opgave, workshop-tider)
- Modtager beskeder til Rani: *"Forstået, jeg giver Rani besked. Saki"*
- Godkender, ændrer deadlines eller træffer beslutninger **aldrig** uden Ranis bekræftelse
- Hvis noget kræver Ranis stillingtagen: *"Det skal Rani tage stilling til. Jeg giver ham besked. Saki"*

---

## Islamiske påmindelser

Saki inkluderer lejlighedsvis islamiske påmindelser i store planlagte beskeder. Disse kommer KUN fra en håndkureret database med verificerede Korancitater og Sahih Hadith — Saki genererer aldrig islamisk indhold selv.

**Påmindelser inkluderes i:**
- Mandags-statusopdateringer
- Ugentlige polls
- Workshop-opsummeringer
- Artikel-reviewanmodninger

**Påmindelser inkluderes IKKE i:**
- Hurtige svar
- Bekræftelsesbesked til Rani
- Fejlnotifikationer
- Kontrol-menu
- To-do lister

Rani kan slå islamiske påmindelser fra og til med `stop_islamic_reminders` / `start_islamic_reminders`.

---

## Test-fase og udrulning

### Hvad Rani skal sætte op (én gang)

**Trin 1 — Opret testgrupper (5 minutter)**
På Ranis personlige WhatsApp, opret 4 grupper med Rani + 1-2 betroede personer (kone, bror, nær ven):
- Saki Test – R&D
- Saki Test – Marketing
- Saki Test – Lærere
- Saki Test – Ekspertise

**Trin 2 — Opret test-Planner (10 minutter)**
I Microsoft Planner, opret en plan kaldet "Saki Test Plan" med disse buckets:
- To Do
- In Progress
- Ready for Review
- Approved
- Done

Tilføj et par fake opgaver tildelt Rani og testpersonerne.

**Trin 3 — Tilføj IDs til konfiguration**
Gruppe-IDs fås automatisk første gang nogen skriver i testgrupperne. Disse tilføjes til Sakis `.env` fil.

**Trin 4 — Skift til test-tilstand**
Skriv din hemmelige kode til Saki, derefter: `set_mode test`

---

### Uge 1-2: Test-tilstand

Prøv alle funktioner i testgrupperne:
- [ ] Mandagsopdatering (trigger med `test_status_update`)
- [ ] Ugentlig poll (trigger med `test_poll`)
- [ ] Artikel-review workflow (trigger med `test_review_request`)
- [ ] "Saki, lav en to do" i en testgruppe
- [ ] Send et billede/lydfil til Saki og se workshopreferatet
- [ ] Test hurtig pause: Skriv `Saki!!!`
- [ ] Test nødstop: Skriv kode → `shutdown` → `wake_up`
- [ ] Test broadcast: `broadcast rd Test besked`
- [ ] Tjek at fejlnotifikationer virker
- [ ] Kontroller islamiske påmindelser er korrekte
- [ ] Kontroller dansk sprogbrug og tone

---

### Uge 3-4: Shadow-tilstand

**Hvad der sker i shadow:**
- Sakis SIM sidder stadig i den gamle telefon i normal WhatsApp
- Saki genererer alle beskeder men sender dem til Ranis private nummer som kladder
- Rani læser kladden og sender manuelt fra den gamle telefon til de rigtige grupper
- Teamet ser beskeder fra Sakis nummer og tror Saki kører — men Rani har fuld kontrol

**Skift til shadow:** `set_mode shadow`

**Hvad Rani tester:**
- [ ] Modtag kladder fra Saki og godkend dem manuelt
- [ ] Brug `force_draft` til at få en kladde med det samme
- [ ] Lær hvornår Saki's timing passer til teamets rytme
- [ ] Se reaktioner fra teamet på Sakis tone og indhold
- [ ] Juster eventuelle tidspunkter via `change_time`

---

### Uge 5+: Live-tilstand

Når Rani er tryg med shadow-tilstanden:

1. Registrer +45 55 22 80 34 hos Meta WhatsApp Business Cloud API
2. Den gamle telefon kan herefter **ikke** længere bruge dette nummer i normal WhatsApp
3. Skift tilstand: `set_mode live`
4. Saki sender nu automatisk til alle rigtige grupper

**Teamet oplever ingen forskel** — de har allerede modtaget "Saki"-beskeder i uger.

---

## Vigtige sikkerhedsregler

- Saki sender **aldrig** til rigtige grupper i test-tilstand — dette er en hard-coded sikkerhedsregel
- Saki sender **aldrig** automatisk til rigtige grupper i shadow-tilstand
- Hvis Saki er usikker på om en gruppe er en testgruppe — sender den **ikke**
- Alle tilstandsskift logges med tidsstempel
- Rani kan altid skrive `Saki!!!` for at sætte alt på pause i 5 timer — i alle tilstande

---

## Grupper Saki understøtter

| Intern kode | Gruppe |
|-------------|--------|
| GROUP_RD_MAIN | R&D-teamet |
| GROUP_MARKETING_CORE | Marketing |
| GROUP_TEACHERS | Lærere |
| GROUP_EXPERTISE_REVIEW | Ekspertise Review |
| GROUP_COMMUNITY | Sakeena Community (kun spørgsmålsovervågning) |

Hvis Rani omdøber en gruppe i WhatsApp, er der ingen konsekvenser — Saki bruger interne kodenavne, ikke display-navne.

---

## Pris (estimat)

| Post | Pris |
|------|------|
| Sakis e-SIM (engangs) | Allerede betalt |
| WhatsApp Business Cloud API | 0 kr./md (under 1.000 samtaler/md) |
| Microsoft Graph API | 0 kr. (inkluderet i M365) |
| Hosting (Railway) | 0-35 kr./md |
| Claude AI API (Anthropic) | 10-50 kr./md |
| Database (PostgreSQL) | 0 kr. (inkluderet i hosting) |
| OpenAI Whisper (lyd-transskription, valgfri) | 5-20 kr./md |
| **Total pr. måned** | **~35-105 kr.** |

---

*Saki er bygget til Sakeena — for at give Rani tid til lederskab, indhold og det der virkelig betyder noget.*
*Barakallahu fik, Rani.*
