# database.py
import sqlite3
import datetime # NEW: Thư viện lấy ngày giờ hệ thống

class Database:
    def __init__(self, db_name="company_data.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        # NEW: Thêm cột last_checkin_date TEXT
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                attendance INTEGER,
                salary REAL,
                last_checkin_date TEXT 
            )
        ''')
        self.conn.commit()

    def fetch_all(self):
        self.cursor.execute("SELECT * FROM employees")
        return self.cursor.fetchall()

    def insert(self, name, role, attendance, salary):
        # Khi mới thêm nhân viên, ngày điểm danh gần nhất để trống ("")
        self.cursor.execute("INSERT INTO employees (name, role, attendance, salary, last_checkin_date) VALUES (?, ?, ?, ?, ?)",
                            (name, role, attendance, salary, ""))
        self.conn.commit()

    def update(self, id, name, role, attendance, salary):
        self.cursor.execute("UPDATE employees SET name=?, role=?, attendance=?, salary=? WHERE id=?",
                            (name, role, attendance, salary, id))
        self.conn.commit()

    def delete(self, id):
        self.cursor.execute("DELETE FROM employees WHERE id=?", (id,))
        self.conn.commit()

    def search_and_filter(self, name, role):
        search_term = f"%{name}%"
        if role == "All" or role == "":
            self.cursor.execute("SELECT * FROM employees WHERE name LIKE ?", (search_term,))
        else:
            self.cursor.execute("SELECT * FROM employees WHERE name LIKE ? AND role = ?", (search_term, role))
        return self.cursor.fetchall()

    # --- HÀM ĐIỂM DANH ĐÃ ĐƯỢC NÂNG CẤP CHỐNG SPAM ---
    def check_in_employee(self, employee_id, max_days):
        # Lấy ngày hôm nay của hệ thống (Định dạng: YYYY-MM-DD)
        today = datetime.date.today().strftime("%Y-%m-%d")
        
        # Tìm nhân viên và kiểm tra ngày điểm danh gần nhất
        self.cursor.execute("SELECT name, attendance, last_checkin_date FROM employees WHERE id = ?", (employee_id,))
        result = self.cursor.fetchone()
        
        if not result:
            return False, "Employee ID not found!"
            
        name, current_attendance, last_checkin_date = result
        
        # LOGIC 1: Kiểm tra xem hôm nay đã điểm danh chưa?
        if last_checkin_date == today:
            return False, f"Anti-Spam: {name} has already checked in TODAY!"
            
        # LOGIC 2: Kiểm tra xem đã làm lố số ngày trong tháng chưa?
        if current_attendance >= max_days:
            return False, f"{name} has reached maximum attendance ({int(max_days)} days)!"
            
        # Nếu vượt qua cả 2 bài test -> Cấp phép cho điểm danh
        new_attendance = current_attendance + 1
        
        # Cập nhật số ngày mới VÀ lưu lại ngày hôm nay là ngày điểm danh gần nhất
        self.cursor.execute("UPDATE employees SET attendance = ?, last_checkin_date = ? WHERE id = ?", 
                            (new_attendance, today, employee_id))
        self.conn.commit()
        
        return True, f"Check-in successful for {name}! (Total: {int(new_attendance)} days)"

    def __del__(self):
        self.conn.close()