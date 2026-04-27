-- ! RULEAZA CA BD_GLOBAL:
CONNECT BD_GLOBAL/parola_global@localhost/homedb1pdb;

-- A. RECONSTRUCȚIA FRAGMENTELOR ORIZONTALE (Reuniune / UNION ALL)
CREATE OR REPLACE VIEW V_REZERVARE AS
SELECT * FROM REZERVARE_AM@link_bd_am
UNION ALL
SELECT * FROM REZERVARE_EU@link_bd_eu;

CREATE OR REPLACE VIEW V_PLATA AS
SELECT * FROM PLATA_AM@link_bd_am
UNION ALL
SELECT * FROM PLATA_EU@link_bd_eu;

CREATE OR REPLACE VIEW V_BILET AS
SELECT * FROM BILET_AM@link_bd_am
UNION ALL
SELECT * FROM BILET_EU@link_bd_eu;


-- B. RECONSTRUCȚIA FRAGMENTULUI VERTICAL (Compunere / JOIN)
CREATE OR REPLACE VIEW V_UTILIZATOR AS
SELECT 
    s.id_user, 
    d.nume, 
    d.prenume, 
    s.email, 
    s.parola, 
    d.telefon, 
    d.data_inregistrare, 
    s.rol
FROM UTILIZATOR_SEC@link_bd_am s
JOIN UTILIZATOR_DATA@link_bd_am d ON s.id_user = d.id_user;
-- (Ambele fragmente există pe AM, deci e mai eficient să facem join-ul direct pe acel server)


-- C. ACCESUL LA TABELELE REPLICATE ȘI UNICE (Sinonime)
-- Pentru datele care sunt identice pe ambele servere, sau care stau într-un singur loc, 
-- creăm pur și simplu un sinonim către nodul principal (AM).
CREATE OR REPLACE SYNONYM TARA FOR TARA@link_bd_am;
CREATE OR REPLACE SYNONYM ORAS FOR ORAS@link_bd_am;
CREATE OR REPLACE SYNONYM AEROPORT FOR AEROPORT@link_bd_am;
CREATE OR REPLACE SYNONYM AVION FOR AVION@link_bd_am;
CREATE OR REPLACE SYNONYM ZBOR FOR ZBOR@link_bd_am;
CREATE OR REPLACE SYNONYM PASAGER FOR PASAGER@link_bd_am;