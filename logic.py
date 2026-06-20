#logic.py
WORKING_DAYS = 22.0

ROLES = ["IT", "Accounting", "Marketing", "HR", "Manager", "Employee","Other"]

def calculate_final_pay(salary, attendance, role, overtime_hours=0):
    """Tính toán lương thực nhận dựa trên ngày công, giờ OT và chức vụ."""
    hourly_rate = (salary / WORKING_DAYS) / 8
    ot_pay = overtime_hours * hourly_rate * 1.5 

    if role == "Manager":
        return round(salary + ot_pay, 2)
    else:
        base_pay = (salary / WORKING_DAYS) * attendance
        return round(base_pay + ot_pay, 2)

def validate_employee_data(name, role, attendance_str, salary_str, overtime_str="0"):
    """Kiểm tra tính hợp lệ của dữ liệu đầu vào trước khi lưu vào Database."""
    if not name or not role or not attendance_str or not salary_str:
        return False, "All fields are required!", None, None, None
    if role not in ROLES:
        return False, "Invalid department/role selected!", None, None, None

    try:
        attendance = float(attendance_str)
        clean_salary = str(salary_str).replace(".", "")
        salary = float(clean_salary)
        
        if not overtime_str: overtime_str = "0"
        overtime = float(overtime_str)
        
        if attendance < 0 or attendance > WORKING_DAYS:
            return False, f"Days attended must be between 0 and {int(WORKING_DAYS)}!", None, None, None
        if salary < 0 or overtime < 0:
            return False, "Salary and Overtime cannot be negative!", None, None, None
            
        return True, "", attendance, salary, overtime
        
    except ValueError:
        return False, "Numbers must be valid!", None, None, None

def format_number(value):
    try:
        return f"{int(float(value)):,}".replace(",", ".")
    except (ValueError, TypeError):
        return "0"