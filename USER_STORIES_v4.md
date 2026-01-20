# Technical User Stories: Fietsvergoeding Applicatie

**Versie:** 4.0 (Aligned met Functional Analysis v2.0)
**Status:** Ready for Development
**Scope:** MVP + Advanced Compliance Features

---

## 1. Context & Datamodel (Voor Developer)

_Gebruik deze definities om de applicatiestatus te begrijpen._

- **Configuratie Instellingen:**
  - `BE_LIMIT_TYPE`: Keuze tussen "YEARLY" of "MONTHLY".
  - `DEADLINE_DAY`: Dag van de maand (bv. 12) waarop de vorige maand sluit.

- **Rit Status:**
  - `processed`: Boolean. Indien `True`, is de rit geëxporteerd naar payroll en mag deze niet meer gewijzigd worden.

---

## 2. User Stories

### US-01: Dashboard, Historiek & Status Inzicht

**Als** medewerker,
**Wil ik** bij het inloggen direct mijn budgetstatus zien en mijn ritten uit het verleden kunnen raadplegen,
**Zodat** ik weet of ik nog actie moet ondernemen voor de deadline.

- **Acceptatie Criteria:**
  - Toon Huidig Maandtotaal (KM + Bedrag).
  - **Dynamische Limiet (BE):** Toon voortgangsbalk (Jaar of Maand) en waarschuw bij >90% verbruik.
  - **Deadline Reminder:** Toon een opvallende melding als de deadline voor de vorige maand **binnen 5 dagen** verstrijkt.
  - **Rit Historiek:**
    - Tabel met alle geregistreerde ritten.
    - **Filter:** Dropdown om te filteren op specifieke maanden.
    - **Status:** Visuele indicator per rit (bv. ⏳ Ingediend / ✅ Uitbetaald).

---

### US-02: Ritregistratie & Flexibiliteit

**Als** flexibele pendelaar,
**Wil ik** tot 2 ritten per dag kunnen registreren, eventueel met verschillende trajecten,
**Zodat** mijn ochtendrit (heen) en avondrit (terug) correct vergoed worden, zelfs als ze verschillen.

- **Acceptatie Criteria:**
  - Selectie van datum, traject (uit dropdown) en type (Enkel/Heen-en-terug).
  - Validatie: Maximaal 2 entries per datum toegestaan.
  - Validatie: Totaal aantal km per dag mag niet onlogisch hoog zijn (bv. > 200km waarschuwing).

---

### US-03: Tijdslot & Correctie Periode (Smart Validation)

**Als** medewerker,
**Wil ik** ritten kunnen invoeren voor de huidige maand én nog correcties doen voor de vorige maand,
**Zodat** ik niet gestraft word als ik mijn administratie een paar dagen later doe.

- **Acceptatie Criteria:**
  - **Rule 1 (Current):** Datums in de _huidige_ maand zijn altijd toegelaten.
  - **Rule 2 (Correction Window):** Datums in de _vorige_ maand zijn toegelaten INDIEN `Vandaag <= DEADLINE_DAY` (bv. de 12e).
  - **Rule 3 (History):** Datums ouder dan de vorige maand zijn geblokkeerd.
  - **Rule 4 (Export Lock):** Als een maand al de status 'Exported' heeft, is invoer altijd geblokkeerd, ongeacht de datum.

---

### US-04: Fiscale Limiet Validatie (België)

**Als** HR Manager,
**Wil ik** dat het systeem invoer blokkeert op basis van onze gekozen bedrijfslimiet (Maand of Jaar),
**Zodat** we conform de fiscale afspraken blijven.

- **Acceptatie Criteria:**
  - Check bij invoer het land van de medewerker. Indien 'BE':
    - Haal setting `BE_LIMIT_TYPE` op.
    - Bereken het relevante totaal (huidige maand of huidig jaar) + nieuwe ritbedrag.
    - Indien `Totaal > Limiet`: Blokkeer opslaan en toon melding: _"Limiet overschreden. Resterend budget: €X"_.

---

### US-05: Fiscale Regels Nederland

