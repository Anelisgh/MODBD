import streamlit as st
import pandas as pd
import database
import time

# Configurare specificatii avioane pentru validare UI
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

# Meniul principal de navigare
menu_options = ["Gestiune Baze Locale", "Vizualizare Bază Globală", "Administrare Globală"]

# Recuperare pagina din URL (pentru a păstra starea la refresh)
current_query_params = st.query_params
default_index = 0
if "page" in current_query_params:
    try:
        default_index = menu_options.index(current_query_params["page"])
    except ValueError:
        pass

page = st.sidebar.selectbox("Navigare Proiect", menu_options, index=default_index)

# Actualizăm URL-ul cu pagina curentă
st.query_params["page"] = page

# Buton de refresh global pentru a reîncărca datele din baza de date
if st.sidebar.button("🔄 Reîncarcă Datele"):
    st.rerun()

if page == "Gestiune Baze Locale":
    st.title("✈️ BlueHorizon - Gestiune Baze Locale")
    
    # Sidebar: Selectarea nodului
    st.sidebar.header("Configurare Conexiune")
    selected_node_label = st.sidebar.selectbox("Selectează Nodul Activ", ["America (BD_AM)", "Europa (BD_EU)"])
    NODE = "AM" if "AM" in selected_node_label else "EU"
    st.sidebar.success(f"Conectat la: **BD_{NODE}**")
    
    # Definire sufix tabele în funcție de nod
    TBL_SUFIX = f"_{NODE}"
    # Accesul la PASAGER diferă: pe AM e local, pe EU e via DB Link
    PASAGER_TBL = "PASAGER" if NODE == "AM" else "PASAGER@link_bd_am"
    
    st.header(f"🛠️ Operațiuni LMD pe Serverul {NODE}")
    
    tab1, tab2, tab3 = st.tabs(["1. Emitere Bilet (Insert)", "2. Profil Utilizator (Update & Triggere)", "3. Istoric Rezervări (Vizualizare)"])
    # ==========================================
    # TAB 1: EMITERE BILET (INSERT TRANZACȚII)
    # ==========================================
    with tab1:
        st.subheader("Creează o nouă rezervare")
        st.info(f"Tranzacția va fi salvată local în tabelele REZERVARE{TBL_SUFIX}, PLATA{TBL_SUFIX} și BILET{TBL_SUFIX}.")
        
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
                                    <span class="label">Ruta</span>
                                    <span class="value">{sel_dep_label} -> {sel_arr_label}</span>
                                </div>
                                <div class="ticket-field">
                                    <span class="label">Clasa & Loc</span>
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
            
    # ==========================================
    # TAB 2: UPDATE PROFIL (DEMO TRIGGERE)
    # ==========================================
    with tab2:
        st.subheader("Actualizare Date Contact (Testare Replicare)")
        
        if NODE == "AM":
            st.info("💡 Nodul **AM** este Master pentru datele de profil. Trigger-ul `trg_sync_utilizator_data_am_eu` va propaga automat schimbarea pe nodul EU.")
        else:
            st.warning("⚠️ Atenție: Pe nodul **EU**, modificările sunt **locale**. Sincronizarea automată este configurată doar dinspre AM spre EU în acest proiect.")
        
        try:
            conn = database.get_connection(NODE)
            cols_u, rows_u = database.run_query(conn, "SELECT id_user, nume, prenume, telefon FROM UTILIZATOR_DATA WHERE ROWNUM <= 20")
            
            if rows_u:
                user_options = {f"{r[1]} {r[2]} (Tel actual: {r[3]})": r[0] for r in rows_u}
                sel_user_label = st.selectbox("Alege Utilizatorul pentru actualizare", list(user_options.keys()))
                sel_user_id = user_options[sel_user_label]
                
                new_phone = st.text_input("Nou număr de telefon", max_chars=15)
                
                if st.button("Actualizează Telefon"):
                    if new_phone:
                        sql_upd = "UPDATE UTILIZATOR_DATA SET telefon = :1 WHERE id_user = :2"
                        database.run_statement(conn, sql_upd, [new_phone, sel_user_id])
                        st.success(f"Număr de telefon actualizat la {new_phone} pe BD_{NODE}!")
                        
                        st.info("📌 **Pentru demonstrație în SQL Developer:**")
                        if NODE == "AM":
                            # Trigger AM→EU există, propagarea e automată
                            st.code(
                                f"-- Trigger trg_sync_utilizator_data_am_eu propagă automat AM → EU\n\n"
                                f"-- 1. Pe BD_AM (Master, unde s-a făcut update-ul):\n"
                                f"SELECT telefon FROM UTILIZATOR_DATA WHERE id_user = {sel_user_id};\n\n"
                                f"-- 2. Pe BD_EU (Replicat automat prin trigger):\n"
                                f"SELECT telefon FROM UTILIZATOR_DATA WHERE id_user = {sel_user_id};",
                                language="sql"
                            )
                        else:
                            # Pe EU nu există trigger de propagare înapoi spre AM
                            st.warning(
                                "⚠️ **Limitare arhitecturală**: Modificarea de mai sus este **locală pe BD_EU** "
                                "și **NU se propagă automat pe BD_AM**. "
                                "Trigger-ul de sincronizare (`trg_sync_utilizator_data_am_eu`) funcționează "
                                "**EXCLUSIV dinspre AM spre EU** (AM este nodul Master). "
                                "Aceasta este o limitare intenționată a arhitecturii de replicare asymetrică."
                            )
                            st.code(
                                f"-- Modificarea s-a aplicat LOCAL pe BD_EU:\n"
                                f"SELECT telefon FROM UTILIZATOR_DATA WHERE id_user = {sel_user_id};\n\n"
                                f"-- ATENȚIE: Pe BD_AM (Master) telefonul RĂMÂNE NEMODIFICAT:\n"
                                f"-- Conectează-te pe BD_AM și verifică:\n"
                                f"SELECT telefon FROM UTILIZATOR_DATA WHERE id_user = {sel_user_id};\n"
                                f"-- Rezultatul de pe AM va diferi de cel de pe EU!",
                                language="sql"
                            )
                    else:
                        st.warning("Introdu un număr valid.")
            conn.close()
        except Exception as e:
            st.error(f"Eroare: {e}")

    # ==========================================
    # TAB 3: ISTORIC REZERVĂRI LOCALE
    # ==========================================
    with tab3:
        st.subheader(f"Ultimele rezervări procesate pe BD_{NODE}")
        try:
            conn = database.get_connection(NODE)
            # Selectăm doar din tabela locală pentru a demonstra fragmentarea orizontală
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

