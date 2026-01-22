# 🚲 Fietsvergoeding Applicatie

**Status:** Production Ready PoC  
**Framework:** Python + Streamlit

---

## 📖 Overzicht

Een intelligente applicatie voor het registreren en berekenen van fietsvergoedingen met automatische toepassing van Belgische en Nederlandse fiscale regels.

**Kernfunctionaliteit:**

- ✅ Automatische fiscale validatie (BE: jaar/maand limieten, NL: fietstype)
- ✅ Configureerbare limiet handhaving (BLOCK/CAP modes)
- ✅ Deadline management met uitzonderingen
- ✅ Smart rit-punten systeem (Enkel=1pt, Heen-Terug=2pt)
- ✅ Export naar Payroll met fiscaal statuut

---

## 🚀 Quick Start

### Vereisten

- Python 3.10+
- pip package manager

### Installatie

```bash
# Clone repository
git clone <repository-url>
cd Fietsvergoeding

# Installeer dependencies
pip install -r requirements.txt

# Start applicatie
python -m streamlit run app.py
```

De applicatie opent automatisch in je browser op `http://localhost:8501`

---

## ⚙️ Features per Versie

### v4.4 - Rit-Punten Systeem

- **Intelligente Daglimiet**: Heen-en-Terug telt als 2 punten, Enkel als 1 punt
- **Verhoogt Accuratie**: Voorkomt combinaties zoals 1 Enkel + 1 Heen-Terug (zou 3/2 punten zijn)

### v4.3 - Stakeholder Feedback

- **NL Bedrijfsfiets Configureerbaar**: HR kan belastbare vergoeding instellen voor bedrijfsfietsen
- **Fiscaal Statuut Export**: CSV bevat 'BELAST'/'ONBELAST' kolom voor Payroll
- **Deadline Uitzonderingen**: Per-employee tijdelijke overrides (bijv. bij ziekte)

### v4.2 - Configureerbaar Enforcement

- **BLOCK/CAP Modes**: Keuze tussen harde blokkade of gedeeltelijke vergoeding bij limiet
- **Rit-Punten Dashboard**: Realtime teller met duidelijke feedback
- **Verbeterde UX**: Tooltips en verklarende teksten

### v4.1 - Basis Features

- Enkel/Heen-en-Terug keuze
- Toekomst validatie
- Maand/Jaar limieten (België)
- Historische correcties
- Export processing met ride locking
- Maand-vergrendeling na export

---

## 👥 Gebruikersrollen

### 🚴 **Werknemer**

- Ritten registreren met flexibele trajectkeuze
- Dashboard met realtime budget status
- Historiek bekijken met filter opties
- Deadline warnings bij late correcties

### 👔 **HR Manager**

- **Configuratie**: Tarieven, limieten, enforcement modes instellen
- **Master Data**: Trajecten goedkeuren, werknemers beheren
- **Uitzonderingen**: Deadline overrides toekennen
- **Export**: Kant-en-klare CSV voor Payroll genereren

---

## 📊 Business Rules

### België (BE)

- **Tarief**: €0.27/km (configureerbaar, max €0.35 belastingvrij)
- **Limiet**: Jaar (€3.160) OF Maand (€265) - HR keuze
- **Enforcement**: BLOCK (weigeren) OF CAP (afkappen tot limiet)

### Nederland (NL)

- **Eigen Fiets**: €0.23/km (belastingvrij maximum)
- **Bedrijfsfiets**: €0.00-€0.23/km (configureerbaar, altijd belastbaar)

### Universeel

- **Daglimiet**: Max 2 rit-punten per dag (Enkel=1, Heen-Terug=2)
- **Deadline**: Ritten huidige maand + vorige maand tot deadline (default: 15e)
- **Export Lock**: Geëxporteerde maanden zijn read-only

---

## 🗂️ Datamodel

### Configuratie Data

