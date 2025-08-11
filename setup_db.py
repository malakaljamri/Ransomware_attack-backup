import sqlite3

def setup_database(db_path='DataBase.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS credit_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_number TEXT,
            card_holder TEXT,
            expiry_date TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Decryption_Keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            password TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Hitmen_for_hire (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            specialty TEXT,
            price INTEGER
        )
    ''')

    # Insert sample data into credit_cards
    cursor.executemany('''
        INSERT INTO credit_cards (card_number, card_holder, expiry_date) VALUES (?, ?, ?)
    ''', [
        ('4005321443334322', 'John Doe', '12/24'),
        ('5555444433332222', 'Jane Smith', '10/23'),
        ('4111222233334444', 'Alice Johnson', '09/25'),
    ])

    # Insert sample passwords into Decryption_Keys (your final challenge passwords)
    cursor.executemany('''
    INSERT INTO Decryption_Keys (password) VALUES (?)
''', [
    ('pas67890FGHIJK420Dyl712345',),
    ('letmein678GHIJK420DJCNCI69ENDK',),
    ('67890FGHIJK420DJCNCI69ENDK',),
])

    # Insert sample data into Hitmen_for_hire
    cursor.executemany('''
        INSERT INTO Hitmen_for_hire (name, specialty, price) VALUES (?, ?, ?)
    ''', [
        ('Viper', 'Stealth', 5000),
        ('Raven', 'Sniper', 7000),
        ('Ghost', 'Infiltration', 6500),
    ])

    conn.commit()
    conn.close()
    print("Database setup complete.")

if __name__ == "__main__":
    setup_database()
