# gui.py
import tkinter as tk
from tkinter import ttk, messagebox
from database import Database
import logic # Import our new logic file

class EmployeeTrackerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Employee Payroll & Attendance Tracker")
        self.root.geometry("850x550")
        
        self.db = Database()
        
        # GUI Variables
        self.id_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.attendance_var = tk.StringVar()
        self.salary_var = tk.StringVar()
        self.search_var = tk.StringVar()

        self.setup_ui()
        self.populate_treeview()

    def setup_ui(self):
        # --- Input Frame ---
        input_frame = tk.Frame(self.root, padx=20, pady=20)
        input_frame.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(input_frame, text="Name:").grid(row=0, column=0, pady=10, sticky="w")
        tk.Entry(input_frame, textvariable=self.name_var).grid(row=0, column=1)

        tk.Label(input_frame, text=f"Days Attended (Max {int(logic.WORKING_DAYS)}):").grid(row=1, column=0, pady=10, sticky="w")
        tk.Entry(input_frame, textvariable=self.attendance_var).grid(row=1, column=1)

        tk.Label(input_frame, text="Base Salary (VND):").grid(row=2, column=0, pady=10, sticky="w")
        tk.Entry(input_frame, textvariable=self.salary_var).grid(row=2, column=1)

        # Buttons
        btn_frame = tk.Frame(input_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        tk.Button(btn_frame, text="Add", width=10, command=self.add_employee).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(btn_frame, text="Update", width=10, command=self.update_employee).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(btn_frame, text="Delete", width=10, command=self.delete_employee).grid(row=1, column=0, padx=5, pady=5)
        tk.Button(btn_frame, text="Clear", width=10, command=self.clear_fields).grid(row=1, column=1, padx=5, pady=5)
        
        tk.Button(btn_frame, text="Calculate Final Pay", bg="#e0f7fa", command=self.show_pay_breakdown).grid(row=2, column=0, columnspan=2, sticky="we", padx=5, pady=10)

        # --- Data Display Frame ---
        display_frame = tk.Frame(self.root, padx=20, pady=20)
        display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Search Bar
        search_frame = tk.Frame(display_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(search_frame, text="Search by Name:").pack(side=tk.LEFT)
        search_entry = tk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)

        # Bind the "Enter" key on the keyboard to trigger the search
        search_entry.bind("<Return>", self.search_employee)
        # Trace the search variable to update live "as you type"
        self.search_var.trace_add("write", self.search_employee)
        tk.Button(search_frame, text="Search", command=self.search_employee).pack(side=tk.LEFT)
        tk.Button(search_frame, text="Reset", command=self.reset_search).pack(side=tk.LEFT, padx=5)

        # Treeview (Table)
        all_columns = ("No.", "ID", "Name", "Attendance", "Salary (VND)", "Final Pay (VND)")
        visible_columns = ("No.", "Name", "Attendance", "Salary (VND)", "Final Pay (VND)")
        
        self.tree = ttk.Treeview(display_frame, columns=all_columns, show="headings", displaycolumns=visible_columns)
        
        for col in visible_columns:
            self.tree.heading(col, text=col)
            width = 50 if col == "No." else (80 if col == "Attendance" else 120)
            self.tree.column(col, width=width, anchor="center")
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<ButtonRelease-1>", self.get_selected_row)

    # --- UI Actions ---
    def populate_treeview(self, rows=None):
        self.tree.delete(*self.tree.get_children())
        if rows is None:
            rows = self.db.fetch_all()
            
        for index, row in enumerate(rows, start=1):
            db_id, name, attendance, salary = row
            # Use logic.py to calculate pay
            final_pay = logic.calculate_final_pay(salary, attendance)
            self.tree.insert("", tk.END, values=(index, db_id, name, attendance, salary, final_pay))

    def add_employee(self):
        is_valid, error_msg, att, sal = logic.validate_employee_data(self.name_var.get(), self.attendance_var.get(), self.salary_var.get())
        if not is_valid:
            messagebox.showerror("Error", error_msg)
            return
            
        self.db.insert(self.name_var.get(), att, sal)
        self.populate_treeview()
        self.clear_fields()
        messagebox.showinfo("Success", "Employee added successfully!")

    def get_selected_row(self, event):
        selected = self.tree.focus()
        if not selected:
            return
        values = self.tree.item(selected, 'values')
        self.id_var.set(values[1])
        self.name_var.set(values[2])
        self.attendance_var.set(values[3])
        self.salary_var.set(values[4])

    def update_employee(self):
        if not self.id_var.get():
            messagebox.showerror("Error", "Select an employee to update!")
            return
            
        is_valid, error_msg, att, sal = logic.validate_employee_data(self.name_var.get(), self.attendance_var.get(), self.salary_var.get())
        if not is_valid:
            messagebox.showerror("Error", error_msg)
            return
            
        self.db.update(self.id_var.get(), self.name_var.get(), att, sal)
        self.populate_treeview()
        self.clear_fields()
        messagebox.showinfo("Success", "Employee updated successfully!")

    def delete_employee(self):
        if not self.id_var.get():
            messagebox.showerror("Error", "Select an employee to delete!")
            return
        self.db.delete(self.id_var.get())
        self.populate_treeview()
        self.clear_fields()
        messagebox.showinfo("Success", "Employee updated successfully!")

    def search_employee(self,*args):
        rows = self.db.search(self.search_var.get())
        self.populate_treeview(rows)

    def reset_search(self):
        self.search_var.set("")
        self.populate_treeview()

    def clear_fields(self):
        self.id_var.set("")
        self.name_var.set("")
        self.attendance_var.set("")
        self.salary_var.set("")

    def show_pay_breakdown(self):
        is_valid, error_msg, att, sal = logic.validate_employee_data(self.name_var.get(), self.attendance_var.get(), self.salary_var.get())
        if not is_valid:
            messagebox.showerror("Error", "Please select a valid employee to calculate pay.")
            return
            
        final_pay = logic.calculate_final_pay(sal, att)
        
        breakdown = (
            f"Employee: {self.name_var.get()}\n"
            f"Base Salary: ${sal:,.0f}\n"
            f"Days Attended: {att} out of {int(logic.WORKING_DAYS)}\n"
            f"-----------------------------------\n"
            f"Calculated Final Pay: ${final_pay:,.0f}"
        )
        messagebox.showinfo("Payroll Details", breakdown)