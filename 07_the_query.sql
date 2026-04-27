
-- 1. OPERAȚII PE NODUL BD_AM (America - Nod Central)
-- Crearea indecșilor compuși pentru optimizarea filtrării locale
CREATE INDEX idx_rez_am_filtru ON REZERVARE_AM(status, data_rezervare);
CREATE INDEX idx_plata_am_status ON PLATA_AM(id_rezervare, status);

-- Colectarea statisticilor pentru a permite CBO să evalueze corect costul
EXEC DBMS_STATS.GATHER_SCHEMA_STATS('BD_AM', CASCADE => TRUE);



-- 2. OPERAȚII PE NODUL BD_EU (Europa - Nod Local)
-- Crearea indecșilor compuși pentru optimizarea filtrării locale
CREATE INDEX idx_rez_eu_filtru ON REZERVARE_EU(status, data_rezervare);
CREATE INDEX idx_plata_eu_status ON PLATA_EU(id_rezervare, status);

-- Colectarea statisticilor pentru a permite CBO să evalueze corect costul
EXEC DBMS_STATS.GATHER_SCHEMA_STATS('BD_EU', CASCADE => TRUE);



-- 3. OPERAȚII PE SCHEMA GLOBALĂ BD_GLOBAL

-- Conectat ca BD_GLOBAL
-- 7.a Analiza RBO (Rule-Based Optimizer)
-- Notă: În 21c planul va fi generat tot de CBO, dar folosim comanda pentru cerință
ALTER SESSION SET OPTIMIZER_MODE = RULE;

EXPLAIN PLAN SET STATEMENT_ID = 'RBO_PLAN' FOR
WITH bilete_ruta AS (
    SELECT b.id_zbor, COUNT(b.id_bilet) AS nr_bilete, SUM(b.pret_final) AS venit_ruta
    FROM V_BILET b
    JOIN V_REZERVARE r ON b.id_rezervare = r.id_rezervare
    JOIN V_PLATA p     ON r.id_rezervare = p.id_rezervare
    WHERE r.data_rezervare >= ADD_MONTHS(SYSDATE, -6) AND p.status = 'ACCEPTATA'
    GROUP BY b.id_zbor
),
nat_per_zbor AS (
    SELECT b.id_zbor, pas.nationalitate, COUNT(*) AS cnt,
           RANK() OVER (PARTITION BY b.id_zbor ORDER BY COUNT(*) DESC) AS rnk
    FROM V_BILET b
    JOIN V_REZERVARE r ON b.id_rezervare = r.id_rezervare
    JOIN V_PLATA p     ON r.id_rezervare = p.id_rezervare
    JOIN PASAGER pas   ON b.id_pasager   = pas.id_pasager
    WHERE r.data_rezervare >= ADD_MONTHS(SYSDATE, -6) AND p.status = 'ACCEPTATA'
    GROUP BY b.id_zbor, pas.nationalitate
)
SELECT a_dep.cod_iata, a_sos.cod_iata, t_dep.nume_tara, t_sos.nume_tara, br.nr_bilete, br.venit_ruta,
       ROUND((br.nr_bilete / av.capacitate) * 100, 2) AS rata_ocupare_pct, np.nationalitate
FROM bilete_ruta br
JOIN nat_per_zbor np ON br.id_zbor = np.id_zbor AND np.rnk = 1
JOIN ZBOR z ON br.id_zbor = z.id_zbor
JOIN AVION av ON z.id_avion = av.id_avion
JOIN AEROPORT a_dep ON z.id_aeroport_plecare = a_dep.id_aeroport
JOIN AEROPORT a_sos ON z.id_aeroport_sosire = a_sos.id_aeroport
JOIN ORAS o_dep ON a_dep.id_oras = o_dep.id_oras
JOIN ORAS o_sos ON a_sos.id_oras = o_sos.id_oras
JOIN TARA t_dep ON o_dep.id_tara = t_dep.id_tara
JOIN TARA t_sos ON o_sos.id_tara = t_sos.id_tara
ORDER BY br.venit_ruta DESC
FETCH FIRST 10 ROWS ONLY;

