-- =========================================================================
-- 1. CREAREA UTILIZATORILOR (SCHEMELOR)
-- =========================================================================
-- rulat cu userul sys

-- A. BAZA DE DATE SURSĂ (Bdd_all)
CREATE USER BLUEHORIZON IDENTIFIED BY parola_sursa DEFAULT TABLESPACE users QUOTA UNLIMITED ON users;
GRANT CONNECT, RESOURCE, CREATE TABLE TO BLUEHORIZON;

-- B. SERVERUL AMERICA (Bd_am) - Nodul Central
CREATE USER BD_AM IDENTIFIED BY parola_am DEFAULT TABLESPACE users QUOTA UNLIMITED ON users;
GRANT CONNECT, RESOURCE TO BD_AM;
GRANT CREATE SESSION, CREATE TABLE, CREATE VIEW, CREATE TRIGGER, CREATE SEQUENCE, CREATE DATABASE LINK TO BD_AM;

-- C. SCHEMA GLOBALĂ - Nivelul de Transparență
CREATE USER BD_GLOBAL IDENTIFIED BY parola_global DEFAULT TABLESPACE users QUOTA UNLIMITED ON users;
GRANT CONNECT, RESOURCE TO BD_GLOBAL;
GRANT CREATE SESSION, CREATE VIEW, CREATE SYNONYM, CREATE DATABASE LINK TO BD_GLOBAL;

-- D. SERVERUL EUROPA (Bd_eu) - Nodul Local
CREATE USER BD_EU IDENTIFIED BY parola_eu DEFAULT TABLESPACE users QUOTA UNLIMITED ON users;
GRANT CONNECT, RESOURCE TO BD_EU;
GRANT CREATE SESSION, CREATE TABLE, CREATE VIEW, CREATE TRIGGER, CREATE SEQUENCE, CREATE DATABASE LINK TO BD_EU;

-- Drepturi pentru migrarea datelor
GRANT SELECT ANY TABLE TO BD_AM;
GRANT SELECT ANY TABLE TO BD_EU;



-- ! Deschide conexiunea BD_AM
-- Legatura de la America spre Europa
CREATE DATABASE LINK link_bd_eu CONNECT TO BD_EU IDENTIFIED BY parola_eu USING 'localhost/xepdb1'; 

-- ! Deschide conexiunea BD_EU
-- Legatura de la Europa spre America 
CREATE DATABASE LINK link_bd_am CONNECT TO BD_AM IDENTIFIED BY parola_am USING 'localhost/xepdb1';

-- ! Deschide conexiunea BD_GLOBAL
-- Schema globala are nevoie de legaturi catre ambele noduri locale
CREATE DATABASE LINK link_bd_am CONNECT TO BD_AM IDENTIFIED BY parola_am USING 'localhost/xepdb1';
CREATE DATABASE LINK link_bd_eu CONNECT TO BD_EU IDENTIFIED BY parola_eu USING 'localhost/xepdb1';
