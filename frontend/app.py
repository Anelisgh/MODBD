import streamlit as st
import pandas as pd
import database
import time
# rulare: streamlit run app.py
# configurare avioane pt validare ui
PLANE_SPECS = {
    'Boeing 737-800':   {'cols': ['A','B','C','D','E','F'], 'rows': 32},
    'Airbus A320':      {'cols': ['A','B','C','D','E','F'], 'rows': 30},
    'Boeing 737-700':   {'cols': ['A','B','C','D','E','F'], 'rows': 25},
    'Boeing 737 MAX 8': {'cols': ['A','B','C','D','E','F'], 'rows': 34},
    'ATR 72-600':       {'cols': ['A','C','D','F'],         'rows': 18}
}

st.set_page_config(page_title="BlueHorizon OLTP", layout="wide")

st.markdown("""
<style>
    .ticket-container { background-color: white; border: 1px solid #ddd; border-radius: 10px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; font-family: 'Courier New', monospace; background-image: radial-gradient(circle at 0 50%, transparent 10px, white 11px), radial-gradient(circle at 100% 50%, transparent 10px, white 11px); background-position: 0 0, 100% 0; background-size: 51% 100%; background-repeat: no-repeat; border-left: 2px dashed #bbb; border-right: 2px dashed #bbb; }
    .ticket-header { font-size: 1.2rem; font-weight: bold; color: #004b8d; border-bottom: 2px dashed #ccc; padding-bottom: 10px; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 2px; display: flex; justify-content: space-between; }
    .ticket-body { display: flex; justify-content: space-between; margin-bottom: 15px; }
    .ticket-field { display: flex; flex-direction: column; }
    .label { font-size: 0.8rem; color: #888; text-transform: uppercase; }
    .value { font-size: 1.1rem; font-weight: bold; color: #333; }
    h1 { color: #004b8d; }
</style>
""", unsafe_allow_html=True)

# meniu navigare
menu_options = ["Gestiune Baze Locale", "Vizualizare Bază Globală", "Administrare Globală"]

# luam pagina din url (pentru a pastra starea de refresh)
current_query_params = st.query_params
default_index = 0
if "page" in current_query_params:
    try:
        default_index = menu_options.index(current_query_params["page"])
    except ValueError:
        pass

page = st.sidebar.selectbox("Navigare Proiect", menu_options, index=default_index)

# actualizam url-ul cu pagina curenta
st.query_params["page"] = page

# buton refresh date
if st.sidebar.button("🔄 Reîncarcă Datele"):
    st.rerun()

