# database.py
import sqlite3

class Database:
    def __init__(self, db_name="company_data.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                attendance INTEGER,
                salary REAL
            )
        ''')
        self.conn.commit()

    def fetch_all(self):
        self.cursor.execute("SELECT * FROM employees")
        return self.cursor.fetchall()

    def insert(self, name, attendance, salary):
        self.cursor.execute("INSERT INTO employees (name, attendance, salary) VALUES (?, ?, ?)",
                            (name, attendance, salary))
        self.conn.commit()

    def update(self, id, name, attendance, salary):
        self.cursor.execute("UPDATE employees SET name=?, attendance=?, salary=? WHERE id=?",
                            (name, attendance, salary, id))
        self.conn.commit()

    def delete(self, id):
        self.cursor.execute("DELETE FROM employees WHERE id=?", (id,))
        self.conn.commit()

    def search(self, name):
        search_term = f"%{name}%"
        self.cursor.execute("SELECT * FROM employees WHERE name LIKE ?", (search_term,))
        return self.cursor.fetchall()

    def __del__(self):
        self.conn.close()