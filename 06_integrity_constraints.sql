-- verificare constrangeri
-- BD_AM: (6.1)
SELECT table_name, constraint_name, constraint_type, status
FROM user_constraints
WHERE table_name IN (
    'TARA','ORAS','AEROPORT','AVION','ZBOR',
    'PASAGER','UTILIZATOR_SEC','UTILIZATOR_DATA',
    'REZERVARE_AM','PLATA_AM','BILET_AM'
)
ORDER BY table_name, constraint_type;
-- BD_EU (6.2)
SELECT table_name, constraint_name, constraint_type, status
FROM user_constraints
WHERE table_name IN (
    'TARA','ORAS','AEROPORT','AVION','ZBOR',
    'UTILIZATOR_DATA','REZERVARE_EU','PLATA_EU','BILET_EU'
)
ORDER BY table_name, constraint_type;

-- Verificare triggere globale pe BD_EU (6.3)
SELECT trigger_name, table_name, triggering_event, status
FROM user_triggers
WHERE trigger_name IN (
    'TRG_FK_REZERVARE_USER_EU',
    'TRG_FK_BILET_PASAGER_EU',
    'TRG_UNIQUE_LOC_BILET_EU'
)
ORDER BY trigger_name;

-- Constrangeri Check: BD_AM (6.4)
ALTER TABLE AVION
  ADD CONSTRAINT chk_avion_capacitate_am CHECK (capacitate > 0 AND capacitate <= 850);
 
ALTER TABLE AVION
  ADD CONSTRAINT chk_avion_an_am CHECK (an_fabricatie >= 1950);
 
ALTER TABLE ZBOR
  ADD CONSTRAINT chk_zbor_aeroport_dif_am CHECK (id_aeroport_plecare <> id_aeroport_sosire);
 
ALTER TABLE ZBOR
  ADD CONSTRAINT chk_zbor_date_am CHECK (data_plecare < data_sosire);
 
ALTER TABLE ZBOR
  ADD CONSTRAINT chk_zbor_pret_am CHECK (pret_standard > 0);
 
ALTER TABLE ZBOR
  ADD CONSTRAINT chk_zbor_durata_am CHECK (durata_estimata > 0);
 
ALTER TABLE ZBOR
  ADD CONSTRAINT chk_zbor_status_am
    CHECK (status IN ('PROGRAMAT','ANULAT','INTARZIAT','IMBARCAT','IN_ZBOR','ATERIZAT'));
 
ALTER TABLE PASAGER
  ADD CONSTRAINT chk_pasager_nat_am CHECK (LENGTH(nationalitate) IN (2, 3));
 
ALTER TABLE UTILIZATOR_SEC
  ADD CONSTRAINT chk_user_rol_am CHECK (rol IN ('CLIENT', 'ADMIN'));
 
ALTER TABLE REZERVARE_AM
  ADD CONSTRAINT chk_rez_reg_am CHECK (regiune_vanzare = 'AM');
 
ALTER TABLE REZERVARE_AM
  ADD CONSTRAINT chk_rez_total_am CHECK (total_de_plata >= 0);
 
ALTER TABLE REZERVARE_AM
  ADD CONSTRAINT chk_rez_status_am
    CHECK (status IN ('IN_ASTEPTARE','CONFIRMATA','ANULATA','FINALIZATA'));
 
ALTER TABLE PLATA_AM
  ADD CONSTRAINT chk_plata_suma_am CHECK (suma_achitata > 0);
 
ALTER TABLE PLATA_AM
  ADD CONSTRAINT chk_plata_metoda_am
    CHECK (metoda_plata IN ('CARD','TRANSFER_BANCAR','CASH'));
 
ALTER TABLE PLATA_AM
  ADD CONSTRAINT chk_plata_status_am
    CHECK (status IN ('IN_PROCESARE','ACCEPTATA','RESPINSA','RAMBURSATA'));
 
ALTER TABLE BILET_AM
  ADD CONSTRAINT chk_bilet_rand_am CHECK (numar_rand > 0 AND numar_rand <= 100);
 
ALTER TABLE BILET_AM
  ADD CONSTRAINT chk_bilet_litera_am
    CHECK (litera_scaun IN ('A','B','C','D','E','F','G','H','J','K'));
 
ALTER TABLE BILET_AM
  ADD CONSTRAINT chk_bilet_clasa_am CHECK (clasa IN ('ECONOMY','BUSINESS'));
 