if page == "Gestiune Baze Locale":
    st.title("✈️ BlueHorizon - Gestiune Baze Locale")
    
    # selectare nodul in sidebar
    st.sidebar.header("Configurare Conexiune")
    selected_node_label = st.sidebar.selectbox("Selectează Nodul Activ", ["America (BD_AM)", "Europa (BD_EU)"])
    NODE = "AM" if "AM" in selected_node_label else "EU"
    st.sidebar.success(f"Conectat la: **BD_{NODE}**")
    
    # def sufix tabele si pasager local/remote
    TBL_SUFIX = f"_{NODE}"
    # Accesul la PASAGER difera: pe AM e local, pe EU e via DB Link
    PASAGER_TBL = "PASAGER" if NODE == "AM" else "PASAGER@link_bd_am"
    
    st.header(f"🛠️ Operațiuni LMD pe Serverul {NODE}")
    
    if NODE == "AM":
        tab1, tab2, tab3, tab4 = st.tabs([
            "1. Emitere Bilet (Insert)",
            "2. Gestiune Plăți (Update Orizontal)",
            "3. Istoric Rezervări (Vizualizare)",
            "4. Demonstrație LMD Local"
        ])
    else:
        tab1, tab2, tab3 = st.tabs([
            "1. Emitere Bilet (Insert)",
            "2. Gestiune Plăți (Update Orizontal)",
            "3. Istoric Rezervări (Vizualizare)"
        ])

    # TAB 1: EMITERE BILET (INSERT TRANZACTII)
    with tab1:
        st.subheader("Creează o nouă rezervare")
        st.info(f"Tranzacția se salvează local în tabelele REZERVARE{TBL_SUFIX}, PLATA{TBL_SUFIX} și BILET{TBL_SUFIX}.")
        
        try:
            conn = database.get_connection(NODE)
            
            # 1. Preluare aeroporturi de plecare cu zboruri programate
            sql_dep = """
                SELECT DISTINCT a.id_aeroport, o.nume_oras || ' (' || a.cod_iata || ')'
                FROM ZBOR z
                JOIN AEROPORT a ON z.id_aeroport_plecare = a.id_aeroport
                JOIN ORAS o ON a.id_oras = o.id_oras
                WHERE z.status = 'PROGRAMAT'
                ORDER BY 2
            """
            cols_dep, rows_dep = database.run_query(conn, sql_dep)
            dict_dep = {r[1]: r[0] for r in rows_dep}
            
            col_ruta1, col_ruta2, col_ruta3 = st.columns(3)
            with col_ruta1:
                sel_dep_label = st.selectbox("1. Plecare", list(dict_dep.keys()))
                id_dep = dict_dep[sel_dep_label]
                
            # 2. Preluare aeroporturi de sosire disponibile din plecarea selectata
            sql_arr = """
                SELECT DISTINCT a.id_aeroport, o.nume_oras || ' (' || a.cod_iata || ')'
                FROM ZBOR z
                JOIN AEROPORT a ON z.id_aeroport_sosire = a.id_aeroport
                JOIN ORAS o ON a.id_oras = o.id_oras
                WHERE z.status = 'PROGRAMAT' AND z.id_aeroport_plecare = :1
                ORDER BY 2
            """
            cols_arr, rows_arr = database.run_query(conn, sql_arr, [id_dep])
            dict_arr = {r[1]: r[0] for r in rows_arr}
            
            with col_ruta2:
                sel_arr_label = st.selectbox("2. Sosire", list(dict_arr.keys()))
                id_arr = dict_arr[sel_arr_label]
                
            # 3. Preluare zboruri specifice pentru ruta aleasa
            sql_zboruri = """
                SELECT z.id_zbor,
                       z.numar_zbor || ' | ' || TO_CHAR(z.data_plecare, 'YYYY-MM-DD HH24:MI'),
                       z.pret_standard,
                       av.model
                FROM ZBOR z
                JOIN AVION av ON z.id_avion = av.id_avion
                WHERE z.status = 'PROGRAMAT' AND z.id_aeroport_plecare = :1 AND z.id_aeroport_sosire = :2
                ORDER BY z.data_plecare
            """
            cols_z, rows_z = database.run_query(conn, sql_zboruri, [id_dep, id_arr])
            
            if not rows_z:
                st.warning("Nu există zboruri programate pe această rută.")
            else:
                dict_zbor = {r[1]: {'id': r[0], 'pret': r[2], 'model': r[3]} for r in rows_z}
                
                with col_ruta3:
                    sel_zbor_label = st.selectbox("3. Alege Zborul", list(dict_zbor.keys()))
                    zbor_selectat = dict_zbor[sel_zbor_label]
                    pret_standard = float(zbor_selectat['pret'])
                    model_avion = zbor_selectat['model']
                
                # 4. Detalii Pasager si Utilizator
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    cols_u, rows_u = database.run_query(conn, "SELECT id_user, nume || ' ' || prenume FROM UTILIZATOR_DATA WHERE ROWNUM <= 100")
                    user_dict = {f"{r[1]} (ID: {r[0]})": r[0] for r in rows_u}
                    selected_user = st.selectbox("Cumpărător (Utilizator)", list(user_dict.keys()))
                    
                with col_p2:
                    cols_p, rows_p = database.run_query(conn, f"SELECT id_pasager, nume || ' ' || prenume FROM {PASAGER_TBL} WHERE ROWNUM <= 100")
                    pasager_dict = {f"{r[1]} (ID: {r[0]})": r[0] for r in rows_p}
                    selected_pasager = st.selectbox("Călător (Pasager)", list(pasager_dict.keys()))
                
                # 5. Configurare Bilet si Calcul Pret
                st.write("---")
                col_b1, col_b2, col_b3, col_b4 = st.columns(4)
                
                with col_b1:
                    clasa = st.selectbox("Clasa", ["ECONOMY", "BUSINESS"])
                    
                with col_b2:
                    specs = PLANE_SPECS.get(model_avion, {'cols': ['A','B','C','D','E','F'], 'rows': 30})
                    rand = st.number_input(f"Rând (Max: {specs['rows']})", min_value=1, max_value=specs['rows'], value=1)
                    
                with col_b3:
                    scaun = st.selectbox("Scaun", specs['cols'])
                    
                with col_b4:
                    # Calcul backend
                    pret_final = pret_standard * 1.5 if clasa == "BUSINESS" else pret_standard
                    st.metric(label="Preț Final de Plată", value=f"{pret_final:.2f} EUR")

                if st.button("Procesează Rezervarea și Plata"):
                    id_u = user_dict[selected_user]
                    id_z = zbor_selectat['id']
                    id_p = pasager_dict[selected_pasager]
                    
                    plsql_code = f"""
                    DECLARE
                        v_rez_id NUMBER;
                    BEGIN
                        -- 1. Insert Rezervare
                        INSERT INTO REZERVARE_{NODE} (id_user, data_rezervare, regiune_vanzare, total_de_plata, status)
                        VALUES (:1, SYSDATE, '{NODE}', :2, 'CONFIRMATA')
                        RETURNING id_rezervare INTO v_rez_id;

                        -- 2. Insert Plata
                        INSERT INTO PLATA_{NODE} (id_rezervare, suma_achitata, metoda_plata, status)
                        VALUES (v_rez_id, :2, 'CARD', 'ACCEPTATA');

                        -- 3. Insert Bilet
                        INSERT INTO BILET_{NODE} (id_rezervare, id_zbor, id_pasager, numar_rand, litera_scaun, clasa, pret_final)
                        VALUES (v_rez_id, :3, :4, :5, :6, :7, :2);
                    END;
                    """
                    try:
                        # Folosim pret_final si clasa in loc de cele statice
                        database.run_statement(conn, plsql_code, [id_u, pret_final, id_z, id_p, rand, scaun, clasa])
                        
                        st.markdown(f"""
                        <div class="ticket-container">
                            <div class="ticket-header">
                                <span>BOARDING PASS - BD_{NODE}</span>
                                <span>{sel_zbor_label.split(' | ')[0]}</span>
                            </div>
                            <div class="ticket-body">
                                <div class="ticket-field">
                                    <span class="label">Pasager</span>
                                    <span class="value">{selected_pasager.split(' (')[0]}</span>
                                </div>
                                <div class="ticket-field">
                                    <span class="label">Rută</span>
                                    <span class="value">{sel_dep_label} -> {sel_arr_label}</span>
                                </div>
                                <div class="ticket-field">
                                    <span class="label">Clasă & Loc</span>
                                    <span class="value">{clasa} | {rand}{scaun}</span>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.success("Tranzacție finalizată cu succes!")
                        st.info("📌 **Pentru demonstrație în SQL Developer:**")
                        st.code(f"-- Conectează-te pe BD_{NODE} și verifică datele noi:\nSELECT * FROM REZERVARE_{NODE} ORDER BY id_rezervare DESC FETCH FIRST 1 ROWS ONLY;\nSELECT * FROM PLATA_{NODE} ORDER BY id_plata DESC FETCH FIRST 1 ROWS ONLY;\nSELECT * FROM BILET_{NODE} ORDER BY id_bilet DESC FETCH FIRST 1 ROWS ONLY;", language="sql")
                        st.balloons()
                    except Exception as ex:
                        st.error(f"Eroare la inserare (ex: Constângere de unicitate loc sau rețea): {ex}")
                        
            conn.close()
        except Exception as e:
            st.error(f"Eroare conexiune: {e}")
            
    # TAB 2: GESTIUNE PLATI LOCALE
    with tab2:
        st.subheader("Gestiune Plăți Locale (Actualizare Status)")
        st.write(f"Procesare tranzacții financiare pentru nodul {NODE}.")
        
        try:
            conn = database.get_connection(NODE)
            
            # 1. Extragem cele mai recente plati locale (limitam la 20)
            sql_plati = f"SELECT id_plata, id_rezervare, suma_achitata, status FROM PLATA_{NODE} ORDER BY id_plata DESC FETCH FIRST 20 ROWS ONLY"
            cols_p, rows_p = database.run_query(conn, sql_plati)
            
            if rows_p:
                # Cream un dictionar pentru dropdown-ul din UI
                # Format: "Plata #12 (Rez: #10) - Suma: 350 - Status: IN_PROCESARE" -> id_plata
                plati_opt = {f"Plata #{r[0]} (Rez: #{r[1]}) - Suma: {r[2]} - Status curent: {r[3]}": r[0] for r in rows_p}
                
                sel_plata_label = st.selectbox("Selectează plata pe care dorești să o procesezi:", list(plati_opt.keys()))
                id_plata_sel = plati_opt[sel_plata_label]
                
                # 2. Selectam noul status (valorile trebuie sa respecte constrangerea CHECK din baza de date)
                nou_status = st.selectbox("Noul Status:", ['IN_PROCESARE', 'ACCEPTATA', 'RESPINSA', 'RAMBURSATA'])
                
                if st.button("Actualizează Status Plată"):
                    # 3. Executam UPDATE-ul exclusiv pe tabelul fizic local
                    update_sql = f"UPDATE PLATA_{NODE} SET status = :1 WHERE id_plata = :2"
                    database.run_statement(conn, update_sql, [nou_status, id_plata_sel])
                    
                    st.success(f"Statusul plății #{id_plata_sel} a fost actualizat la '{nou_status}' pe serverul local BD_{NODE}.")
                    
                    st.info("📌 **Pentru demonstrație în SQL Developer:**")
                    st.code(
                        f"SELECT * FROM PLATA_{NODE} WHERE id_plata = {id_plata_sel};", 
                        language="sql"
                    )
            else:
                st.info(f"Nu există plăți înregistrate pe nodul {NODE} în acest moment.")
                
            conn.close()
        except Exception as e:
            st.error(f"Eroare: {e}")

    # TAB 3: ISTORIC REZERVARI LOCALE
    with tab3:
        st.subheader(f"Ultimele rezervări procesate pe BD_{NODE}")
        try:
            conn = database.get_connection(NODE)
            sql_istoric = f"""
                SELECT * FROM (
                    SELECT R.*, U.nume || ' ' || U.prenume AS Client
                    FROM REZERVARE_{NODE} R
                    JOIN UTILIZATOR_DATA U ON R.id_user = U.id_user
                    ORDER BY R.id_rezervare DESC
                ) WHERE ROWNUM <= 15
            """
            cols_i, rows_i = database.run_query(conn, sql_istoric)
            if rows_i:
                df_istoric = pd.DataFrame(rows_i, columns=cols_i)
                st.dataframe(df_istoric, use_container_width=True)
                st.caption("Atenție: Pe BD_AM id-urile sunt impare, pe BD_EU sunt pare.")
            else:
                st.info("Nicio rezervare găsită pe acest nod.")
            conn.close()
        except Exception as e:
            st.error(f"Eroare: {e}")

    # TAB 4: DOAR PE BD_AM — toate cele 3 tipuri de fragmentare (Cerinta 3)
    if NODE == "AM":
        with tab4:
            st.subheader("Demonstrație LMD Local → Efect Global")
            st.info(
                "Toate operațiile de mai jos se execută **local pe BD_AM**. "
                "Efectele lor sunt vizibile imediat la nivel global prin vederile și sinonimele schemei BD_GLOBAL."
            )

            sec_oriz, sec_vert, sec_repl = st.tabs([
                "A. Fragment Orizontal (PLATA_AM)",
                "B. Fragment Vertical (UTILIZATOR_DATA)",
                "C. Relație Replicată (AVION)"
            ])

            # SECTIUNEA C: FRAGMENT ORIZONTAL
            with sec_oriz:
                st.write(
                    "**Operație locală:** UPDATE status pe `PLATA_AM` (BD_AM) → "
                    "modificarea apare imediat în vederea globală `V_PLATA` (UNION ALL cu PLATA_EU)."
                )
                try:
                    conn = database.get_connection("AM")
                    cols_p, rows_p = database.run_query(
                        conn,
                        "SELECT id_plata, id_rezervare, suma_achitata, status "
                        "FROM PLATA_AM ORDER BY id_plata DESC FETCH FIRST 20 ROWS ONLY"
                    )
                    if rows_p:
                        plati_opt = {
                            f"Plata #{r[0]} (Rez: #{r[1]}) - Suma: {r[2]} - Status: {r[3]}": r[0]
                            for r in rows_p
                        }
                        sel_plata = st.selectbox(
                            "Selectează plata (PLATA_AM local)",
                            list(plati_opt.keys()),
                            key="demo_sel_plata"
                        )
                        id_plata_demo = plati_opt[sel_plata]
                        nou_status_oriz = st.selectbox(
                            "Noul Status:",
                            ['IN_PROCESARE', 'ACCEPTATA', 'RESPINSA', 'RAMBURSATA'],
                            key="demo_status_oriz"
                        )
                        if st.button("Actualizează Status Local (Fragment Orizontal)"):
                            database.run_statement(
                                conn,
                                "UPDATE PLATA_AM SET status = :1 WHERE id_plata = :2",
                                [nou_status_oriz, id_plata_demo]
                            )
                            st.success(
                                f"Statusul plății #{id_plata_demo} actualizat la '{nou_status_oriz}' pe BD_AM."
                            )
                            st.info("📌 **Pentru demonstrație în SQL Developer:**")
                            st.code(
                                f"-- 1. Pe BD_AM (fragmentul orizontal local modificat):\n"
                                f"SELECT id_plata, status FROM PLATA_AM WHERE id_plata = {id_plata_demo};\n\n"
                                f"-- 2. La nivel GLOBAL (vizibil in V_PLATA prin UNION ALL cu PLATA_EU):\n"
                                f"SELECT id_plata, status FROM V_PLATA WHERE id_plata = {id_plata_demo};",
                                language="sql"
                            )
                    else:
                        st.info("Nu există plăți pe BD_AM.")
                    conn.close()
                except Exception as e:
                    st.error(f"Eroare: {e}")

            # SECTIUNEA A: FRAGMENT VERTICAL
            with sec_vert:
                st.write(
                    "**Operație locală:** UPDATE telefon pe `UTILIZATOR_DATA` (BD_AM) → "
                    "propagat automat pe BD_EU prin trigger-ul `trg_sync_utilizator_data_am_eu` → "
                    "modificarea apare imediat în `V_UTILIZATOR` la nivel global (JOIN vertical)."
                )
                try:
                    conn = database.get_connection("AM")
                    cols_u, rows_u = database.run_query(
                        conn,
                        "SELECT id_user, nume || ' ' || prenume || ' (Tel: ' || NVL(telefon, 'N/A') || ')' "
                        "FROM UTILIZATOR_DATA WHERE ROWNUM <= 20"
                    )
                    if rows_u:
                        user_vert_opt = {r[1]: r[0] for r in rows_u}
                        sel_vert_u = st.selectbox(
                            "Selectează Utilizatorul (UTILIZATOR_DATA local)",
                            list(user_vert_opt.keys()),
                            key="sel_vert_u"
                        )
                        u_vert_id = user_vert_opt[sel_vert_u]
                        new_tel = st.text_input(
                            "Număr Telefon Nou", placeholder="ex: 0721000001", key="new_tel"
                        )
                        if st.button("Actualizează Telefon Local (Fragment Vertical)"):
                            if new_tel:
                                database.run_statement(
                                    conn,
                                    "UPDATE UTILIZATOR_DATA SET telefon = :1 WHERE id_user = :2",
                                    [new_tel, u_vert_id]
                                )
                                st.success(
                                    f"Telefonul utilizatorului ID={u_vert_id} actualizat local pe BD_AM."
                                )
                                st.success(
                                    "✅ Trigger-ul `trg_sync_utilizator_data_am_eu` s-a declanșat "
                                    "automat și a propagat modificarea pe BD_EU."
                                )
                                st.info("📌 **Pentru demonstrație în SQL Developer:**")
                                st.code(
                                    f"-- 1. Pe BD_AM (sursa fragmentului vertical):\n"
                                    f"SELECT id_user, telefon FROM UTILIZATOR_DATA WHERE id_user = {u_vert_id};\n\n"
                                    f"-- 2. Pe BD_EU (propagat automat prin trg_sync_utilizator_data_am_eu):\n"
                                    f"SELECT id_user, telefon FROM UTILIZATOR_DATA WHERE id_user = {u_vert_id};\n\n"
                                    f"-- 3. La nivel GLOBAL (vizibil in V_UTILIZATOR prin JOIN vertical AM+EU):\n"
                                    f"SELECT id_user, nume, prenume, telefon FROM V_UTILIZATOR WHERE id_user = {u_vert_id};",
                                    language="sql"
                                )
                            else:
                                st.warning("Introdu un număr de telefon valid.")
                    else:
                        st.info("Nu s-au găsit utilizatori pe BD_AM.")
                    conn.close()
                except Exception as e:
                    st.error(f"Eroare: {e}")

            # SECTIUNEA B: RELATIE REPLICATA
            with sec_repl:
                st.write(
                    "**Operație locală:** UPDATE capacitate pe `AVION` (BD_AM) → "
                    "propagat automat pe BD_EU prin trigger-ul `trg_sync_avion_am_eu` → "
                    "modificarea apare imediat prin sinonimul global `AVION` (pointează pe BD_AM)."
                )
                try:
                    conn = database.get_connection("AM")
                    cols_av, rows_av = database.run_query(
                        conn,
                        "SELECT id_avion, numar_inmatriculare || ' | ' || model || "
                        "' (cap: ' || capacitate || ' locuri)' FROM AVION WHERE ROWNUM <= 20"
                    )
                    if rows_av:
                        avion_opt = {r[1]: r[0] for r in rows_av}
                        sel_avion = st.selectbox(
                            "Selectează Avionul (AVION local)",
                            list(avion_opt.keys()),
                            key="sel_avion"
                        )
                        av_id = avion_opt[sel_avion]
                        new_cap = st.number_input(
                            "Capacitate Nouă (locuri)", min_value=1, max_value=850, value=150, key="new_cap"
                        )
                        if st.button("Actualizează Capacitate Local (Relație Replicată)"):
                            database.run_statement(
                                conn,
                                "UPDATE AVION SET capacitate = :1 WHERE id_avion = :2",
                                [new_cap, av_id]
                            )
                            st.success(
                                f"Capacitatea avionului ID={av_id} actualizată la {new_cap} locuri pe BD_AM."
                            )
                            st.success(
                                "✅ Trigger-ul `trg_sync_avion_am_eu` s-a declanșat automat "
                                "și a propagat modificarea pe BD_EU."
                            )
                            st.info("📌 **Pentru demonstrație în SQL Developer:**")
                            st.code(
                                f"-- 1. Pe BD_AM (tabela sursa a relatiei replicate):\n"
                                f"SELECT model, capacitate FROM AVION WHERE id_avion = {av_id};\n\n"
                                f"-- 2. Pe BD_EU (propagat automat prin trg_sync_avion_am_eu):\n"
                                f"SELECT model, capacitate FROM AVION WHERE id_avion = {av_id};\n\n"
                                f"-- 3. La nivel GLOBAL (prin sinonimul AVION -> BD_AM):\n"
                                f"SELECT model, capacitate FROM AVION WHERE id_avion = {av_id};",
                                language="sql"
                            )
                    else:
                        st.info("Nu s-au găsit avioane pe BD_AM.")
                    conn.close()
                except Exception as e:
                    st.error(f"Eroare: {e}")

elif page == "Vizualizare Bază Globală":
    st.title("🌍 BlueHorizon - Vizualizare Bază Globală")
    st.sidebar.success("Conectat la: BD_GLOBAL")
    
    st.info("Ești conectat la schema **BD_GLOBAL**. Datele afișate aici sunt reconstruite automat din fragmentele aflate pe BD_AM și BD_EU prin vederi.")
    
    try:
        conn = database.get_connection("GLOBAL")
        tab_oriz, tab_vert, tab_repl = st.tabs(["1. BILET – Fragmente Orizontale (UNION)", "2. UTILIZATOR – Fragmente Verticale (JOIN)", "3. ZBOR – Relații Replicate (SINONIM)"])
        
        with tab_oriz:
            st.subheader("Vizualizare Fragmente Orizontale Reconstruite")
            st.write("Vizualizarea `V_BILET` face `UNION ALL` între `BILET_AM` și `BILET_EU`.")
            
            sql_bilete = """
                SELECT * FROM (
                    SELECT b.ID_BILET, b.ID_REZERVARE, b.ID_ZBOR, b.ID_PASAGER, 
                           b.NUMAR_RAND, b.LITERA_SCAUN, b.CLASA, b.PRET_FINAL,
                           r.regiune_vanzare AS "Regiune", r.status AS STATUS_REZERVARE
                    FROM V_BILET b
                    JOIN V_REZERVARE r ON b.id_rezervare = r.id_rezervare
                    ORDER BY b.id_bilet DESC
                ) WHERE ROWNUM <= 100
            """
            cols_b, rows_b = database.run_query(conn, sql_bilete)
            if rows_b:
                df_b = pd.DataFrame(rows_b, columns=cols_b)
                def color_regiune(val):
                    color = '#e6f2ff' if val == 'AM' else '#f0f9e8'
                    return f'background-color: {color}'
                
                st.dataframe(df_b.style.map(color_regiune, subset=['Regiune']), use_container_width=True)
                st.caption("Notă: Rândurile albastre provin din fragmentul AM, cele verzi din fragmentul EU.")
                
        with tab_vert:
            st.subheader("Vizualizare Fragmente Verticale Reconstruite")
            st.write("Vizualizarea `V_UTILIZATOR` face `JOIN` între datele distribuite de profil și securitate.")
            
            sql_utilizatori = """
                SELECT * FROM (
                    SELECT id_user, nume, prenume, email, parola, telefon, data_inregistrare, rol
                    FROM V_UTILIZATOR
                    ORDER BY id_user
                ) WHERE ROWNUM <= 50
            """
            cols_u, rows_u = database.run_query(conn, sql_utilizatori)
            if rows_u:
                df_u = pd.DataFrame(rows_u, columns=cols_u)
                st.dataframe(df_u, use_container_width=True)

        with tab_repl:
            st.subheader("Vizualizare Relații Replicate")
            st.write("Tabelul `ZBOR` este accesat transparent printr-un sinonim, reflectând modificările realizate pe orice nod local.")
            
            sql_zbor_global = """
                SELECT * FROM (
                    SELECT ID_ZBOR, ID_AVION, ID_AEROPORT_PLECARE, ID_AEROPORT_SOSIRE, 
                           NUMAR_ZBOR, DATA_PLECARE, DATA_SOSIRE, DATA_PLECARE_EFECTIVA, 
                           DATA_SOSIRE_EFECTIVA, DURATA_ESTIMATA, PRET_STANDARD, STATUS
                    FROM ZBOR
                    ORDER BY DATA_PLECARE DESC
                ) WHERE ROWNUM <= 50
            """
            cols_z, rows_z = database.run_query(conn, sql_zbor_global)
            if rows_z:
                df_z = pd.DataFrame(rows_z, columns=cols_z)
                st.dataframe(df_z, use_container_width=True)

        conn.close()
    except Exception as e:
        st.error(f"Eroare conexiune: {e}")

elif page == "Administrare Globală":
    st.title("⚖️ BlueHorizon - Administrare Globală")
    st.sidebar.success("Conectat la: **BD_GLOBAL** (Nivel LMD)")
    try:
        conn = database.get_connection("GLOBAL")
        tab_upd_oriz, tab_upd_vert, tab_upd_repl = st.tabs(["Update Global (Orizontal)", "Update Global (Vertical)", "Update Global (Replicat)"])

        # UPDATE PE FRAGMENTE ORIZONTALE
        with tab_upd_oriz:
            st.subheader("Anulare Rezervare la Nivel Global")
            st.write(
                "Trigger-ul `trg_upd_rezervare_global` (INSTEAD OF UPDATE ON V_REZERVARE) "
                "rutează automat update-ul spre `REZERVARE_AM` (ID impar) sau `REZERVARE_EU` (ID par). "
                "Deoarece `V_PLATA` nu are un trigger INSTEAD OF echivalent, actualizarea plății "
                "se face explicit prin DB Link spre ambele fragmente (rândul există doar pe unul)."
            )
            
            sql_sel = 'SELECT * FROM (SELECT id_rezervare, regiune_vanzare AS "Regiune", status FROM V_REZERVARE WHERE status != \'ANULATA\' ORDER BY id_rezervare DESC) WHERE ROWNUM <= 10'
            cols, rows = database.run_query(conn, sql_sel)
            if rows:
                rez_options = {f"Rez #{r[0]} ({r[1]}) - Status: {r[2]}": r[0] for r in rows}
                sel_rez = st.selectbox("Selectează Rezervarea Globală", list(rez_options.keys()))
                id_to_cancel = rez_options[sel_rez]

                if st.button("Anulează Rezervarea Global"):
                    # REZERVARE: trigger-ul INSTEAD OF (trg_upd_rezervare_global) ruteaza automat
                    # pe fragmentul corect (AM daca ID impar, EU daca ID par).
                    # PLATA: nu are trigger INSTEAD OF, deci facem update direct pe ambele fragmente;
                    # randul exista doar pe unul, pe celalalt UPDATE-ul afecteaza 0 randuri.
                    plsql_cancel = """
                    BEGIN
                        -- Folosim VIEW-ul: trigger-ul INSTEAD OF rutează spre AM sau EU automat
                        UPDATE V_REZERVARE SET status = 'ANULATA' WHERE id_rezervare = :1;
                        -- PLATA nu are trigger INSTEAD OF, update direct pe ambele fragmente
                        UPDATE PLATA_AM@link_bd_am SET status = 'RAMBURSATA' WHERE id_rezervare = :1;
                        UPDATE PLATA_EU@link_bd_eu SET status = 'RAMBURSATA' WHERE id_rezervare = :1;
                    END;
                    """
                    database.run_statement(conn, plsql_cancel, [id_to_cancel])
                    st.success(f"Rezervarea {id_to_cancel} și Plata asociată au fost actualizate global!")

                    st.info("📌 **Pentru demonstrație în SQL Developer:**")
                    node_tip = "impar → BD_AM" if id_to_cancel % 2 != 0 else "par → BD_EU"
                    st.code(f"""-- ID {id_to_cancel} este {node_tip}
-- trg_upd_rezervare_global a ruteat UPDATE-ul pe VIEW spre fragmentul corect.

-- Baza BD_AM (va conține rândul dacă ID impar):
SELECT status FROM REZERVARE_AM WHERE id_rezervare = {id_to_cancel};
SELECT status FROM PLATA_AM WHERE id_rezervare = {id_to_cancel};

-- Baza BD_EU (va conține rândul dacă ID par):
SELECT status FROM REZERVARE_EU WHERE id_rezervare = {id_to_cancel};
SELECT status FROM PLATA_EU WHERE id_rezervare = {id_to_cancel};""", language="sql")
                    
                    st.divider()
                    st.subheader("🔍 Verificarea Integrității pe Noduri")
                    st.write("Verificăm dacă atât Rezervarea cât și Plata s-au actualizat pe fragmentul local corespunzător:")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write("**Nod AM (REZERVARE & PLATA)**")
                        conn_am = database.get_connection("AM")
                        res_am = database.run_query(conn_am, 
                            "SELECT r.id_rezervare, r.status as status_rez, p.status as status_plata FROM REZERVARE_AM r JOIN PLATA_AM p ON r.id_rezervare = p.id_rezervare WHERE r.id_rezervare = :1", [id_to_cancel])
                        conn_am.close()
                        if res_am[1]:
                            st.json(dict(zip(res_am[0], res_am[1][0])))
                        else:
                            st.write("❌ Rândul nu aparține acestui fragment.")
                            
                    with c2:
                        st.write("**Nod EU (REZERVARE & PLATA)**")
                        conn_eu = database.get_connection("EU")
                        res_eu = database.run_query(conn_eu, 
                            "SELECT r.id_rezervare, r.status as status_rez, p.status as status_plata FROM REZERVARE_EU r JOIN PLATA_EU p ON r.id_rezervare = p.id_rezervare WHERE r.id_rezervare = :1", [id_to_cancel])
                        conn_eu.close()
                        if res_eu[1]:
                            st.json(dict(zip(res_eu[0], res_eu[1][0])))
                        else:
                            st.write("❌ Rândul nu aparține acestui fragment.")

        # UPDATE PE FRAGMENTE VERTICALE
        with tab_upd_vert:
            st.subheader("Modificare Nume Utilizator Global")
            st.write(
                "Trigger-ul `trg_upd_utilizator_global` (INSTEAD OF UPDATE ON V_UTILIZATOR) "
                "interceptează update-ul pe view și îl redirecționează spre `UTILIZATOR_DATA@link_bd_am`. "
                "La rândul lui, trigger-ul `trg_sync_utilizator_data_am_eu` de pe BD_AM "
                "propagă automat modificarea și pe BD_EU. Lanțul complet: "
                "**Global UPDATE V_UTILIZATOR → AM (INSTEAD OF) → EU (sync trigger)**."
            )
            
            sql_u = "SELECT * FROM (SELECT id_user, nume, prenume FROM V_UTILIZATOR) WHERE ROWNUM <= 10"
            cols_u, rows_u = database.run_query(conn, sql_u)
            user_opt = {f"ID {r[0]}: {r[1]} {r[2]}": r[0] for r in rows_u}
            sel_u = st.selectbox("Selectează Utilizatorul Global", list(user_opt.keys()))
            u_id = user_opt[sel_u]
            new_nume = st.text_input("Nume Nou")

            if st.button("Actualizează Nume Global"):
                database.run_statement(conn, "UPDATE V_UTILIZATOR SET nume = :1 WHERE id_user = :2", [new_nume, u_id])
                st.success("Numele a fost actualizat la nivel global prin lanțul de triggere!")

                st.info("📌 **Pentru demonstrație în SQL Developer:**")
                st.code(
                    f"-- Lanț triggere: Global → trg_upd_utilizator_global → AM → trg_sync_utilizator_data_am_eu → EU\n\n"
                    f"-- 1. Pe BD_GLOBAL (sursa UPDATE-ului pe view):\n"
                    f"UPDATE V_UTILIZATOR SET nume = 'NoumeNou' WHERE id_user = {u_id};\n\n"
                    f"-- 2. Pe BD_AM (unde INSTEAD OF a scris efectiv):\n"
                    f"SELECT nume FROM UTILIZATOR_DATA WHERE id_user = {u_id};\n\n"
                    f"-- 3. Pe BD_EU (propagat automat prin trg_sync_utilizator_data_am_eu):\n"
                    f"SELECT nume FROM UTILIZATOR_DATA WHERE id_user = {u_id};",
                    language="sql"
                )
                
                st.divider()
                st.subheader("🔍 Verificarea Propagării Verticale (Lanț 2 Triggere)")
                st.write("Modificarea pornită de la Global a traversat automat AM și a ajuns pe EU:")
                c1, c2 = st.columns(2)
                with c1:
                    st.write("**Nod AM (scris de `trg_upd_utilizator_global`)**")
                    conn_am = database.get_connection("AM")
                    res_am = database.run_query(conn_am, "SELECT id_user, nume FROM UTILIZATOR_DATA WHERE id_user = :1", [u_id])
                    conn_am.close()
                    st.write(res_am[1])
                with c2:
                    st.write("**Nod EU (propagat de `trg_sync_utilizator_data_am_eu`)**")
                    conn_eu = database.get_connection("EU")
                    res_eu = database.run_query(conn_eu, "SELECT id_user, nume FROM UTILIZATOR_DATA WHERE id_user = :1", [u_id])
                    conn_eu.close()
                    st.write(res_eu[1])

        # UPDATE PE RELATII REPLICATE
        with tab_upd_repl:
            st.subheader("Actualizare Preț Zbor Global")
            st.write("Modificăm prețul prin sinonimul global `ZBOR`. Modificarea se face pe `BD_AM`.")
            
            sql_z = "SELECT * FROM (SELECT id_zbor, numar_zbor, pret_standard FROM ZBOR) WHERE ROWNUM <= 10"
            cols_z, rows_z = database.run_query(conn, sql_z)
            zbor_opt = {f"{r[1]} - Preț actual: {r[2]} EUR": r[0] for r in rows_z}
            sel_z = st.selectbox("Selectează Zborul Global", list(zbor_opt.keys()))
            z_id = zbor_opt[sel_z]
            new_price = st.number_input("Preț Nou", min_value=1.0)

            if st.button("Actualizează Preț Global"):
                database.run_statement(conn, "UPDATE ZBOR SET pret_standard = :1 WHERE id_zbor = :2", [new_price, z_id])
                st.success("Prețul a fost actualizat pe nodul master (AM)!")
                
                st.info("📌 **Pentru demonstrație în SQL Developer:**")
                st.code(f"-- 1. Pe BD_AM (Tabela Sursă are noul preț):\nSELECT pret_standard FROM ZBOR WHERE id_zbor = {z_id};\n\n-- 2. Pe BD_EU (Materialized View are VECHIUL preț până la Refresh):\nSELECT pret_standard FROM ZBOR WHERE id_zbor = {z_id};", language="sql")
                
                st.session_state['last_z_id'] = z_id # salvam ID-ul pentru refresh-ul de mai jos
                
            if 'last_z_id' in st.session_state:
                st.divider()
                st.subheader("🔍 Verificarea Propagării (Materialized View)")
                c1, c2 = st.columns(2)
                with c1:
                    st.write("**Nod AM (Master Table)**")
                    conn_am = database.get_connection("AM")
                    res_am = database.run_query(conn_am, "SELECT numar_zbor, pret_standard FROM ZBOR WHERE id_zbor = :1", [st.session_state['last_z_id']])
                    conn_am.close()
                    st.json(dict(zip(res_am[0], res_am[1][0])))
                with c2:
                    st.write("**Nod EU (Materialized View)**")
                    conn_eu = database.get_connection("EU")
                    res_eu = database.run_query(conn_eu, "SELECT numar_zbor, pret_standard FROM ZBOR WHERE id_zbor = :1", [st.session_state['last_z_id']])
                    conn_eu.close()
                    st.json(dict(zip(res_eu[0], res_eu[1][0])))
                    if st.button("⚡ Execută Refresh MView (Sincronizare Manuală)"):
                        refresh_plsql = """
                        BEGIN
                            -- Dezactivăm FK-ul temporar pentru a permite mecanismului de FAST REFRESH sa modifice rândurile
                            EXECUTE IMMEDIATE 'ALTER TABLE BILET_EU DISABLE CONSTRAINT fk_bil_zbor_eu';
                            
                            -- Rulăm refresh-ul
                            DBMS_MVIEW.REFRESH('ZBOR', 'F');
                            
                            -- Reactivăm FK-ul (validând datele)
                            EXECUTE IMMEDIATE 'ALTER TABLE BILET_EU ENABLE CONSTRAINT fk_bil_zbor_eu';
                        END;
                        """
                        conn_refresh = database.get_connection("EU")
                        database.run_statement(conn_refresh, refresh_plsql)
                        conn_refresh.close()
                        st.success("Refresh executat cu succes pe BD_EU!")
                        st.info("📌 **Pentru demonstrație în SQL Developer:**")
                        st.code(f"-- Execută codul ăsta pe BD_EU:\nSELECT pret_standard FROM ZBOR WHERE id_zbor = {st.session_state['last_z_id']};\n-- *Acum prețul de pe EU este aliniat cu cel de pe AM!*", language="sql")

        conn.close()
    except Exception as e:
        st.error(f"Eroare: {e}")
