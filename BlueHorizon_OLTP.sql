CREATE USER BLUEHORIZON IDENTIFIED BY parola_oltp DEFAULT TABLESPACE users QUOTA UNLIMITED ON users;

GRANT CONNECT, RESOURCE, CREATE VIEW TO BLUEHORIZON;
GRANT CREATE SESSION TO BLUEHORIZON;
GRANT CREATE TABLE TO BLUEHORIZON;
GRANT CREATE SEQUENCE TO BLUEHORIZON;
GRANT CREATE TRIGGER TO BLUEHORIZON;

-- CREATE TABLES
-- UTILIZATOR
CREATE TABLE UTILIZATOR (
    id_user NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nume VARCHAR2(100) NOT NULL,
    prenume VARCHAR2(100) NOT NULL,
    email VARCHAR2(255) NOT NULL UNIQUE,
    parola VARCHAR2(255) NOT NULL,
    telefon VARCHAR2(20),
    data_inregistrare DATE DEFAULT SYSDATE NOT NULL,
    rol VARCHAR2(20) DEFAULT 'CLIENT' NOT NULL,
    CONSTRAINT chk_email CHECK (REGEXP_LIKE(email, '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')),
    CONSTRAINT chk_rol CHECK (rol IN ('CLIENT', 'ADMIN'))
);

-- PASAGER
CREATE TABLE PASAGER (
    id_pasager NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nume VARCHAR2(100) NOT NULL,
    prenume VARCHAR2(100) NOT NULL,
    data_nasterii DATE NOT NULL,
    numar_document VARCHAR2(50) NOT NULL, -- seria si nr de la CI (nu punem CNP, pt ca ne-am limita doar la ro)
    nationalitate VARCHAR2(3) NOT NULL,
    CONSTRAINT chk_nationalitate CHECK (LENGTH(nationalitate) = 2 OR LENGTH(nationalitate) = 3)
);

-- TARA
CREATE TABLE TARA (
    id_tara NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nume_tara VARCHAR2(100) NOT NULL UNIQUE,
    cod_iso_2 CHAR(2) NOT NULL UNIQUE, -- RO, FR, US
    CONSTRAINT chk_cod_iso_2 CHECK (cod_iso_2 = UPPER(cod_iso_2) AND LENGTH(cod_iso_2) = 2)
);

-- ORAS
CREATE TABLE ORAS (
    id_oras NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_tara NUMBER NOT NULL,
    nume_oras VARCHAR2(100) NOT NULL,
    CONSTRAINT fk_oras_tara FOREIGN KEY (id_tara) REFERENCES TARA(id_tara),
    CONSTRAINT uq_oras_tara UNIQUE (nume_oras, id_tara)
);

-- AEROPOR
CREATE TABLE AEROPORT (
    id_aeroport NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_oras NUMBER NOT NULL,
    cod_iata CHAR(3) NOT NULL UNIQUE,
    nume_aeroport VARCHAR2(200) NOT NULL,
    CONSTRAINT fk_aeroport_oras FOREIGN KEY (id_oras) REFERENCES ORAS(id_oras),
    CONSTRAINT chk_cod_iata CHECK (cod_iata = UPPER(cod_iata) AND LENGTH(cod_iata) = 3)
);

-- AVION
CREATE TABLE AVION (
    id_avion NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    numar_inmatriculare VARCHAR2(20) NOT NULL UNIQUE,
    model VARCHAR2(100) NOT NULL,
    capacitate NUMBER NOT NULL,
    an_fabricatie NUMBER(4) NOT NULL,
    CONSTRAINT chk_capacitate CHECK (capacitate > 0 AND capacitate <= 850),
    CONSTRAINT chk_an_fabricatie CHECK (an_fabricatie >= 1950)
);

-- ZBOR
CREATE TABLE ZBOR (
    id_zbor NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_avion NUMBER NOT NULL,
    id_aeroport_plecare NUMBER NOT NULL,
    id_aeroport_sosire NUMBER NOT NULL,
    numar_zbor VARCHAR2(10) NOT NULL,
    data_plecare TIMESTAMP NOT NULL,
    data_sosire TIMESTAMP NOT NULL,
    data_plecare_efectiva TIMESTAMP, -- pentru calc intarzierilor
    data_sosire_efectiva TIMESTAMP, -- pentru calc intarzierilor
    durata_estimata NUMBER NOT NULL, -- in minute
    pret_standard NUMBER(10,2) NOT NULL, -- adica pretul economy, pentru business va fi diferit (setam in backend pret_standard * 1.5 = business salvand-o in tabela BILET ca pret_final)
    status VARCHAR2(20) DEFAULT 'PROGRAMAT' NOT NULL,
    CONSTRAINT fk_zbor_avion FOREIGN KEY (id_avion) REFERENCES AVION(id_avion),
    CONSTRAINT fk_zbor_aeroport_plecare FOREIGN KEY (id_aeroport_plecare) REFERENCES AEROPORT(id_aeroport),
    CONSTRAINT fk_zbor_aeroport_sosire FOREIGN KEY (id_aeroport_sosire) REFERENCES AEROPORT(id_aeroport),
    CONSTRAINT chk_aeroport_diferit CHECK (id_aeroport_plecare != id_aeroport_sosire),
    CONSTRAINT chk_date_zbor CHECK (data_plecare < data_sosire),
    CONSTRAINT chk_pret_standard CHECK (pret_standard > 0),
    CONSTRAINT chk_durata CHECK (durata_estimata > 0),
    CONSTRAINT chk_status_zbor CHECK (status IN ('PROGRAMAT', 'ANULAT', 'INTARZIAT', 'IMBARCAT', 'IN_ZBOR', 'ATERIZAT'))
);

