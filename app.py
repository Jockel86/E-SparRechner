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

# Das Eingabefeld greift nun direkt auf den Session-State zu und aktualisiert sich sofort!
st.session_state["kraftstoffpreis_val"] = st.number_input(
    f"Ø {selected_fuel_short}-Preis (€/Liter)",
    min_value=0.0,
    value=st.session_state["kraftstoffpreis_val"],
    step=0.01,
    format="%.2f",
    key="kraftstoffpreis_input_field",
    help=(
        "Wird über Buttons direkt übernommen oder kann manuell angepasst werden."
    ),
)
