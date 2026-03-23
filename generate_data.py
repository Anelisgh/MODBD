import random
from datetime import datetime, timedelta

NUM_USERS = 50
NUM_PASSENGERS = 80
NUM_FLIGHTS = 100
NUM_RESERVATIONS = 350
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2027, 6, 1) 
SIMULATED_NOW = datetime(2026, 1, 11, 12, 0, 0)

PLANE_SPECS = {
    'Boeing 737-800':   {'cols': ['A','B','C','D','E','F'], 'rows': 32},
    'Airbus A320':      {'cols': ['A','B','C','D','E','F'], 'rows': 30},
    'Boeing 737-700':   {'cols': ['A','B','C','D','E','F'], 'rows': 25},
    'Boeing 737 MAX 8': {'cols': ['A','B','C','D','E','F'], 'rows': 34},
    'ATR 72-600':       {'cols': ['A','C','D','F'],         'rows': 18}
}

planes = [
    ('YR-ASD', 'Boeing 737-800', 189, 2015),
    ('YR-BCA', 'Airbus A320', 180, 2018),
    ('YR-XYZ', 'Boeing 737-700', 148, 2010),
    ('YR-MAX', 'Boeing 737 MAX 8', 200, 2022),
    ('YR-ATR', 'ATR 72-600', 70, 2019)
]

def random_date(start, end):
    return start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

def escape_sql(val):
    if val is None:
        return "NULL"
    if isinstance(val, str):
        return "'" + val.replace("'", "''") + "'"
    if isinstance(val, datetime):
        return "TIMESTAMP '" + val.strftime('%Y-%m-%d %H:%M:%S') + "'"
    if isinstance(val, (int, float)):
        return str(val)
    return "NULL"

first_names = ["Andrei","Maria","Ion","Elena","Radu","Ana","Mihai","Cristina",
               "Alex","Ioana","David","Sofia","George","Diana","Vlad","Anca",
               "Robert","Carmen","Dan","Irina"]
last_names = ["Popescu","Ionescu","Radu","Dumitru","Stoica","Gheorghe","Stan",
              "Matei","Rusu","Munteanu","Popa","Marinescu","Dragomir","Vasilescu"]
domains = ["gmail.com","yahoo.com","outlook.com","example.com"]

countries = [
    {'name': 'Romania', 'code': 'RO', 'cities': [
        {'name': 'Bucuresti', 'airports': [('OTP', 'Henri Coanda Intl')]},
        {'name': 'Cluj-Napoca', 'airports': [('CLJ', 'Avram Iancu')]},
        {'name': 'Timisoara', 'airports': [('TSR', 'Traian Vuia')]},
        {'name': 'Iasi', 'airports': [('IAS', 'Iasi International')]}
    ]},
    {'name': 'UK', 'code': 'GB', 'cities': [{'name': 'London', 'airports': [('LHR', 'Heathrow')]}]},
    {'name': 'France', 'code': 'FR', 'cities': [{'name': 'Paris', 'airports': [('CDG', 'Charles de Gaulle')]}]},
    {'name': 'Germany', 'code': 'DE', 'cities': [{'name': 'Frankfurt', 'airports': [('FRA', 'Frankfurt am Main')]}]},
    {'name': 'Netherlands', 'code': 'NL', 'cities': [{'name': 'Amsterdam', 'airports': [('AMS', 'Schiphol')]}]},
    {'name': 'Spain', 'code': 'ES', 'cities': [{'name': 'Barcelona', 'airports': [('BCN', 'El Prat')]}]},
    {'name': 'UAE', 'code': 'AE', 'cities': [{'name': 'Dubai', 'airports': [('DXB', 'Dubai International')]}]}
]

occupied_seats = {}

def get_available_seat(flight_id, plane_model):
    """Genereaza un loc valid si liber specific pentru modelul avionului"""
    if flight_id not in occupied_seats:
        occupied_seats[flight_id] = set()
   
    specs = PLANE_SPECS.get(plane_model, {'cols': ['A','B','C','D','E','F'], 'rows': 30})
    available_cols = specs['cols']
    max_rows = specs['rows']

    for _ in range(100):
        row = random.randint(1, max_rows)
        seat = random.choice(available_cols)
        key = f"{row}-{seat}"
        
        if key not in occupied_seats[flight_id]:
            occupied_seats[flight_id].add(key)
            return row, seat
            
    return 1, available_cols[0] 

total_airports = sum(len(city['airports']) for country in countries for city in country['cities'])

statements = []
statements.append("SET DEFINE OFF;")
statements.append("")