-- Afișare Plan RBO
SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY(NULL, 'RBO_PLAN', 'ALL'));


-- 7.b Analiza CBO (Cost-Based Optimizer)
ALTER SESSION SET OPTIMIZER_MODE = ALL_ROWS;

EXPLAIN PLAN SET STATEMENT_ID = 'CBO_PLAN' FOR
WITH bilete_ruta AS (
    SELECT b.id_zbor, COUNT(b.id_bilet) AS nr_bilete, SUM(b.pret_final) AS venit_ruta
    FROM V_BILET b
    JOIN V_REZERVARE r ON b.id_rezervare = r.id_rezervare
    JOIN V_PLATA p     ON r.id_rezervare = p.id_rezervare
    WHERE r.data_rezervare >= ADD_MONTHS(SYSDATE, -6) AND p.status = 'ACCEPTATA'
    GROUP BY b.id_zbor
),
nat_per_zbor AS (
    SELECT b.id_zbor, pas.nationalitate, COUNT(*) AS cnt,
           RANK() OVER (PARTITION BY b.id_zbor ORDER BY COUNT(*) DESC) AS rnk
    FROM V_BILET b
    JOIN V_REZERVARE r ON b.id_rezervare = r.id_rezervare
    JOIN V_PLATA p     ON r.id_rezervare = p.id_rezervare
    JOIN PASAGER pas   ON b.id_pasager   = pas.id_pasager
    WHERE r.data_rezervare >= ADD_MONTHS(SYSDATE, -6) AND p.status = 'ACCEPTATA'
    GROUP BY b.id_zbor, pas.nationalitate
)
SELECT a_dep.cod_iata, a_sos.cod_iata, t_dep.nume_tara, t_sos.nume_tara, br.nr_bilete, br.venit_ruta,
       ROUND((br.nr_bilete / av.capacitate) * 100, 2) AS rata_ocupare_pct, np.nationalitate
FROM bilete_ruta br
JOIN nat_per_zbor np ON br.id_zbor = np.id_zbor AND np.rnk = 1
JOIN ZBOR z ON br.id_zbor = z.id_zbor
JOIN AVION av ON z.id_avion = av.id_avion
JOIN AEROPORT a_dep ON z.id_aeroport_plecare = a_dep.id_aeroport
JOIN AEROPORT a_sos ON z.id_aeroport_sosire = a_sos.id_aeroport
JOIN ORAS o_dep ON a_dep.id_oras = o_dep.id_oras
JOIN ORAS o_sos ON a_sos.id_oras = o_sos.id_oras
JOIN TARA t_dep ON o_dep.id_tara = t_dep.id_tara
JOIN TARA t_sos ON o_sos.id_tara = t_sos.id_tara
ORDER BY br.venit_ruta DESC
FETCH FIRST 10 ROWS ONLY;

-- Afișare Plan CBO
SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY(NULL, 'CBO_PLAN', 'ALL'));


