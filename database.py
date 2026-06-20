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
        # 1. Bảng lưu thông tin Nhân viên (Giữ nguyên)
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
        
        # 2. BẢNG MỚI: Nhật ký chấm công chi tiết theo từng ngày (Liên kết qua emp_id)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance_logs (
                log_id INT AUTO_INCREMENT PRIMARY KEY,
                emp_id INT,
                log_date VARCHAR(20),
                log_time VARCHAR(20),
                status VARCHAR(50),
                FOREIGN KEY(emp_id) REFERENCES employees(id) ON DELETE CASCADE
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
        now = datetime.datetime.now()
        today_date = now.strftime("%Y-%m-%d") # Format: 2026-06-20
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
        
        # A. Cập nhật bảng gốc
        update_query = "UPDATE employees SET attendance = %s, last_checkin_date = %s, last_checkin_time = %s, status = %s, on_time_count = %s, late_count = %s WHERE id = %s"
        self.cursor.execute(update_query, (new_attendance, today_date, now_time_str, status, new_ontime, new_late, employee_id))
        
        # B. THÊM LOG VÀO BẢNG NHẬT KÝ (Ghi lại lịch sử)
        log_query = "INSERT INTO attendance_logs (emp_id, log_date, log_time, status) VALUES (%s, %s, %s, %s)"
        self.cursor.execute(log_query, (employee_id, today_date, now_time_str, status))
        
        self.conn.commit()
        
        return True, f"[{now_time_str}] Check-in {status.upper()} for {name}!", status

    # --- HÀM MỚI: LỌC LỊCH SỬ THEO THÁNG/NĂM ---
    def get_attendance_history(self, month, year):
        # Tạo chuỗi tìm kiếm (VD: 2026-06-%)
        search_pattern = f"{year}-{month}-%"
        
        # Kỹ thuật JOIN 2 bảng để lấy Tên nhân viên ghép với Lịch sử quét mã
        query = '''
            SELECT e.name, e.role, a.log_date, a.log_time, a.status 
            FROM attendance_logs a
            JOIN employees e ON a.emp_id = e.id
            WHERE a.log_date LIKE %s
            ORDER BY a.log_date DESC, a.log_time DESC
        '''
        self.cursor.execute(query, (search_pattern,))
        return self.cursor.fetchall()

    def __del__(self):
        if hasattr(self, 'conn') and self.conn.is_connected():
            self.cursor.close()
            self.conn.close()