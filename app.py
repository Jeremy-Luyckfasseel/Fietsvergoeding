"""
Fietsvergoeding PoC v4.1 - Enhanced Edition
=============================================
Version: 4.1 (Compliant with Updated Functional Analysis)
Author: Antigravity AI

Beschrijving:
Deze applicatie berekent fietsvergoedingen met strikte scheiding tussen HR (Configuratie/Master Data)
en Werknemers (Transactionele Data).

Nieuwe Features v4.1:
- **Enkel/Retour keuze**: Medewerkers kunnen kiezen tussen enkele rit of heen-en-terug
- **Toekomst validatie**: Geen ritten in de toekomst toegestaan
- Keuze tussen maandelijkse en jaarlijkse limieten (België)
- Historische correcties (huidige maand + vorige maand tot deadline)
- Export processing met ride marking om dubbele betalingen te voorkomen
- Export geschiedenis tracking
- Verbeterde employee portal met realtime totalen en status dashboard
- Maand-vergrendeling na export

Architectuur & Data Management:
1. Configuratie Data: Tarieven, limieten en deadline (beheerd door HR).
2. Master Data: Werknemers en hun vaste trajecten (Verklaring op Eer).
3. Transactionele Data: De effectieve ritten (gegenereerd door werknemers).
4. Export History: Logging van exports naar Payroll.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

# =============================================================================
# 1. STATE MANAGEMENT (In-Memory Database)
# =============================================================================

def init_session_state():
    """
    Initialiseert de applicatie state.
    Simuleert een database met 3 tabellen: Config, Users (Master), Rides (Transactions).
    """
    # 1. CONFIGURATIE DATA (Standaard waarden, aanpasbaar door HR)
    if "config" not in st.session_state:
        st.session_state.config = {
            "BE_RATE": 0.27,
            "BE_LIMIT_TYPE": "YEARLY",  # NEW: YEARLY or MONTHLY
            "BE_YEARLY_LIMIT": 3160.00,
            "BE_MONTHLY_LIMIT": 265.00,  # NEW: ~3160/12
            "NL_RATE": 0.23,
            "DEADLINE_DAY": 15,
            "MAX_RIDES_DAY": 2
        }

    # 2. MASTER DATA (Werknemers & Vaste Trajecten)
    if "employees" not in st.session_state:
        st.session_state.employees = {
            "Jean (BE)": {
                "id": 101,
                "name": "Jean Dupont",
                "country": "BE",
                "bike_type": "own",
                "current_year_total": 3140.00,
                "trajectories": {"Thuis-Werk (Brussel)": 25} # VASTE AFSTAND (Verklaring op Eer)
            },
            "Kees (NL - Eigen fiets)": {
                "id": 102,
                "name": "Kees Jansen",
                "country": "NL",
                "bike_type": "own",
                "current_year_total": 500.00,
                "trajectories": {"Thuis-Werk (Utrecht)": 15}
            },
            "Sophie (NL - Bedrijfsfiets)": {
                "id": 103,
                "name": "Sophie de Vries",
                "country": "NL",
                "bike_type": "company",
                "current_year_total": 0.00,
                "trajectories": {"Thuis-Werk (Amsterdam)": 10}
            }
        }

    # 3. TRANSACTIONELE DATA (Ritten)
    if "rides" not in st.session_state:
        st.session_state.rides = []
    
    # 4. EXPORT HISTORY (Logging van exports naar Payroll)
    if "export_history" not in st.session_state:
        st.session_state.export_history = []

# =============================================================================
# 2. BUSINESS LOGIC (Core Domain)
# =============================================================================

def calculate_period_total(employee_id, start_date, end_date):
    """
    Berekent het totaal bedrag voor een specifieke periode.
    Gebruikt voor maand- en jaarlimiet controles.
    """
    total = 0.0
    for ride in st.session_state.rides:
        if ride["employee_id"] == employee_id:
            if start_date <= ride["date"] <= end_date:
                total += ride["amount"]
    return total

def is_month_exported(date_obj):
    """
    Controleert of een maand al geëxporteerd is (en dus read-only moet zijn).
    """
    for export in st.session_state.export_history:
        if export["period_start"] <= date_obj <= export["period_end"]:
            return True
    return False

def validate_ride_submission(employee, date_obj, trajectory_name, ride_type):
    """
    Valideert een rit tegen de HUIDIGE configuratie regels.
    Nieuwe versie: Ondersteunt maand/jaar limieten, historische correcties, export locking, en single/return trips.
    """
    cfg = st.session_state.config
    msgs = []
    is_valid = True
    
    # Haal vaste afstand op uit Master Data (Niet user input!)
    distance = employee["trajectories"][trajectory_name]
    
    # 0. Toekomst Check (NIEUW v4.1)
    if date_obj > date.today():
        return False, ["❌ Je kan geen ritten in de toekomst registreren."], 0.0
    
    # 1. Export Lock Check (Nieuwe Regel)
    if is_month_exported(date_obj):
        return False, ["❌ Deze maand is al geëxporteerd en kan niet meer gewijzigd worden."], 0.0
    
    # 2. Tijdvenster Validatie (Huidige maand + Vorige maand tot deadline)
    today = date.today()
    current_month_start = date(today.year, today.month, 1)
    
    # Bereken vorige maand
    if today.month == 1:
        previous_month_start = date(today.year - 1, 12, 1)
    else:
        previous_month_start = date(today.year, today.month - 1, 1)
    
    # Deadline voor vorige maand
    deadline_previous_month = date(today.year, today.month, cfg["DEADLINE_DAY"])
    
    # Logica:
    # - Huidige maand: altijd toegestaan
    # - Vorige maand: alleen tot deadline van huidige maand
    # - Ouder dan vorige maand: niet toegestaan
    if date_obj >= current_month_start:
        # Huidige maand - OK
        pass
    elif date_obj >= previous_month_start and today <= deadline_previous_month:
        # Vorige maand voor deadline - OK
        msgs.append(f"ℹ️ Let op: je corrigeert een rit uit de vorige maand (deadline: {deadline_previous_month})")
    else:
        # Te oud of na deadline
        return False, [f"❌ Deze datum kan niet meer worden ingevoerd (alleen huidige + vorige maand tot {deadline_previous_month})"], 0.0

    # 3. Daglimiet Check (PO Requirement: Hard Block at 2)
    rides_today = [r for r in st.session_state.rides 
                   if r["employee_id"] == employee["id"] and r["date"] == date_obj]
    if len(rides_today) >= cfg["MAX_RIDES_DAY"]:
        return False, ["❌ Je hebt het maximum van 2 ritten voor deze datum bereikt."], 0.0

    # 4. Berekening (NU MET KEUZE ENKEL/RETOUR - v4.1)
    factor = 2 if ride_type == "Heen-en-Terug" else 1
    total_km = distance * factor
    amount = 0.0
    
    if employee["country"] == "BE":
        amount = total_km * cfg["BE_RATE"]
        
        # Fiscale Limiet Check (NU MET MAAND/JAAR KEUZE!)
        if cfg["BE_LIMIT_TYPE"] == "MONTHLY":
            # Bereken maand totaal
            month_start = date(date_obj.year, date_obj.month, 1)
            if date_obj.month == 12:
                month_end = date(date_obj.year, 12, 31)
            else:
                next_month = date_obj.month + 1
                month_end = date(date_obj.year, next_month, 1) - relativedelta(days=1)
            
            month_total = calculate_period_total(employee["id"], month_start, month_end)
            
            if (month_total + amount) > cfg["BE_MONTHLY_LIMIT"]:
                return False, [f"❌ Maandelijkse limiet (€{cfg['BE_MONTHLY_LIMIT']:.2f}) overschreden!"], 0.0
        else:  # YEARLY
            # Bereken jaar totaal
            year_start = date(date_obj.year, 1, 1)
            year_end = date(date_obj.year, 12, 31)
            year_total = calculate_period_total(employee["id"], year_start, year_end)
            
            if (year_total + amount) > cfg["BE_YEARLY_LIMIT"]:
                return False, [f"❌ Jaarlijkse limiet (€{cfg['BE_YEARLY_LIMIT']:.2f}) overschreden!"], 0.0
            
    elif employee["country"] == "NL":
        if employee["bike_type"] == "company":
            amount = 0.0
            msgs.append("ℹ️ Bedrijfsfiets (NL) = €0 vergoeding.")
        else:
            amount = total_km * cfg["NL_RATE"]

    msgs.append(f"✅ Rit gevalideerd: €{amount:.2f} voor {total_km}km")
    return True, msgs, amount

# =============================================================================
# 3. UI LAYOUTS (Role Based)
# =============================================================================

def render_hr_dashboard():
    st.header("👔 HR Admin Dashboard")
    st.markdown("Beheer Configuratie en Master Data.")
    
    tab1, tab2, tab3 = st.tabs(["⚙️ Configuratie", "👥 Medewerkers Beheer", "📊 Export"])
    
    with tab1:
        st.subheader("Systeem Parameters (Configuratie Data)")
        st.info("⚠️ Pas op: Wijzigingen hebben direct effect op nieuwe ritten!")
        
        # Wettelijke grenzen (voor waarschuwingen, geen harde blokkade)
        BE_TAX_FREE_MAX = 0.35  # Wettelijk belastingvrij maximum België
        BE_UNUSUAL_LOW = 0.10   # Ongebruikelijk laag
        NL_TAX_FREE_MAX = 0.23  # Wettelijk belastingvrij maximum Nederland
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### 🇧🇪 België")
            new_be = st.number_input("Tarief BE (€/km)", value=st.session_state.config["BE_RATE"], step=0.01)
            
            # Fiscale waarschuwingen België (geen blokkade!)
            if new_be >= 0.36:  # Boven €0.35 = belastbaar
                st.warning(f"⚠️ **Fiscale waarschuwing:** Dit tarief (€{new_be:.2f}) is hoger dan het wettelijk vrijgestelde maximum van €0.35. Het surplus is belastbaar voor de werknemer!")
            elif new_be < BE_UNUSUAL_LOW:
                st.warning(f"⚠️ **Opmerking:** Dit tarief (€{new_be:.2f}) is ongebruikelijk laag. Het wettelijk minimum advies is €{BE_UNUSUAL_LOW:.2f}.")
            
            # NIEUWE FEATURE: Limiet Type Selectie
            st.markdown("**Fiscale Limiet Type:**")
            new_limit_type = st.radio(
                "Kies limiet type",
                options=["YEARLY", "MONTHLY"],
                index=0 if st.session_state.config["BE_LIMIT_TYPE"] == "YEARLY" else 1,
                horizontal=True,
                help="Bepaalt of het fiscale plafond per maand of per jaar wordt toegepast"
            )
            
            if new_limit_type == "YEARLY":
                new_yearly_limit = st.number_input(
                    "Jaarlijkse Limiet (€)", 
                    value=st.session_state.config["BE_YEARLY_LIMIT"], 
                    step=100.0,
                    help="Maximaal belastingvrij bedrag per kalenderjaar (bv. €3.160)"
                )
                st.caption(f"≈ €{new_yearly_limit/12:.2f}/maand")
            else:  # MONTHLY
                new_monthly_limit = st.number_input(
                    "Maandelijkse Limiet (€)", 
                    value=st.session_state.config["BE_MONTHLY_LIMIT"], 
                    step=10.0,
                    help="Maximaal belastingvrij bedrag per maand (bv. €265)"
                )
                st.caption(f"≈ €{new_monthly_limit*12:.2f}/jaar")
            
        with c2:
            st.markdown("##### 🇳🇱 Nederland")
            new_nl = st.number_input("Tarief NL (€/km)", value=st.session_state.config["NL_RATE"], step=0.01)
            
            # Fiscale waarschuwingen Nederland
            if new_nl >= 0.24:  # Boven €0.23 = belastbaar
                st.warning(f"⚠️ **Fiscale waarschuwing:** Dit tarief (€{new_nl:.2f}) is hoger dan het wettelijk vrijgestelde maximum van €0.23. Het surplus is belastbaar voor de werknemer!")
        
        # NIEUWE FEATURE: Deadline Configuratie
        st.divider()
        st.markdown("##### ⏰ Invoer Deadline")
        new_deadline_day = st.slider(
            "Deadline dag van de maand",
            min_value=1,
            max_value=28,
            value=st.session_state.config["DEADLINE_DAY"],
            help="Deadline voor het invoeren van ritten van de vorige maand (bv. 15 = ritten van december moeten uiterlijk 15 januari worden ingevoerd)"
        )
        st.caption(f"Medewerkers kunnen ritten invoeren voor de huidige maand en de vorige maand tot de {new_deadline_day}e.")
        
        if st.button("💾 Sla Configuratie Op"):
            st.session_state.config["BE_RATE"] = new_be
            st.session_state.config["BE_LIMIT_TYPE"] = new_limit_type
            st.session_state.config["NL_RATE"] = new_nl
            st.session_state.config["DEADLINE_DAY"] = new_deadline_day
            
            # Update limits based on type
            if new_limit_type == "YEARLY":
                st.session_state.config["BE_YEARLY_LIMIT"] = new_yearly_limit
            else:
                st.session_state.config["BE_MONTHLY_LIMIT"] = new_monthly_limit
                
            st.success("✅ Configuratie bijgewerkt!")
            st.rerun()

    with tab2:
        st.subheader("Medewerkers Beheer (Master Data)")
        st.markdown("**PO Requirement:** Alleen HR mag trajecten toevoegen en goedkeuren.")
        
        col_add_emp, col_add_route = st.columns(2)
        
        # LEFT: Add New Employee
        with col_add_emp:
            st.markdown("##### ➕ Nieuwe Medewerker")
            with st.form("add_employee"):
                name = st.text_input("Naam")
                country = st.selectbox("Land", ["BE", "NL"])
                bike = st.selectbox("Type Fiets", ["own", "company"])
                traj_name = st.text_input("Initieel Traject (bv. Thuis-Werk)")
                traj_dist = st.number_input("Afstand (km - Enkel)", min_value=1)
                
                if st.form_submit_button("➕ Voeg Medewerker Toe"):
                    new_key = f"{name} ({country})"
                    if new_key in st.session_state.employees:
                        st.error(f"❌ Medewerker '{new_key}' bestaat al!")
                    else:
                        st.session_state.employees[new_key] = {
                            "id": len(st.session_state.employees) + 100,
                            "name": name,
                            "country": country,
                            "bike_type": bike,
                            "current_year_total": 0.0,
                            "trajectories": {traj_name: traj_dist}
                        }
                        st.success(f"✅ Medewerker {name} toegevoegd!")
                        st.rerun()
        
        # RIGHT: Add Route to Existing Employee
        with col_add_route:
            st.markdown("##### 🛣️ Traject Toevoegen (Bestaande Medewerker)")
            with st.form("add_route"):
                selected_emp = st.selectbox("Selecteer Medewerker", list(st.session_state.employees.keys()))
                new_traj_name = st.text_input("Nieuw Traject Naam")
                new_traj_dist = st.number_input("Afstand (km - Enkel)", min_value=1, key="route_dist")
                
                # Juridische Compliance Check (Visual reminder van business proces)
                declaration_checked = st.checkbox("✓ Verklaring op eer ontvangen en gecontroleerd", value=False)
                
                if st.form_submit_button("🛣️ Traject Goedkeuren"):
                    if not declaration_checked:
                        st.error("❌ Verklaring op eer moet eerst gecontroleerd worden!")
                    elif new_traj_name in st.session_state.employees[selected_emp]["trajectories"]:
                        st.error(f"❌ Traject '{new_traj_name}' bestaat al voor deze medewerker!")
                    else:
                        st.session_state.employees[selected_emp]["trajectories"][new_traj_name] = new_traj_dist
                        st.success(f"✅ Traject '{new_traj_name}' goedgekeurd voor {selected_emp}!")
                        st.rerun()

    with tab3:
        st.subheader("📊 Export naar Payroll")
        
        # Filter onverwerkte ritten
        unprocessed_rides = [r for r in st.session_state.rides if not r.get("processed", False)]
        
        if unprocessed_rides:
            st.success(f"✅ {len(unprocessed_rides)} nieuwe rit(ten) klaar voor export")
            
            # Preview van te exporteren ritten
            df = pd.DataFrame(unprocessed_rides)
            df_display = df.copy()
            df_display["date"] = pd.to_datetime(df_display["date"]).dt.strftime("%d-%m-%Y")
            df_display["distance"] = df_display["distance"].apply(lambda x: f"{x} km")
            df_display["amount"] = df_display["amount"].apply(lambda x: f"€{x:.2f}")
            df_display["rate_applied"] = df_display["rate_applied"].apply(lambda x: f"€{x:.2f}/km")
            
            df_display = df_display.rename(columns={
                "date": "Datum",
                "employee_id": "Medewerker ID",
                "employee_name": "Naam",
                "trajectory": "Traject",
                "distance": "Afstand",
                "amount": "Bedrag",
                "rate_applied": "Tarief"
            })
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            # Totaal bedrag
            total_amount = sum([r["amount"] for r in unprocessed_rides])
            st.metric("Totaal te exporteren bedrag", f"€{total_amount:.2f}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # CSV export met processing
                if st.button("📥 Verwerk Export en Download", type="primary"):
                    # 1. Genereer export file
                    csv = df.to_csv(sep=";", index=False).encode('utf-8')
                    
                    # 2. Bepaal export periode
                    dates = [r["date"] for r in unprocessed_rides]
                    period_start = min(dates)
                    period_end = max(dates)
                    
                    # 3. Maak export batch ID
                    batch_id = len(st.session_state.export_history) + 1
                    export_timestamp = datetime.now()
                    
                    # 4. Markeer alle ritten als verwerkt
                    for ride in st.session_state.rides:
                        if not ride.get("processed", False):
                            ride["processed"] = True
                            ride["export_batch_id"] = batch_id
                            ride["export_timestamp"] = export_timestamp
                    
                    # 5. Log export in geschiedenis
                    st.session_state.export_history.append({
                        "batch_id": batch_id,
                        "export_date": export_timestamp,
                        "period_start": period_start,
                        "period_end": period_end,
                        "ride_count": len(unprocessed_rides),
                        "total_amount": total_amount
                    })
                    
                    st.success(f"✅ Export Batch #{batch_id} verwerkt! Download hieronder:")
                    st.download_button(
                        "⬇️ Download Payroll CSV",
                        csv,
                        f"payroll_batch_{batch_id}_{export_timestamp.strftime('%Y%m%d_%H%M%S')}.csv",
                        "text/csv",
                        key="download_csv"
                    )
                    st.rerun()
            
            with col2:
                st.info("ℹ️ Na verwerking worden deze ritten vergrendeld en niet meer weergegeven.")
        else:
            st.info("✔️ Geen nieuwe ritten om te exporteren. Alle ritten zijn al verwerkt.")
        
        # Export Geschiedenis
        st.divider()
        st.markdown("#### 📜 Export Geschiedenis")
        
        if st.session_state.export_history:
            export_df = pd.DataFrame(st.session_state.export_history)
            export_df["export_date"] = pd.to_datetime(export_df["export_date"]).dt.strftime("%d-%m-%Y %H:%M")
            export_df["period_start"] = pd.to_datetime(export_df["period_start"]).dt.strftime("%d-%m-%Y")
            export_df["period_end"] = pd.to_datetime(export_df["period_end"]).dt.strftime("%d-%m-%Y")
            export_df["total_amount"] = export_df["total_amount"].apply(lambda x: f"€{x:.2f}")
            
            export_df = export_df.rename(columns={
                "batch_id": "Batch #",
                "export_date": "Export Datum",
                "period_start": "Periode Start",
                "period_end": "Periode Eind",
                "ride_count": "Aantal Ritten",
                "total_amount": "Totaal Bedrag"
            })
            
            st.dataframe(export_df, use_container_width=True, hide_index=True)
        else:
            st.caption("Nog geen exports uitgevoerd.")

def render_employee_portal():
    st.header("🚲 Werknemer Portaal")
    
    # Login Simulatie
    user_key = st.selectbox("Kies je account (Simulatie Login)", list(st.session_state.employees.keys()))
    employee = st.session_state.employees[user_key]
    
    # Calculate current month and year totals for this employee
    today = date.today()
    month_start = date(today.year, today.month, 1)
    if today.month == 12:
        month_end = date(today.year, 12, 31)
    else:
        month_end = date(today.year, today.month + 1, 1) - relativedelta(days=1)
    
    year_start = date(today.year, 1, 1)
    year_end = date(today.year, 12, 31)
    
    month_total = calculate_period_total(employee["id"], month_start, month_end)
    year_total = calculate_period_total(employee["id"], year_start, year_end)
    
    # Determine rate
    if employee["country"] == "BE":
        rate = st.session_state.config["BE_RATE"]
    elif employee["bike_type"] == "company":
        rate = 0.00
    else:
        rate = st.session_state.config["NL_RATE"]
    
    # 1. Enhanced Dashboard (Read-Only Master Data + Totals)
    with st.expander("👤 Mijn Dashboard", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Land", employee["country"])
        col2.metric("Fiets", "Bedrijf" if employee["bike_type"] == "company" else "Eigen")
        col3.metric("Tarief", f"€{rate:.2f}/km")
        col4.metric("Deze Maand", f"€{month_total:.2f}")
        
        # For Belgian employees, show limit status
        if employee["country"] == "BE":
            cfg = st.session_state.config
            st.divider()
            st.markdown("##### 📊 Fiscale Limiet Status (België)")
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.metric("Dit Jaar", f"€{year_total:.2f}")
                
            with col_b:
                if cfg["BE_LIMIT_TYPE"] == "YEARLY":
                    limit = cfg["BE_YEARLY_LIMIT"]
                    remaining = limit - year_total
                    progress = year_total / limit if limit > 0 else 0
                    st.metric(f"Jaarlijkse Limiet ({cfg['BE_LIMIT_TYPE']})", f"€{limit:.2f}")
                    
                    if progress >= 0.9:
                        st.warning(f"⚠️ Let op! Je benadert de jaarlijkse limiet. Nog €{remaining:.2f} beschikbaar.")
                    
                    st.progress(progress, text=f"€{remaining:.2f} resterend")
                else:  # MONTHLY
                    limit = cfg["BE_MONTHLY_LIMIT"]
                    remaining = limit - month_total
                    progress = month_total / limit if limit > 0 else 0
                    st.metric(f"Maandelijkse Limiet ({cfg['BE_LIMIT_TYPE']})", f"€{limit:.2f}")
                    
                    if progress >= 0.9:
                        st.warning(f"⚠️ Let op! Je benadert de maandelijkse limiet. Nog €{remaining:.2f} beschikbaar.")
                    
                    st.progress(progress, text=f"€{remaining:.2f} resterend")
        
        # Deadline reminder
        deadline_day = st.session_state.config["DEADLINE_DAY"]
        deadline_date = date(today.year, today.month, deadline_day)
        days_until_deadline = (deadline_date - today).days
        
        if 0 < days_until_deadline <= 5:
            st.warning(f"📅 Let op: Nog {days_until_deadline} dag(en) tot de deadline ({deadline_date}) voor ritten uit de vorige maand!")

    # 2. Rit Registratie (Transactionele Data)
    st.subheader("📝 Nieuwe Rit Registreren")
    with st.form("ride_add"):
        c1, c2 = st.columns(2)
        with c1:
            r_date = st.date_input("Datum", date.today())
        with c2:
            # NIEUW v4.1: Keuze rondrit
            r_type = st.radio("Type Rit", ["Heen-en-Terug", "Enkel"], horizontal=True)
        
        # PO Requirement: Werknemer kan ALLEEN kiezen uit door HR goedgekeurde trajecten
        r_traj = st.selectbox("Traject (Goedgekeurd door HR)", list(employee["trajectories"].keys()))
        
        # Toon dynamische info
        single_dist = employee["trajectories"][r_traj]
        total_dist = single_dist * (2 if r_type == "Heen-en-Terug" else 1)
        st.caption(f"ℹ️ {r_traj}: {single_dist} km x {2 if r_type == 'Heen-en-Terug' else 1} = **{total_dist} km**")
        
        if st.form_submit_button("🚀 Dien In"):
            # Geef r_type mee aan de validatie
            valid, msgs, amount = validate_ride_submission(employee, r_date, r_traj, r_type)
            
            if valid:
                st.session_state.rides.append({
                    "date": r_date,
                    "employee_id": employee["id"],
                    "employee_name": employee["name"],
                    "trajectory": r_traj,
                    "ride_type": r_type,  # Sla het type op
                    "distance": total_dist,
                    "amount": amount,
                    "rate_applied": rate,
                    "processed": False  # NEW: Default to unprocessed
                })
                st.success("✅ Rit geregistreerd!")
                st.rerun()
            else:
                for m in msgs: st.error(m)
    
    # 3. Ride History View
    st.divider()
    st.subheader("📜 Mijn Ritten")
    
    my_rides = [r for r in st.session_state.rides if r["employee_id"] == employee["id"]]
    
    if my_rides:
        # Month filter
        months_with_rides = sorted(list(set([r["date"].strftime("%Y-%m") for r in my_rides])), reverse=True)
        selected_month = st.selectbox(
            "Filter per maand",
            options=["Alle"] + months_with_rides,
            index=0
        )
        
        # Filter rides
        if selected_month != "Alle":
            filtered_rides = [r for r in my_rides if r["date"].strftime("%Y-%m") == selected_month]
        else:
            filtered_rides = my_rides
        
        # Display table
        if filtered_rides:
            df = pd.DataFrame(filtered_rides)
            df_display = df.copy()
            df_display["date"] = pd.to_datetime(df_display["date"]).dt.strftime("%d-%m-%Y")
            df_display["distance"] = df_display["distance"].apply(lambda x: f"{x} km")
            df_display["amount"] = df_display["amount"].apply(lambda x: f"€{x:.2f}")
            df_display["status"] = df_display["processed"].apply(lambda x: "✅ Verwerkt" if x else "⏳ Nieuw")
            
            df_display = df_display.rename(columns={
                "date": "Datum",
                "trajectory": "Traject",
                "distance": "Afstand",
                "amount": "Bedrag",
                "status": "Status"
            })
            
            # Select only relevant columns
            cols_to_show = ["Datum", "Traject", "Afstand", "Bedrag", "Status"]
            st.dataframe(df_display[cols_to_show], use_container_width=True, hide_index=True)
            
            # Summary
            filtered_total = sum([r["amount"] for r in filtered_rides])
            st.metric("Totaal Geselecteerde Periode", f"€{filtered_total:.2f}")
        else:
            st.info("Geen ritten in deze periode.")
    else:
        st.info("Je hebt nog geen ritten geregistreerd.")

# =============================================================================
# 4. MAIN APP ENTRY
# =============================================================================

def main():
    st.set_page_config(page_title="Fietsvergoeding v4.0", layout="wide")
    init_session_state()
    
    # SIDEBAR: Rol Selectie (RBAC Simulatie)
    role = st.sidebar.radio("Log in als:", ("👤 Werknemer", "👔 HR Manager"))
    st.sidebar.divider()
    
    if role == "👔 HR Manager":
        render_hr_dashboard()
    else:
        render_employee_portal()

if __name__ == "__main__":
    main()