ALTER TABLE BILET_AM
  ADD CONSTRAINT chk_bilet_pret_am CHECK (pret_final > 0);
  
-- Verificare constrangeri BD_AM 
-- TEST 1: Capacitate avion invalida (0 nu este permis)
INSERT INTO AVION (id_avion, numar_inmatriculare, model, capacitate, an_fabricatie)
VALUES (9901, 'YR-TST1', 'Test Model', 0, 2020);

-- TEST 2: An fabricatie invalid (inainte de 1950)
INSERT INTO AVION (id_avion, numar_inmatriculare, model, capacitate, an_fabricatie)
VALUES (9902, 'YR-TST2', 'Test Model', 150, 1930);

-- TEST 3: Regiune vanzare gresita pe REZERVARE_AM (nu poate fi 'EU')
INSERT INTO REZERVARE_AM (id_rezervare, id_user, data_rezervare, regiune_vanzare, total_de_plata, status)
VALUES (9901, 1, SYSDATE, 'EU', 500, 'CONFIRMATA');

-- TEST 4: Total de plata negativ
INSERT INTO REZERVARE_AM (id_rezervare, id_user, data_rezervare, regiune_vanzare, total_de_plata, status)
VALUES (9902, 1, SYSDATE, 'AM', -100, 'CONFIRMATA');

-- TEST 5: Suma achitata 0 sau negativa
INSERT INTO REZERVARE_AM (id_rezervare, id_user, data_rezervare, regiune_vanzare, total_de_plata, status)
VALUES (9903, 1, SYSDATE, 'AM', 300, 'CONFIRMATA');

INSERT INTO PLATA_AM (id_plata, id_rezervare, suma_achitata, data_plata, metoda_plata, status)
VALUES (9901, 9903, -50, SYSTIMESTAMP, 'CARD', 'ACCEPTATA');

ROLLBACK;


-- Constrangeri Check: BD_EU (6.5)
ALTER TABLE TARA
  ADD CONSTRAINT chk_cod_iso_2_eu
    CHECK (cod_iso_2 = UPPER(cod_iso_2) AND LENGTH(cod_iso_2) = 2);
 
ALTER TABLE AVION
  ADD CONSTRAINT chk_avion_capacitate_eu CHECK (capacitate > 0 AND capacitate <= 850);
 
ALTER TABLE AVION
  ADD CONSTRAINT chk_avion_an_eu CHECK (an_fabricatie >= 1950);
 
ALTER TABLE ZBOR
  ADD CONSTRAINT chk_zbor_aeroport_dif_eu CHECK (id_aeroport_plecare <> id_aeroport_sosire);
 
ALTER TABLE ZBOR
  ADD CONSTRAINT chk_zbor_date_eu CHECK (data_plecare < data_sosire);
 
ALTER TABLE ZBOR
  ADD CONSTRAINT chk_zbor_pret_eu CHECK (pret_standard > 0);
 
ALTER TABLE ZBOR
  ADD CONSTRAINT chk_zbor_durata_eu CHECK (durata_estimata > 0);
 
ALTER TABLE ZBOR
  ADD CONSTRAINT chk_zbor_status_eu
    CHECK (status IN ('PROGRAMAT','ANULAT','INTARZIAT','IMBARCAT','IN_ZBOR','ATERIZAT'));
 
ALTER TABLE REZERVARE_EU
  ADD CONSTRAINT chk_rez_reg_eu CHECK (regiune_vanzare = 'EU');
 
ALTER TABLE REZERVARE_EU
  ADD CONSTRAINT chk_rez_total_eu CHECK (total_de_plata >= 0);
 
ALTER TABLE REZERVARE_EU
  ADD CONSTRAINT chk_rez_status_eu
    CHECK (status IN ('IN_ASTEPTARE','CONFIRMATA','ANULATA','FINALIZATA'));
 
ALTER TABLE PLATA_EU
  ADD CONSTRAINT chk_plata_suma_eu CHECK (suma_achitata > 0);
 
ALTER TABLE PLATA_EU
  ADD CONSTRAINT chk_plata_metoda_eu
    CHECK (metoda_plata IN ('CARD','TRANSFER_BANCAR','CASH'));
 
ALTER TABLE PLATA_EU
  ADD CONSTRAINT chk_plata_status_eu
    CHECK (status IN ('IN_PROCESARE','ACCEPTATA','RESPINSA','RAMBURSATA'));
 
