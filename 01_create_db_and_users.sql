-- conetat ca sys

-- 0. Crearea schemei sursa
CREATE USER BLUEHORIZON IDENTIFIED BY parola_oltp DEFAULT TABLESPACE users QUOTA UNLIMITED ON users;

GRANT CONNECT, RESOURCE, CREATE VIEW TO BLUEHORIZON;
GRANT CREATE SESSION TO BLUEHORIZON;
GRANT CREATE TABLE TO BLUEHORIZON;
GRANT CREATE SEQUENCE TO BLUEHORIZON;
GRANT CREATE TRIGGER TO BLUEHORIZON;

-- 1. Crearea schemei pentru SERVERUL AMERICA (Nod central)
CREATE USER BD_AM IDENTIFIED BY parola_am DEFAULT TABLESPACE users QUOTA UNLIMITED ON users;
GRANT CONNECT, RESOURCE TO BD_AM;
GRANT CREATE SESSION, CREATE TABLE, CREATE VIEW, CREATE TRIGGER, CREATE SEQUENCE TO BD_AM;
GRANT CREATE DATABASE LINK TO BD_AM; -- Esential pentru a comunica cu Europa

-- 2. Crearea schemei pentru SERVERUL EUROPA (Nod local)
CREATE USER BD_EU IDENTIFIED BY parola_eu DEFAULT TABLESPACE users QUOTA UNLIMITED ON users;
GRANT CONNECT, RESOURCE TO BD_EU;
GRANT CREATE SESSION, CREATE TABLE, CREATE VIEW, CREATE TRIGGER, CREATE SEQUENCE TO BD_EU;
GRANT CREATE DATABASE LINK TO BD_EU; -- Esential pentru a comunica cu America

-- 3. Crearea schemei GLOBALE (Nivelul de transparenta)
CREATE USER BD_GLOBAL IDENTIFIED BY parola_global DEFAULT TABLESPACE users QUOTA UNLIMITED ON users;
GRANT CONNECT, RESOURCE TO BD_GLOBAL;
GRANT CREATE SESSION, CREATE VIEW, CREATE SYNONYM TO BD_GLOBAL;
GRANT CREATE DATABASE LINK TO BD_GLOBAL;

-- Acordăm drepturi de citire schemei sursă (BLUEHORIZON) către noile scheme
-- pentru a putea face ulterior INSERT INTO ... SELECT din ea
GRANT SELECT ANY TABLE TO BD_AM;
GRANT SELECT ANY TABLE TO BD_EU;



-- ! RULEAZA CA BD_AM:
CONNECT BD_AM/parola_am@localhost/homedb1pdb;
-- Legatura de la America spre Europa
CREATE DATABASE LINK link_bd_eu 
CONNECT TO BD_EU IDENTIFIED BY parola_eu 
USING 'localhost/homedb1pdb';


-- ! RULEAZA CA BD_EU:
CONNECT BD_EU/parola_eu@localhost/homedb1pdb;
-- Legatura de la Europa spre America (pentru a verifica pasagerii la imbarcare)
CREATE DATABASE LINK link_bd_am 
CONNECT TO BD_AM IDENTIFIED BY parola_am 
USING 'localhost/homedb1pdb';

-- ! RULEAZA CA BD_GLOBAL:
CONNECT BD_GLOBAL/parola_global@localhost/homedb1pdb;
-- Schema globala are nevoie de legaturi catre ambele noduri fizice
CREATE DATABASE LINK link_bd_am CONNECT TO BD_AM IDENTIFIED BY parola_am USING 'localhost/homedb1pdb';
CREATE DATABASE LINK link_bd_eu CONNECT TO BD_EU IDENTIFIED BY parola_eu USING 'localhost/homedb1pdb';
