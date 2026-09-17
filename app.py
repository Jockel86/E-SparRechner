import datetime
import requests
import streamlit as st

# Seitenkonfiguration für PC und mobile Ansicht (iPhone)
st.set_page_config(
    page_title="E-Auto Ersparnisrechner", page_icon="⚡", layout="centered"
)


# Funktion für historische Durchschnittspreise
def get_historical_fuel_average(fuel_type, period):
  if fuel_type == "Diesel":
    if period == "Letzte 3 Monate":
      return 1.74
    elif period == "Letzte 6 Monate":
      return 1.72
    elif period == "Letzte 12 Monate":
      return 1.68
    else:
      return 1.70
  else:  # Benzin (Super E10)
    if period == "Letzte 3 Monate":
      return 1.78
    elif period == "Letzte 6 Monate":
      return 1.75
    elif period == "Letzte 12 Monate":
      return 1.72
    else:
      return 1.75


# Funktion für tagesaktuelle Live-Preise mit manuellem Fallback
def get_live_fuel_price(fuel_type):
  try:
    headers = {"User-Agent": "Mozilla/5.0"}
    url = "https://benzinpreis-aktuell.de/api.v2.php?data=nationwide"
    response = requests.get(url, headers=headers, timeout=3)
    if response.status_code == 200:
      data = response.json()
      if fuel_type == "Diesel":
        return float(data.get("diesel", 1.72))
      else:
        return float(data.get("e10", 1.75))
  except Exception:
    pass

  return 1.72 if fuel_type == "Diesel" else 1.75


# Titel & Autor
st.title("⚡ E-Auto vs. Verbrenner ")
st.write(
    "Vergleiche deine Ladekosten flexibel und berechne, wann sich das"
    " E-Auto amortisiert."
)
st.caption("Entwickelt von Jochen Vortkamp")

# ==========================================
# SESSION STATE INITIALISIERUNG
# ==========================================
if "kwh_val" not in st.session_state:
  st.session_state["kwh_val"] = 250.0
if "strompreis_val" not in st.session_state:
  st.session_state["strompreis_val"] = 0.30
if "pv_aktiv" not in st.session_state:
  st.session_state["pv_aktiv"] = True
if "pv_anteil_val" not in st.session_state:
  st.session_state["pv_anteil_val"] = 50.0
if "pv_preis_val" not in st.session_state:
  st.session_state["pv_preis_val"] = 0.08
if "verbrauch_ev_val" not in st.session_state:
  st.session_state["verbrauch_ev_val"] = 18.0
if "verbrauch_verbrenner_val" not in st.session_state:
  st.session_state["verbrauch_verbrenner_val"] = 7.5
if "kraftstoffpreis_val" not in st.session_state:
  st.session_state["kraftstoffpreis_val"] = 1.75
if "kaufpreis_ev_val" not in st.session_state:
  st.session_state["kaufpreis_ev_val"] = 35000.0
if "restwert_aktiv" not in st.session_state:
  st.session_state["restwert_aktiv"] = True
if "restwert_val" not in st.session_state:
  st.session_state["restwert_val"] = 5000.0
if "praemie_aktiv" not in st.session_state:
  st.session_state["praemie_aktiv"] = False
if "praemie_val" not in st.session_state:
  st.session_state["praemie_val"] = 3000.0
if "zeitraum_text" not in st.session_state:
  st.session_state["zeitraum_text"] = datetime.date.today().strftime("%B %Y")
if "thg_aktiv" not in st.session_state:
  st.session_state["thg_aktiv"] = False
if "thg_wert" not in st.session_state:
  st.session_state["thg_wert"] = 150.0
if "steuer_aktiv" not in st.session_state:
  st.session_state["steuer_aktiv"] = False
if "steuer_verbrenner_wert" not in st.session_state:
  st.session_state["steuer_verbrenner_wert"] = 120.0


# 1. Zeitraum-Auswahl
st.header("1. Abrechnungszeitraum wählen")
zeitraum_modus = st.radio(
    "Wie möchtest du den Zeitraum definieren?",
    ["Monatlich", "Ganzes Jahr", "Gesamt (Individuell)"],
    horizontal=True,
    key="zeitraum_modus_radio",
)

