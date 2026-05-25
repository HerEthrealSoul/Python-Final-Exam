import tkinter as tk
from tkinter import ttk, messagebox
from database import Database

# Initialize our database
db = Database()

class EmployeeTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Employee Payroll & Attendance Tracker")
        self.root.geometry("850x550")
        
        # --- NEW: Define Business Rules ---
        self.WORKING_DAYS = 22.0  # Max days in the calculation formula
        
        # GUI Variables
        self.id_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.attendance_var = tk.StringVar()
        self.salary_var = tk.StringVar()
        self.search_var = tk.StringVar()

        # Setup GUI Layout
        self.setup_ui()
        self.populate_treeview()

    def setup_ui(self):
        """Build the GUI components."""
        # --- Input Frame ---
        input_frame = tk.Frame(self.root, padx=20, pady=20)
        input_frame.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(input_frame, text="Name:").grid(row=0, column=0, pady=10, sticky="w")
        tk.Entry(input_frame, textvariable=self.name_var).grid(row=0, column=1)

        tk.Label(input_frame, text=f"Days Attended (Max {int(self.WORKING_DAYS)}):").grid(row=1, column=0, pady=10, sticky="w")
        tk.Entry(input_frame, textvariable=self.attendance_var).grid(row=1, column=1)

        tk.Label(input_frame, text="Base Salary ($):").grid(row=2, column=0, pady=10, sticky="w")
        tk.Entry(input_frame, textvariable=self.salary_var).grid(row=2, column=1)

        # Buttons
        btn_frame = tk.Frame(input_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        tk.Button(btn_frame, text="Add", width=10, command=self.add_employee).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(btn_frame, text="Update", width=10, command=self.update_employee).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(btn_frame, text="Delete", width=10, command=self.delete_employee).grid(row=1, column=0, padx=5, pady=5)
        tk.Button(btn_frame, text="Clear", width=10, command=self.clear_fields).grid(row=1, column=1, padx=5, pady=5)
        
        tk.Button(btn_frame, text="Calculate Final Pay", bg="#e0f7fa", command=self.calculate_pay).grid(row=2, column=0, columnspan=2, sticky="we", padx=5, pady=10)

        # --- Data Display Frame ---
        display_frame = tk.Frame(self.root, padx=20, pady=20)
        display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Search Bar
        search_frame = tk.Frame(display_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(search_frame, text="Search by Name:").pack(side=tk.LEFT)
        tk.Entry(search_frame, textvariable=self.search_var).pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)
        tk.Button(search_frame, text="Search", command=self.search_employee).pack(side=tk.LEFT)
        tk.Button(search_frame, text="Reset", command=self.reset_search).pack(side=tk.LEFT, padx=5)

        # Treeview (Table)
        all_columns = ("No.", "ID", "Name", "Attendance", "Salary", "Final Pay")
        visible_columns = ("No.", "Name", "Attendance", "Salary", "Final Pay")
        
        self.tree = ttk.Treeview(display_frame, columns=all_columns, show="headings", displaycolumns=visible_columns)
        
        for col in visible_columns:
            self.tree.heading(col, text=col)
            width = 50 if col == "No." else (80 if col == "Attendance" else 120)
            self.tree.column(col, width=width, anchor="center")
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<ButtonRelease-1>", self.get_selected_row)

    # --- NEW: Validation Helper ---
    def validate_inputs(self):
        """Checks if all inputs are valid before saving or calculating."""
        if not self.name_var.get() or not self.salary_var.get() or not self.attendance_var.get():
            messagebox.showerror("Error", "All fields are required!")
            return False
            
        try:
            attendance = float(self.attendance_var.get())
            salary = float(self.salary_var.get())
            
            # The exact rule you asked for:
            if attendance < 0 or attendance > self.WORKING_DAYS:
                messagebox.showerror("Error", f"Days attended must be between 0 and {int(self.WORKING_DAYS)}!")
                return False
                
            if salary < 0:
                messagebox.showerror("Error", "Salary cannot be negative!")
                return False
                
            return True # Everything is perfect
            
        except ValueError:
            messagebox.showerror("Error", "Attendance/Salary must be numbers!")
            return False

    # --- Feature Methods ---
    def calculate_pay(self):
        if not self.validate_inputs(): # Check rules first
            return
            
        attendance = float(self.attendance_var.get())
        salary = float(self.salary_var.get())
        
        # Uses the constant variable now
        final_pay = (salary / self.WORKING_DAYS) * attendance
        
        breakdown = (
            f"Employee: {self.name_var.get()}\n"
            f"Base Salary: ${salary:,.2f}\n"
            f"Days Attended: {attendance} out of {int(self.WORKING_DAYS)}\n"
            f"-----------------------------------\n"
            f"Calculated Final Pay: ${final_pay:,.2f}"
        )
        messagebox.showinfo("Payroll Details", breakdown)

    def reset_search(self):
        self.search_var.set("")
        self.populate_treeview()

    # --- Database Interface Methods ---
    def populate_treeview(self, rows=None):
        self.tree.delete(*self.tree.get_children())
        if rows is None:
            rows = db.fetch_all()
            
        # enumerate(rows, start=1) automatically counts 1, 2, 3...
        for index, row in enumerate(rows, start=1):
            try:
                db_id = row[0]     # The real hidden Database ID
                name = row[1]
                attendance = float(row[2])
                salary = float(row[3])
                final_pay = round((salary / self.WORKING_DAYS) * attendance, 2)
                
                # We package everything into the all_columns format
                display_row = (index, db_id, name, attendance, salary, final_pay)
                self.tree.insert("", tk.END, values=display_row)
            except (ValueError, TypeError):
                pass

    def add_employee(self):
        if not self.validate_inputs(): # Check rules first
            return
            
        db.insert(self.name_var.get(), self.attendance_var.get(), self.salary_var.get())
        self.populate_treeview()
        self.clear_fields()

    def get_selected_row(self, event):
        selected = self.tree.focus()
        if not selected:
            return
        values = self.tree.item(selected, 'values')
        
        # values format is now: (No., ID, Name, Attendance, Salary, Final Pay)
        self.id_var.set(values[1])         # Hidden Database ID
        self.name_var.set(values[2])       # Name
        self.attendance_var.set(values[3]) # Attendance
        self.salary_var.set(values[4])     # Salary

    def update_employee(self):
        if not self.id_var.get():
            messagebox.showerror("Error", "Select an employee to update!")
            return
            
        if not self.validate_inputs(): # Check rules first
            return
            
        db.update(self.id_var.get(), self.name_var.get(), self.attendance_var.get(), self.salary_var.get())
        self.populate_treeview()
        self.clear_fields()

    def delete_employee(self):
        if not self.id_var.get():
            messagebox.showerror("Error", "Select an employee to delete!")
            return
        db.delete(self.id_var.get())
        self.populate_treeview()
        self.clear_fields()

    def search_employee(self):
        rows = db.search(self.search_var.get())
        self.populate_treeview(rows)

    def clear_fields(self):
        self.id_var.set("")
        self.name_var.set("")
        self.attendance_var.set("")
        self.salary_var.set("")

if __name__ == "__main__":
    root = tk.Tk()
    app = EmployeeTracker(root)
    root.mainloop()