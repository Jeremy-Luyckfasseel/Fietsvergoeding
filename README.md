# 🚲 Fietsvergoeding PoC

Proof of Concept voor een fietsvergoeding applicatie voor België en Nederland, gebouwd met Python en Streamlit.

## Functionaliteit

Deze applicatie demonstreert de volgende business regels:

- **België 🇧🇪**: Validatie van fiscale limiet (€3.160/jaar) en berekening (€0,27/km).
- **Nederland 🇳🇱**: Onderscheid tussen 'Eigen fiets' (onbelast €0,23/km) en 'Bedrijfsfiets' (geen vergoeding).
- **Algemeen**:
  - Maximale invoer van 2 ritten per dag.
  - Deadline controle (15e van de volgende maand).
  - Export functionaliteit naar CSV (Payroll simulatie).

## Installatie & Gebruik

### Vereisten

- Python 3.8+
- pip

### Installatie

1.  Installeer de benodigde packages:
    ```bash
    pip install -r requirements.txt
    ```

### Applicatie Starten

1.  Start de Streamlit server:
    ```bash
    streamlit run app.py
    ```
2.  De applicatie opent automatisch in je browser (meestal op `http://localhost:8501`).

## Test Scenario's

Gebruik de volgende gebruikers in de dropdown om de validatie te testen:

1.  **Jean (BE)**:

    - Heeft al €3.140 vergoed gekregen (limiet is €3.160).
    - _Test_: Voeg een rit toe van > 40km (heen+terug) om de limiet te overschrijden en de validatie foutmelding te zien.

2.  **Sophie (NL - Bedrijfsfiets)**:

    - _Test_: Voeg een rit toe. De vergoeding zal €0,00 blijven omdat ze een bedrijfsfiets heeft.

3.  **Kees (NL - Eigen fiets)**:
    - _Test_: Voeg een rit toe. De vergoeding wordt berekend aan €0,23/km.
