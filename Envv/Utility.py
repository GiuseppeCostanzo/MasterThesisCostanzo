# This Utility.py contains various classes and functions to support the GUI

from tkinter import ttk
import tkinter as tk

class Table(tk.Frame):
    def __init__(self, master, headers, data):
        super().__init__(master)
        self.headers = headers
        self.data = data
        self.create_table()

    def create_table(self):
        self.tree = ttk.Treeview(self, columns=self.headers, show="headings")

        # Aggiunta header
        for header in self.headers:
            self.tree.heading(header, text=header, anchor="center")
            self.tree.column(header, width=80)

        for row in self.data:
            self.tree.insert("", "end", values=row)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(expand=True, fill="both")