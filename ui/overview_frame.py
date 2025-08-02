import tkinter as tk
from tkinter import ttk

class OverviewFrame(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        tk.Label(self, text="Device Status", font=("Arial", 14, "bold")).pack(pady=10)
        self.container = tk.Frame(self)
        self.container.pack(fill=tk.BOTH, expand=True)
        self.update_status()

    def update_status(self):
        for w in self.container.winfo_children():
            w.destroy()

        # Wi‑Fi
        tk.Label(self.container, text="Wi‑Fi Devices", font=("Arial", 12, "bold")).pack(pady=5)
        status = self.app.wifi_mgr.get_status()
        for ifname, info in status.items():
            frame = tk.Frame(self.container)
            frame.pack(fill=tk.X, pady=2)
            # Ensure info is a dict, not a string
            if isinstance(info, dict):
                tk.Label(frame, text=f"{ifname}: {info.get('role', 'unknown')}", font=("Arial", 12)).pack(side=tk.LEFT)
                if info.get('role') == 'client':
                    tk.Label(frame, text=f"Connected to {info.get('ssid', 'unknown')}", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
                    tk.Button(frame, text="Disconnect", command=lambda i=ifname: self.app.wifi_mgr.disconnect(i), font=("Arial", 12), width=10, height=2)\
                        .pack(side=tk.RIGHT)
                elif info.get('role') == 'ap':
                    tk.Label(frame, text=f"AP SSID: {info.get('ssid', 'unknown')}", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
                    tk.Button(frame, text="Stop AP", command=lambda i=ifname: self.app.router_mgr.stop_ap(i), font=("Arial", 12), width=10, height=2)\
                        .pack(side=tk.RIGHT)
            else:
                # fallback for string info
                tk.Label(frame, text=f"{ifname}: {info}", font=("Arial", 12)).pack(side=tk.LEFT)

        # Bluetooth
        tk.Label(self.container, text="Bluetooth Devices", font=("Arial", 12, "bold")).pack(pady=5)
        paired = self.app.bt_mgr.get_paired()
        for mac, name in paired:
            connected = self.app.bt_mgr.is_connected(mac)
            tk.Label(self.container, text=f"{name} ({mac}): {'✔' if connected else '✘'}", font=("Arial", 12)).pack()
