import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re
import os
import time
import logging
import json
import hashlib
from datetime import datetime
from pathlib import Path
from .utils import (export_to_csv, create_backup, validate_job_data, 
                   get_job_statistics)

# Initialize logging
logging.basicConfig(filename="error_log.txt", level=logging.ERROR, 
                    format="%(asctime)s - %(levelname)s - %(message)s")

# Get the user's home directory for storing application data
APP_DIR = Path.home() / ".tintelligent"
APP_DIR.mkdir(exist_ok=True)

BACKUP_DIR = APP_DIR / "backups"
CONFIG_FILE = APP_DIR / "config.json"
ADMIN_PASSWORD = hashlib.sha256("Chronya82!".encode()).hexdigest()

class SearchFrame(ttk.Frame):
    def __init__(self, parent, database_path, **kwargs):
        super().__init__(parent, **kwargs)
        self.database_path = database_path
        
        # Search inputs
        self.search_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.search_var).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(self, text="Search", 
                  command=self.search).pack(side=tk.LEFT, padx=5)
        
        # Filter options
        self.filter_var = tk.StringVar(value="all")
        ttk.Radiobutton(self, text="All", value="all", 
                       variable=self.filter_var).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(self, text="Last 30 days", value="recent", 
                       variable=self.filter_var).pack(side=tk.LEFT, padx=5)
    
    def search(self):
        # Implementation of search functionality
        search_term = self.search_var.get()
        filter_value = self.filter_var.get()
        
        # Update results in parent dashboard
        if hasattr(self.master, 'update_jobs_display'):
            self.master.update_jobs_display(search_term, filter_value)

def show_dashboard(database_path):
    dashboard_window = tk.Toplevel()
    dashboard_window.title("Job Statistics Dashboard")
    dashboard_window.geometry("800x600")

    # Create frames
    search_frame = SearchFrame(dashboard_window, database_path)
    search_frame.pack(fill=tk.X, padx=10, pady=5)

    stats_frame = ttk.LabelFrame(dashboard_window, text="Statistics")
    stats_frame.pack(fill=tk.X, padx=10, pady=5)

    # Display statistics
    stats = get_job_statistics(database_path)
    
    ttk.Label(stats_frame, 
              text=f"Total Jobs: {stats['total_jobs']}").pack(pady=2)
    ttk.Label(stats_frame, 
              text=f"Jobs (Last 30 Days): {stats['recent_jobs']}").pack(pady=2)
    ttk.Label(stats_frame, 
              text=f"Total Paint Mixed: {stats['total_paint']} units").pack(pady=2)

    # Export button
    def export_data():
        output_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if output_path:
            if export_to_csv(database_path, output_path):
                messagebox.showinfo("Success", "Data exported successfully!")
            else:
                messagebox.showerror("Error", "Failed to export data")

    ttk.Button(dashboard_window, text="Export to CSV", 
               command=export_data).pack(pady=5)

    # Jobs table
    tree = ttk.Treeview(dashboard_window, 
                        columns=("Job #", "Manufacturer", "Paint Code", 
                                "Amount", "Date"),
                        show="headings")
    
    # Define headings and column widths
    for col in tree["columns"]:
        tree.heading(col, text=col)
        tree.column(col, width=100)

    # Add scrollbar
    scrollbar = ttk.Scrollbar(dashboard_window, orient="vertical", 
                             command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    # Pack the table and scrollbar
    tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

def create_job(database_path):
    def save_job():
        # Get form data
        job_data = {
            'job_number': job_number_entry.get(),
            'manufacturer': manufacturer_entry.get(),
            'paint_code': paint_code_entry.get(),
            'color_name': color_name_entry.get(),
            'mixed_amount': mixed_amount_entry.get()
        }
        
        # Validate input
        valid, message = validate_job_data(job_data)
        if not valid:
            messagebox.showerror("Invalid Input", message)
            return
        
        try:
            conn = sqlite3.connect(database_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO jobs (
                    job_number, manufacturer, paint_code, 
                    color_name, mixed_amount, created_at
                ) VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (
                job_data['job_number'],
                job_data['manufacturer'],
                job_data['paint_code'],
                job_data['color_name'],
                float(job_data['mixed_amount'])
            ))
            
            conn.commit()
            conn.close()
            
            # Create backup after successful job creation
            create_backup(database_path, BACKUP_DIR)
            
            messagebox.showinfo("Success", "Job created successfully!")
            job_window.destroy()
            
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Job number already exists")
        except Exception as e:
            logging.error(f"Failed to save job: {e}")
            messagebox.showerror("Error", "Failed to save job")

    job_window = tk.Toplevel()
    job_window.title("Create Job")
    job_window.geometry("400x500")

    # Create form fields
    ttk.Label(job_window, text="Job Number:").pack(pady=5)
    job_number_entry = ttk.Entry(job_window)
    job_number_entry.pack(pady=5)

    ttk.Label(job_window, text="Manufacturer:").pack(pady=5)
    manufacturer_entry = ttk.Entry(job_window)
    manufacturer_entry.pack(pady=5)
    manufacturer_entry.insert(0, "Matthews Paint")

    ttk.Label(job_window, text="Paint Code:").pack(pady=5)
    paint_code_entry = ttk.Entry(job_window)
    paint_code_entry.pack(pady=5)

    ttk.Label(job_window, text="Color Name:").pack(pady=5)
    color_name_entry = ttk.Entry(job_window)
    color_name_entry.pack(pady=5)

    ttk.Label(job_window, text="Amount to Mix:").pack(pady=5)
    mixed_amount_entry = ttk.Entry(job_window)
    mixed_amount_entry.pack(pady=5)

    ttk.Button(job_window, text="Save Job", 
               command=save_job).pack(pady=20)

def main():
    config = load_config()

    if not config or not os.path.exists(config.get("database_path", "")):
        messagebox.showinfo("Setup", "Please select a database location.")
        database_path = select_database()
        if not database_path:
            messagebox.showerror("Error", "No database selected. Exiting.")
            return
        save_config(database_path)
        show_legal_notice()
    elif not config.get("legal_notice_accepted", False):
        show_legal_notice()

    database_path = config["database_path"]
    
    # Create backup directory
    BACKUP_DIR.mkdir(exist_ok=True)
    
    # Initialize the main window
    root = tk.Tk()
    root.title("Tintelligent")
    root.geometry("400x300")
    
    # Set window icon
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)
    
    # Create a main frame with padding
    main_frame = ttk.Frame(root, padding="20")
    main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    # Configure grid weights
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    main_frame.columnconfigure(0, weight=1)

    # Buttons
    style = ttk.Style()
    style.configure("Action.TButton", padding=10)

    ttk.Button(main_frame,
               text="Create Job", 
               command=lambda: create_job(database_path),
               style="Action.TButton").grid(row=0, column=0, pady=10, 
                                          sticky=(tk.W, tk.E))
    
    ttk.Button(main_frame, 
               text="Show Dashboard", 
               command=lambda: show_dashboard(database_path),
               style="Action.TButton").grid(row=1, column=0, pady=10, 
                                          sticky=(tk.W, tk.E))
    
    ttk.Button(main_frame, 
               text="Administrator Mode", 
               command=lambda: admin_mode(database_path),
               style="Action.TButton").grid(row=2, column=0, pady=10, 
                                          sticky=(tk.W, tk.E))

    # Create initial backup
    create_backup(database_path, BACKUP_DIR)

    root.mainloop()

if __name__ == "__main__":
    main()