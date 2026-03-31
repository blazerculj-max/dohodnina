def kalkulator_pokojnine_2026(pokojnina_mesecna, renta_mesecna):
    """
    Izračun dohodnine za upokojence v Sloveniji (vsi davčni razredi 2026).
    Vključuje 50% olajšavo za rento iz 2. stebra in 13,5% pokojninsko olajšavo.
    """
    
    # --- KONSTANTE ZA LETO 2026 (Predvideni pragovi) ---
    SPLOSNA_OLASAVA = 5551.93
    POKOJNINSKA_OL_STOPNJA = 0.135
    PRAG_AKONTACIJE_RENTE = 160.0  # Meja, nad katero se trga 25% akontacija
    
    # Lestvica: (zgornja meja razreda, davčna stopnja)
    # Razredi so progresivni: 16%, 26%, 33%, 39%, 50%
    LESTVICA = [
        (9721.43, 0.16),
        (20177.30, 0.26),
        (35560.00, 0.33),
        (74160.00, 0.39),
        (float('inf'), 0.50)
    ]

    # 1. LETNI BRUTO IN AKONTACIJE
    pok_letna = pokojnina_mesecna * 12
    renta_letna = renta_mesecna * 12
    
    # Izračun mesečne akontacije rente (če je nad 160€)
    akontacija_rente_mesecna = 0
    if renta_mesecna >= PRAG_AKONTACIJE_RENTE:
        # Akontacija se računa kot 25% od 50% bruto zneska
        akontacija_rente_mesecna = (renta_mesecna * 0.50) * 0.25
    
    akontacija_rente_letna = akontacija_rente_mesecna * 12

    # 2. DAVČNA OSNOVA
    # Renta iz 2. stebra je obdavčena le 50% (ZDoh-2)
    bruto_osnova = pok_letna + (renta_letna * 0.50)
    neto_davcna_osnova = max(0, bruto_osnova - SPLOSNA_OLASAVA)

    # 3. IZRAČUN ODMERJENE DOHODNINE (Progresivno čez vse razrede)
    preostala_osnova = neto_davcna_osnova
    odmerjena_dohodnina = 0
    prejsnji_prag = 0
    
    for prag, stopnja in LESTVICA:
        if preostala_osnova <= 0:
            break
        
        sirina_razreda = prag - prejsnji_prag
        obdavcljivo_v_razredu = min(preostala_osnova, sirina_razreda)
        
        odmerjena_dohodnina += obdavcljivo_v_razredu * stopnja
        preostala_osnova -= obdavcljivo_v_razredu
        prejsnji_prag = prag

    # 4. POKOJNINSKA OLAJŠAVA (13,5% od pokojnine ZPIZ)
    pok_olajsava = pok_letna * POKOJNINSKA_OL_STOPNJA
    
    # Končni letni dolg (ne more biti manj kot 0)
    dejanska_letna_dohodnina = max(0, odmerjena_dohodnina - pok_olajsava)

    # 5. PORAČUN (Kaj pravi FURS ob koncu leta)
    # Razlika med tem, kar bi moral plačati, in tem, kar je bilo že odtegnjeno
    poracun = dejanska_letna_dohodnina - akontacija_rente_letna

    # --- PODROBEN IZPIS ---
    print(f"--- ANALIZA OBDAVČITVE ZA LETO 2026 ---")
    print(f"Mesečna pokojnina: {pokojnina_mesecna:,.2f} € | Letna: {pok_letna:,.2f} €")
    print(f"Mesečna renta:     {renta_mesecna:,.2f} € | Letna: {renta_letna:,.2f} €")
    print(f"Mesečna akontacija (odtegljaj): {akontacija_rente_mesecna:,.2f} €")
    print("-" * 50)
    print(f"Skupna davčna osnova (po olajšavi): {neto_davcna_osnova:,.2f} €")
    print(f"Odmerjena dohodnina (pred olajšavo): {odmerjena_dohodnina:,.2f} €")
    print(f"Pokojninska olajšava (13,5%):      -{pok_olajsava:,.2f} €")
    print(f"Dejanski letni dolg dohodnine:      {dejanska_letna_dohodnina:,.2f} €")
    print("-" * 50)
    
    if poracun > 0:
        print(f"REZULTAT: DOPLAČILO FURS-u: {poracun:,.2f} €")
    elif poracun < 0:
        print(f"REZULTAT: VRAČILO DOHODNINE: {abs(poracun):,.2f} €")
    else:
        print(f"REZULTAT: Ni doplačila ali vračila.")
    
    print(f"Efektivna obdavčitev celotne rente: {(dejanska_letna_dohodnina/renta_letna)*100 if renta_letna > 0 else 0:.2f} %")

# Primer za visoko pokojnino, da se aktivirajo višji razredi:
kalkulator_pokojnine_2026(pokojnina_mesecna=3000, renta_mesecna=500)
