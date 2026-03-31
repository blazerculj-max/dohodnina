import streamlit as st
import pandas as pd

# Nastavitve strani
st.set_page_config(page_title="Davčni Kalkulator Pokojnin 2026", layout="wide")

st.title("📊 Informativni izračun dohodnine za upokojence (2026)")
st.caption("Avtor: @blazerculj-max | Vir podatkov: ZDoh-2 in napovedi za 2026")

# --- STRANSKA VRSTICA ZA VNOS ---
st.sidebar.header("Vnosni podatki")
pok_mesecna = st.sidebar.number_input("Mesečna pokojnina (ZPIZ) [€]", min_value=0.0, value=1500.0, step=50.0)
renta_mesecna = st.sidebar.number_input("Mesečna renta (2. steber) [€]", min_value=0.0, value=100.0, step=10.0)

st.sidebar.divider()
st.sidebar.subheader("Nastavitve olajšav")
splosna_olajsava = st.sidebar.number_input("Splošna olajšava (letna) [€]", value=5551.93)
st.sidebar.info("Standardna splošna olajšava za leto 2026.")

# --- IZRAČUN ---
def izracunaj_dohodnino(pok, renta, splosna):
    # Letni zneski
    pok_letna = pok * 12
    renta_letna = renta * 12
    
    # 50% rente v osnovo (ZDoh-2)
    renta_v_osnovi = renta_letna * 0.5
    bruto_osnova = pok_letna + renta_v_osnovi
    
    # Neto davčna osnova
    neto_osnova = max(0.0, bruto_osnova - splosna)
    
    # Lestvica 2026 (vsi razredi)
    razredi = [
        (9721.43, 0.16), (20177.30, 0.26), (35560.00, 0.33), (74160.00, 0.39), (float('inf'), 0.50)
    ]
    
    odmerjena = 0.0
    preostanek = neto_osnova
    prejsnji_prag = 0.0
    for prag, stopnja in razredi:
        if preostanek <= 0: break
        v_razredu = min(preostanek, prag - prejsnji_prag)
        odmerjena += v_razredu * stopnja
        preostanek -= v_razredu
        prejsnji_prag = prag
        
    # Pokojninska olajšava (13,5%)
    pok_olajsava = pok_letna * 0.135
    koncni_dolg = max(0.0, odmerjena - pok_olajsava)
    
    # --- NOVO: IZRAČUN AKONTACIJE ---
    # Če je renta >= 160€, se takoj odtegne 25% od polovice zneska
    if renta >= 160.0:
        akontacija_mesecna = (renta * 0.5) * 0.25
        renta_neto_mesecna = renta - akontacija_mesecna
        je_akontacija = True
    else:
        akontacija_mesecna = 0.0
        renta_neto_mesecna = renta
        je_akontacija = False
    
    return {
        "pok_letna": pok_letna,
        "renta_letna": renta_letna,
        "renta_v_osnovi": renta_v_osnovi,
        "neto_osnova": neto_osnova,
        "odmerjena": odmerjena,
        "pok_olajsava": pok_olajsava,
        "koncni_dolg": koncni_dolg,
        "akontacija_mesecna": akontacija_mesecna,
        "renta_neto_mesecna": renta_neto_mesecna,
        "je_akontacija": je_akontacija,
        "poracun": koncni_dolg - (akontacija_mesecna * 12)
    }

rez = izracunaj_dohodnino(pok_mesecna, renta_mesecna, splosna_olajsava)

# --- PRIKAZ REZULTATOV ---
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Letni dolg dohodnine", f"{rez['koncni_dolg']:,.2f} €")
with c2:
    st.metric("Mesečna akontacija (odteg)", f"{rez['akontacija_mesecna']:,.2f} €", delta="- Akontacija" if rez['je_akontacija'] else None, delta_color="inverse")
with c3:
    st.metric("Neto nakazilo rente", f"{rez['renta_neto_mesecna']:,.2f} €")

st.divider()

# Opozorilo glede praga 160€
if rez['je_akontacija']:
    st.warning(f"⚠️ **Pozor:** Ker vaša renta znaša {renta_mesecna} € (nad mejo 160 €), vam zavarovalnica vsak mesec avtomatično odtegne **25 % akontacije dohodnine** od davčne osnove. Ta znesek boste poračunali ob koncu leta.")
else:
    st.info("ℹ️ Renta je pod pragom 160 €, zato se mesečna akontacija dohodnine ne odteguje.")

# Razlaga v obliki tabele
st.subheader("Podroben letni razrez")
data = {
    "Postavka": ["Bruto pokojnina (ZPIZ)", "Bruto dodatna renta (2. steber)", "Obdavčljivi del rente (50%)", "SKUPAJ BRUTO OSNOVA", "Splošna olajšava", "Neto davčna osnova", "Odmerjena dohodnina", "Pokojninska olajšava (13,5%)", "KONČNI LETNI DOLG"],
    "Znesek [€]": [
        f"{rez['pok_letna']:,.2f}", f"{rez['renta_letna']:,.2f}", f"{rez['renta_v_osnovi']:,.2f}",
        f"{rez['pok_letna'] + rez['renta_v_osnovi']:,.2f}", f"-{splosna_olajsava:,.2f}", f"{rez['neto_osnova']:,.2f}",
        f"{rez['odmerjena']:,.2f}", f"-{rez['pok_olajsava']:,.2f}", f"{rez['koncni_dolg']:,.2f}"
    ]
}
st.table(pd.DataFrame(data))

# Poračun
st.subheader("Poračun ob koncu leta")
if rez['poracun'] > 0:
    st.error(f"Ob koncu leta boste morali DOPLAČATI približno **{rez['poracun']:,.2f} €** (vaše akontacije niso pokrile celotnega dolga).")
elif rez['poracun'] < 0:
    st.success(f"Ob koncu leta boste prejeli VRAČILO v višini približno **{abs(rez['poracun']):,.2f} €** (plačali ste preveč akontacij).")
else:
    st.info("Vaša dohodnina je v celoti pokrita z olajšavami ali akontacijami. Ni večjih doplačil.")
