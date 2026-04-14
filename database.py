import sqlite3

def create_database():
    conn = sqlite3.connect("resqnow.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hospitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialization TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            available_beds INTEGER,
            cost_government REAL,
            cost_private REAL
        )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_database()
    print("Database created successfully!")