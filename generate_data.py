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
    'Boeing 737-800': {'cols': ['A', 'B', 'C', 'D', 'E', 'F'], 'rows': 32},
    'Airbus A320': {'cols': ['A', 'B', 'C', 'D', 'E', 'F'], 'rows': 30},
    'Boeing 737-700': {'cols': ['A', 'B', 'C', 'D', 'E', 'F'], 'rows': 25},
    'Boeing 737 MAX 8': {'cols': ['A', 'B', 'C', 'D', 'E', 'F'], 'rows': 34},
    'ATR 72-600': {'cols': ['A', 'C', 'D', 'F'], 'rows': 18}
}

planes = [
    ('YR-ASD', 'Boeing 737-800', 189, 2015),
    ('YR-BCA', 'Airbus A320', 180, 2018),
    ('YR-XYZ', 'Boeing 737-700', 148, 2010),
    ('YR-MAX', 'Boeing 737 MAX 8', 200, 2022),
    ('YR-ATR', 'ATR 72-600', 70, 2019)
]


def random_date(start, end):
    return start + timedelta(
        seconds=random.randint(0, int((end - start).total_seconds()))
    )


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


first_names = [
    "Andrei", "Maria", "Ion", "Elena", "Radu", "Ana", "Mihai", "Cristina",
    "Alex", "Ioana", "David", "Sofia", "George", "Diana", "Vlad", "Anca",
    "Robert", "Carmen", "Dan", "Irina"
]

last_names = [
    "Popescu", "Ionescu", "Radu", "Dumitru", "Stoica", "Gheorghe", "Stan",
    "Matei", "Rusu", "Munteanu", "Popa", "Marinescu", "Dragomir", "Vasilescu"
]

domains = [
    "gmail.com", "yahoo.com", "outlook.com", "example.com"
]

countries = [
    # EUROPA
    {
        'name': 'Romania',
        'code': 'RO',
        'cities': [
            {'name': 'Bucuresti', 'airports': [('OTP', 'Henri Coanda Intl')]},
            {'name': 'Cluj-Napoca', 'airports': [('CLJ', 'Avram Iancu')]},
            {'name': 'Timisoara', 'airports': [('TSR', 'Traian Vuia')]},
            {'name': 'Iasi', 'airports': [('IAS', 'Iasi International')]}
        ]
    },
    {
        'name': 'UK',
        'code': 'GB',
        'cities': [
            {'name': 'London', 'airports': [('LHR', 'Heathrow')]}
        ]
    },
    {
        'name': 'France',
        'code': 'FR',
        'cities': [
            {'name': 'Paris', 'airports': [('CDG', 'Charles de Gaulle')]}
        ]
    },
    {
        'name': 'Germany',
        'code': 'DE',
        'cities': [
            {'name': 'Frankfurt', 'airports': [('FRA', 'Frankfurt am Main')]}
        ]
    },
    {
        'name': 'Netherlands',
        'code': 'NL',
        'cities': [
            {'name': 'Amsterdam', 'airports': [('AMS', 'Schiphol')]}
        ]
    },
    {
        'name': 'Spain',
        'code': 'ES',
        'cities': [
            {'name': 'Barcelona', 'airports': [('BCN', 'El Prat')]}
        ]
    },

    # AMERICA
    {
        'name': 'United States',
        'code': 'US',
        'cities': [
            {'name': 'New York', 'airports': [('JFK', 'John F. Kennedy')]},
            {'name': 'Los Angeles', 'airports': [('LAX', 'Los Angeles Intl')]},
            {'name': 'Miami', 'airports': [('MIA', 'Miami Intl')]}
        ]
    },
    {
        'name': 'Canada',
        'code': 'CA',
        'cities': [
            {'name': 'Toronto', 'airports': [('YYZ', 'Toronto Pearson')]}
        ]
    },
    {
        'name': 'Brazil',
        'code': 'BR',
        'cities': [
            {'name': 'Sao Paulo', 'airports': [('GRU', 'Guarulhos Intl')]}
        ]
    }
]

occupied_seats = {}


def get_available_seat(flight_id, plane_model):
    """
    Genereaza un loc valid si liber specific pentru modelul avionului
    """
    if flight_id not in occupied_seats:
        occupied_seats[flight_id] = set()

    specs = PLANE_SPECS.get(
        plane_model,
        {'cols': ['A', 'B', 'C', 'D', 'E', 'F'], 'rows': 30}
    )

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


total_airports = sum(
    len(city['airports'])
    for country in countries
    for city in country['cities']
)

statements = []
statements.append("SET DEFINE OFF;")
statements.append("")

# TARI / ORASE / AEROPORTURI
statements.append("-- TARI, ORASE SI AEROPORTURI")

