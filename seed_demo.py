import sqlite3

def seed_demo_db():
    conn = sqlite3.connect('app/demo.db')
    cursor = conn.cursor()

    # Artists
    cursor.execute('''CREATE TABLE IF NOT EXISTS artists (
        artist_id INTEGER PRIMARY KEY,
        name TEXT
    )''')
    artists_data = [
        (1, "The 1975"),
        (2, "Ricky Montgomery"),
        (3, "Ravyn Lenae"),
        (4, "Alanis Morissette"),
        (5, "Alice In Chains")
    ]
    cursor.executemany("INSERT OR IGNORE INTO artists (artist_id, name) VALUES (?, ?)", artists_data)

    # Albums
    cursor.execute('''CREATE TABLE IF NOT EXISTS albums (
        album_id INTEGER PRIMARY KEY,
        title TEXT,
        artist_id INTEGER,
        FOREIGN KEY (artist_id) REFERENCES artists (artist_id)
    )''')
    albums_data = [
        (1, "Being Funny in a Foreign Language (2022)", 1),
        (2, "Montgomery Ricky (2016)", 2),
        (3, "Hypnos", 2),
        (4, "Let There Be Rock", 1),
        (5, "Big Ones", 3)
    ]
    cursor.executemany("INSERT OR IGNORE INTO albums (album_id, title, artist_id) VALUES (?, ?, ?)", albums_data)

    # Tracks
    cursor.execute('''CREATE TABLE IF NOT EXISTS tracks (
        track_id INTEGER PRIMARY KEY,
        name TEXT,
        album_id INTEGER,
        milliseconds INTEGER,
        unit_price REAL,
        composer TEXT,
        FOREIGN KEY (album_id) REFERENCES albums (album_id)
    )''')
    tracks_data = [
        (1, "About You", 1, 343719, 0.99, "Matthew Healy"),
        (2, "Line Without a Hook", 2, 342562, 0.99, "Ricky Montgomery"),
        (3, "Love Me Not", 3, 230619, 0.99, "Ravyn Lenae"),
        (4, "Restless and Wild", 3, 252051, 0.99, "Unknown"),
        (5, "Princess of the Dawn", 3, 375418, 0.99, "Unknown")
    ]
    cursor.executemany("INSERT OR IGNORE INTO tracks (track_id, name, album_id, milliseconds, unit_price, composer) VALUES (?, ?, ?, ?, ?, ?)", tracks_data)

    # Departments (from prompt)
    cursor.execute('''CREATE TABLE IF NOT EXISTS departments (
        "DepartmentId" INTEGER PRIMARY KEY,
        "Name" TEXT
    )''')
    cursor.executemany("INSERT OR IGNORE INTO departments (\"DepartmentId\", \"Name\") VALUES (?, ?)", [(1, "IT"), (2, "HR")])
    
    # Employees (from prompt)
    cursor.execute('''CREATE TABLE IF NOT EXISTS employees (
        "EmployeeId" INTEGER PRIMARY KEY,
        "Name" TEXT,
        "Salary" REAL,
        "DepartmentId" INTEGER
    )''')
    cursor.executemany("INSERT OR IGNORE INTO employees (\"EmployeeId\", \"Name\", \"Salary\", \"DepartmentId\") VALUES (?, ?, ?, ?)", [
        (1, "John Doe", 80000.0, 1),
        (2, "Jane Smith", 90000.0, 1)
    ])

    # Users (from prompt)
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT
    )''')
    cursor.executemany("INSERT OR IGNORE INTO users (id, name) VALUES (?, ?)", [(1, "Admin")])

    conn.commit()
    conn.close()
    print("Local demo.db seeded successfully.")

if __name__ == "__main__":
    seed_demo_db()
