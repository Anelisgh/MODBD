-- ❗ CONECTAT CA BD_AM
-- 1. TABELE REPLICATE (Nomenclatoare si Zboruri)
CREATE TABLE TARA (
    id_tara NUMBER PRIMARY KEY,
    nume_tara VARCHAR2(100) NOT NULL UNIQUE,
    cod_iso_2 CHAR(2) NOT NULL UNIQUE,
    CONSTRAINT chk_cod_iso_2 CHECK (cod_iso_2 = UPPER(cod_iso_2) AND LENGTH(cod_iso_2) = 2)
);

CREATE TABLE ORAS (
    id_oras NUMBER PRIMARY KEY,
    id_tara NUMBER NOT NULL,
    nume_oras VARCHAR2(100) NOT NULL,
    CONSTRAINT fk_oras_tara FOREIGN KEY (id_tara) REFERENCES TARA(id_tara)
);

CREATE TABLE AEROPORT (
    id_aeroport NUMBER PRIMARY KEY,
    id_oras NUMBER NOT NULL,
    cod_iata CHAR(3) NOT NULL UNIQUE,
    nume_aeroport VARCHAR2(200) NOT NULL,
    CONSTRAINT fk_aeroport_oras FOREIGN KEY (id_oras) REFERENCES ORAS(id_oras)
);

CREATE TABLE AVION (
    id_avion NUMBER PRIMARY KEY,
    numar_inmatriculare VARCHAR2(20) NOT NULL UNIQUE,
    model VARCHAR2(100) NOT NULL,
    capacitate NUMBER NOT NULL,
    an_fabricatie NUMBER(4) NOT NULL
);

CREATE TABLE ZBOR (
    id_zbor NUMBER PRIMARY KEY,
    id_avion NUMBER NOT NULL,
    id_aeroport_plecare NUMBER NOT NULL,
    id_aeroport_sosire NUMBER NOT NULL,
    numar_zbor VARCHAR2(10) NOT NULL,
    data_plecare TIMESTAMP NOT NULL,
    data_sosire TIMESTAMP NOT NULL,
    data_plecare_efectiva TIMESTAMP,
    data_sosire_efectiva TIMESTAMP,
    durata_estimata NUMBER NOT NULL,
    pret_standard NUMBER(10,2) NOT NULL,
    status VARCHAR2(20) DEFAULT 'PROGRAMAT' NOT NULL,
    CONSTRAINT fk_zbor_avion FOREIGN KEY (id_avion) REFERENCES AVION(id_avion),
    CONSTRAINT fk_zbor_dep FOREIGN KEY (id_aeroport_plecare) REFERENCES AEROPORT(id_aeroport),
    CONSTRAINT fk_zbor_arr FOREIGN KEY (id_aeroport_sosire) REFERENCES AEROPORT(id_aeroport)
);

-- 2. TABELA CENTRALIZATA (Pasager)
CREATE TABLE PASAGER (
    id_pasager NUMBER PRIMARY KEY,
    nume VARCHAR2(100) NOT NULL,
    prenume VARCHAR2(100) NOT NULL,
    data_nasterii DATE NOT NULL,
    numar_document VARCHAR2(50) NOT NULL,
    nationalitate VARCHAR2(3) NOT NULL
);

-- 3. FRAGMENTE VERTICALE (Utilizator)
CREATE TABLE UTILIZATOR_SEC (
    id_user NUMBER PRIMARY KEY,
    email VARCHAR2(255) NOT NULL UNIQUE,
    parola VARCHAR2(255) NOT NULL,
    rol VARCHAR2(20) NOT NULL
);

CREATE TABLE UTILIZATOR_DATA (
    id_user NUMBER PRIMARY KEY,
    nume VARCHAR2(100) NOT NULL,
    prenume VARCHAR2(100) NOT NULL,
    telefon VARCHAR2(20),
    data_inregistrare DATE NOT NULL,
    CONSTRAINT FK_USER_VERT_LOCAL FOREIGN KEY (id_user) REFERENCES UTILIZATOR_SEC(id_user)
);

-- 4. FRAGMENTE ORIZONTALE (Tranzactii AM - ID-uri IMPARE)
CREATE TABLE REZERVARE_AM (
    id_rezervare NUMBER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 2) PRIMARY KEY,
    id_user NUMBER NOT NULL,
    data_rezervare DATE DEFAULT SYSDATE NOT NULL,
    regiune_vanzare VARCHAR2(2) DEFAULT 'AM' NOT NULL,
    total_de_plata NUMBER(10,2) NOT NULL,
    status VARCHAR2(20) NOT NULL,
    CONSTRAINT fk_rez_user_am FOREIGN KEY (id_user) REFERENCES UTILIZATOR_SEC(id_user)
);

CREATE TABLE PLATA_AM (
    id_plata NUMBER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 2) PRIMARY KEY,
    id_rezervare NUMBER NOT NULL,
    suma_achitata NUMBER(10,2) NOT NULL,
    data_plata TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
    metoda_plata VARCHAR2(50) NOT NULL,
    status VARCHAR2(20) NOT NULL,
    CONSTRAINT fk_plata_rez_am FOREIGN KEY (id_rezervare) REFERENCES REZERVARE_AM(id_rezervare)
);

CREATE TABLE BILET_AM (
    id_bilet NUMBER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 2) PRIMARY KEY,
    id_rezervare NUMBER NOT NULL,
    id_zbor NUMBER NOT NULL,
    id_pasager NUMBER NOT NULL,
    numar_rand NUMBER NOT NULL,
    litera_scaun CHAR(1) NOT NULL,
    clasa VARCHAR2(20) NOT NULL,
    pret_final NUMBER(10,2) NOT NULL,
    CONSTRAINT fk_bil_rez_am FOREIGN KEY (id_rezervare) REFERENCES REZERVARE_AM(id_rezervare),
    CONSTRAINT fk_bil_zbor_am FOREIGN KEY (id_zbor) REFERENCES ZBOR(id_zbor),
    CONSTRAINT fk_bil_pas_am FOREIGN KEY (id_pasager) REFERENCES PASAGER(id_pasager)
);