ALTER TABLE BILET_EU
  ADD CONSTRAINT chk_bilet_rand_eu CHECK (numar_rand > 0 AND numar_rand <= 100);
 
ALTER TABLE BILET_EU
  ADD CONSTRAINT chk_bilet_litera_eu
    CHECK (litera_scaun IN ('A','B','C','D','E','F','G','H','J','K'));
 
ALTER TABLE BILET_EU
  ADD CONSTRAINT chk_bilet_clasa_eu CHECK (clasa IN ('ECONOMY','BUSINESS'));
 
ALTER TABLE BILET_EU
  ADD CONSTRAINT chk_bilet_pret_eu CHECK (pret_final > 0);
  
-- Verificare constrangeri BD_EU
-- TEST 1: Cod ISO invalid (trebuie sa fie UPPER si lungime 2)
INSERT INTO TARA (id_tara, nume_tara, cod_iso_2)
VALUES (9901, 'TestTara', 'ro');

-- TEST 2: Regiune vanzare gresita pe REZERVARE_EU (trebuie sa fie 'EU')
INSERT INTO REZERVARE_EU (id_rezervare, id_user, data_rezervare, regiune_vanzare, total_de_plata, status)
VALUES (9901, 1, SYSDATE, 'AM', 300, 'CONFIRMATA');

-- TEST 3: Metoda plata invalida
INSERT INTO REZERVARE_EU (id_rezervare, id_user, data_rezervare, regiune_vanzare, total_de_plata, status)
VALUES (9902, 1, SYSDATE, 'EU', 200, 'CONFIRMATA');

INSERT INTO PLATA_EU (id_plata, id_rezervare, suma_achitata, data_plata, metoda_plata, status)
VALUES (9901, 9902, 200, SYSTIMESTAMP, 'BITCOIN', 'ACCEPTATA');

ROLLBACK;

-- TEST 4: Insert valid
INSERT INTO TARA (id_tara, nume_tara, cod_iso_2)
VALUES (9901, 'TestTara', 'RO');

ROLLBACK;


-- TRIGGER GLOBAL pentru REZERVARE_EU.id_user (6.6)
-- BD_EU
CREATE OR REPLACE TRIGGER trg_fk_rezervare_user_eu
BEFORE INSERT OR UPDATE OF id_user ON REZERVARE_EU
FOR EACH ROW
DECLARE
    v_count NUMBER;
BEGIN
    SELECT COUNT(*)
    INTO   v_count
    FROM   UTILIZATOR_SEC@link_bd_am
    WHERE  id_user = :NEW.id_user;
 
    IF v_count = 0 THEN
        RAISE_APPLICATION_ERROR(
            -20001,
            'Eroare FK global: Utilizatorul cu id=' || :NEW.id_user ||
            ' nu exista in UTILIZATOR_SEC pe BD_AM.'
        );
    END IF;
END;
/
 
-- TEST: Inserare rezervare cu ID utilizator inexistent
INSERT INTO REZERVARE_EU (id_rezervare, id_user, data_rezervare, regiune_vanzare, total_de_plata, status)
VALUES (9940, 99999, SYSDATE, 'EU', 300, 'CONFIRMATA'); 
ROLLBACK;

-- TRIGGER GLOBAL FK pentru PASAGERI (6.7)
CREATE OR REPLACE TRIGGER trg_fk_bilet_pasager_eu
BEFORE INSERT OR UPDATE OF id_pasager ON BILET_EU
FOR EACH ROW
DECLARE
    v_count NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM PASAGER@link_bd_am
    WHERE id_pasager = :NEW.id_pasager;

    IF v_count = 0 THEN
        RAISE_APPLICATION_ERROR(-20002, 'Pasagerul cu id=' || :NEW.id_pasager || ' nu exista pe BD_AM.');
    END IF;
END;
/

-- testare trigger FK global: rulare pe BD_EU
-- Inserare rezervare suport 
INSERT INTO REZERVARE_EU (id_rezervare, id_user, data_rezervare, regiune_vanzare, total_de_plata, status)
VALUES (9960, 1, SYSDATE, 'EU', 400, 'CONFIRMATA');

-- TEST 1: Insert bilet cu pasager care nu exista pe BD_AM
INSERT INTO BILET_EU (id_rezervare, id_zbor, id_pasager, numar_rand, litera_scaun, clasa, pret_final)
VALUES (9960, 1, 88888, 10, 'A', 'ECONOMY', 250);
-- => Eroare: Pasagerul cu id=88888 nu exista in PASAGER pe BD_AM.

