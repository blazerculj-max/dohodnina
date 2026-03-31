import streamlit as st
import pandas as pd

# 1. NASTAVITVE STRANI
st.set_page_config(page_title="Davčni Kalkulator 2026", layout="wide")

st.title("📊 Napredni davčni kalkulator za upokojence (2026)")
st.markdown("""
Ta kalkulator upošteva zakonodajo za leto 2026, vključno s prispevki za dolgotrajno oskrbo (DO), 
obveznim zdravstvenim prispevkom (OZP) in progresivno dohodninsko lestvico.
""")

# 2. STRANSKA VRSTICA (VNOSI)
with st.sidebar:
    st.header("Vnosni podatki")
    pok_mesecna = st.number_input("Mesečna bruto pokojnina (ZPIZ) [€]", min_value=0.0, value=1500.0, step=50.0)
    
    st.divider()
    vrsta_izplacila = st.radio("Izplačilo iz 2. stebra (PDPZ):", ["Mesečna renta", "Enkratni odkup"])
    
    if vrsta_izplacila == "Mesečna renta":
        renta_znesek = st.number_input("Mesečna bruto renta [€]", min_value=0.0, value=200.0, step=10.0)
        renta_letna = renta_znesek * 12
    else:
        renta_letna = st.number_input("Celotni znesek odkupa [€]", min_value=0.0, value=20000.0, step=500.0)
        renta_znesek = 0
        
    st.divider()
    je_senior = st.checkbox("Uveljavljam seniorsko olajšavo (70+ let)")
    
    # Konstante 2026
    S_OL_LETNA = 5551.93
    SEN_OL_LETNA = 1665.60  # 138,80 € * 12
    OZP_MESECNI = 35.00
    DO_STOPNJA = 0.01  # 1%
    POK_OL_STOPNJA = 0.135  # 13,5%

# 3. LOGIKA IZRAČUNA
def izracunaj_davek(pok_m, r_letna, r_mesecna, s_ol, sen_ol, je_sen, tip):
    # A) MESEČNI ODTEGLJAJ OD POKOJNINE (Akontacija ZPIZ)
    # ZPIZ upošteva OZP in DO prispevek pri določanju davčne osnove
    m_prispevek_do = pok_m * 0.01
    m_osnova_za_davek = pok_m - m_prispevek_do - 35.0
    m_olajsava = (s_ol / 12) + (sen_ol / 12 if je_sen else 0)
    m_neto_osnova = max(0.0, m_osnova_za_davek - m_olajsava)
    
    # Mesečna akontacija (16% v 1. razredu) minus 13,5% pokojninske olajšave
    m_akontacija_zpiz = max(0.0, (m_neto_osnova * 0.16) - (pok_m * 0.135))
    akontacija_zpiz_letna = m_akontacija_zpiz * 12

    # B) MESEČNI ODTEGLJAJ OD RENTE (Akontacija 2. steber)
    if tip == "Enkratni odkup":
        # Pri odkupu se vedno odtegne 25% od celotnega bruto zneska (ker 100% vstopa v osnovo)
        akontacija_2st_letna = r_letna * 0.25
        m_akontacija_renta = akontacija_2st_letna # Prikaz za tabelo
    else:
        # Pri mesečni renti se odtegne 25% od 50% zneska, če je znesek >= 160 EUR
        if r_mesecna >= 160.0:
            m_akontacija_renta = (r_mesecna * 0.5) * 0.25
        else:
            m_akontacija_renta = 0.0
        akontacija_2st_letna = m_akontacija_renta * 12

    # C) LETNA DOHODNINSKA NAPOVED (Končni izračun FURS)
    pok_letna = pok_m * 12
    skupni_bruto = pok_letna + r_letna
    
    # Prispevki, ki znižujejo davčno osnovo
    letni_prispevek_do = skupni_bruto * 0.01
    letni_prispevek_ozp = 35.0 * 12
    
    # Davčna osnova: Renta 50%, Odkup 100%
    renta_v_osnovi = r_letna * 0.5 if tip == "Mesečna renta" else r_letna
    
    letna_neto_osnova = (pok_letna + renta_v_osnovi) - letni_prispevek_do - letni_prispevek_ozp - s_ol
    if je_sen:
        letna_neto_osnova -= sen_ol
    letna_neto_osnova = max(0.0, letna_neto_osnova)

    # Progresivna lestvica 2026
    razredi = [
        ("1. razred (16%)", 9721.43, 0.16),
        ("2. razred (26%)", 20177.30, 0.26),
        ("3. razred (33%)", 35560.00, 0.33),
        ("4. razred (39%)", 74160.00, 0.39),
        ("5. razred (50%)", float('inf'), 0.50)
    ]
    
    odmerjena_dohodnina = 0.0
    ostanek = letna_neto_osnova
    prejsnji = 0.0
    razclenitev_list = []
    
    for ime, prag, stopnja in razredi:
        v_razredu = min(max(0.0, ostanek), prag - prejsnji)
        davek = v_razredu * stopnja
        razclenitev_list.append([ime, v_razredu, davek])
        odmerjena_dohodnina += davek
        ostanek -= v_razredu
        prejsnji = prag

    pok_olajsava_letna = pok_letna * 0.135
    koncni_letni_dolg = max(0.0, odmerjena_dohodnina - pok_olajsava_letna)
    skupna_placana_akontacija = akontacija_zpiz_letna + akontacija_2st_letna
    
    return {
        "m_ak_zpiz": m_akontacija_zpiz,
        "m_ak_renta": m_akontacija_renta,
        "letna_osnova": letna_neto_osnova,
        "razclenitev": razclenitev_list,
        "koncni_dolg": koncni_letni_dolg,
        "ak_zpiz_letna": akontacija_zpiz_letna,
        "ak_renta_letna": akontacija_2st_letna,
        "ak_skupaj": skupna_placana_akontacija,
        "poracun": koncni_letni_dolg - skupna_placana_akontacija,
        "prispevki_letni": letni_prispevek_do + letni_prispevek_ozp,
        "pok_letna": pok_letna,
        "renta_letna": r_letna,
        "renta_v_osnovi": renta_v_osnovi
    }