-- 7.c Sugestie Optimizare - Cererea SQL Optimizată
EXPLAIN PLAN SET STATEMENT_ID = 'OPT_PLAN' FOR
WITH date_ruta AS (
    SELECT b.id_zbor, b.id_bilet, b.pret_final, pas.nationalitate
    FROM V_BILET b
    JOIN V_REZERVARE r ON b.id_rezervare = r.id_rezervare
    JOIN V_PLATA p     ON r.id_rezervare = p.id_rezervare
    JOIN PASAGER pas   ON b.id_pasager   = pas.id_pasager
    WHERE r.data_rezervare >= ADD_MONTHS(SYSDATE, -6) AND p.status = 'ACCEPTATA'
),
agregate AS (
    SELECT id_zbor, COUNT(id_bilet) AS nr_bilete, SUM(pret_final) AS venit_ruta,
           STATS_MODE(nationalitate) AS nationalitate_predominanta
    FROM date_ruta
    GROUP BY id_zbor
)
SELECT /*+ LEADING(ag) USE_HASH(z av a_dep a_sos o_dep o_sos t_dep t_sos) NO_MERGE(ag) */
    a_dep.cod_iata AS iata_plecare, a_sos.cod_iata AS iata_sosire,
    t_dep.nume_tara AS tara_plecare, t_sos.nume_tara AS tara_sosire,
    ag.nr_bilete AS total_bilete, ag.venit_ruta AS venit_total,
    ROUND((ag.nr_bilete / av.capacitate) * 100, 2) AS rata_ocupare_pct,
    ag.nationalitate_predominanta
FROM agregate ag
JOIN ZBOR z ON ag.id_zbor = z.id_zbor
JOIN AVION av ON z.id_avion = av.id_avion
JOIN AEROPORT a_dep ON z.id_aeroport_plecare = a_dep.id_aeroport
JOIN AEROPORT a_sos ON z.id_aeroport_sosire = a_sos.id_aeroport
JOIN ORAS o_dep ON a_dep.id_oras = o_dep.id_oras
JOIN ORAS o_sos ON a_sos.id_oras = o_sos.id_oras
JOIN TARA t_dep ON o_dep.id_tara = t_dep.id_tara
JOIN TARA t_sos ON o_sos.id_tara = t_sos.id_tara
ORDER BY ag.venit_ruta DESC
FETCH FIRST 10 ROWS ONLY;

-- Afișare Plan Optimizat
SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY(NULL, 'OPT_PLAN', 'ALL'));

-- EXECUȚIE FINALĂ (Rezultatul Raportului)
WITH date_ruta AS (
    SELECT b.id_zbor, b.id_bilet, b.pret_final, pas.nationalitate
    FROM V_BILET b
    JOIN V_REZERVARE r ON b.id_rezervare = r.id_rezervare
    JOIN V_PLATA p     ON r.id_rezervare = p.id_rezervare
    JOIN PASAGER pas   ON b.id_pasager   = pas.id_pasager
    WHERE r.data_rezervare >= ADD_MONTHS(SYSDATE, -6) AND p.status = 'ACCEPTATA'
),
agregate AS (
    SELECT id_zbor, COUNT(id_bilet) AS nr_bilete, SUM(pret_final) AS venit_ruta,
           STATS_MODE(nationalitate) AS nationalitate_predominanta
    FROM date_ruta
    GROUP BY id_zbor
)
SELECT /*+ LEADING(ag) USE_HASH(z av a_dep a_sos o_dep o_sos t_dep t_sos) NO_MERGE(ag) */
    a_dep.cod_iata, a_sos.cod_iata, t_dep.nume_tara, t_sos.nume_tara,
    ag.nr_bilete, ag.venit_ruta, ROUND((ag.nr_bilete / av.capacitate) * 100, 2) AS ocupare,
    ag.nationalitate_predominanta
FROM agregate ag
JOIN ZBOR z ON ag.id_zbor = z.id_zbor
JOIN AVION av ON z.id_avion = av.id_avion
JOIN AEROPORT a_dep ON z.id_aeroport_plecare = a_dep.id_aeroport
JOIN AEROPORT a_sos ON z.id_aeroport_sosire = a_sos.id_aeroport
JOIN ORAS o_dep ON a_dep.id_oras = o_dep.id_oras
JOIN ORAS o_sos ON a_sos.id_oras = o_sos.id_oras
JOIN TARA t_dep ON o_dep.id_tara = t_dep.id_tara
JOIN TARA t_sos ON o_sos.id_tara = t_sos.id_tara
ORDER BY ag.venit_ruta DESC
FETCH FIRST 10 ROWS ONLY;