jahres_faktor = 1.0

if zeitraum_modus == "Monatlich":
  st.session_state["zeitraum_text"] = st.text_input(
      "Monat / Zeitraum",
      value=st.session_state["zeitraum_text"],
      key="label_monat",
  )
  st.session_state["kwh_val"] = st.number_input(
      "Im Monat geladene kWh",
      min_value=0.0,
      value=st.session_state["kwh_val"],
      step=10.0,
      format="%.1f",
      key="kwh_monat_input",
  )
  jahres_faktor = 1.0 / 12.0
elif zeitraum_modus == "Ganzes Jahr":
  st.session_state["zeitraum_text"] = st.text_input(
      "Jahr",
      value=str(datetime.date.today().year),
      key="label_jahr",
  )
  st.session_state["kwh_val"] = st.number_input(
      "Im ganzen Jahr geladene kWh",
      min_value=0.0,
      value=3000.0,
      step=100.0,
      format="%.1f",
      key="kwh_jahr_input",
  )
  jahres_faktor = 1.0
else:
  st.session_state["zeitraum_text"] = st.text_input(
      "Bezeichnung (z.B. Gesamter Zeitraum / 3 Jahre)",
      value="Gesamter Zeitraum (z.B. 2 Jahre)",
      key="label_gesamt",
  )
  st.session_state["kwh_val"] = st.number_input(
      "Insgesamt geladene kWh",
      min_value=0.0,
      value=10000.0,
      step=500.0,
      format="%.1f",
      key="kwh_gesamt_input",
  )
  anzahl_jahre = st.number_input(
      "Entspricht einem Zeitraum von (Jahren):",
      min_value=0.25,
      value=2.0,
      step=0.25,
      key="anzahl_jahre_input",
  )
  jahres_faktor = anzahl_jahre

# 2. Verbrenner-Typ & Kraftstoff
st.header("2. Verbrenner-Typ & Kraftstoff")
kraftstoff_art = st.radio(
    "Welchen Verbrenner möchtest du zum Vergleich heranziehen?",
    ["Benzin (Super E10/E5)", "Diesel"],
    horizontal=True,
    key="kraftstoff_art_radio",
)

selected_fuel_short = "Diesel" if "Diesel" in kraftstoff_art else "Benzin"

# 3. Kraftstoffpreis-Quellen & Sofort-Übernahme
st.header("3. Kraftstoffpreis abrufen")

col_btn1, col_btn2 = st.columns(2)

with col_btn1:
  if st.button("🌐 Tagesaktuellen Live-Preis", use_container_width=True):
    live_preis = get_live_fuel_price(selected_fuel_short)
    st.session_state["kraftstoffpreis_val"] = live_preis
    st.success(f"Live-Preis übernommen: Ø {live_preis:.2f} €/l")
    st.rerun()

with col_btn2:
  hist_wahl = st.selectbox(
      "Historischer Schnitt:",
      [
          "Aktueller Trend",
          "Letzte 3 Monate",
          "Letzte 6 Monate",
          "Letzte 12 Monate",
      ],
      label_visibility="collapsed",
      key="hist_wahl_select",
  )
  if st.button("📊 Historischen Schnitt", use_container_width=True):
    hist_preis = get_historical_fuel_average(selected_fuel_short, hist_wahl)
    st.session_state["kraftstoffpreis_val"] = hist_preis
    st.success(f"Historischer Schnitt übernommen: Ø {hist_preis:.2f} €/l")
    st.rerun()

st.number_input(
    f"Ø {selected_fuel_short}-Preis (€/Liter)",
    min_value=0.0,
    step=0.01,
    format="%.2f",
    key="kraftstoffpreis_val",
    help=(
        "Wird über Buttons direkt übernommen oder kann manuell angepasst"
        " werden."
    ),
)

# 4. Tarife, Verbrauch & Kaufpreis
st.header("4. Tarife, Verbrauch & Kaufpreis")