statements.append("-- TARI, ORASE SI AEROPORTURI")
for country in countries:
    for city in country['cities']:
        for code, name in city['airports']:
            statements.append(f"INSERT INTO TARA (nume_tara, cod_iso_2) SELECT {escape_sql(country['name'])}, {escape_sql(country['code'])} FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM TARA WHERE cod_iso_2 = {escape_sql(country['code'])});")
            statements.append(f"INSERT INTO ORAS (id_tara, nume_oras) SELECT id_tara, {escape_sql(city['name'])} FROM TARA WHERE cod_iso_2 = {escape_sql(country['code'])} AND NOT EXISTS (SELECT 1 FROM ORAS WHERE nume_oras = {escape_sql(city['name'])} AND id_tara = (SELECT id_tara FROM TARA WHERE cod_iso_2 = {escape_sql(country['code'])}));")
            statements.append(f"INSERT INTO AEROPORT (id_oras, cod_iata, nume_aeroport) SELECT (SELECT id_oras FROM ORAS WHERE nume_oras = {escape_sql(city['name'])} AND id_tara = (SELECT id_tara FROM TARA WHERE cod_iso_2 = {escape_sql(country['code'])})), {escape_sql(code)}, {escape_sql(name)} FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM AEROPORT WHERE cod_iata = {escape_sql(code)});")

statements.append("")
statements.append("-- AVIOANE")
for plane in planes:
    statements.append(f"INSERT INTO AVION (numar_inmatriculare, model, capacitate, an_fabricatie) SELECT {escape_sql(plane[0])}, {escape_sql(plane[1])}, {plane[2]}, {plane[3]} FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM AVION WHERE numar_inmatriculare = {escape_sql(plane[0])});")

statements.append("")
statements.append("-- UTILIZATORI")
roles = ['CLIENT'] * (NUM_USERS - 5) + ['ADMIN'] * 5
random.shuffle(roles)
for i in range(NUM_USERS):
    fname = random.choice(first_names)
    lname = random.choice(last_names)
    email = f"{fname.lower()}.{lname.lower()}{i+1}@{random.choice(domains)}"
    phone = f"07{random.randint(10000000,99999999)}"
    reg_date = random_date(datetime(2020,1,1), datetime(2023,1,1))
    rol = roles[i]
    statements.append(f"INSERT INTO UTILIZATOR (nume, prenume, email, parola, telefon, data_inregistrare, rol) SELECT {escape_sql(lname)}, {escape_sql(fname)}, {escape_sql(email)}, 'parola123', {escape_sql(phone)}, {escape_sql(reg_date)}, '{rol}' FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM UTILIZATOR WHERE email = {escape_sql(email)});")

statements.append("")
statements.append("-- PASAGERI")
for i in range(NUM_PASSENGERS):
    fname = random.choice(first_names)
    lname = random.choice(last_names)
    dob = random_date(datetime(1960,1,1), datetime(2015,1,1))
    doc_num = f"XY{random.randint(100000,999999)}"
    nat = random.choice(['RO','GB','FR','DE','US'])
    statements.append(f"INSERT INTO PASAGER (nume, prenume, data_nasterii, numar_document, nationalitate) VALUES ({escape_sql(lname)}, {escape_sql(fname)}, {escape_sql(dob)}, {escape_sql(doc_num)}, {escape_sql(nat)});")

statements.append("")
statements.append("COMMIT;")
statements.append("")

statements.append("-- ZBORURI")
flights_data = []
for i in range(NUM_FLIGHTS):
    origin_idx = random.randint(1, total_airports)
    dest_idx = random.randint(1, total_airports)
    while dest_idx == origin_idx:
        dest_idx = random.randint(1, total_airports)
    
    dep_time = random_date(START_DATE, END_DATE)
    duration = 60 * random.randint(1,4) + random.randint(0,30)
    arr_time = dep_time + timedelta(minutes=duration)
    price = random.randint(50, 400)
    
    selected_plane = random.choice(planes)
    plane_reg = selected_plane[0]
    plane_model = selected_plane[1]

    eff_dep_time = None
    eff_arr_time = None
    status = 'PROGRAMAT'

    if dep_time > SIMULATED_NOW:
        status = 'PROGRAMAT'
        eff_dep_time = None
        eff_arr_time = None
    else:
        dice = random.random()
        
        if dice < 0.05:
            status = 'ANULAT'
            eff_dep_time = None
            eff_arr_time = None
        
        else:
            is_delayed = random.random() < 0.40 
            
            if is_delayed:
                delay_minutes = random.randint(15, 240)
                eff_dep_time = dep_time + timedelta(minutes=delay_minutes)
                eff_arr_time = arr_time + timedelta(minutes=delay_minutes)
            else:
                eff_dep_time = dep_time
                eff_arr_time = arr_time
            if eff_dep_time > SIMULATED_NOW:
                status = 'INTARZIAT'
            elif eff_dep_time <= SIMULATED_NOW < eff_arr_time:
                status = 'IN_ZBOR'
            else:
                status = 'ATERIZAT'

    sql = f"INSERT INTO ZBOR (id_avion, id_aeroport_plecare, id_aeroport_sosire, numar_zbor, data_plecare, data_sosire, data_plecare_efectiva, data_sosire_efectiva, durata_estimata, pret_standard, status) VALUES (" \
          f"(SELECT id_avion FROM AVION WHERE numar_inmatriculare = {escape_sql(plane_reg)}), " \
          f"(SELECT id_aeroport FROM (SELECT id_aeroport, ROWNUM rn FROM AEROPORT ORDER BY id_aeroport) WHERE rn = {origin_idx}), " \
          f"(SELECT id_aeroport FROM (SELECT id_aeroport, ROWNUM rn FROM AEROPORT ORDER BY id_aeroport) WHERE rn = {dest_idx}), " \
          f"'RO{100+i}', {escape_sql(dep_time)}, {escape_sql(arr_time)}, " \
          f"{escape_sql(eff_dep_time)}, {escape_sql(eff_arr_time)}, " \
          f"{duration}, {price}, '{status}');"
          
    statements.append(sql)
    flights_data.append({
        'index': i+1, 
        'price': price, 
        'dep_time': dep_time, 
        'status': status,
        'model': plane_model
    })

