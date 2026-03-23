CREATE OR REPLACE PACKAGE PKG_ETL_BLUEHORIZON AS
    PROCEDURE LOAD_ALL;
    PROCEDURE LOAD_DIM_TIMP;
    PROCEDURE LOAD_DIMENSIUNI;
    PROCEDURE LOAD_FACT;
END PKG_ETL_BLUEHORIZON;
/

CREATE OR REPLACE PACKAGE BODY PKG_ETL_BLUEHORIZON AS

    PROCEDURE LOAD_DIM_TIMP IS
        v_start_date DATE := DATE '2023-01-01';
        v_end_date DATE := DATE '2026-12-31';
        v_curr_date DATE;
    BEGIN
        v_curr_date := v_start_date;
        WHILE v_curr_date <= v_end_date LOOP
            BEGIN
                INSERT INTO DIM_TIMP (data_calendaristica, an, trimestru, luna, nume_luna, nume_zi, zi)
                VALUES (
                    v_curr_date,
                    EXTRACT(YEAR FROM v_curr_date),
                    TO_NUMBER(TO_CHAR(v_curr_date, 'Q')),
                    EXTRACT(MONTH FROM v_curr_date),
                    TRIM(TO_CHAR(v_curr_date, 'Month')),
                    TRIM(TO_CHAR(v_curr_date, 'Day')),
                    EXTRACT(DAY FROM v_curr_date)
                );
            EXCEPTION WHEN DUP_VAL_ON_INDEX THEN
                NULL;
            END;
            v_curr_date := v_curr_date + 1;
        END LOOP;
        COMMIT;
    END LOAD_DIM_TIMP;

    PROCEDURE LOAD_DIMENSIUNI IS
    BEGIN
        -- DIM_AEROPORT
        MERGE INTO DIM_AEROPORT trg
        USING (
            SELECT 
                A.id_aeroport,
                A.cod_iata,
                A.nume_aeroport,
                O.nume_oras AS oras,
                T.nume_tara AS tara
            FROM BLUEHORIZON.AEROPORT A
            JOIN BLUEHORIZON.ORAS O ON A.id_oras = O.id_oras
            JOIN BLUEHORIZON.TARA T ON O.id_tara = T.id_tara
        ) src
        ON (trg.id_aeroport_oltp = src.id_aeroport)
        WHEN MATCHED THEN
            UPDATE SET 
                trg.cod_iata = src.cod_iata,
                trg.nume_aeroport = src.nume_aeroport,
                trg.oras = src.oras,
                trg.tara = src.tara
        WHEN NOT MATCHED THEN
            INSERT (id_aeroport_oltp, cod_iata, nume_aeroport, oras, tara)
            VALUES (src.id_aeroport, src.cod_iata, src.nume_aeroport, src.oras, src.tara);
            
        -- DIM_AVION
        MERGE INTO DIM_AVION trg
        USING (SELECT * FROM BLUEHORIZON.AVION) src
        ON (trg.id_avion_oltp = src.id_avion)
        WHEN MATCHED THEN
            UPDATE SET
                trg.numar_inmatriculare = src.numar_inmatriculare,
                trg.model = src.model,
                trg.capacitate = src.capacitate,
                trg.an_fabricatie = src.an_fabricatie
        WHEN NOT MATCHED THEN
            INSERT (id_avion_oltp, numar_inmatriculare, model, capacitate, an_fabricatie)
            VALUES (src.id_avion, src.numar_inmatriculare, src.model, src.capacitate, src.an_fabricatie);
            
        -- DIM_PASAGER
        MERGE INTO DIM_PASAGER trg
        USING (
            SELECT 
                id_pasager, 
                nationalitate,
                FLOOR(MONTHS_BETWEEN(SYSDATE, data_nasterii) / 12) as varsta
            FROM BLUEHORIZON.PASAGER
        ) src
        ON (trg.id_pasager_oltp = src.id_pasager)
        WHEN MATCHED THEN
            UPDATE SET
                trg.nationalitate = src.nationalitate,
                trg.varsta = src.varsta,
                trg.grupa_varsta = CASE 
                    WHEN src.varsta BETWEEN 0 AND 1 THEN 'Infant'
                    WHEN src.varsta BETWEEN 2 AND 11 THEN 'Copil'
                    WHEN src.varsta BETWEEN 12 AND 17 THEN 'Adolescent'
                    WHEN src.varsta BETWEEN 18 AND 30 THEN 'Adult Tanar'
                    WHEN src.varsta BETWEEN 31 AND 60 THEN 'Adult'
                    ELSE 'Senior'
                END
        WHEN NOT MATCHED THEN
            INSERT (id_pasager_oltp, nationalitate, varsta, grupa_varsta)
            VALUES (src.id_pasager, src.nationalitate, src.varsta, 
                    CASE 
                        WHEN src.varsta BETWEEN 0 AND 1 THEN 'Infant'
                        WHEN src.varsta BETWEEN 2 AND 11 THEN 'Copil'
                        WHEN src.varsta BETWEEN 12 AND 17 THEN 'Adolescent'
                        WHEN src.varsta BETWEEN 18 AND 30 THEN 'Adult Tanar'
                        WHEN src.varsta BETWEEN 31 AND 60 THEN 'Adult'
                        ELSE 'Senior'
                    END);
                    
        -- DIM_UTILIZATOR
        MERGE INTO DIM_UTILIZATOR trg
        USING (
            SELECT 
                id_user,
                FLOOR(MONTHS_BETWEEN(SYSDATE, data_inregistrare) / 12) as vechime
            FROM BLUEHORIZON.UTILIZATOR
        ) src
        ON (trg.id_user_oltp = src.id_user)
        WHEN MATCHED THEN
            UPDATE SET trg.vechime_cont_ani = src.vechime
        WHEN NOT MATCHED THEN
            INSERT (id_user_oltp, vechime_cont_ani) VALUES (src.id_user, src.vechime);
            
        COMMIT;
    END LOAD_DIMENSIUNI;

    PROCEDURE LOAD_FACT IS
    BEGIN
        DELETE FROM FACT_VANZARI;
        
        INSERT INTO FACT_VANZARI (
            id_dim_timp_rezervare,
            id_dim_timp_plecare,
            id_dim_aeroport_plecare,
            id_dim_aeroport_sosire,
            id_dim_avion,
            id_dim_pasager,
            id_dim_clasa,
            id_dim_utilizator,
            data_plecare_part,
            pret_bilet,
            durata_zbor,
            minute_intarziere,
            status_zbor
        )
        SELECT
            TR.id_dim_timp AS id_dim_timp_rezervare,
            TP.id_dim_timp AS id_dim_timp_plecare,
            DAP.id_dim_aeroport AS id_dim_aeroport_plecare,
            DAS.id_dim_aeroport AS id_dim_aeroport_sosire,
            DAV.id_dim_avion AS id_dim_avion,
            DPAS.id_dim_pasager AS id_dim_pasager,
            DC.id_dim_clasa AS id_dim_clasa,
            DU.id_dim_utilizator AS id_dim_utilizator,
            TRUNC(Z.data_plecare) AS data_plecare_part,
            B.pret_final AS pret_bilet,
            COALESCE(
                ROUND((CAST(Z.data_sosire_efectiva AS DATE) - CAST(Z.data_plecare_efectiva AS DATE)) * 24 * 60, 2),
                Z.durata_estimata
            ) AS durata_zbor,
            CASE 
                WHEN Z.data_plecare_efectiva IS NOT NULL AND Z.data_plecare_efectiva > Z.data_plecare THEN 
                    ROUND((CAST(Z.data_plecare_efectiva AS DATE) - CAST(Z.data_plecare AS DATE)) * 24 * 60, 2)
                ELSE 0 
            END AS minute_intarziere,
            Z.status AS status_zbor
        FROM BLUEHORIZON.BILET B
        JOIN BLUEHORIZON.REZERVARE R ON B.id_rezervare = R.id_rezervare
        JOIN BLUEHORIZON.ZBOR Z ON B.id_zbor = Z.id_zbor
        JOIN DIM_TIMP TR ON TRUNC(TR.data_calendaristica) = TRUNC(R.data_rezervare)
        JOIN DIM_TIMP TP ON TRUNC(TP.data_calendaristica) = TRUNC(Z.data_plecare)
        JOIN DIM_AEROPORT DAP ON DAP.id_aeroport_oltp = Z.id_aeroport_plecare
        JOIN DIM_AEROPORT DAS ON DAS.id_aeroport_oltp = Z.id_aeroport_sosire
        JOIN DIM_AVION DAV ON DAV.id_avion_oltp = Z.id_avion
        JOIN DIM_PASAGER DPAS ON DPAS.id_pasager_oltp = B.id_pasager
        JOIN DIM_CLASA DC ON DC.nume_clasa = B.clasa
        JOIN DIM_UTILIZATOR DU ON DU.id_user_oltp = R.id_user;
        
        COMMIT;
    END LOAD_FACT;

    PROCEDURE LOAD_ALL IS
    BEGIN
        LOAD_DIM_TIMP;
        LOAD_DIMENSIUNI;
        LOAD_FACT;
    END LOAD_ALL;

END PKG_ETL_BLUEHORIZON;
/

BEGIN
    PKG_ETL_BLUEHORIZON.LOAD_ALL;
END;
/

-- Verificam
SELECT 'DIM_TIMP' AS Tabela, COUNT(*) AS Linii FROM DIM_TIMP
UNION ALL
SELECT 'DIM_AEROPORT', COUNT(*) FROM DIM_AEROPORT
UNION ALL
SELECT 'DIM_AVION', COUNT(*) FROM DIM_AVION
UNION ALL
SELECT 'DIM_PASAGER', COUNT(*) FROM DIM_PASAGER
UNION ALL
SELECT 'DIM_UTILIZATOR', COUNT(*) FROM DIM_UTILIZATOR
UNION ALL
SELECT 'FACT_VANZARI', COUNT(*) FROM FACT_VANZARI;