```python
{
    "BE_RATE": 0.27,
    "BE_LIMIT_TYPE": "YEARLY",  # of "MONTHLY"
    "BE_LIMIT_ENFORCE_MODE": "BLOCK",  # of "CAP"
    "NL_RATE": 0.23,
    "NL_COMPANY_BIKE_RATE": 0.00,  # Configureerbaar
    "DEADLINE_DAY": 15,
    "MAX_RIDES_DAY": 2  # rit-punten
}
```

### Master Data (Read-Only voor Werknemer)

- Werknemers: ID, Naam, Land, Fietstype
- Trajecten: Naam, Afstand (km) - Goedgekeurd door HR

### Transactionele Data

- Ritten: Datum, Traject, Type (Enkel/Heen-Terug), Bedrag
- Status: Processed (na export), Fiscal Status (BELAST/ONBELAST)

---

## 📤 Export Workflow

1. **HR triggert export** via Dashboard → Export tab
2. **Systeem genereert CSV** met:
   - Werknemer ID & Naam
   - Totaal kilometers & Bedrag
   - **Fiscaal Statuut** (BELAST/ONBELAST)
   - Timestamp in filename
3. **Ritten worden gemarkeerd** als `processed=True`
4. **Maand wordt vergrendeld** tegen wijzigingen

### CSV Voorbeeld

```csv
date;employee_id;employee_name;distance;amount;fiscal_status
2026-01-22;103;Sophie de Vries;20;3.00;BELAST
2026-01-22;102;Kees Jansen;30;6.90;ONBELAST
```

---

## 🧪 Testing

### Test Scenario's

**Rit-Punten Validatie:**

```
0/2 punten + Enkel (1pt) = ✅ OK (1/2)
0/2 punten + Heen-Terug (2pt) = ✅ OK (2/2)
1/2 punten + Enkel (1pt) = ✅ OK (2/2)
1/2 punten + Heen-Terug (2pt) = ❌ GEWEIGERD (zou 3/2 zijn)
```

**BE Limiet Enforcement:**

- BLOCK mode: Rit volledig geweigerd bij overschrijding
- CAP mode: €20 van €27 vergoed als €20 binnen limiet past

**Deadline Exceptions:**

- Normaal: Ritten na 15e geblokkeerd voor vorige maand
- Met exception: Ritten tot exception datum toegestaan

---

## 🏗️ Architectuur

### Tech Stack

- **Backend**: Python 3.10+ (Business Logic)
- **Frontend**: Streamlit 1.28+ (Rapid UI)
- **Data Processing**: Pandas (Export generatie)
- **State Management**: st.session_state (PoC - in-memory)

### Separation of Concerns

- **UI Layer**: `render_hr_dashboard()`, `render_employee_portal()`
- **Business Logic**: `validate_ride_submission()`, `calculate_period_total()`
- **Data Layer**: Session state met duidelijke data categorieën

---

## 🔮 Productie Roadmap

| Aspect          | PoC Status                | Productie Vereiste                     |
| --------------- | ------------------------- | -------------------------------------- |
| **Database**    | In-memory (session_state) | PostgreSQL/MySQL met persistentie      |
| **Auth**        | Simulatie dropdown        | Azure AD / SSO integratie              |
| **Hosting**     | Localhost                 | Docker container op Azure App Service  |
| **Concurrency** | Single user               | Multi-user met database locking        |
| **Backup**      | Geen                      | Dagelijkse backups + disaster recovery |

### Migratie Inschatting

- **Business Logic**: ✅ Ongewijzigd herbruikbaar
- **Data Layer**: ⚠️ Refactor naar Repository pattern (~2-3 dagen)
- **UI Layer**: ✅ Minimale aanpassingen

---

## 📚 Documentatie

- **Functionele Analyse**: Volledige requirements en business rules
- **User Stories**: Gedetailleerde acceptatiecriteria per feature
- **Walkthrough**: Demo recordings en test scenarios

---

## 📄 License

Proof of Concept - Internal Use Only

---