for country in countries:
    for city in country['cities']:
        for code, name in city['airports']:
            statements.append(
                f"INSERT INTO TARA (nume_tara, cod_iso_2) "
                f"SELECT {escape_sql(country['name'])}, {escape_sql(country['code'])} "
                f"FROM DUAL "
                f"WHERE NOT EXISTS "
                f"(SELECT 1 FROM TARA WHERE cod_iso_2 = {escape_sql(country['code'])});"
            )

            statements.append(
                f"INSERT INTO ORAS (id_tara, nume_oras) "
                f"SELECT id_tara, {escape_sql(city['name'])} "
                f"FROM TARA "
                f"WHERE cod_iso_2 = {escape_sql(country['code'])} "
                f"AND NOT EXISTS ("
                f"SELECT 1 FROM ORAS "
                f"WHERE nume_oras = {escape_sql(city['name'])} "
                f"AND id_tara = ("
                f"SELECT id_tara FROM TARA "
                f"WHERE cod_iso_2 = {escape_sql(country['code'])}"
                f"));"
            )

            statements.append(
                f"INSERT INTO AEROPORT (id_oras, cod_iata, nume_aeroport) "
                f"SELECT ("
                f"SELECT id_oras FROM ORAS "
                f"WHERE nume_oras = {escape_sql(city['name'])} "
                f"AND id_tara = ("
                f"SELECT id_tara FROM TARA "
                f"WHERE cod_iso_2 = {escape_sql(country['code'])}"
                f")"
                f"), "
                f"{escape_sql(code)}, "
                f"{escape_sql(name)} "
                f"FROM DUAL "
                f"WHERE NOT EXISTS ("
                f"SELECT 1 FROM AEROPORT "
                f"WHERE cod_iata = {escape_sql(code)}"
                f");"
            )

# AVIOANE
statements.append("")
statements.append("-- AVIOANE")

for plane in planes:
    statements.append(
        f"INSERT INTO AVION "
        f"(numar_inmatriculare, model, capacitate, an_fabricatie) "
        f"SELECT {escape_sql(plane[0])}, "
        f"{escape_sql(plane[1])}, "
        f"{plane[2]}, "
        f"{plane[3]} "
        f"FROM DUAL "
        f"WHERE NOT EXISTS ("
        f"SELECT 1 FROM AVION "
        f"WHERE numar_inmatriculare = {escape_sql(plane[0])}"
        f");"
    )

# UTILIZATORI
statements.append("")
statements.append("-- UTILIZATORI")

roles = ['CLIENT'] * (NUM_USERS - 5) + ['ADMIN'] * 5
random.shuffle(roles)

for i in range(NUM_USERS):
    fname = random.choice(first_names)
    lname = random.choice(last_names)
    email = f"{fname.lower()}.{lname.lower()}{i+1}@{random.choice(domains)}"
    phone = f"07{random.randint(10000000, 99999999)}"
    reg_date = random_date(
        datetime(2020, 1, 1),
        datetime(2023, 1, 1)
    )
    rol = roles[i]

    statements.append(
        f"INSERT INTO UTILIZATOR "
        f"(nume, prenume, email, parola, telefon, data_inregistrare, rol) "
        f"SELECT {escape_sql(lname)}, "
        f"{escape_sql(fname)}, "
        f"{escape_sql(email)}, "
        f"'parola123', "
        f"{escape_sql(phone)}, "
        f"{escape_sql(reg_date)}, "
        f"'{rol}' "
        f"FROM DUAL "
        f"WHERE NOT EXISTS ("
        f"SELECT 1 FROM UTILIZATOR "
        f"WHERE email = {escape_sql(email)}"
        f");"
    )

# PASAGERI
statements.append("")
statements.append("-- PASAGERI")

for i in range(NUM_PASSENGERS):
    fname = random.choice(first_names)
    lname = random.choice(last_names)
    dob = random_date(datetime(1960, 1, 1), datetime(2015, 1, 1))
    doc_num = f"XY{random.randint(100000, 999999)}"
    nat = random.choice(['RO', 'GB', 'FR', 'DE', 'US'])

    statements.append(
        f"INSERT INTO PASAGER "
        f"(nume, prenume, data_nasterii, numar_document, nationalitate) "
        f"VALUES ("
        f"{escape_sql(lname)}, "
        f"{escape_sql(fname)}, "
        f"{escape_sql(dob)}, "
        f"{escape_sql(doc_num)}, "
        f"{escape_sql(nat)}"
        f");"
    )

statements.append("")
statements.append("COMMIT;")

output_path = "insert_oltp.sql"

with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(statements))

print(
    f"Generated {output_path} "
    f"with users, passengers, countries, airports and planes."
)
