import streamlit as st
import pandas as pd

# 1. NASTAVITVE STRANI
st.set_page_config(page_title="Davčni Kalkulator 2026", layout="wide")

st.title("📊 Profesionalni davčni kalkulator za upokojence (2026)")
st.caption("Vključuje prispevke (DO, OZP), seniorsko olajšavo (138,80 €/mesec) in progresivno lestvico 2026.")

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
    # Seniorska olajšava: 138,80 € * 12 = 1.665,60 €
    seniorska_olajsava_letna = 1665.60 
    ozp_mesecni = 35.00
    do_stopnja = 0.01 

# 3. LOGIKA IZRAČUNA
def izracunaj_vse(pok_m, r_letna, r_mesecna, splosna, sen_ol_l, je_sen, tip):
    pok_letna = pok_m * 12
    skupni_bruto_vseh_prejemkov = pok_letna + r_letna
    
    # PRISPEVKI (znižujejo davčno osnovo)
    prispevek_do = skupni_bruto_vseh_prejemkov * 0.01
    prispevek_ozp = 35.0 * 12
    
    # DAVČNA OSNOVA: Renta 50%, Odkup 100%
    renta_v_osnovi = r_letna * 0.5 if tip == "Mesečna renta" else r_letna
    
    # Izračun osnove pred olajšavami
    osnova_pred_olajsavami = (pok_letna + renta_v_osnovi) - prispevek_do - prispevek_ozp
    
    # Odštevanje olajšav
    neto_osnova = max(0.0, osnova_pred_olajsavami - splosna)
    if je_sen:
        neto_osnova = max(0.0, neto_osnova - sen_ol_l)

    # PROGRESIVNA LESTVICA 2026
    razredi = [
        ("1. razred (16%)", 9721.43, 0.16),
        ("2. razred (26%)", 20177.30, 0.26),
        ("3. razred (33%)", 35560.00, 0.33),
        ("4. razred (39%)", 74160.00, 0.39),
        ("5. razred (50%)", float('inf'), 0.50)
    ]
    
    odmerjena = 0.0
    ostanek = neto_osnova
    prejsnji = 0.0
    razclenitev_tabela = []
    
    for ime, prag, stopnja in razredi:
        v_razredu = min(max(0.0, ostanek), prag - prejsnji)
        davek = v_razredu * stopnja
        razclenitev_tabela.append([ime, v_razredu, davek])
        odmerjena += davek
        ostanek -= v_razredu
        prejsnji = prag

    # POKOJNINSKA OLAJŠAVA (13,5%)
    pok_olajsava = pok_letna * 0.135
    koncni_letni_dolg = max(0.0, odmerjena - pok_olajsava)
    
    # AKONTACIJA
    if tip == "Enkratni odkup":
        # Akontacija 25% od celotnega odkupa (ker gre 100% v osnovo)
        akontacija_skupna = r_letna * 0.25
    else:
        # Akontacija 25% od polovice (če renta >= 160€)
        akontacija_m = (r_mesecna * 0.5 * 0.25) if r_mesecna >= 160.0 else 0.0
        akontacija_skupna = akontacija_m * 12
        
    return {
        "pok_letna": pok_letna,
        "renta_letna": r_letna,
        "renta_v_osnovi": renta_v_osnovi,
        "prispevek_do": prispevek_do,
        "prispevek_ozp": prispevek_ozp,
        "neto_osnova": neto_osnova,
        "odmerjena": odmerjena,
        "razclenitev": razclenitev_tabela,
        "pok_olajsava": pok_olajsava,
        "koncni_dolg": koncni_letni_dolg,
        "akontacija_skupna": akontacija_skupna,
        "poracun": koncni_letni_dolg - akontacija_skupna
    }

rez = izracunaj_vse(pok_mesecna, renta_letna, renta_znesek, splosna_olajsava, seniorska_olajsava_letna, je_seniorka, vrsta_izplacila)

# 4. PRIKAZ REZULTATOV
st.subheader("1. Razčlenitev dohodnine po razredih")
df_raz = pd.DataFrame(rez['razclenitev'], columns=["Razred", "Osnova v razredu [€]", "Davek [€]"])
st.table(df_raz.style.format({"Osnova v razredu [€]": "{:,.2f}", "Davek [€]": "{:,.2f}"}))

st.subheader("2. Podroben letni razrez")
tabela_rows = [
    ["Bruto pokojnina (ZPIZ)", f"{rez['pok_letna']:,.2f} €"],
    ["Znesek iz 2. stebra (Renta/Odkup)", f"{rez['renta_letna']:,.2f} €"],
    ["Vstop v davčno osnovo", f"{rez['renta_v_osnovi']:,.2f} €" + (" (100%)" if vrsta_izplacila == "Enkratni odkup" else " (50%)")],
    ["Prispevek za dolgotrajno oskrbo (1%)", f"-{rez['prispevek_do']:,.2f} €"],
    ["Zdravstveni prispevek (OZP)", f"-{rez['prispevek_ozp']:,.2f} €"],
    ["Splošna davčna olajšava", f"-{splosna_olajsava:,.2f} €"]
]

if je_seniorka:
    tabela_rows.append(["Seniorska olajšava (138,80 €/mesec)", f"-{seniorska_olajsava_letna:,.2f} €"])

tabela_rows.extend([
    ["Neto davčna osnova", f"{rez['neto_osnova']:,.2f} €"],
    ["SKUPAJ ODMERJENA DOHODNINA", f"{rez['odmerjena']:,.2f} €"],
    ["Pokojninska olajšava (13,5%)", f"-{rez['pok_olajsava']:,.2f} €"],
    ["KONČNI LETNI DOLG (FURS)", f"{rez['koncni_dolg']:,.2f} €"],
    ["Že plačana akontacija", f"-{rez['akontacija_skupna']:,.2f} €"]
])

st.table(pd.DataFrame(tabela_rows, columns=["Postavka", "Znesek"]))

# 5. KONČNI PORAČUN
st.divider()
if rez['poracun'] > 0:
    st.error(f"⚠️ **DOPLAČILO:** Pri dohodninski napovedi boste morali doplačati še **{rez['poracun']:,.2f} €**.")
elif rez['poracun'] < 0:
    st.success(f"✅ **VRAČILO:** FURS vam bo vrnil preveč plačano akontacijo v višini **{abs(rez['poracun']):,.2f} €**.")
else:
    st.info("Ni večjih doplačil ali vračila.")
