# Analyse Rapport - Project Fietsvergoeding

## Deel 1: Functionele Analyse

### 1. Probleemstelling & Scope

**Doel:** Het ontwikkelen van een Proof of Concept (PoC) applicatie voor het correct berekenen en registreren van fietsvergoedingen voor medewerkers in België en Nederland.

**In-Scope:**

- Registratie van fietsritten door medewerkers.
- Automatische validatie van land-specifieke regels (BE: limietcontrole, NL: fiets-type).
- Export functionaliteit van gevalideerde ritten naar een Payroll-compatibel formaat (CSV).
- Beheer van dagelijkse limieten (max. 2 ritten).

**Out-of-Scope:**

- De effectieve financiële uitbetaling (gebeurt in Payroll).
- Authenticatie en gebruikersbeheer (wordt in PoC gesimuleerd via selectie).
- Beheer van fiets leasing contracten.

### 2. Stakeholders

- **Werknemer (Eindgebruiker):** Wilt eenvoudig en snel ritten registreren en direct weten of deze vergoed worden.
- **HR / Payroll (Data Ontvanger):** Heeft een correcte, geconsolideerde lijst van te vergoeden ritten nodig voor de maandelijkse loonverwerking.
- **Finance (Budgethouder):** Wilt zekerheid dat fiscale plafonds (zoals de BE €3.160 limiet) strikt worden nageleefd om boetes te vermijden.

### 3. Systeemkoppelingen

De applicatie functioneert als een "voorportaal" voor het Payroll-systeem.

- **Export-Module:** Er is een expliciete _one-way_ koppeling voorzien via CSV-export. De applicatie genereert `fietsvergoeding_export_YYYYMMDD.csv` die dient als input voor de batch-verwerking in het Payroll-systeem.

### 4. Data Management

Conform de theorie wordt de data strikt gecategoriseerd:

- **Master Data (Stamgegevens):**

  - _Werknemersgegevens:_ ID, Naam, Land.
  - _Vaste Trajecten:_ Omschrijving (bv. "Thuis-Werk"), Afstand in km.
  - _Fiets-types:_ Eigen fiets vs. Bedrijfsfiets (bepaalt belastbaarheid in NL).
  - _Bron:_ Deze data verandert zelden en wordt beheerd door HR.

- **Transactionele Data (Bewegingsgegevens):**

  - _De ritten:_ Datum, Gekoppelde Werknemer, Gekozen Traject, Type (Enkel/Retour), Berekend Bedrag.
  - _Bron:_ Dagelijks gegenereerd door de gebruikersacties.

- **Configuratie Data (Parameters):**
  - _BE_RATE_PER_KM:_ €0,27
  - _BE_YEARLY_LIMIT:_ €3.160,00
  - _NL_RATE_PER_KM:_ €0,23
  - _DEADLINE_DAY:_ 15 (van volgende maand)
  - _Bron:_ Beheerd door App Administrator / Finance (aanpasbaar bij wetswijzigingen).

---

## Deel 2: Technische Analyse

### 1. Architectuur

Er is gekozen voor een **Rapid Application Development (RAD)** aanpak met **Python** en **Streamlit**.

- **Waarom Python?** Krachtige libraries voor datamanagement (Pandas) en berekeningen, wat essentieel is voor de fiscale validaties.
- **Waarom Streamlit?** "Low-code" filosofie. Het stelt ons in staat om de business logica direct te vertalen naar een werkende UI zonder complexe frontend frameworks (React/Angular) op te zetten. Dit past perfect bij het doel van een PoC: snel business value aantonen.

### 2. Technische Keuzes

- **Validatie Logica:**
  De validatie gebeurt _server-side_ (in Python) direct bij het indienen van het formulier. Dit garandeert dat er geen "foute" data in het systeem komt (Garbage In, Garbage Out preventie).

- **State Management (Session State vs. Database):**
  - _PoC Keuze:_ We gebruiken `st.session_state` (in-memory opslag) om ritten tijdelijk op te slaan tijdens de sessie. Dit is voldoende voor demo-doeleinden.
  - _Productie Vereiste:_ In een productie-omgeving **moet** dit vervangen worden door een persistente SQL-database (bv. PostgreSQL). Dit is noodzakelijk voor data-integriteit, audit-logs en het behouden van historie over sessies heen.