-- REZERVARE
CREATE TABLE REZERVARE (
    id_rezervare NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_user NUMBER NOT NULL,
    data_rezervare DATE DEFAULT SYSDATE NOT NULL,
    total_de_plata NUMBER(10,2) NOT NULL, -- pentru ca o rezervare poate contine mai mult de un bilet
    status VARCHAR2(20) DEFAULT 'IN_ASTEPTARE' NOT NULL,
    CONSTRAINT fk_rezervare_user FOREIGN KEY (id_user) REFERENCES UTILIZATOR(id_user),
    CONSTRAINT chk_total_plata CHECK (total_de_plata >= 0),
    CONSTRAINT chk_status_rezervare CHECK (status IN ('IN_ASTEPTARE', 'CONFIRMATA', 'ANULATA', 'FINALIZATA'))
);

-- PLATA
CREATE TABLE PLATA (
    id_plata NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_rezervare NUMBER NOT NULL,
    suma_achitata NUMBER(10,2) NOT NULL,
    data_plata TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
    metoda_plata VARCHAR2(50) NOT NULL,
    status VARCHAR2(20) DEFAULT 'IN_PROCESARE' NOT NULL, -- pana se face plata
    CONSTRAINT fk_plata_rezervare FOREIGN KEY (id_rezervare) REFERENCES REZERVARE(id_rezervare),
    CONSTRAINT chk_suma_achitata CHECK (suma_achitata > 0),
    CONSTRAINT chk_metoda_plata CHECK (metoda_plata IN ('CARD', 'TRANSFER_BANCAR', 'CASH')),
    CONSTRAINT chk_status_plata CHECK (status IN ('IN_PROCESARE', 'ACCEPTATA', 'RESPINSA', 'RAMBURSATA'))
);

-- BILET (relatia many-to-many intre REZERVARE și ZBOR)
CREATE TABLE BILET (
    id_bilet NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_rezervare NUMBER NOT NULL,
    id_zbor NUMBER NOT NULL,
    id_pasager NUMBER NOT NULL,
    numar_rand NUMBER NOT NULL,
    litera_scaun CHAR(1) NOT NULL,
    clasa VARCHAR2(20) DEFAULT 'ECONOMY' NOT NULL,
    pret_final NUMBER(10,2) NOT NULL,
    CONSTRAINT fk_bilet_rezervare FOREIGN KEY (id_rezervare) REFERENCES REZERVARE(id_rezervare),
    CONSTRAINT fk_bilet_zbor FOREIGN KEY (id_zbor) REFERENCES ZBOR(id_zbor),
    CONSTRAINT fk_bilet_pasager FOREIGN KEY (id_pasager) REFERENCES PASAGER(id_pasager),
    CONSTRAINT chk_numar_rand CHECK (numar_rand > 0 AND numar_rand <= 100),
    CONSTRAINT chk_litera_scaun CHECK (litera_scaun IN ('A','B','C','D','E','F','G','H','J','K')),
    CONSTRAINT chk_clasa CHECK (clasa IN ('ECONOMY', 'BUSINESS')),
    CONSTRAINT chk_pret_final CHECK (pret_final > 0),
    CONSTRAINT uk_loc_zbor UNIQUE (id_zbor, numar_rand, litera_scaun)
);

-- Reminder: Oracle creeaza automat un index cand:
-- definim un PK
-- definim UK (UNIQUE)

-- INDECSI PENTRU OLTP
-- 1. INDECSI DE BUSINESS (pt cautari rapide)

-- ruta (plecare, sosire) + data
-- acopera si id_aeroport_plecare
CREATE INDEX idx_zbor_cautare_ruta ON ZBOR(id_aeroport_plecare, id_aeroport_sosire, data_plecare);

-- istoric client (rezervarile sale)
-- acopera si id_user
CREATE INDEX idx_rezervare_istoric ON REZERVARE(id_user, data_rezervare);

-- verifica unicitatea unui loc
-- keep in mind ca oracle a creat automat un index pentru
-- CONSTRAINT uk_loc_zbor UNIQUE (id_zbor, numar_rand, litera_scaun)
-- deci automat si pentru id_zbor

-- 2. INDECȘI PENTRU FKs RAMASE NEACOPERITE
-- pentru coloanele FK care, mai sus, nu sunt primele din sir, adica in primul index se va face unul automat pentru id_aer_plec, dar nu si pe celelalte 2

-- Tabela ZBOR
CREATE INDEX idx_zbor_avion ON ZBOR(id_avion);
CREATE INDEX idx_zbor_sosire ON ZBOR(id_aeroport_sosire); -- plecarea e acoperita de idx_zbor_cautare_ruta
-- toate zborurile intr-o zi
CREATE INDEX idx_zbor_data_simpla ON ZBOR(data_plecare);
-- pt filtrarea pe baza statusului
CREATE INDEX idx_zbor_status ON ZBOR(status);

-- Tabela BILET
-- biletele unui pasager
CREATE INDEX idx_bilet_pasager ON BILET(id_pasager);
-- ce bilet ii apartine unei rezervari
CREATE INDEX idx_bilet_rezervare ON BILET(id_rezervare);
-- Tabela PLATA
-- ce rezervare ii apartine platii
CREATE INDEX idx_plata_rezervare ON PLATA(id_rezervare);

-- Tabela ORAS
-- pt popularea listei de orase cand se selecteaza o tara
CREATE INDEX idx_oras_tara ON ORAS(id_tara);

-- Tabela AEROPORT
-- pt a gasi aeroporturile dintr-un oras
CREATE INDEX idx_aeroport_oras ON AEROPORT(id_oras);

-- Tabela REZERVARE
-- pt filtrarea pe baza statusului
CREATE INDEX idx_rezervare_status ON REZERVARE(status);