#database.py
import mysql.connector
import datetime

class Database:
    def __init__(self):
        self.conn = mysql.connector.connect(
            host="localhost",       
            user="root",            
            password=""            
        )
        self.cursor = self.conn.cursor()
        self.cursor.execute("CREATE DATABASE IF NOT EXISTS `employee-payroll-and-attendance-tracker`")
        self.cursor.execute("USE `employee-payroll-and-attendance-tracker`")
        self.create_table()

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                role VARCHAR(100) NOT NULL,
                attendance INT,
                salary DOUBLE,
                last_checkin_date VARCHAR(20),
                last_checkin_time VARCHAR(20),
                status VARCHAR(50),
                on_time_count INT DEFAULT 0,
                late_count INT DEFAULT 0,
                overtime_hours DOUBLE DEFAULT 0
            )
        ''')
        self.conn.commit()

    def fetch_all(self):
        self.cursor.execute("SELECT * FROM employees")
        return self.cursor.fetchall()

    def insert(self, name, role, attendance, salary, overtime=0):
        query = "INSERT INTO employees (name, role, attendance, salary, last_checkin_date, last_checkin_time, status, overtime_hours) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        self.cursor.execute(query, (name, role, attendance, salary, "", "", "No Data", overtime))
        self.conn.commit()

    def update(self, id, name, role, attendance, salary, overtime):
        query = "UPDATE employees SET name=%s, role=%s, attendance=%s, salary=%s, overtime_hours=%s WHERE id=%s"
        self.cursor.execute(query, (name, role, attendance, salary, overtime, id))
        self.conn.commit()

    def delete(self, id):
        self.cursor.execute("DELETE FROM employees WHERE id=%s", (id,))
        self.conn.commit()

    def search_and_filter(self, name, role):
        search_term = f"%{name}%"
        if role == "All" or role == "":
            query = "SELECT * FROM employees WHERE name LIKE %s"
            self.cursor.execute(query, (search_term,))
        else:
            query = "SELECT * FROM employees WHERE name LIKE %s AND role = %s"
            self.cursor.execute(query, (search_term, role))
        return self.cursor.fetchall()

    def check_in_employee(self, employee_id, max_days):
        """Xử lý logic điểm danh: Chống spam, kiểm tra giới hạn ngày, và xác định đi muộn/đúng giờ."""
        now = datetime.datetime.now()
        today_date = now.strftime("%Y-%m-%d")
        now_time_str = now.strftime("%H:%M:%S")
        
        work_start_time = datetime.time(8, 30, 0) 
        
        if now.time() > work_start_time:
            status = "Late"
            late_add, ontime_add = 1, 0
        else:
            status = "On Time"
            late_add, ontime_add = 0, 1

        query = "SELECT name, attendance, last_checkin_date, on_time_count, late_count FROM employees WHERE id = %s"
        self.cursor.execute(query, (employee_id,))
        result = self.cursor.fetchone()
        
        if not result:
            return False, "Employee ID not found!", ""
            
        name, current_attendance, last_checkin_date, cur_ontime, cur_late = result
        
        if last_checkin_date == today_date:
            return False, f"Anti-Spam: {name} has already checked in TODAY!", "Spam"
            
        if current_attendance >= max_days:
            return False, f"{name} has reached maximum attendance!", "Max"
            
        new_attendance = current_attendance + 1
        new_ontime = cur_ontime + ontime_add
        new_late = cur_late + late_add
        
        update_query = "UPDATE employees SET attendance = %s, last_checkin_date = %s, last_checkin_time = %s, status = %s, on_time_count = %s, late_count = %s WHERE id = %s"
        self.cursor.execute(update_query, (new_attendance, today_date, now_time_str, status, new_ontime, new_late, employee_id))
        self.conn.commit()
        
        return True, f"[{now_time_str}] Check-in {status.upper()} for {name}!", status

    def __del__(self):
        if hasattr(self, 'conn') and self.conn.is_connected():
            self.cursor.close()
            self.conn.close()