st.session_state["strompreis_val"] = st.number_input(
    "Ø Netz-Strompreis (€/kWh)",
    min_value=0.0,
    value=st.session_state["strompreis_val"],
    step=0.01,
    format="%.3f",
    help="Dein durchschnittlicher Strompreis aus dem Netz.",
    key="strompreis_input_field",
)

st.session_state["pv_aktiv"] = st.checkbox(
    "Eigene PV-Anlage (Solarstrom) einbeziehen",
    value=st.session_state["pv_aktiv"],
    help="Berücksichtige einen prozentualen Anteil an günstigem PV-Strom.",
)

if st.session_state["pv_aktiv"]:
  col_pv1, col_pv2 = st.columns(2)
  with col_pv1:
    st.session_state["pv_anteil_val"] = st.slider(
        "PV-Anteil am Ladestrom (%)",
        min_value=0.0,
        max_value=100.0,
        value=st.session_state["pv_anteil_val"],
        step=5.0,
        key="pv_anteil_slider",
    )
  with col_pv2:
    st.session_state["pv_preis_val"] = st.number_input(
        "PV-Strompreis / entgangene Vergütung (€/kWh)",
        min_value=0.0,
        value=st.session_state["pv_preis_val"],
        step=0.01,
        format="%.3f",
        help=(
            "Kosten pro selbstgenutzter kWh (z.B. Einspeisevergütung als"
            " Opportunitätskosten)."
        ),
        key="pv_preis_input",
    )

st.session_state["verbrauch_ev_val"] = st.number_input(
    "E-Auto Verbrauch (kWh / 100 km)",
    min_value=0.0,
    value=st.session_state["verbrauch_ev_val"],
    step=0.5,
    help="Durchschnittlicher Verbrauch deines E-Autos.",
    key="verbrauch_ev_input_field",
)

if (
    st.session_state["verbrauch_verbrenner_val"] == 7.5
    and selected_fuel_short == "Diesel"
):
  st.session_state["verbrauch_verbrenner_val"] = 6.0

st.session_state["verbrauch_verbrenner_val"] = st.number_input(
    "Verbrenner Vergleichs-Verbrauch (l / 100 km)",
    min_value=0.0,
    value=st.session_state["verbrauch_verbrenner_val"],
    step=0.5,
    help="Was ein vergleichbarer Verbrenner auf 100 km verbraucht.",
    key="verbrauch_verbrenner_input_field",
)

# 5. THG-Quote, Kfz-Steuer & Amortisation (inkl. Restwert / Prämie)
st.header("5. THG-Quote, Kfz-Steuer & Amortisation")

st.session_state["thg_aktiv"] = st.checkbox(
    "THG-Quote einrechnen (jährliche Prämie für E-Autos)",
    value=st.session_state["thg_aktiv"],
)
if st.session_state["thg_aktiv"]:
  st.session_state["thg_wert"] = st.number_input(
      "Erwartete THG-Prämie pro Jahr (€)",
      min_value=0.0,
      value=st.session_state["thg_wert"],
      step=10.0,
      help=(
          "Erlös, den du jährlich durch den Verkauf deiner THG-Quote"
          " erhältst."
      ),
  )

st.session_state["steuer_aktiv"] = st.checkbox(
    "Kfz-Steuerbefreiung für E-Autos berücksichtigen",
    value=st.session_state["steuer_aktiv"],
    help=(
        "Reine Elektroautos sind in Deutschland aktuell von der Kfz-Steuer"
        " befreit."
    ),
)
if st.session_state["steuer_aktiv"]:
  st.session_state["steuer_verbrenner_wert"] = st.number_input(
      "Kfz-Steuer des Vergleichs-Verbrenners pro Jahr (€)",
      min_value=0.0,
      value=st.session_state["steuer_verbrenner_wert"],
      step=10.0,
      help=(
          "Was ein vergleichbarer Verbrenner jährlich an Kfz-Steuer kostet"
          " (E-Auto zahlt 0 €)."
      ),
  )

