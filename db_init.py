import sqlite3

# Connect (this will create the file if it doesn't exist)
conn = sqlite3.connect('tamperdb.sqlite3')

c = conn.cursor()

# Create table to store file records
c.execute("""CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    stored_name TEXT,
    salt TEXT,
    hash TEXT,
    version INTEGER,
    timestamp TEXT

)
""")

conn.commit()
conn.close()

print("Database initialized successfully.")
