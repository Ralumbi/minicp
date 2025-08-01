import tkinter as tk
from tkinter import messagebox
import subprocess

class BluetoothManagerFrame(tk.Frame):
    """
    Launches the system's Blueman manager for full-fledged Bluetooth control.
    """
    def __init__(self, master, app):
        super().__init__(master)
        self.build_ui()

    def build_ui(self):
        tk.Label(self, text="Bluetooth", font=(None,12,"bold")).pack(pady=10)
        tk.Button(
            self,
            text="Open Bluetooth Manager",
            command=self.open_blueman,
            width=25,
            height=2
        ).pack(pady=20)
        tk.Label(
            self,
            text="Use the system Blueman GUI to scan, pair, and connect devices.",
            wraplength=300,
            justify="center"
        ).pack(padx=10)

    def open_blueman(self):
        try:
            subprocess.Popen(["blueman-manager"])
        except FileNotFoundError:
            messagebox.showerror(
                "Blueman Not Found",
                "blueman-manager not installed. Please install Blueman:\n\n"
                "    sudo apt update\n"
                "    sudo apt install blueman\n"
            )