st.subheader("Amortisations-Berechnung (Kaufpreis & Abzüge)")
st.session_state["kaufpreis_ev_val"] = st.number_input(
    "E-Auto Anschaffungspreis / Bruttokaufpreis (€)",
    min_value=0.0,
    value=st.session_state["kaufpreis_ev_val"],
    step=500.0,
    format="%.2f",
    help="Bruttokaufpreis des E-Autos.",
    key="kaufpreis_ev_input_field",
)

st.session_state["restwert_aktiv"] = st.checkbox(
    "Inzahlungnahme / Restwert des alten Fahrzeugs abziehen",
    value=st.session_state["restwert_aktiv"],
)
if st.session_state["restwert_aktiv"]:
  st.session_state["restwert_val"] = st.number_input(
      "Erlös / Restwert Altfahrzeug (€)",
      min_value=0.0,
      value=st.session_state["restwert_val"],
      step=500.0,
      format="%.2f",
      help="Erzielter Verkaufspreis oder Inzahlungnahme-Wert des alten Autos.",
  )

st.session_state["praemie_aktiv"] = st.checkbox(
    "E-Auto Prämie / Hersteller-Rabatt / Förderung abziehen",
    value=st.session_state["praemie_aktiv"],
)
if st.session_state["praemie_aktiv"]:
  st.session_state["praemie_val"] = st.number_input(
      "Höhe der Prämie / Förderung (€)",
      min_value=0.0,
      value=st.session_state["praemie_val"],
      step=100.0,
      format="%.2f",
      help="Staatliche oder herstellerseitige Förderungen.",
  )

