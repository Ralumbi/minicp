import tkinter as tk
from tkinter import ttk

class OverviewFrame(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        tk.Label(self, text="Device Status", font=(None,12,"bold")).pack(pady=5)
        self.container = tk.Frame(self)
        self.container.pack(fill=tk.BOTH, expand=True)
        self.update_status()

    def update_status(self):
        for w in self.container.winfo_children(): w.destroy()

        # Wi‑Fi
        tk.Label(self.container, text="Wi‑Fi Devices", font=(None,10,"bold")).pack(pady=3)
        status = self.app.wifi_mgr.get_status()
        for ifname, info in status.items():
            frame = tk.Frame(self.container)
            frame.pack(fill=tk.X, pady=1)
            tk.Label(frame, text=f"{ifname}: {info['role']}").pack(side=tk.LEFT)
            if info['role']=='client':
                tk.Label(frame, text=f"Connected to {info['ssid']}").pack(side=tk.LEFT, padx=5)
                tk.Button(frame, text="Disconnect",
                          command=lambda i=ifname: self.app.wifi_mgr.disconnect(i)
                ).pack(side=tk.RIGHT)
            elif info['role']=='ap':
                tk.Label(frame, text=f"AP SSID: {info['ssid']}").pack(side=tk.LEFT, padx=5)
                tk.Button(frame, text="Stop AP",
                          command=lambda i=ifname: self.app.router_mgr.stop_ap(i)
                ).pack(side=tk.RIGHT)

        # Bluetooth
        tk.Label(self.container, text="Bluetooth Devices", font=(None,10,"bold")).pack(pady=3)
        paired = self.app.bt_mgr.get_paired()
        for mac,name in paired:
            connected = self.app.bt_mgr.is_connected(mac)
            tk.Label(self.container, text=f"{name} ({mac}): {'✔' if connected else '✘'}").pack()

        self.after(5000, self.update_status)