-- ❗ CONECTAT CA BD_EU
-- 1. TABELE REPLICATE (Nomenclatoare si Zboruri)
CREATE TABLE TARA (
    id_tara NUMBER PRIMARY KEY,
    nume_tara VARCHAR2(100) NOT NULL UNIQUE,
    cod_iso_2 CHAR(2) NOT NULL UNIQUE,
    CONSTRAINT chk_cod_iso_2_eu CHECK (cod_iso_2 = UPPER(cod_iso_2) AND LENGTH(cod_iso_2) = 2)
);

CREATE TABLE ORAS (
    id_oras NUMBER PRIMARY KEY,
    id_tara NUMBER NOT NULL,
    nume_oras VARCHAR2(100) NOT NULL,
    CONSTRAINT fk_oras_tara_eu FOREIGN KEY (id_tara) REFERENCES TARA(id_tara)
);

CREATE TABLE AEROPORT (
    id_aeroport NUMBER PRIMARY KEY,
    id_oras NUMBER NOT NULL,
    cod_iata CHAR(3) NOT NULL UNIQUE,
    nume_aeroport VARCHAR2(200) NOT NULL,
    CONSTRAINT fk_aeroport_oras_eu FOREIGN KEY (id_oras) REFERENCES ORAS(id_oras)
);

CREATE TABLE AVION (
    id_avion NUMBER PRIMARY KEY,
    numar_inmatriculare VARCHAR2(20) NOT NULL UNIQUE,
    model VARCHAR2(100) NOT NULL,
    capacitate NUMBER NOT NULL,
    an_fabricatie NUMBER(4) NOT NULL
);

CREATE TABLE ZBOR (
    id_zbor NUMBER PRIMARY KEY,
    id_avion NUMBER NOT NULL,
    id_aeroport_plecare NUMBER NOT NULL,
    id_aeroport_sosire NUMBER NOT NULL,
    numar_zbor VARCHAR2(10) NOT NULL,
    data_plecare TIMESTAMP NOT NULL,
    data_sosire TIMESTAMP NOT NULL,
    data_plecare_efectiva TIMESTAMP,
    data_sosire_efectiva TIMESTAMP,
    durata_estimata NUMBER NOT NULL,
    pret_standard NUMBER(10,2) NOT NULL,
    status VARCHAR2(20) NOT NULL,
    CONSTRAINT fk_zbor_avion_eu FOREIGN KEY (id_avion) REFERENCES AVION(id_avion),
    CONSTRAINT fk_zbor_dep_eu FOREIGN KEY (id_aeroport_plecare) REFERENCES AEROPORT(id_aeroport),
    CONSTRAINT fk_zbor_arr_eu FOREIGN KEY (id_aeroport_sosire) REFERENCES AEROPORT(id_aeroport)
);

-- 2. FRAGMENT VERTICAL REPLICAT (Utilizator Data)
CREATE TABLE UTILIZATOR_DATA (
    id_user NUMBER PRIMARY KEY,
    nume VARCHAR2(100) NOT NULL,
    prenume VARCHAR2(100) NOT NULL,
    telefon VARCHAR2(20),
    data_inregistrare DATE NOT NULL
);

-- 3. FRAGMENTE ORIZONTALE (Tranzactii EU - ID-uri PARE)
CREATE TABLE REZERVARE_EU (
    id_rezervare NUMBER GENERATED ALWAYS AS IDENTITY (START WITH 2 INCREMENT BY 2) PRIMARY KEY,
    id_user NUMBER NOT NULL, -- FK logic catre UTILIZATOR_SEC@BD_AM
    data_rezervare DATE DEFAULT SYSDATE NOT NULL,
    regiune_vanzare VARCHAR2(2) DEFAULT 'EU' NOT NULL,
    total_de_plata NUMBER(10,2) NOT NULL,
    status VARCHAR2(20) NOT NULL
);

CREATE TABLE PLATA_EU (
    id_plata NUMBER GENERATED ALWAYS AS IDENTITY (START WITH 2 INCREMENT BY 2) PRIMARY KEY,
    id_rezervare NUMBER NOT NULL,
    suma_achitata NUMBER(10,2) NOT NULL,
    data_plata TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
    metoda_plata VARCHAR2(50) NOT NULL,
    status VARCHAR2(20) NOT NULL,
    CONSTRAINT fk_plata_rez_eu FOREIGN KEY (id_rezervare) REFERENCES REZERVARE_EU(id_rezervare)
);

CREATE TABLE BILET_EU (
    id_bilet NUMBER GENERATED ALWAYS AS IDENTITY (START WITH 2 INCREMENT BY 2) PRIMARY KEY,
    id_rezervare NUMBER NOT NULL,
    id_zbor NUMBER NOT NULL,
    id_pasager NUMBER NOT NULL, -- FK logic catre PASAGER@BD_AM
    numar_rand NUMBER NOT NULL,
    litera_scaun CHAR(1) NOT NULL,
    clasa VARCHAR2(20) NOT NULL,
    pret_final NUMBER(10,2) NOT NULL,
    CONSTRAINT fk_bil_rez_eu FOREIGN KEY (id_rezervare) REFERENCES REZERVARE_EU(id_rezervare),
    CONSTRAINT fk_bil_zbor_eu FOREIGN KEY (id_zbor) REFERENCES ZBOR(id_zbor)
);