# Berechnung starten
if st.button("Ersparnis berechnen", type="primary", use_container_width=True):
  kwh = st.session_state["kwh_val"]
  v_ev = st.session_state["verbrauch_ev_val"]
  strom = st.session_state["strompreis_val"]
  v_verb = st.session_state["verbrauch_verbrenner_val"]
  spritpreis = st.session_state["kraftstoffpreis_val"]
  zeit_label = st.session_state["zeitraum_text"]

  # Effektiven Kaufpreis nach Abzügen ermitteln
  brutto_kaufpreis = st.session_state["kaufpreis_ev_val"]
  abzug_restwert = (
      st.session_state["restwert_val"]
      if st.session_state["restwert_aktiv"]
      else 0.0
  )
  abzug_praemie = (
      st.session_state["praemie_val"]
      if st.session_state["praemie_aktiv"]
      else 0.0
  )
  effektiver_kaufpreis = max(0.0, brutto_kaufpreis - abzug_restwert - abzug_praemie)

  # 1. Gefahrene Kilometer ermitteln
  if v_ev > 0:
    gefahrene_km = (kwh / v_ev) * 100
  else:
    gefahrene_km = 0

  # 2. Kosten E-Auto (Ladekosten mit PV-Mix Berechnung)
  if st.session_state["pv_aktiv"]:
    pv_anteil = st.session_state["pv_anteil_val"] / 100.0
    pv_preis = st.session_state["pv_preis_val"]
    kwh_pv = kwh * pv_anteil
    kwh_netz = kwh * (1.0 - pv_anteil)
    kosten_ev = (kwh_pv * pv_preis) + (kwh_netz * strom)
  else:
    kosten_ev = kwh * strom

  # 3. Kosten Verbrenner für dieselbe Strecke (Kraftstoff)
  liter_benoetigt = (gefahrene_km / 100) * v_verb
  kosten_verbrenner = liter_benoetigt * spritpreis

  # 4. THG-Quote & Steuer anteilig auf den Zeitraum anrechnen
  thg_erloes_zeitraum = (
      (st.session_state["thg_wert"] * jahres_faktor)
      if st.session_state["thg_aktiv"]
      else 0.0
  )
  steuer_ersparnis_zeitraum = (
      (st.session_state["steuer_verbrenner_wert"] * jahres_faktor)
      if st.session_state["steuer_aktiv"]
      else 0.0
  )

  gesamtersparnis_verbrenner_seite = (
      kosten_verbrenner + steuer_ersparnis_zeitraum + thg_erloes_zeitraum
  )
  ersparnis_euro = gesamtersparnis_verbrenner_seite - kosten_ev

  if kosten_verbrenner > 0:
    ersparnis_prozent = (ersparnis_euro / gesamtersparnis_verbrenner_seite) * 100
  else:
    ersparnis_prozent = 0

  # 5. Amortisation basierend auf effektivem Kaufpreis berechnen
  if gefahrene_km > 0 and ersparnis_euro > 0:
    ersparnis_pro_km = ersparnis_euro / gefahrene_km
    km_bis_amortisation = (
        effektiver_kaufpreis / ersparnis_pro_km if ersparnis_pro_km > 0 else 0
    )
  else:
    ersparnis_pro_km = 0
    km_bis_amortisation = 0

  # Ausgabe
  st.divider()
  st.subheader(f"Auswertung für: {zeit_label} ({selected_fuel_short})")

  m1, m2 = st.columns(2)
  m1.metric(
      label="Gefahrene Strecke (geschätzt)",
      value=f"{gefahrene_km:,.0f} km".replace(",", "."),
      help="Basierend auf geladenen kWh und E-Auto-Verbrauch.",
  )
  m2.metric(
      label="Gesamt-Ersparnis (inkl. Fixkosten)",
      value=f"{ersparnis_euro:,.2f} €".replace(",", "."),
      delta=f"{ersparnis_prozent:.1f}% günstiger",
  )

  st.write("")
  st.markdown("### Kostenvergleich im Detail:")

  if st.session_state["pv_aktiv"]:
    energiekosten_label = (
        f"Ladekosten-Mix ({st.session_state['pv_anteil_val']:.0f}% PV à"
        f" {st.session_state['pv_preis_val']:.2f} €, Rest Netz à"
        f" {strom:.2f} €)"
    )
  else:
    energiekosten_label = "Energiekosten (Laden über Netz)"

  details_kategorien = [energiekosten_label]
  details_kosten_ev = [f"{kosten_ev:,.2f} €".replace(",", ".")]
  details_kosten_verb = [f"{kosten_verbrenner:,.2f} €".replace(",", ".")]

  if st.session_state["steuer_aktiv"]:
    details_kategorien.append("Kfz-Steuer (E-Auto: 0 €)")
    details_kosten_ev.append("0,00 €")
    details_kosten_verb.append(
        f"{steuer_ersparnis_zeitraum:,.2f} €".replace(",", ".")
    )

  if st.session_state["thg_aktiv"]:
    details_kategorien.append("THG-Quoten Erlös")
    details_kosten_ev.append(
        f"-{thg_erloes_zeitraum:,.2f} € (Gutschrift)".replace(",", ".")
    )
    details_kosten_verb.append("0,00 €")

  comparison_data = {
      "Kategorie": details_kategorien,
      "E-Auto Kosten (€)": details_kosten_ev,
      f"Verbrenner ({selected_fuel_short}) (€)": details_kosten_verb,
  }
  st.table(comparison_data)

  if ersparnis_euro > 0:
    st.success(
        f"🎉 Im Zeitraum **{zeit_label}** hast du unter Berücksichtigung von"
        f" Sprit, Ladekosten, Steuer und THG insgesamt **{ersparnis_euro:,.2f}"
        " €** profitiert!".replace(",", ".")
    )

    if effektiver_kaufpreis > 0 and ersparnis_pro_km > 0:
      st.markdown("### 📈 Amortisations-Analyse:")
      st.info(
          f"💡 Der effektive Netto-Aufpreis beträgt **{effektiver_kaufpreis:,.2f}"
          f" €** (nach Abzügen). Durch die laufenden Einsparungen ergibt sich"
          f" eine Entlastung von ca. **{ersparnis_pro_km * 100:.2f} Cent pro"
          f" Kilometer**. Die Amortisation ist somit nach ca."
          f" **{km_bis_amortisation:,.0f} gefahrenen Kilometern**"
          " erreicht.".replace(",", ".")
      )
  else:
    st.info(
        "In diesem Zeitraum waren die Gesamtkosten (oder der gewählte"
        " Zeitraum ist zu kurz für die Fixkosten) höher."
    )
