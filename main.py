# main.py
import tkinter as tk
from gui import EmployeeTrackerUI

if __name__ == "__main__":
    root = tk.Tk()
    app = EmployeeTrackerUI(root)
    root.mainloop()