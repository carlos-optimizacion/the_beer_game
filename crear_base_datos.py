import sqlite3

conexion = sqlite3.connect("beer_game.db")
cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS teams (
    team_id TEXT PRIMARY KEY,
    team_name TEXT,
    creation_date TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS players (
    player_id TEXT PRIMARY KEY,
    team_id TEXT,
    name TEXT,
    role TEXT,
    email TEXT,
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS game_parameters (
    team_id TEXT PRIMARY KEY,
    initial_stock INTEGER,
    lead_time INTEGER,
    delay_time INTEGER,
    holding_cost REAL,
    backorder_cost REAL,
    weeks_total INTEGER,
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS rounds (
    round_id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id TEXT,
    week INTEGER,
    role TEXT,
    stock INTEGER,
    backorder INTEGER,
    incoming_order INTEGER,
    incoming_shipment INTEGER,
    placed_order INTEGER,
    sent_shipment INTEGER,
    total_cost REAL,
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS demands (
    team_id TEXT,
    week INTEGER,
    demand INTEGER,
    PRIMARY KEY (team_id, week),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
)
""")

conexion.commit()
conexion.close()

print("✅ Base de datos creada correctamente.")