-- TEST 2: Insert bilet cu pasager care exista pe BD_AM
INSERT INTO BILET_EU (id_rezervare, id_zbor, id_pasager, numar_rand, litera_scaun, clasa, pret_final)
VALUES (9960, 1, 1, 10, 'B', 'ECONOMY', 250);

-- TEST 3: Update catre un pasager inexistent
UPDATE BILET_EU
SET    id_pasager = 88888
WHERE  id_rezervare = 9960 AND litera_scaun = 'B';
-- => Eroare: Pasagerul cu id=88888 nu exista in PASAGER pe BD_AM.

ROLLBACK;

-- TRIGGERE GLOBAL UNIQUE: LOC IN AVION (BILET_AM + BILET_EU) (6.8)
-- TRIGGER pe BD_AM
CREATE OR REPLACE TRIGGER trg_unique_loc_bilet_am
BEFORE INSERT OR UPDATE OF id_zbor, numar_rand, litera_scaun ON BILET_AM
FOR EACH ROW
DECLARE
    v_count NUMBER;
BEGIN
    SELECT COUNT(*)
    INTO   v_count
    FROM   BILET_EU@link_bd_eu
    WHERE  id_zbor       = :NEW.id_zbor
      AND  numar_rand    = :NEW.numar_rand
      AND  litera_scaun  = :NEW.litera_scaun;
 
    IF v_count > 0 THEN
        RAISE_APPLICATION_ERROR(
            -20003,
            'Eroare UNIQUE global: Locul rand=' || :NEW.numar_rand ||
            ', scaun=' || :NEW.litera_scaun ||
            ' pe zborul id=' || :NEW.id_zbor ||
            ' este deja ocupat in BILET_EU (BD_EU).'
        );
    END IF;
END;
/
 
-- TRIGGER pe BD_EU
CREATE OR REPLACE TRIGGER trg_unique_loc_bilet_eu
BEFORE INSERT OR UPDATE OF id_zbor, numar_rand, litera_scaun ON BILET_EU
FOR EACH ROW
DECLARE
    v_count NUMBER;
BEGIN
    SELECT COUNT(*)
    INTO   v_count
    FROM   BILET_AM@link_bd_am
    WHERE  id_zbor       = :NEW.id_zbor
      AND  numar_rand    = :NEW.numar_rand
      AND  litera_scaun  = :NEW.litera_scaun;
 
    IF v_count > 0 THEN
        RAISE_APPLICATION_ERROR(
            -20004,
            'Eroare UNIQUE global: Locul rand=' || :NEW.numar_rand ||
            ', scaun=' || :NEW.litera_scaun ||
            ' pe zborul id=' || :NEW.id_zbor ||
            ' este deja ocupat in BILET_AM (BD_AM).'
        );
    END IF;
END;
/
 
-- verificare trigger UNIQUE global loc in avion
-- BD_AM: Inserare bilet pe nodul din America (Locul 15C)
INSERT INTO REZERVARE_AM (id_rezervare, id_user, data_rezervare, regiune_vanzare, total_de_plata, status)
VALUES (9970, 1, SYSDATE, 'AM', 350, 'CONFIRMATA');

INSERT INTO BILET_AM (id_rezervare, id_zbor, id_pasager, numar_rand, litera_scaun, clasa, pret_final)
VALUES (9970, 1, 1, 15, 'C', 'ECONOMY', 200);

COMMIT;
 
-- BD_EU, acelasi loc (zbor 1, rand 15, scaun C)
INSERT INTO REZERVARE_EU (id_rezervare, id_user, data_rezervare, regiune_vanzare, total_de_plata, status)
VALUES (9971, 1, SYSDATE, 'EU', 350, 'CONFIRMATA');

INSERT INTO BILET_EU (id_rezervare, id_zbor, id_pasager, numar_rand, litera_scaun, clasa, pret_final)
VALUES (9971, 1, 1, 15, 'C', 'ECONOMY', 200);

ROLLBACK;
 
-- Conectat ca BD_AM: curatare
DELETE FROM BILET_AM    WHERE id_rezervare = 9970;
DELETE FROM REZERVARE_AM WHERE id_rezervare = 9970;
COMMIT;
 
