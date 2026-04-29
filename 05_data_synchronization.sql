-- ex 5
-- Asigurarea sincronizarii datelor pentru replicate

-- METODA 1: SINCRONIZARE PRIN TRIGGERE

---------------------------
-- TARA
---------------------------

-- trigger: BD_AM 
CREATE OR REPLACE TRIGGER trg_sync_tara_am_eu
AFTER INSERT OR UPDATE OR DELETE ON TARA
FOR EACH ROW
BEGIN
    IF INSERTING THEN
        INSERT INTO TARA@link_bd_eu (id_tara, nume_tara, cod_iso_2)
        VALUES (:NEW.id_tara, :NEW.nume_tara, :NEW.cod_iso_2);

    ELSIF UPDATING THEN
        UPDATE TARA@link_bd_eu
        SET nume_tara = :NEW.nume_tara,
            cod_iso_2 = :NEW.cod_iso_2
        WHERE id_tara = :OLD.id_tara;

    ELSIF DELETING THEN
        DELETE FROM TARA@link_bd_eu
        WHERE id_tara = :OLD.id_tara;
    END IF;
END;
/

-- testare insert: BD_AM
INSERT INTO TARA (id_tara, nume_tara, cod_iso_2)
VALUES (999, 'TEST_SYNC', 'TS');

COMMIT;

-- verificare insert: BD_EU
SELECT * FROM TARA WHERE id_tara = 999;

-- test update: BD_AM
UPDATE TARA
SET nume_tara = 'TEST_SYNC_UPDATED'
WHERE id_tara = 999;

COMMIT;

-- verificare update: BD_EU
SELECT * FROM TARA WHERE id_tara = 999;

-- test delete: BD_AM
DELETE FROM TARA WHERE id_tara = 999;

COMMIT;

-- verificare delete: BD_EU
SELECT * FROM TARA WHERE id_tara = 999;

------------------
-- AVION
------------------
-- trigger: BD_AM
CREATE OR REPLACE TRIGGER trg_sync_avion_am_eu
AFTER INSERT OR UPDATE OR DELETE ON AVION
FOR EACH ROW
BEGIN
    IF INSERTING THEN
        INSERT INTO AVION@link_bd_eu
        (id_avion, numar_inmatriculare, model, capacitate, an_fabricatie)
        VALUES
        (:NEW.id_avion, :NEW.numar_inmatriculare, :NEW.model, :NEW.capacitate, :NEW.an_fabricatie);

    ELSIF UPDATING THEN
        UPDATE AVION@link_bd_eu
        SET numar_inmatriculare = :NEW.numar_inmatriculare,
            model = :NEW.model,
            capacitate = :NEW.capacitate,
            an_fabricatie = :NEW.an_fabricatie
        WHERE id_avion = :OLD.id_avion;

    ELSIF DELETING THEN
        DELETE FROM AVION@link_bd_eu
        WHERE id_avion = :OLD.id_avion;
    END IF;
END;
/

-- test insert: BD_AM
INSERT INTO AVION (id_avion, numar_inmatriculare, model, capacitate, an_fabricatie)
VALUES (999, 'TEST999', 'TEST_MODEL', 100, 2020);

COMMIT;

-- verificare insert: BD_EU
SELECT * 
FROM AVION
WHERE id_avion = 999;

-- test update: BD_AM
UPDATE AVION
SET model = 'TEST_MODEL_UPDATED'
WHERE id_avion = 999;

COMMIT;

-- verificare update: BD_EU
SELECT * 
FROM AVION
WHERE id_avion = 999;

-- test delete: BD_AM
DELETE FROM AVION
WHERE id_avion = 999;

COMMIT;

-- verificare delete: BD_EU
SELECT * 
FROM AVION
WHERE id_avion = 999;

---------------------------
-- UTILIZATOR_DATA
---------------------------

-- trigger: BD_AM
CREATE OR REPLACE TRIGGER trg_sync_utilizator_data_am_eu
AFTER INSERT OR UPDATE OR DELETE ON UTILIZATOR_DATA
FOR EACH ROW
BEGIN
    IF INSERTING THEN
        INSERT INTO UTILIZATOR_DATA@link_bd_eu
        (id_user, nume, prenume, telefon, data_inregistrare)
        VALUES
        (:NEW.id_user, :NEW.nume, :NEW.prenume, :NEW.telefon, :NEW.data_inregistrare);

    ELSIF UPDATING THEN
        UPDATE UTILIZATOR_DATA@link_bd_eu
        SET nume = :NEW.nume,
            prenume = :NEW.prenume,
            telefon = :NEW.telefon,
            data_inregistrare = :NEW.data_inregistrare
        WHERE id_user = :OLD.id_user;

    ELSIF DELETING THEN
        DELETE FROM UTILIZATOR_DATA@link_bd_eu
        WHERE id_user = :OLD.id_user;
    END IF;
END;
/

-- testare insert: BD_AM
INSERT INTO UTILIZATOR_DATA (id_user, nume, prenume, telefon, data_inregistrare)
VALUES (999, 'TEST_NUME', 'TEST_PRENUME', '0700000000', SYSDATE);

COMMIT;

-- verificare insert: BD_EU
SELECT *
FROM UTILIZATOR_DATA
WHERE id_user = 999;

-- testare update: BD_AM
UPDATE UTILIZATOR_DATA
SET telefon = '0711111111'
WHERE id_user = 999;

COMMIT;

-- verificare update: BD_EU
SELECT *
FROM UTILIZATOR_DATA
WHERE id_user = 999;

-- testare delete: BD_AM
DELETE FROM UTILIZATOR_DATA
WHERE id_user = 999;

COMMIT;

-- verificare delete BD_EU
SELECT *
FROM UTILIZATOR_DATA
WHERE id_user = 999;

-- METODA 2: SINCRONIZARE PRIN VIZUALIZARI MATERIALIZATE
--------------
-- ZBOR
--------------

-- BD_AM:
-- creare log pentru a inregistra modificarile
CREATE MATERIALIZED VIEW LOG ON ZBOR
WITH PRIMARY KEY
INCLUDING NEW VALUES;

-- BD_EU
-- creare MView peste tabela existenta
CREATE MATERIALIZED VIEW ZBOR
ON PREBUILT TABLE
REFRESH FAST ON DEMAND
WITH PRIMARY KEY
AS SELECT * FROM ZBOR@link_bd_am;

-- TESTARE METODA 2 (Refresh la MView)

-- 1. pe BD_AM: modificam statusul zborului
UPDATE ZBOR SET status = 'INTARZIAT' WHERE id_zbor = 1;
COMMIT;

-- 2. pe BD_EU: se declanseaza actualizarea datelor din fișierul LOG
EXECUTE DBMS_MVIEW.REFRESH(UPPER('ZBOR'), 'F');

-- 3. pe BD_EU: se verifica preluarea noului status
SELECT status FROM ZBOR WHERE id_zbor = 1;
