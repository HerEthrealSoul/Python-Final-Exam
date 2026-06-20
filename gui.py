#gui.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.font as tkfont
import csv
from database import Database
import logic
import cv2
from PIL import Image, ImageTk
from fpdf import FPDF
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import datetime

class EmployeeTrackerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Employee Payroll & Attendance Tracker")
        self.root.geometry("950x600")
        self.root.geometry("1050x650")
        self.root.configure(bg="#F0F2F5")

        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        self.style.configure("Treeview", 
                             background="#FFFFFF",
                             foreground="#333333",
                             rowheight=35,
                             fieldbackground="#FFFFFF",
                             font=("Segoe UI", 10))                             
        
        self.style.configure("Treeview.Heading", 
                             font=("Segoe UI", 10, "bold"), 
                             background="#E2E8F0", 
                             foreground="#1E293B",
                             relief="flat")
                             
        self.style.map("Treeview", background=[("selected", "#E1EFFE")], foreground=[("selected", "#1E40AF")])
        
        self.db = Database()
        
        self.id_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.role_var = tk.StringVar() 
        self.attendance_var = tk.StringVar()
        self.salary_var = tk.StringVar()
        self.overtime_var = tk.StringVar(value="0")
        
        self.search_var = tk.StringVar()
        self.filter_var = tk.StringVar() 

        self.setup_ui()
        self.populate_treeview()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        input_frame = tk.LabelFrame(self.root, text=" 📝 Employee Details ", padx=20, pady=20, font=("Arial", 10, "bold"), fg="#333")
        input_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(20, 10), pady=20)
        input_frame.columnconfigure(1, weight=1)

        tk.Label(input_frame, text="Name:").grid(row=0, column=0, pady=10, padx=(0, 10), sticky="w")
        ttk.Entry(input_frame, textvariable=self.name_var).grid(row=0, column=1, sticky="we")
        
        tk.Label(input_frame, text="Department/Role:").grid(row=1, column=0, pady=10, padx=(0, 10), sticky="w")
        role_combo = ttk.Combobox(input_frame, textvariable=self.role_var, values=logic.ROLES, state="readonly")
        role_combo.grid(row=1, column=1, sticky="we")
        self.role_var.trace_add("write", self.auto_fill_attendance)

        tk.Label(input_frame, text=f"Days Attended (Max {int(logic.WORKING_DAYS)}):").grid(row=2, column=0, pady=10, padx=(0, 10), sticky="w")
        ttk.Entry(input_frame, textvariable=self.attendance_var).grid(row=2, column=1, sticky="we")

        tk.Label(input_frame, text="Base Salary (VND/month):").grid(row=3, column=0, pady=10, padx=(0, 10), sticky="w")
        ttk.Entry(input_frame, textvariable=self.salary_var).grid(row=3, column=1, sticky="we")

        tk.Label(input_frame, text="Overtime (Hours):").grid(row=4, column=0, pady=10, padx=(0, 10), sticky="w")
        ttk.Entry(input_frame, textvariable=self.overtime_var).grid(row=4, column=1, sticky="we")

        btn_frame = tk.Frame(input_frame, bg=input_frame.cget("bg")) 
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        def create_btn(parent, text, bg_color, fg_color, cmd, row, col, width=12, colspan=1):
            tk.Button(parent, text=text, bg=bg_color, fg=fg_color, command=cmd, width=width,
                      font=("Segoe UI", 9, "bold"), relief="solid", borderwidth=1, 
                      cursor="hand2", pady=5).grid(row=row, column=col, columnspan=colspan, padx=5, pady=5, sticky="we")

        create_btn(btn_frame, "Add", "#0284C7", "white", self.add_employee, 0, 0)       
        create_btn(btn_frame, "Update", "#D97706", "white", self.update_employee, 0, 1) 
        create_btn(btn_frame, "Delete", "#DC2626", "white", self.delete_employee, 1, 0) 
        create_btn(btn_frame, "Clear", "#475569", "white", self.clear_fields, 1, 1)     

        create_btn(btn_frame, "Export PDF", "#FEF2F2", "#991B1B", self.generate_pdf_payslip, 2, 0) 
        create_btn(btn_frame, "Export Excel", "#F0FDF4", "#166534", self.export_to_excel, 2, 1) 
        
        create_btn(btn_frame, "📸 Scanner", "#EFF6FF", "#1E3A8A", self.open_attendance_window, 3, 0, colspan=2)

        stats_frame = tk.LabelFrame(input_frame, text=" 📊 Quick Statistics ", padx=15, pady=15, font=("Segoe UI", 10, "bold"), fg="#1e293b", bg="white")
        stats_frame.grid(row=6, column=0, columnspan=2, sticky="we", pady=10)

        self.stat_emp_var = tk.StringVar(value="Total Employees: 0")
        self.stat_att_var = tk.StringVar(value="Avg Attendance: 0.0 days")
        self.stat_pay_var = tk.StringVar(value="Total Payroll: 0 ₫")

        tk.Label(stats_frame, textvariable=self.stat_emp_var, font=("Segoe UI", 10), bg="white").pack(anchor="w", pady=2)
        tk.Label(stats_frame, textvariable=self.stat_att_var, font=("Segoe UI", 10), bg="white").pack(anchor="w", pady=2)
        tk.Label(stats_frame, textvariable=self.stat_pay_var, font=("Segoe UI", 11, "bold"), fg="#dc2626", bg="white").pack(anchor="w", pady=5)
        
        btn_container = tk.Frame(stats_frame, bg="white")
        btn_container.pack(fill=tk.X, pady=(15, 0))
        
        tk.Button(btn_container, text="📊 Charts", command=self.show_charts, bg="#FFF7ED", fg="#C2410C", font=("Segoe UI", 9, "bold"), relief="solid", borderwidth=1, cursor="hand2", pady=4).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        tk.Button(btn_container, text="🏆 KPI", command=self.show_kpi_board, bg="#FAF5FF", fg="#7E22CE", font=("Segoe UI", 9, "bold"), relief="solid", borderwidth=1, cursor="hand2", pady=4).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        tk.Button(btn_container, text="📅 History", command=self.show_history_board, bg="#F8FAFC", fg="#334155", font=("Segoe UI", 9, "bold"), relief="solid", borderwidth=1, cursor="hand2", pady=4).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        display_frame = tk.Frame(self.root, padx=10, pady=20)
        display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        search_container = tk.Frame(display_frame)
        search_container.pack(fill=tk.X, pady=(0, 15))
        
        search_frame = tk.Frame(search_container)
        search_frame.pack(anchor="center") 
        
        tk.Label(search_frame, text="Search Name:").pack(side=tk.LEFT)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind("<Return>", self.apply_filters)
        search_entry.bind("<KeyRelease>", self.apply_filters)
        
        tk.Label(search_frame, text="Filter Role:").pack(side=tk.LEFT, padx=(15, 0))
        filter_combo = ttk.Combobox(search_frame, textvariable=self.filter_var, values=["All"] + logic.ROLES, state="readonly", width=12)
        filter_combo.pack(side=tk.LEFT, padx=5)
        filter_combo.current(0) 
        filter_combo.bind("<<ComboboxSelected>>", self.apply_filters)

        tk.Button(search_frame, text="Reset", command=self.reset_search, width=8).pack(side=tk.LEFT, padx=5)

        tree_frame = tk.Frame(display_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        all_columns = ("No.", "ID", "Name", "Role", "Attendance", "Salary (VND)", "Final Pay (VND)", "Status")
        visible_columns = ("No.", "Name", "Role", "Attendance", "Salary (VND)", "Final Pay (VND)", "Status")
        
        h_scroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        v_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        self.tree = ttk.Treeview(
            tree_frame, 
            columns=all_columns, 
            show="headings", 
            displaycolumns=visible_columns,
            xscrollcommand=h_scroll.set,
            yscrollcommand=v_scroll.set
        )
        
        h_scroll.config(command=self.tree.xview)
        v_scroll.config(command=self.tree.yview)

        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        for col in visible_columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c, False))
            width = 40 if col == "No." else (70 if col == "Attendance" else (90 if col == "Role" else 110))
            self.tree.column(col, width=width, anchor="center")
        
        self.tree.bind("<ButtonRelease-1>", self.get_selected_row)
        self.tree.bind("<Double-1>", self.auto_resize_column)

    def populate_treeview(self, rows=None):
        self.tree.delete(*self.tree.get_children())
        if rows is None:
            rows = self.db.fetch_all()
            
        # Thêm tag màu xen kẽ
        self.tree.tag_configure('oddrow', background="#F8FAFC")
        self.tree.tag_configure('evenrow', background="#FFFFFF")

        for index, row in enumerate(rows, start=1):
            db_id, name, role, attendance, salary, last_date, last_time, status, on_time, late, ot = row
            final_pay = logic.calculate_final_pay(salary, attendance, role, ot)
            
            fmt_salary = logic.format_number(salary)
            fmt_final_pay = logic.format_number(final_pay)
            
            # Kiểm tra chẵn lẻ để gắn tag màu
            tags = ('evenrow',) if index % 2 == 0 else ('oddrow',)
            
            self.tree.insert("", tk.END, values=(index, db_id, name, role, attendance, fmt_salary, fmt_final_pay, status), tags=tags)
            
        self.update_statistics()

    def add_employee(self):
        is_valid, msg, att, sal, ot = logic.validate_employee_data(self.name_var.get(), self.role_var.get(), self.attendance_var.get(), self.salary_var.get(), self.overtime_var.get())
        if is_valid:
            self.db.insert(self.name_var.get(), self.role_var.get(), att, sal, ot)
            self.populate_treeview()
            messagebox.showinfo("Success", "Employee added successfully!")

    def update_employee(self):
        is_valid, msg, att, sal, ot = logic.validate_employee_data(self.name_var.get(), self.role_var.get(), self.attendance_var.get(), self.salary_var.get(), self.overtime_var.get())
        if is_valid and self.id_var.get():
            self.db.update(self.id_var.get(), self.name_var.get(), self.role_var.get(), att, sal, ot)
            self.populate_treeview()
            messagebox.showinfo("Success", "Updated successfully!")

    def get_selected_row(self, event):
        selected = self.tree.focus()
        if not selected: return
        values = self.tree.item(selected, 'values')
        self.id_var.set(values[1])
        self.name_var.set(values[2])
        self.role_var.set(values[3])
        self.attendance_var.set(values[4])
        self.salary_var.set(values[5])
        
        for row in self.db.fetch_all():
            if str(row[0]) == values[1]:
                self.overtime_var.set(str(row[10]))

    def delete_employee(self):
        if not self.id_var.get():
            messagebox.showerror("Error", "Please select an employee to delete!")
            return
            
        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to permanently delete this employee?")
        if confirm:
            self.db.delete(self.id_var.get())
            self.populate_treeview()
            self.clear_fields()
            messagebox.showinfo("Success", "Employee deleted successfully!")

    def apply_filters(self, *args):
        """Lấy giá trị hiện tại của cả ô Search và ô Filter để lọc dữ liệu cùng lúc."""
        current_name = self.search_var.get()
        current_role = self.filter_var.get()
        
        rows = self.db.search_and_filter(current_name, current_role)
        self.populate_treeview(rows)

    def reset_search(self):
        self.search_var.set("")
        self.filter_var.set("All")
        self.populate_treeview()

    def clear_fields(self):
        self.id_var.set("")
        self.name_var.set("")
        self.role_var.set("")
        self.attendance_var.set("")
        self.salary_var.set("")
        self.overtime_var.set("0")

    def auto_fill_attendance(self, *args):
        """Tự động điền đủ ngày công cho chức vụ Manager."""
        if self.role_var.get() == "Manager":
            self.attendance_var.set(str(int(logic.WORKING_DAYS)))

    def show_pay_breakdown(self):
        is_valid, error_msg, att, sal = logic.validate_employee_data(self.name_var.get(), self.role_var.get(), self.attendance_var.get(), self.salary_var.get())
        if not is_valid:
            messagebox.showerror("Error", "Please select a valid employee to calculate pay.")
            return
            
        role = self.role_var.get()
        final_pay = logic.calculate_final_pay(sal, att, role)
        
        note = "(Manager Privilege: 100% Salary)" if role == "Manager" else f"({att}/{int(logic.WORKING_DAYS)} days)"
        
        breakdown = (
            f"Employee: {self.name_var.get()}\n"
            f"Role: {role}\n"
            f"Base Salary: {sal:,.0f} ₫\n"
            f"Days Attended: {note}\n"
            f"-----------------------------------\n"
            f"Calculated Final Pay: {final_pay:,.0f} ₫"
        )
        messagebox.showinfo("Payroll Details", breakdown)

    def export_to_excel(self):
        rows = self.tree.get_children()
        if not rows:
            messagebox.showwarning("Warning", "No data available in the table to export!")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files (Excel)", "*.csv"), ("All Files", "*.*")],
            title="Save Payroll Report As"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, mode="w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)
                
                headers = ["No.", "Full Name", "Department/Role", "Days Attended", "Base Salary (VND)", "Final Pay (VND)"]
                writer.writerow(headers)
                
                for row_id in rows:
                    row_values = self.tree.item(row_id, "values")
                    clean_row = [
                        row_values[0],  
                        row_values[2],  
                        row_values[3],  
                        row_values[4],  
                        f"{float(row_values[5].replace('.', '')):,.0f}", 
                        f"{float(row_values[6].replace('.', '')):,.0f}"  
                    ]
                    writer.writerow(clean_row)
                    
            messagebox.showinfo("Success", "Data successfully exported to Excel!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not export file: {str(e)}")
    
    def auto_resize_column(self, event):
        """Tính toán và cập nhật độ rộng cột dựa trên nội dung thực tế (bỏ qua cột ID bị ẩn)."""
        region = self.tree.identify_region(event.x, event.y)
        
        if region in ("separator", "heading"):
            col_id = self.tree.identify_column(event.x)
            display_col_index = int(col_id.replace('#', '')) - 1
            
            visible_columns = ("No.", "Name", "Role", "Attendance", "Salary (VND)", "Final Pay (VND)", "Status")
            all_columns = ("No.", "ID", "Name", "Role", "Attendance", "Salary (VND)", "Final Pay (VND)", "Status")
            
            if display_col_index >= len(visible_columns):
                return
                
            col_name = visible_columns[display_col_index]
            real_data_index = all_columns.index(col_name)
            
            font = tkfont.nametofont("TkDefaultFont")
            max_width = font.measure(col_name) + 20 
            
            for row in self.tree.get_children():
                row_values = self.tree.item(row, 'values')
                if row_values:
                    cell_text = str(row_values[real_data_index])
                    text_width = font.measure(cell_text) + 20
                    if text_width > max_width:
                        max_width = text_width

            self.tree.column(col_name, width=max_width, minwidth=max_width, stretch=False)
    
    def open_attendance_window(self):
        """Mở cửa sổ có tích hợp Camera quét mã QR trực tiếp."""
        self.scan_win = tk.Toplevel(self.root)
        self.scan_win.title("Webcam QR Scanner")
        self.scan_win.geometry("450x550")
        self.scan_win.resizable(False, False)
        self.scan_win.attributes("-topmost", True)
        
        self.scan_win.protocol("WM_DELETE_WINDOW", self.close_attendance_window)

        tk.Label(self.scan_win, text="PLEASE SCAN QR CODE", font=("Arial", 12, "bold"), fg="#1565c0").pack(pady=10)
        
        self.video_label = tk.Label(self.scan_win, bg="black", width=400, height=300)
        self.video_label.pack(pady=10)

        tk.Label(self.scan_win, text="Or enter ID manually:", font=("Arial", 10)).pack()
        self.qr_var = tk.StringVar()
        qr_entry = tk.Entry(self.scan_win, textvariable=self.qr_var, font=("Arial", 14), justify="center", width=10)
        qr_entry.pack(pady=5)
        qr_entry.bind("<Return>", lambda event: self.process_check_in(self.qr_var.get()))

        self.status_label = tk.Label(self.scan_win, text="Starting Camera...", font=("Arial", 10, "italic"), fg="gray")
        self.status_label.pack(pady=10)

        self.qr_detector = cv2.QRCodeDetector()
        self.cap = cv2.VideoCapture(0)
        self.update_camera()

    def update_camera(self):
        if not hasattr(self, 'cap') or not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if ret:
            frame = cv2.resize(frame, (400, 300))
            
            # Sử dụng AI của OpenCV để nhận diện và giải mã QR
            data, bbox, _ = self.qr_detector.detectAndDecode(frame)
            
            if data:
                if bbox is not None:
                    for i in range(len(bbox[0])):
                        pt1 = tuple(bbox[0][i].astype(int))
                        pt2 = tuple(bbox[0][(i+1) % len(bbox[0])].astype(int))
                        cv2.line(frame, pt1, pt2, (0, 255, 0), 3)
                
                cv_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(cv_img)
                self.photo = ImageTk.PhotoImage(image=pil_img)
                self.video_label.config(image=self.photo)

                self.process_check_in(data)
                return
            
            cv_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(cv_img)
            self.photo = ImageTk.PhotoImage(image=pil_img)
            self.video_label.config(image=self.photo)

        self.camera_loop = self.scan_win.after(15, self.update_camera)

    def process_check_in(self, raw_id):
        """Xử lý ID nhận được từ Camera hoặc nhập tay."""
        raw_id = str(raw_id).strip()
        print(f"\n---> [DEBUG] Camera scanned: '{raw_id}'")
        self.qr_var.set("") 

        if not raw_id:
            return

        try:
            emp_id = int(raw_id)
            success, message, status_type = self.db.check_in_employee(emp_id, logic.WORKING_DAYS)

            if success:
                if status_type == "Late":
                    self.status_label.config(text=message, fg="red")
                else:
                    self.status_label.config(text=message, fg="green")
                    
                self.populate_treeview() 
                
                self.scan_win.after_cancel(self.camera_loop)
                self.scan_win.after(1000, self.update_camera)
            else:
                self.status_label.config(text=f"Failed: {message}", fg="orange")
                self.scan_win.after_cancel(self.camera_loop)
                self.scan_win.after(1500, self.update_camera)

        except ValueError:
            self.status_label.config(text="Error: Invalid QR Code!", fg="red")

    def close_attendance_window(self):
        """Hàm dọn dẹp giải phóng bộ nhớ và tắt Webcam."""
        if hasattr(self, 'camera_loop'):
            self.scan_win.after_cancel(self.camera_loop)
            
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
            
        self.scan_win.destroy()

    def update_statistics(self):
        """Tính toán và cập nhật số liệu thống kê tổng quan."""
        rows = self.tree.get_children()
        total_emp = len(rows)
        
        if total_emp == 0:
            self.stat_emp_var.set("Total Employees: 0")
            self.stat_att_var.set("Avg Attendance: 0 days")
            self.stat_pay_var.set("Total Payroll: 0")
            return
            
        total_att = 0.0
        total_pay = 0.0
        
        for row in rows:
            values = self.tree.item(row, 'values')
            try:
                total_att += float(values[4])
                clean_pay = str(values[6]).replace(".", "")
                total_pay += float(clean_pay)
            except ValueError:
                pass
                
        avg_att = total_att / total_emp
        
        self.stat_emp_var.set(f"Total Employees: {total_emp}")
        self.stat_att_var.set(f"Avg Attendance: {avg_att:.1f} days")
        self.stat_pay_var.set(f"Total Payroll: {logic.format_number(total_pay)} ₫")

    def sort_by_column(self, col, reverse):
        """Sắp xếp dữ liệu Treeview khi click vào tiêu đề cột."""
        data_list = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
        
        try:
            data_list.sort(key=lambda t: float(t[0].replace('.', '')), reverse=reverse)
        except ValueError:
            data_list.sort(reverse=reverse)

        for index, (val, child) in enumerate(data_list):
            self.tree.move(child, '', index)

        self.tree.heading(col, command=lambda: self.sort_by_column(col, not reverse))

    def generate_pdf_payslip(self):
        """Tính năng tạo và in phiếu lương ra file PDF."""
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Warning", "Please select an employee from the table to generate a payslip!")
            return

        values = self.tree.item(selected, 'values')
        name = values[2]
        role = values[3]
        attendance = values[4]
        base_salary = values[5]
        final_pay = values[6]

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=f"Payslip_{name.replace(' ', '_')}.pdf",
            filetypes=[("PDF Files", "*.pdf")],
            title="Save Payslip As"
        )
        if not file_path:
            return

        try:
            pdf = FPDF()
            pdf.add_page()
            
            pdf.rect(10, 10, 190, 120)

            pdf.set_font("Arial", 'B', 18)
            pdf.cell(190, 15, txt="OFFICIAL PAYSLIP", ln=True, align='C')
            pdf.set_font("Arial", 'I', 10)
            pdf.cell(190, 5, txt="Employee Payroll & Attendance System", ln=True, align='C')
            pdf.ln(10)

            pdf.set_font("Arial", 'B', 12)
            
            data = [
                ("Employee Name:", name),
                ("Department/Role:", role),
                ("Days Attended:", f"{attendance} days"),
                ("Base Salary:", f"{base_salary} VND")
            ]
            
            for item in data:
                pdf.cell(60, 10, txt=item[0], border=0)
                pdf.set_font("Arial", '', 12)
                pdf.cell(100, 10, txt=item[1], border=0, ln=True)
                pdf.set_font("Arial", 'B', 12)

            pdf.line(20, 85, 190, 85)
            pdf.ln(10)

            pdf.set_font("Arial", 'B', 14)
            pdf.set_text_color(200, 0, 0)
            pdf.cell(60, 10, txt="FINAL PAY:", border=0)
            pdf.cell(100, 10, txt=f"{final_pay} VND", border=0, ln=True)

            pdf.output(file_path)
            messagebox.showinfo("Success", f"PDF Payslip generated successfully at:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF:\n{str(e)}")

    def show_charts(self):
        """Tính năng phân tích và vẽ biểu đồ Data Visualization."""
        rows = self.tree.get_children()
        if not rows:
            messagebox.showwarning("Warning", "No data available to generate charts!")
            return

        role_counts = {}
        role_payroll = {}

        for row in rows:
            values = self.tree.item(row, 'values')
            role = values[3]
            clean_pay = float(str(values[6]).replace(".", ""))

            role_counts[role] = role_counts.get(role, 0) + 1
            role_payroll[role] = role_payroll.get(role, 0.0) + clean_pay

        chart_win = tk.Toplevel(self.root)
        chart_win.title("Dashboard Analytics - Charts")
        chart_win.geometry("1000x500")

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))

        all_roles = list(role_counts.keys())
        color_palette = plt.cm.Set3.colors
        role_color_map = {role: color_palette[i % len(color_palette)] for i, role in enumerate(all_roles)}

        labels_pie = list(role_counts.keys())
        sizes_pie = list(role_counts.values())
        colors_pie = [role_color_map[role] for role in labels_pie] 

        ax1.pie(sizes_pie, labels=labels_pie, autopct='%1.1f%%', startangle=140, colors=colors_pie)
        ax1.set_title("Employee Distribution by Role", fontweight="bold")

        labels_bar = list(role_payroll.keys())
        sizes_bar = list(role_payroll.values())
        colors_bar = [role_color_map[role] for role in labels_bar] 

        bars = ax2.bar(labels_bar, sizes_bar, color=colors_bar) 
        ax2.set_title("Total Payroll by Role (VND)", fontweight="bold")
        ax2.tick_params(axis='x', rotation=30) 
        
        ax2.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x)).replace(",", ".")))

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=chart_win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def show_kpi_board(self):
        """Mở Bảng xếp hạng Kỷ luật (KPI & Performance)."""
        kpi_win = tk.Toplevel(self.root)
        kpi_win.title("🏆 Employee KPI & Performance Board")
        kpi_win.geometry("850x400")

        tk.Label(kpi_win, text="PUNCTUALITY & OVERTIME PERFORMANCE", font=("Arial", 14, "bold"), fg="#4a148c").pack(pady=15)

        columns = ("Name", "Role", "Total Scans", "On Time", "Late", "Punctuality Rate", "Overtime (Hrs)")
        kpi_tree = ttk.Treeview(kpi_win, columns=columns, show="headings", height=12)
        
        for col in columns:
            kpi_tree.heading(col, text=col)
            kpi_tree.column(col, width=110, anchor="center")
            
        kpi_tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        kpi_data = []
        for row in self.db.fetch_all():
            name = row[1]
            role = row[2]
            on_time = row[8]
            late = row[9]
            ot = row[10]
            total_scans = on_time + late
            
            if total_scans > 0:
                punctuality = (on_time / total_scans) * 100
                rate_str = f"{punctuality:.1f}%"
            else:
                punctuality = 0
                rate_str = "No Data"

            kpi_data.append((name, role, total_scans, on_time, late, rate_str, ot, punctuality))

        kpi_data.sort(key=lambda x: (x[7], x[6], x[2]), reverse=True)

        for data in kpi_data:
            kpi_tree.insert("", tk.END, values=data[:7])

    def show_history_board(self):
        """Mở cửa sổ xem Nhật ký điểm danh theo Tháng/Năm."""
        hist_win = tk.Toplevel(self.root)
        hist_win.title("📅 Monthly Attendance History")
        hist_win.geometry("700x500")

        top_frame = tk.Frame(hist_win, pady=15)
        top_frame.pack(fill=tk.X)

        tk.Label(top_frame, text="Select Month:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(20, 5))
        
        month_var = tk.StringVar()
        month_combo = ttk.Combobox(top_frame, textvariable=month_var, values=[f"{i:02d}" for i in range(1, 13)], state="readonly", width=5)
        month_combo.pack(side=tk.LEFT, padx=5)
        
        current_month = datetime.datetime.now().strftime("%m")
        month_combo.set(current_month)

        tk.Label(top_frame, text="Year:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(15, 5))
        
        year_var = tk.StringVar()
        year_combo = ttk.Combobox(top_frame, textvariable=year_var, values=["2024", "2025", "2026", "2027", "2028"], state="readonly", width=8)
        year_combo.pack(side=tk.LEFT, padx=5)
        
        current_year = datetime.datetime.now().strftime("%Y")
        year_combo.set(current_year)

        tree_frame = tk.Frame(hist_win, padx=20, pady=10)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("Name", "Role", "Date", "Time", "Status")
        hist_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            hist_tree.heading(col, text=col)
            width = 150 if col == "Name" else 100
            hist_tree.column(col, width=width, anchor="center")
            
        hist_tree.pack(fill=tk.BOTH, expand=True)
        
        def fetch_history():
            m = month_var.get()
            y = year_var.get()
                        
            hist_tree.delete(*hist_tree.get_children())
            
            logs = self.db.get_attendance_history(m, y)
            
            if not logs:
                messagebox.showinfo("Info", f"No attendance records found for {m}/{y}.", parent=hist_win)
                return
                
            for log in logs:
                hist_tree.insert("", tk.END, values=log)

        tk.Button(top_frame, text="🔍 Search Logs", command=fetch_history, bg="#1976d2", fg="white", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=20)
        
        fetch_history()

    def on_closing(self):
        """Hàm dọn dẹp toàn bộ tài nguyên phần cứng trước khi thoát app."""
        if hasattr(self, 'camera_loop'):
            try:
                self.scan_win.after_cancel(self.camera_loop)
            except Exception:
                pass
                
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
            

        if hasattr(self, 'db'):
            del self.db
            
        self.root.destroy()
        
        import sys
        sys.exit(0)