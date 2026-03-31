import streamlit as st
import pandas as pd

# 1. NASTAVITVE STRANI
st.set_page_config(page_title="Davčni Kalkulator 2026", layout="wide")

st.title("📊 Profesionalni davčni kalkulator za upokojence (2026)")
st.caption("Vključuje pragove za odtegljaj akontacije (1.724 € / 2.019 €) in prispevke.")

# 2. STRANSKA VRSTICA (VNOSI)
with st.sidebar:
    st.header("Vnosni podatki")
    pok_mesecna = st.number_input("Mesečna pokojnina (Bruto) [€]", min_value=0.0, value=1500.0, step=50.0)
    
    st.divider()
    vrsta_izplacila = st.sidebar.radio("Način izplačila iz 2. stebra:", ["Mesečna renta", "Enkratni odkup"])
    
    if vrsta_izplacila == "Mesečna renta":
        renta_znesek = st.sidebar.number_input("Mesečna renta [€]", min_value=0.0, value=100.0)
        renta_letna = renta_znesek * 12
    else:
        renta_letna = st.sidebar.number_input("Znesek enkratnega odkupa [€]", min_value=0.0, value=20000.0)
        renta_znesek = 0
        
    st.divider()
    je_seniorka = st.checkbox("Uveljavljam seniorsko olajšavo (70+ let)")
    
    # Parametri 2026
    splosna_olajsava = 5551.93
    seniorska_ol_letna = 1665.60 
    ozp_mesecni = 35.00
    do_stopnja = 0.01 

# 3. LOGIKA IZRAČUNA
def izracunaj_vse(pok_m, r_letna, r_mesecna, splosna, sen_ol_l, je_sen, tip):
    # A) IZRAČUN MESEČNE AKONTACIJE OD POKOJNINE (ZPIZ)
    # ZPIZ upošteva: Bruto - 1% DO - 35€ OZP - mesečna splošna/seniorska olajšava
    m_osnova = pok_m - (pok_m * 0.01) - 35.0
    m_olajsava = (splosna / 12) + (sen_ol_l / 12 if je_sen else 0)
    m_neto_osnova = max(0.0, m_osnova - m_olajsava)
    
    # Preprosta lestvica za mesečni odtegljaj (16% v prvem razredu)
    # Prag 1.724 € (brez seniorske) oziroma 2.019 € (s seniorsko)
    m_davek = m_neto_osnova * 0.16
    m_pok_olajsava = pok_m * 0.135
    akontacija_zpiz_mesecna = max(0.0, m_davek - m_pok_olajsava)
    akontacija_zpiz_letna = akontacija_zpiz_mesecna * 12

    # B) CELOLETNI IZRAČUN (DOHODNINSKA NAPOVED)
    pok_letna = pok_m * 12
    skupni_bruto = pok_letna + r_letna
    prispevek_do = skupni_bruto * 0.01
    prispevek_ozp = 35.0 * 12
    
    renta_v_osnovi = r_letna * 0.5 if tip == "Mesečna renta" else r_letna
    neto_osnova = max(0.0, (pok_letna + renta_v_osnovi) - prispevek_do - prispevek_ozp - splosna - (sen_ol_l if je_sen else 0))

    # Lestvica
    razredi = [("1. razred (16%)", 9721.43, 0.16), ("2. razred (26%)", 20177.30, 0.26), ("3. razred (33%)", 35560.00, 0.33), ("4. razred (39%)", 74160.00, 0.39), ("5. razred (50%)", float('inf'), 0.50)]
    odmerjena = 0.0
    ostanek = neto_osnova
    prejsnji = 0.0
    razclenitev = []
    for ime, prag, stopnja in razredi:
        v_razredu = min(max(0.0, ostanek), prag - prejsnji)
        davek = v_razredu * stopnja
        razclenitev.append([ime, v_razredu, davek])
        odmerjena += davek
        ostanek -= v_razredu
        prejsnji = prag

    pok_olajsava_letna = pok_letna * 0.135
    koncni_letni_dolg = max(0.0, odmerjena - pok_olajsava_letna)
    
    # C) AKONTACIJA 2. STEBRA
    if tip == "Enkratni odkup":
        akontacija_2_steber = r_letna * 0.25
    else:
        akontacija_2_steber = (r_mesecna * 0.5 * 0.25 * 12) if r_mesecna >= 160.0 else 0.0
        
    skupna_placana_akontacija = akontacija_zpiz_letna + akontacija_2_steber
    
    return {
        "pok_letna": pok_letna,
        "renta_letna": r_letna,
        "renta_v_osnovi": renta_v_osnovi,
        "prispevki": prispevek_do + prispevek_ozp,
        "neto_osnova": neto_osnova,
        "odmerjena": odmerjena,
        "razclenitev": razclenitev,
        "pok_olajsava": pok_olajsava_letna,
        "koncni_dolg": koncni_letni_dolg,
        "akontacija_zpiz_letna": akontacija_zpiz_letna,
        "akontacija_2_steber": akontacija_2_steber,
        "akontacija_skupna": skupna_placana_akontacija,
        "poracun": koncni_letni_dolg - skupna_placana_akontacija
    }

rez = izracunaj_vse(pok_mesecna, renta_letna, renta_znesek, splosna_olajsava, seniorska_ol_letna, je_seniorka, vrsta_izplacila)

# 4. PRIKAZ V TABELI
st.subheader("Podroben letni razrez")
tabela_rows = [
    ["Bruto pokojnina (ZPIZ)", f"{rez['pok_letna']:,.2f} €"],
    ["Znesek iz 2. stebra", f"{rez['renta_letna']:,.2f} €"],
    ["Neto davčna osnova", f"{rez['neto_osnova']:,.2f} €"],
    ["SKUPAJ ODMERJENA DOHODNINA", f"{rez['odmerjena']:,.2f} €"],
    ["Pokojninska olajšava (13,5%)", f"-{rez['pok_olajsava']:,.2f} €"],
    ["KONČNI LETNI DOLG (FURS)", f"{rez['koncni_dolg']:,.2f} €"],
    ["Plačana akontacija od pokojnine (ZPIZ)", f"-{rez['akontacija_zpiz_letna']:,.2f} €"],
    ["Plačana akontacija od 2. stebra", f"-{rez['akontacija_2_steber']:,.2f} €"],
    ["SKUPAJ PLAČANA AKONTACIJA", f"-{rez['akontacija_skupna']:,.2f} €"]
]
st.table(pd.DataFrame(tabela_rows, columns=["Postavka", "Znesek"]))

# PORAČUN
if rez['poracun'] > 0:
    st.error(f"DOPLAČILO: Pri dohodninski napovedi boste morali doplačati še **{rez['poracun']:,.2f} €**.")
else:
    st.success(f"VRAČILO: FURS vam bo vrnil **{abs(rez['poracun']):,.2f} €**.")
