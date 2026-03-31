import streamlit as st
import pandas as pd

# Nastavitve strani
st.set_page_config(page_title="Davčni Kalkulator Pokojnin 2026", layout="wide")

st.title("📊 Informativni izračun dohodnine za upokojence (2026)")
st.caption("Avtor: @blazerculj-max | Vir podatkov: ZDoh-2 in napovedi za 2026")

# --- STRANSKA VRSTICA ZA VNOS ---
st.sidebar.header("Vnosni podatki")
pok_mesecna = st.sidebar.number_input("Mesečna pokojnina (ZPIZ) [€]", min_value=0.0, value=1500.0, step=50.0)

st.sidebar.divider()
st.sidebar.subheader("Izplačilo iz 2. stebra")
vrsta_izplacila = st.sidebar.radio("Način izplačila:", ["Mesečna renta", "Enkratni odkup"])

if vrsta_izplacila == "Mesečna renta":
    renta_znesek = st.sidebar.number_input("Mesečni znesek rente [€]", min_value=0.0, value=100.0, step=10.0)
    renta_letna = renta_znesek * 12
else:
    renta_letna = st.sidebar.number_input("Celotni znesek enkratnega odkupa [€]", min_value=0.0, value=5000.0, step=100.0)
    renta_znesek = 0 

st.sidebar.divider()
splosna_olajsava = st.sidebar.number_input("Splošna olajšava (letna) [€]", value=5551.93)

# --- IZRAČUN ---
def izracunaj_dohodnino(pok_m, r_letna, r_mesecna, splosna, tip):
    pok_letna = pok_m * 12
    
    # DIFERENCIACIJA DAVČNE OSNOVE:
    if tip == "Mesečna renta":
        # Le 50% rente gre v davčno osnovo (ZDoh-2, 40. člen)
        renta_v_osnovi = r_letna * 0.5
    else:
        # Enkratni odkup gre v davčno osnovo v CELOTI (100%)
        renta_v_osnovi = r_letna
        
    bruto_osnova = pok_letna + renta_v_osnovi
    neto_osnova = max(0.0, bruto_osnova - splosna)
    
    # Lestvica 2026 (progresivna)
    razredi = [(9721.43, 0.16), (20177.30, 0.26), (35560.00, 0.33), (74160.00, 0.39), (float('inf'), 0.50)]
    odmerjena = 0.0
    preostanek = neto_osnova
    prejsnji_prag = 0.0
    for prag, stopnja in razredi:
        if preostanek <= 0: break
        v_razredu = min(preostanek, prag - prejsnji_prag)
        odmerjena += v_razredu * stopnja
        preostanek -= v_razredu
        prejsnji_prag = prag
        
    pok_olajsava = pok_letna * 0.135
    koncni_letni_dolg = max(0.0, odmerjena - pok_olajsava)
    
    # LOGIKA AKONTACIJE
    if tip == "Enkratni odkup":
        # Akontacija 25% od CELOTNEGA zneska odkupa (ker gre 100% v osnovo)
        akontacija_skupna = r_letna * 0.25
        renta_neto_izplacilo = r_letna - akontacija_skupna
        prikaz_akontacija = akontacija_skupna
    else:
        # Mesečna renta: akontacija 25% od polovice (le nad 160€ bruto)
        if r_mesecna >= 160.0:
            akontacija_m = (r_mesecna * 0.5) * 0.25
        else:
            akontacija_m = 0.0
        akontacija_skupna = akontacija_m * 12
        renta_neto_izplacilo = r_mesecna - akontacija_m
        prikaz_akontacija = akontacija_m
    
    return {
        "pok_letna": pok_letna,
        "renta_letna": r_letna,
        "renta_v_osnovi": renta_v_osnovi,
        "neto_osnova": neto_osnova,
        "odmerjena": odmerjena,
        "pok_olajsava": pok_olajsava,
        "koncni_dolg": koncni_letni_dolg,
        "prikaz_akontacija": prikaz_akontacija,
        "akontacija_skupna": akontacija_skupna,
        "renta_neto_prikaz": renta_neto_izplacilo,
        "poracun": koncni_letni_dolg - akontacija_skupna
    }

rez = izracunaj_dohodnino(pok_mesecna, renta_letna, renta_znesek, splosna_olajsava, vrsta_izplacila)

# --- PRIKAZ REZULTATOV ---
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Letni dolg dohodnine", f"{rez['koncni_dolg']:,.2f} €")
with c2:
    label_ak = "Akontacija (plačano takoj)" if vrsta_izplacila == "Enkratni odkup" else "Mesečna akontacija (odteg)"
    st.metric(label_ak, f"{rez['prikaz_akontacija']:,.2f} €", delta_color="inverse")
with c3:
    label_neto = "Neto prejemek"
    st.metric(label_neto, f"{rez['renta_neto_prikaz']:,.2f} €")

st.divider()

# Opozorila
if vrsta_izplacila == "Enkratni odkup":
    st.error(f"⚠️ **Kritično opozorilo:** Enkratni odkup se v davčno osnovo šteje v **CELOTI (100 %)**. Vaša davčna osnova se je povečala za {rez['renta_letna']:,.2f} €.")
elif renta_znesek >= 160:
    st.warning("Mesečna renta presega 160 €, zato se sproti odteguje akontacija (25 % od polovice).")

# --- RAZPREDELNICA ---
st.subheader("Podroben letni razrez")
rows = [
    ["Bruto pokojnina (ZPIZ)", f"{rez['pok_letna']:,.2f} €"],
    ["Znesek iz 2. stebra (Renta/Odkup)", f"{rez['renta_letna']:,.2f} €"],
    ["Vstop v davčno osnovo", f"{rez['renta_v_osnovi']:,.2f} €" + (" (100 %)" if vrsta_izplacila == "Enkratni odkup" else " (50 %)")],
    ["SKUPNA BRUTO OSNOVA", f"{rez['pok_letna'] + rez['renta_v_osnovi']:,.2f} €"],
    ["Splošna olajšava", f"-{splosna_olajsava:,.2f} €"],
    ["Neto davčna osnova", f"{rez['neto_osnova']:,.2f} €"],
    ["Odmerjena dohodnina", f"{rez['odmerjena']:,.2f} €"],
    ["Pokojninska olajšava (13,5 %)", f"-{rez['pok_olajsava']:,.2f} €"],
    ["KONČNI LETNI DOLG", f"{rez['koncni_dolg']:,.2f} €"],
    ["Že plačana akontacija", f"-{rez['akontacija_skupna']:,.2f} €"]
]

st.table(pd.DataFrame(rows, columns=["Postavka", "Znesek"]))

# Poračun
st.subheader("Poračun ob koncu leta")
if rez['poracun'] > 0:
    st.error(f"DOPLAČILO: Kljub plačani akontaciji boste morali doplačati še **{rez['poracun']:,.2f} €**.")
elif rez['poracun'] < 0:
    st.success(f"VRAČILO: FURS vam bo vrnil preveč plačano akontacijo v višini **{abs(rez['poracun']):,.2f} €**.")
else:
    st.info("Ni večjih doplačil ali vračila.")
