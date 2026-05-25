# gui.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.font as tkfont
import csv
from database import Database
import logic

import cv2
from PIL import Image, ImageTk

class EmployeeTrackerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Employee Payroll & Attendance Tracker")
        self.root.geometry("950x600") 
        
        self.db = Database()
        
        # GUI Variables
        self.id_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.role_var = tk.StringVar() 
        self.attendance_var = tk.StringVar()
        self.salary_var = tk.StringVar()
        
        self.search_var = tk.StringVar()
        self.filter_var = tk.StringVar() 

        self.setup_ui()
        self.populate_treeview()

    def setup_ui(self):
        # --- Input Frame ---
        input_frame = tk.Frame(self.root, padx=20, pady=20)
        input_frame.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(input_frame, text="Name:").grid(row=0, column=0, pady=10, sticky="w")
        tk.Entry(input_frame, textvariable=self.name_var).grid(row=0, column=1)
        
        # Role Dropdown
        tk.Label(input_frame, text="Department/Role:").grid(row=1, column=0, pady=10, sticky="w")
        role_combo = ttk.Combobox(input_frame, textvariable=self.role_var, values=logic.ROLES, state="readonly")
        role_combo.grid(row=1, column=1)

        self.role_var.trace_add("write", self.auto_fill_attendance)

        tk.Label(input_frame, text=f"Days Attended (Max {int(logic.WORKING_DAYS)}):").grid(row=2, column=0, pady=10, sticky="w")
        tk.Entry(input_frame, textvariable=self.attendance_var).grid(row=2, column=1)

        tk.Label(input_frame, text="Base Salary (VND):").grid(row=3, column=0, pady=10, sticky="w")
        tk.Entry(input_frame, textvariable=self.salary_var).grid(row=3, column=1)

        # Buttons
        btn_frame = tk.Frame(input_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        tk.Button(btn_frame, text="Add", width=10, command=self.add_employee).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(btn_frame, text="Update", width=10, command=self.update_employee).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(btn_frame, text="Delete", width=10, command=self.delete_employee).grid(row=1, column=0, padx=5, pady=5)
        tk.Button(btn_frame, text="Clear", width=10, command=self.clear_fields).grid(row=1, column=1, padx=5, pady=5)
        
        tk.Button(btn_frame, text="Calculate Final Pay", bg="#e0f7fa", command=self.show_pay_breakdown).grid(row=2, column=0, columnspan=2, sticky="we", padx=5, pady=10)

        # --- Data Display Frame ---
        display_frame = tk.Frame(self.root, padx=20, pady=20)
        display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Search & Filter Frame
        search_frame = tk.Frame(display_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(search_frame, text="Search Name:").pack(side=tk.LEFT)
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=15)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind("<Return>", self.apply_filters)
        search_entry.bind("<KeyRelease>", self.apply_filters)
        
        # Filter Dropdown
        tk.Label(search_frame, text="Filter Role:").pack(side=tk.LEFT, padx=(15, 0))
        filter_combo = ttk.Combobox(search_frame, textvariable=self.filter_var, values=["All"] + logic.ROLES, state="readonly", width=10)
        filter_combo.pack(side=tk.LEFT, padx=5)
        filter_combo.current(0) 
        filter_combo.bind("<<ComboboxSelected>>", self.apply_filters)

        tk.Button(search_frame, text="Reset", command=self.reset_search).pack(side=tk.LEFT, padx=5)
        tk.Button(search_frame, text="Export Excel", bg="#e8f5e9", fg="#2e7d32", command=self.export_to_excel).pack(side=tk.LEFT, padx=5)
        tk.Button(search_frame, text="Open Scanner", bg="#e3f2fd", fg="#0d47a1", command=self.open_attendance_window).pack(side=tk.LEFT, padx=5)

        # Treeview (Table)
        # Tạo một Frame phụ để chứa Table và Scrollbar cho gọn
        tree_frame = tk.Frame(display_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        all_columns = ("No.", "ID", "Name", "Role", "Attendance", "Salary (VND)", "Final Pay (VND)")
        visible_columns = ("No.", "Name", "Role", "Attendance", "Salary (VND)", "Final Pay (VND)")
        
        # Tạo thanh cuộn ngang và dọc
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
        
        # Cấu hình lệnh cuộn
        h_scroll.config(command=self.tree.xview)
        v_scroll.config(command=self.tree.yview)

        # 4. Sắp xếp vị trí các thành phần bằng giao diện Grid để khít nhau
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        # Đảm bảo bảng giãn nở đều trong frame phụ
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        for col in visible_columns:
            self.tree.heading(col, text=col)
            width = 40 if col == "No." else (70 if col == "Attendance" else (90 if col == "Role" else 110))
            self.tree.column(col, width=width, anchor="center")
        
        self.tree.bind("<ButtonRelease-1>", self.get_selected_row)
        self.tree.bind("<Double-1>", self.auto_resize_column)

    # --- UI Actions ---
    def populate_treeview(self, rows=None):
        self.tree.delete(*self.tree.get_children())
        if rows is None:
            rows = self.db.fetch_all()
            
        for index, row in enumerate(rows, start=1):
            db_id, name, role, attendance, salary, _ = row
            final_pay = logic.calculate_final_pay(salary, attendance, role)
            self.tree.insert("", tk.END, values=(index, db_id, name, role, attendance, salary, final_pay))

    def add_employee(self):
        is_valid, error_msg, att, sal = logic.validate_employee_data(self.name_var.get(), self.role_var.get(), self.attendance_var.get(), self.salary_var.get())
        if not is_valid:
            messagebox.showerror("Error", error_msg)
            return
            
        self.db.insert(self.name_var.get(), self.role_var.get(), att, sal)
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
        self.role_var.set(values[3])
        self.attendance_var.set(values[4])
        self.salary_var.set(values[5])

    def update_employee(self):
        if not self.id_var.get():
            messagebox.showerror("Error", "Please select an employee to update!")
            return
            
        is_valid, error_msg, att, sal = logic.validate_employee_data(self.name_var.get(), self.role_var.get(), self.attendance_var.get(), self.salary_var.get())
        if not is_valid:
            messagebox.showerror("Error", error_msg)
            return
            
        confirm = messagebox.askyesno("Confirm Update", f"Are you sure you want to update details for {self.name_var.get()}?")
        if confirm:
            self.db.update(self.id_var.get(), self.name_var.get(), self.role_var.get(), att, sal)
            self.populate_treeview()
            self.clear_fields()
            messagebox.showinfo("Success", "Employee updated successfully!")

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
        """Lấy giá trị hiện tại của cả ô Search và ô Filter để lọc dữ liệu cùng lúc"""
        current_name = self.search_var.get()
        current_role = self.filter_var.get()
        
        # Gọi hàm mới trong database
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

    def auto_fill_attendance(self, *args):
        """Auto-fill attendance for Managers"""
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
                        f"{float(row_values[5]):,.0f}", 
                        f"{float(row_values[6]):,.0f}"  
                    ]
                    writer.writerow(clean_row)
                    
            messagebox.showinfo("Success", "Data successfully exported to Excel!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not export file: {str(e)}")
    
    def auto_resize_column(self, event):
        """Tính năng nâng cao: Double click vào Tiêu đề hoặc Vạch chia để tự giãn cột"""
        region = self.tree.identify_region(event.x, event.y)
        
        if region in ("separator", "heading"):
            col_id = self.tree.identify_column(event.x)
            display_col_index = int(col_id.replace('#', '')) - 1
            
            # Cần cả 2 mảng để đối chiếu vị trí thực tế do ta đã ẩn cột ID
            visible_columns = ("No.", "Name", "Role", "Attendance", "Salary (VND)", "Final Pay (VND)")
            all_columns = ("No.", "ID", "Name", "Role", "Attendance", "Salary (VND)", "Final Pay (VND)")
            
            if display_col_index >= len(visible_columns):
                return
                
            # Tên cột đang được click
            col_name = visible_columns[display_col_index]
            # VỊ TRÍ THỰC SỰ của dữ liệu trong tuple
            real_data_index = all_columns.index(col_name)
            
            font = tkfont.nametofont("TkDefaultFont")
            max_width = font.measure(col_name) + 20 
            
            for row in self.tree.get_children():
                row_values = self.tree.item(row, 'values')
                if row_values:
                    # Lấy đúng dữ liệu dựa trên real_data_index
                    cell_text = str(row_values[real_data_index])
                    text_width = font.measure(cell_text) + 20
                    if text_width > max_width:
                        max_width = text_width

            self.tree.column(col_name, width=max_width, minwidth=max_width, stretch=False)
    
    def open_attendance_window(self):
        """Mở cửa sổ có tích hợp Camera quét mã QR trực tiếp (Dùng OpenCV nguyên bản)"""
        self.scan_win = tk.Toplevel(self.root)
        self.scan_win.title("Webcam QR Scanner")
        self.scan_win.geometry("450x550")
        self.scan_win.resizable(False, False)
        self.scan_win.attributes("-topmost", True)
        
        self.scan_win.protocol("WM_DELETE_WINDOW", self.close_attendance_window)

        tk.Label(self.scan_win, text="MỜI ĐƯA MÃ QR VÀO CAMERA", font=("Arial", 12, "bold"), fg="#1565c0").pack(pady=10)
        
        self.video_label = tk.Label(self.scan_win, bg="black", width=400, height=300)
        self.video_label.pack(pady=10)

        tk.Label(self.scan_win, text="Hoặc gõ ID thủ công rồi Enter:", font=("Arial", 10)).pack()
        self.qr_var = tk.StringVar()
        qr_entry = tk.Entry(self.scan_win, textvariable=self.qr_var, font=("Arial", 14), justify="center", width=10)
        qr_entry.pack(pady=5)
        qr_entry.bind("<Return>", lambda event: self.process_check_in(self.qr_var.get()))

        self.status_label = tk.Label(self.scan_win, text="Đang khởi động Camera...", font=("Arial", 10, "italic"), fg="gray")
        self.status_label.pack(pady=10)

        # Khởi tạo bộ đọc QR của chính OpenCV (Không cần pyzbar)
        self.qr_detector = cv2.QRCodeDetector()

        self.cap = cv2.VideoCapture(0)
        self.update_camera()

    def update_camera(self):
        """Hàm này sẽ chạy liên tục để lấy từng khung hình từ Webcam đưa lên giao diện"""
        if not hasattr(self, 'cap') or not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if ret:
            frame = cv2.resize(frame, (400, 300))
            
            # --- AI NHẬN DIỆN MÃ QR BẰNG OPENCV ---
            data, bbox, _ = self.qr_detector.detectAndDecode(frame)
            
            # Nếu tìm thấy mã QR (data có chứa dữ liệu)
            if data:
                # Vẽ khung xanh lá cây bao quanh mã QR
                if bbox is not None:
                    for i in range(len(bbox[0])):
                        pt1 = tuple(bbox[0][i].astype(int))
                        pt2 = tuple(bbox[0][(i+1) % len(bbox[0])].astype(int))
                        cv2.line(frame, pt1, pt2, (0, 255, 0), 3)
                
                # Ép Tkinter dán hình ảnh có khung xanh lên màn hình ngay lập tức!
                cv_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(cv_img)
                self.photo = ImageTk.PhotoImage(image=pil_img)
                self.video_label.config(image=self.photo)

                # Gửi ID đi điểm danh
                self.process_check_in(data)

                return
            
            # --- CHUYỂN ĐỔI HÌNH ẢNH SANG TKINTER ---
            cv_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(cv_img)
            self.photo = ImageTk.PhotoImage(image=pil_img)
            
            self.video_label.config(image=self.photo)

        self.camera_loop = self.scan_win.after(15, self.update_camera)

    def process_check_in(self, raw_id):
        """Xử lý ID nhận được (từ Camera hoặc từ bàn phím)"""
        raw_id = str(raw_id).strip()
        print(f"\n---> [DEBUG] Camera vừa quét được chữ: '{raw_id}'")
        self.qr_var.set("") 

        if not raw_id:
            return

        try:
            emp_id = int(raw_id)
            # Gọi hàm kiểm tra và điểm danh trong database.py
            success, message = self.db.check_in_employee(emp_id, logic.WORKING_DAYS)

            if success:
                self.status_label.config(text=message, fg="green")
                self.populate_treeview() # Làm mới bảng hiển thị chính
                
                self.scan_win.after_cancel(self.camera_loop)
                self.scan_win.after(2000, self.update_camera)
            else:
                self.status_label.config(text=f"Failed: {message}", fg="orange")
                # Nếu quét thất bại (ví dụ spam), dừng camera lại 2 giây để người dùng đọc thông báo lỗi
                self.scan_win.after_cancel(self.camera_loop)
                self.scan_win.after(2000, self.update_camera)

        except ValueError:
            self.status_label.config(text="Error: QR Code không phải là ID hợp lệ!", fg="red")

    def close_attendance_window(self):
        """Hàm dọn dẹp bộ nhớ: Cực kỳ quan trọng để tắt đèn Webcam trên Laptop"""
        if hasattr(self, 'camera_loop'):
            self.scan_win.after_cancel(self.camera_loop)
            
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release() # lệnh tắt cam
            
        self.scan_win.destroy()