statements.append("")
statements.append("COMMIT;")
statements.append("")

statements.append("-- REZERVARI, BILETE SI PLATI")
statements.append("DECLARE")
statements.append("  v_rez_id NUMBER;")
statements.append("BEGIN")

count_ops = 0
for i in range(NUM_RESERVATIONS):
    user_idx = random.randint(1, NUM_USERS)
    
    flight = random.choice(flights_data)
    flight_idx = flight['index']
    
    res_date = flight['dep_time'] - timedelta(days=random.randint(1,60))
    if res_date < datetime(2020,1,1):
        res_date = datetime(2023,1,1)

    if res_date > SIMULATED_NOW:
        continue

    num_tickets = random.randint(1, 4)
    tickets = []
    total_price = 0
    
    for _ in range(num_tickets):
        pas_idx = random.randint(1, NUM_PASSENGERS)
        is_business = random.random() > 0.90
        
        ticket_price = flight['price'] * 1.8 if is_business else flight['price']
        total_price += ticket_price
        clasa = 'BUSINESS' if is_business else 'ECONOMY'
        
        row, seat = get_available_seat(flight_idx, flight['model'])
        
        tickets.append({
            'pas_idx': pas_idx, 
            'clasa': clasa, 
            'pret': ticket_price, 
            'row': row, 
            'seat': seat
        })
    
    pay_method = random.choice(['CARD', 'TRANSFER_BANCAR', 'CASH'])
    
    if flight['status'] == 'ANULAT':
        res_status = 'ANULATA' 
        pay_status = 'RAMBURSATA'
    else:
        res_status = 'CONFIRMATA'
        pay_status = 'ACCEPTATA'


    statements.append(f"  -- Rezervare {i+1}")
    statements.append(f"  INSERT INTO REZERVARE (id_user, data_rezervare, total_de_plata, status) VALUES ((SELECT id_user FROM (SELECT id_user, ROWNUM rn FROM UTILIZATOR ORDER BY id_user) WHERE rn = {user_idx}), {escape_sql(res_date)}, {total_price}, '{res_status}') RETURNING id_rezervare INTO v_rez_id;")
    statements.append(f"  INSERT INTO PLATA (id_rezervare, suma_achitata, data_plata, metoda_plata, status) VALUES (v_rez_id, {total_price}, {escape_sql(res_date)}, '{pay_method}', '{pay_status}');")
    
    for ticket in tickets:
        statements.append(f"  INSERT INTO BILET (id_rezervare, id_zbor, id_pasager, numar_rand, litera_scaun, clasa, pret_final) VALUES (v_rez_id, (SELECT id_zbor FROM (SELECT id_zbor, ROWNUM rn FROM ZBOR ORDER BY id_zbor) WHERE rn = {flight_idx}), (SELECT id_pasager FROM (SELECT id_pasager, ROWNUM rn FROM PASAGER ORDER BY id_pasager) WHERE rn = {ticket['pas_idx']}), {ticket['row']}, {escape_sql(ticket['seat'])}, {escape_sql(ticket['clasa'])}, {ticket['pret']});")
    
    count_ops += 1
    if count_ops % 50 == 0:
        statements.append("  COMMIT;")

statements.append("  COMMIT;")
statements.append("END;")
statements.append("/")

output_path = 'insert_oltp.sql'

with open(output_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(statements))

print(f"Generated {output_path} with {NUM_FLIGHTS} flights and approx {NUM_RESERVATIONS} reservations.")