rez = izracunaj_davek(pok_mesecna, renta_letna, renta_znesek, S_OL_LETNA, SEN_OL_LETNA, je_senior, vrsta_izplacila)

# 4. PRIKAZ REZULTATOV (KPI)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Končni letni dolg (FURS)", f"{rez['koncni_dolg']:,.2f} €")
with col2:
    st.metric("Skupaj plačane akontacije", f"{rez['ak_skupaj']:,.2f} €")
with col3:
    poracun_val = rez['poracun']
    st.metric("Poračun (Doplačilo/Vračilo)", f"{abs(poracun_val):,.2f} €", 
              delta="Doplačilo" if poracun_val > 0 else "Vračilo", delta_color="inverse" if poracun_val > 0 else "normal")

st.divider()

# 5. TABELA: RAZČLENITEV PO RAZREDIH
st.subheader("1. Obdavčitev po progresivnih razredih")
df_raz = pd.DataFrame(rez['razclenitev'], columns=["Razred", "Osnova v razredu [€]", "Davek [€]"])
st.table(df_raz.style.format({"Osnova v razredu [€]": "{:,.2f}", "Davek [€]": "{:,.2f}"}))

# 6. TABELA: PODROBEN LETNI RAZREZ
st.subheader("2. Podroben letni razrez in prispevki")
tabelarični_podatki = [
    ["Bruto pokojnina (ZPIZ)", f"{rez['pok_letna']:,.2f} €"],
    ["Bruto znesek iz 2. stebra", f"{rez['renta_letna']:,.2f} €"],
    ["Vstop v davčno osnovo (PDPZ)", f"{rez['renta_v_osnovi']:,.2f} €"],
    ["Prispevek za dolgotrajno oskrbo (1%)", f"-{rez['pok_letna']*0.01 + rez['renta_letna']*0.01:,.2f} €"],
    ["Zdravstveni prispevek (OZP)", f"-{35.0*12:,.2f} €"],
    ["Splošna olajšava", f"-{S_OL_LETNA:,.2f} €"]
]
if je_senior:
    tabelarični_podatki.append(["Seniorska olajšava (138,80 €/m)", f"-{SEN_OL_LETNA:,.2f} €"])

tabelarični_podatki.extend([
    ["Neto davčna osnova", f"{rez['letna_osnova']:,.2f} €"],
    ["Pokojninska olajšava (13,5% od pokojnine)", f"-{rez['pok_letna']*0.135:,.2f} €"],
    ["KONČNI LETNI DOLG", f"{rez['koncni_dolg']:,.2f} €"],
    ["Akontacija plačana pri ZPIZ (Letno)", f"-{rez['ak_zpiz_letna']:,.2f} €"],
    ["Akontacija plačana pri PDPZ (Letno)", f"-{rez['ak_renta_letna']:,.2f} €"]
])

st.table(pd.DataFrame(tabelarični_podatki, columns=["Postavka", "Znesek"]))

# 7. INFO SPOROČILA
st.divider()
if pok_mesecna < (1724 if not je_senior else 2019):
    st.info(f"ℹ️ Vaša pokojnina je pod pragom za odtegljaj akontacije (ZPIZ vam mesečno ne trga dohodnine).")
else:
    st.warning(f"⚠️ Vaša pokojnina presega prag; ZPIZ vam mesečno trga {rez['m_ak_zpiz']:.2f} € akontacije.")

if vrsta_izplacila == "Mesečna renta" and renta_znesek >= 160:
    st.warning(f"⚠️ Renta presega 160 €, zato zavarovalnica mesečno odvede {rez['m_ak_renta']:.2f} € akontacije.")
