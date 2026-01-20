Context: Project Fietsvergoeding (Proof of Concept)

1. Projectbeschrijving
   We bouwen een Proof of Concept (PoC) voor een applicatie voor fietsvergoedingen. De app wordt gebruikt door medewerkers in België en Nederland om hun woon-werkverkeer te registreren. De focus ligt op de correcte toepassing van fiscale regels per land en validatie van invoer.

Doel van de PoC: Een werkend prototype tonen waarin een gebruiker ritten kan registreren, waarbij het systeem automatisch berekent of dit toegelaten is en wat de vergoeding is.

2. Business Regels (Cruciaal voor Logica)
   Algemeen (Alle gebruikers)
   Registratie: Een gebruiker kiest een datum en een traject.

Beperking: Maximaal 2 ritten (trajecten) per dag.

Combinaties: Een gebruiker mag 2 verschillende trajecten op 1 dag combineren (bv. 's ochtends traject A, 's middags traject B).

Deadline: Ritten mogen niet ingevoerd worden na de 15e van de volgende maand.

Specifiek: België (BE)
Vergoeding: Standaard €0,27 per km (tussen €0,10 en €0,35 wettelijk).

Limiet: Er geldt een fiscaal maximum van €3.160,00 per jaar.

Validatie: Zodra het totaalbedrag (huidig + nieuwe rit) de €3.160 overschrijdt, moet het systeem de invoer blokkeren of waarschuwen.

Specifiek: Nederland (NL)
Vergoeding: Maximaal €0,23 onbelast. Alles daarboven is belast.

Fietsstatus:

Eigen fiets: Vergoeding is onbelast (tot €0,23).

Bedrijfsfiets (Lease): Geen onbelaste kilometervergoeding mogelijk (vergoeding = €0).

3. Gewenste Data Structuur (Mock Data)
   Gebruik deze dummy-data in de code om de applicatie te testen zonder database:

Gebruikers (Employees):

Jean (BE):

Land: België

Reeds vergoed dit jaar: €3.140,00 (Vlakbij de limiet!)

Traject A: Thuis-Werk (25 km)

Kees (NL - Eigen fiets):

Land: Nederland

Fiets: Eigen fiets

Traject A: Thuis-Werk (15 km)

Sophie (NL - Bedrijfsfiets):

Land: Nederland

Fiets: Bedrijfsfiets

Traject A: Thuis-Werk (10 km)

4. Technische Stack voor de PoC
   Taal: Python

Framework: Streamlit (voor snelle UI en data visualisatie) of een eenvoudige HTML/JS/Flask opzet.

Architectuur:

Input: Selectiebox voor medewerker (simulatie login).

Formulier: Datum kiezer, Traject selectie (Dropdown), Checkbox "Heen/Terug".

Validatie Logica: Functie die checkt of de regels (BE limiet / NL fiets) worden nageleefd.

Output: Toon direct het berekende bedrag en de nieuwe totaalstand. Toon een rode foutmelding als de limiet (BE) overschreden wordt.

5. Opdracht voor Copilot
   Genereer de code voor deze applicatie. Zorg voor:

Een class of dictionary structuur voor de Employee en Ride data.

Logica die checkt: if country == 'BE' and total > 3160: Block.

Logica die checkt: if country == 'NL' and bike_type == 'Company': Rate = 0.

Een simpele interface waarin ik als "Jean" een rit kan toevoegen waardoor ik over de limiet ga (om de validatie te testen).

Een "Export" knop die simuleert dat de data naar Payroll (CSV) gaat.