elif page == "Vizualizare Bază Globală":
    st.title("🌍 BlueHorizon - Vizualizare Bază Globală")
    st.sidebar.header("Configurare Conexiune")
    st.sidebar.success("Conectat la: **BD_GLOBAL**")
    
    st.info("Ești conectat la schema **BD_GLOBAL**. Datele afișate aici sunt reconstruite automat din fragmentele aflate pe BD_AM și BD_EU, fără ca aplicația să știe unde sunt stocate fizic.")
    
    try:
        conn = database.get_connection("GLOBAL")
        
        # Tab-uri conform cerințelor de vizualizare a efectelor operațiilor LMD
        tab_oriz, tab_vert, tab_repl = st.tabs([
            "1. BILET – Fragmente Orizontale (UNION)", 
            "2. UTILIZATOR – Fragmente Verticale (JOIN)",
            "3. ZBOR – Relații Replicate (SINONIM)"
        ])
        
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
            st.write("Vizualizarea `V_UTILIZATOR` face `JOIN` între datele de securitate și datele de profil distribuite.")
            
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
    
    st.warning("""
        Atenție: Operațiile realizate aici sunt rutate explicit către fragmentele locale corespunzătoare 
        prin Database Links (link_bd_am / link_bd_eu), asigurând transparența la nivel de aplicație.
    """)

    try:
        conn = database.get_connection("GLOBAL")
        tab_upd_oriz, tab_upd_vert, tab_upd_repl = st.tabs([
            "Update Global (Orizontal)", 
            "Update Global (Vertical)",
            "Update Global (Replicat)"
        ])

        # --- UPDATE PE FRAGMENTE ORIZONTALE ---
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
                    # REZERVARE: trigger-ul INSTEAD OF (trg_upd_rezervare_global) rutează automat
                    # pe fragmentul corect (AM dacă ID impar, EU dacă ID par).
                    # PLATA: nu are trigger INSTEAD OF, deci facem update direct pe ambele fragmente;
                    # rândul există doar pe unul, pe celălalt UPDATE-ul afectează 0 rânduri.
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

        # --- UPDATE PE FRAGMENTE VERTICALE ---
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
                # Folosim direct VIEW-ul — trigger-ul INSTEAD OF (trg_upd_utilizator_global)
                # elimină ORA-01732 și redirecționează update-ul spre UTILIZATOR_DATA@link_bd_am.
                # Trigger-ul de sync de pe AM propagă apoi automat modificarea pe EU.
                database.run_statement(
                    conn,
                    "UPDATE V_UTILIZATOR SET nume = :1 WHERE id_user = :2",
                    [new_nume, u_id]
                )
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

        # --- UPDATE PE RELAȚII REPLICATE ---
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
                
                st.session_state['last_z_id'] = z_id # Salvăm ID-ul pentru refresh-ul de mai jos
                
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