**Als** Nederlandse medewerker,
**Wil ik** dat de vergoeding correct berekend wordt op basis van mijn fiets-type,
**Zodat** ik weet of mijn vergoeding belast of onbelast is.

- **Acceptatie Criteria:**
  - Indien `Bike_Type == 'Company'` (Lease): Zet tarief automatisch op €0,00 (of configureerbaar laag tarief). Toon info-icoon: _"Bedrijfsfiets = Geen onbelaste km-vergoeding"_.
  - Indien `Bike_Type == 'Own'`: Reken met standaard NL-tarief (max €0,23).

---

### US-06: Export & Dubbele Betaling Preventie

**Als** Payroll Officer,
**Wil ik** een export draaien die de ritten markeert als 'verwerkt',
**Zodat** medewerkers niet per ongeluk volgende maand opnieuw uitbetaald worden.

- **Acceptatie Criteria:**
  - Actie: Knop "Genereer Payroll Export" (zichtbaar voor Admin).
  - Scope: Selecteer alle ritten met status `processed = False`.
  - **Processing:**
    1. Genereer CSV met tijdstempel in de bestandsnaam (bv. `payroll_batch_1_20260119_213045.csv`).
    2. Update deze ritten in de database: zet `processed = True`.
    3. Link deze ritten aan een uniek `batch_id`.
  - UI: Toon in de export-historiek hoeveel ritten er in deze batch zaten.

---

### US-07: Configuratie Beheer

**Als** HR Admin,
**Wil ik** de limiet-types en deadline dag kunnen wijzigen via een scherm,
**Zodat** ik geen IT'er nodig heb als het beleid verandert.

- **Acceptatie Criteria:**
  - Settings scherm met:
    - Dropdown: Limit Type (Monthly/Yearly).
    - Slider/Input: Deadline Day (1-28).
    - Inputs: Bedragen per km (BE/NL).
  - Wijziging is direct actief voor nieuwe invoer.

---

## 3. Technische Opmerking voor Implementatie

- **State Management:** Gebruik Streamlit `st.session_state` om de ritten, users en settings te bewaren tijdens de sessie.
- **Persistency:** Voor de PoC is het voldoende als de data reset bij een herstart, maar de logica (validatie/processing) moet wel functioneel werken tijdens de demo.

---

## 4. Implementatie Status (v4.0)

| User Story                            | Status      | Implementatie                                                                                                              |
| ------------------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------- |
| US-01: Dashboard & Status Inzicht     | ✅ Compleet | [`render_employee_portal()`](file:///c:/Users/luyck/OneDrive/Documenten/Github/Fietsvergoeding/app.py#L445-L549)           |
| US-02: Ritregistratie & Flexibiliteit | ✅ Compleet | Max 2 ritten/dag gevalideerd                                                                                               |
| US-03: Tijdslot & Correctie Periode   | ✅ Compleet | [`validate_ride_submission()`](file:///c:/Users/luyck/OneDrive/Documenten/Github/Fietsvergoeding/app.py#L117-L145)         |
| US-04: Fiscale Limiet Validatie (BE)  | ✅ Compleet | Maand/Jaar logica geïmplementeerd                                                                                          |
| US-05: Fiscale Regels Nederland       | ✅ Compleet | Bedrijfsfiets = €0,00 automatisch                                                                                          |
| US-06: Export & Dubbele Betaling      | ✅ Compleet | [`render_hr_dashboard()`](file:///c:/Users/luyck/OneDrive/Documenten/Github/Fietsvergoeding/app.py#L342-L443) - Export tab |
| US-07: Configuratie Beheer            | ✅ Compleet | Volledig configureerbaar via UI                                                                                            |

---

**Zie ook:**

- 📄 [Implementation Plan](file:///C:/Users/luyck/.gemini/antigravity/brain/ebb77674-187a-4d47-9e77-bdad5b09c68b/implementation_plan.md)
- 📄 [Walkthrough v4.0](file:///C:/Users/luyck/.gemini/antigravity/brain/ebb77674-187a-4d47-9e77-bdad5b09c68b/walkthrough.md)
- 🚀 [Live Applicatie](http://localhost:8501)
