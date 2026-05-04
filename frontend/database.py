import oracledb
import os
from dotenv import load_dotenv

load_dotenv()

# setam dsn-ul (schemele sunt pe acelasi pdb)
DB_DSN = os.getenv("DB_DSN", "localhost:1521/HOMEDB1PDB")

def get_connection(node="AM"):
    # returneaza conexiunea pt schema aleasa
    try:
        # alegem user si parola in functie de nod
        if node == "AM":
            user = "BD_AM"
            password = "parola_am"
        elif node == "EU":
            user = "BD_EU"
            password = "parola_eu"
        elif node == "GLOBAL":
            user = "BD_GLOBAL"
            password = "parola_global"
        else:
            raise ValueError("nod invalid. alege AM, EU sau GLOBAL.")
            
        connection = oracledb.connect(
            user=user,
            password=password,
            dsn=DB_DSN
        )
        return connection
    except Exception as e:
        raise Exception(f"eroare la conectarea spre nodul {node}: {e}")

def run_query(connection, query, params=None):
    # functia asta ruleaza select-uri
    cursor = connection.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        return columns, rows
    finally:
        cursor.close()

def run_statement(connection, statement, params=None):
    # functia asta ruleaza insert/update/delete
    cursor = connection.cursor()
    try:
        if params:
            cursor.execute(statement, params)
        else:
            cursor.execute(statement)
        connection.commit()
    finally:
        cursor.close()
