# logic.py
WORKING_DAYS = 22.0

ROLES = ["IT", "Accounting", "Marketing", "HR", "Manager", "Other"]

def calculate_final_pay(salary, attendance, role):
    """Calculates the final pay based on attendance and role."""
    if role == "Manager":
        # Privilege: Managers always receive 100% base salary
        return round(salary, 2)
    else:
        # Regular employees are paid based on attendance proportion
        return round((salary / WORKING_DAYS) * attendance, 2)

def validate_employee_data(name, role, attendance_str, salary_str):
    """
    Checks if the inputs are valid.
    """
    if not name or not role or not attendance_str or not salary_str:
        return False, "All fields are required!", None, None
        
    if role not in ROLES:
        return False, "Invalid department/role selected!", None, None

    try:
        attendance = float(attendance_str)
        salary = float(salary_str)
        
        if attendance < 0 or attendance > WORKING_DAYS:
            return False, f"Days attended must be between 0 and {int(WORKING_DAYS)}!", None, None
            
        if salary < 0:
            return False, "Salary cannot be negative!", None, None
            
        return True, "", attendance, salary
        
    except ValueError:
        return False, "Attendance and Salary must be numeric values!", None, None