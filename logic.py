# logic.py

# Business Constants
WORKING_DAYS = 30.0

def calculate_final_pay(salary, attendance):
    """Calculates the final pay based on attendance."""
    return round((salary / WORKING_DAYS) * attendance, 2)

def validate_employee_data(name, attendance_str, salary_str):
    """
    Checks if the inputs are valid.
    Returns a tuple: (is_valid, error_message, attendance_float, salary_float)
    """
    if not name or not attendance_str or not salary_str:
        return False, "All fields are required!", None, None
        
    try:
        attendance = float(attendance_str)
        salary = float(salary_str)
        
        if attendance < 0 or attendance > WORKING_DAYS:
            return False, f"Days attended must be between 0 and {int(WORKING_DAYS)}!", None, None
            
        if salary < 0:
            return False, "Salary cannot be negative!", None, None
            
        return True, "", attendance, salary
        
    except ValueError:
        return False, "Attendance and Salary must be numbers!", None, None