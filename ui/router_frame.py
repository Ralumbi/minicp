import tkinter as tk
from tkinter import messagebox, ttk
from ui.keyboard import KeyboardPopup

class RouterSetupFrame(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.keyboard_popup = None
        self.keyboard_lock = False
        self.build_ui()

    def build_ui(self):
        # AP status
        tk.Label(self, text="Access Point Status:", font=("Arial", 10)).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.status_lbl = tk.Label(self, text="Stopped", font=("Arial", 10))
        self.status_lbl.grid(row=0, column=1, columnspan=2, sticky="w", padx=5, pady=5)

        # Adapter selector
        tk.Label(self, text="Adapter:", font=("Arial", 10)).grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.iface_var = tk.StringVar()
        self.iface_cb = ttk.Combobox(self, textvariable=self.iface_var, state="readonly", font=("Arial", 10))
        self.iface_cb.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.iface_cb.bind("<<ComboboxSelected>>", lambda e: self.update_status())

        tk.Button(self, text="Refresh", command=self.refresh_ifaces, font=("Arial", 10), width=10, height=2)\
            .grid(row=1, column=2, sticky="ew", padx=5, pady=5)

        self.refresh_ifaces()

        # SSID & PSK
        tk.Label(self, text="SSID:", font=("Arial", 10)).grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.ssid_entry = tk.Entry(self, font=("Arial", 10))
        self.ssid_entry.grid(row=2, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        self.ssid_entry.bind('<FocusIn>', lambda e: self.open_keyboard(self.ssid_entry))

        tk.Label(self, text="Password:", font=("Arial", 10)).grid(row=3, column=0, sticky="w", padx=5, pady=5)
        tk.Label(self, text="Band:", font=("Arial", 10)).grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.band_var = tk.StringVar(value="bg")
        self.band_cb = ttk.Combobox(self, textvariable=self.band_var, values=["bg", "a"], state="readonly", font=("Arial", 10))
        self.band_cb.grid(row=4, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        self.psk_entry = tk.Entry(self, show="*", font=("Arial", 10))
        self.psk_entry.grid(row=3, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        self.psk_entry.bind('<FocusIn>', lambda e: self.open_keyboard(self.psk_entry))

        # Buttons
        tk.Button(self, text="Start AP", bg="green", fg="white", command=self.start_ap, font=("Arial", 10), width=10, height=2)\
            .grid(row=5, column=0, padx=5, pady=5, sticky="ew")
        tk.Button(self, text="Stop AP", bg="red", fg="white", command=self.stop_ap, font=("Arial", 10), width=10, height=2)\
            .grid(row=5, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

        for c in range(3):
            self.grid_columnconfigure(c, weight=1)

    def refresh_ifaces(self):
        adapters = self.app.wifi_mgr.list_adapters()
        self.iface_cb['values'] = adapters
        if adapters:
            self.iface_var.set(adapters[0])
        else:
            self.iface_var.set('')
        self.update_status()

    def start_ap(self):
        ifname = self.iface_var.get()
        ssid = self.ssid_entry.get().strip()
        psk = self.psk_entry.get().strip()
        if not (ifname and ssid and psk):
            messagebox.showwarning("Input Error", "Adapter, SSID and Password required.")
            return
        ok, msg = self.app.router_mgr.start_ap(ifname, ssid, psk)
        if not ok:
            messagebox.showerror("AP Error", msg)
        else:
            messagebox.showinfo("Access Point", f"AP started on {ifname}")
        self.update_status()

    def stop_ap(self):
        ifname = self.iface_var.get()
        self.app.router_mgr.stop_ap(ifname)
        messagebox.showinfo("Access Point", f"AP stopped on {ifname}")
        self.update_status()

    def update_status(self):
        ifname = self.iface_var.get()
        if ifname:
            running = self.app.router_mgr.is_running(ifname)
            self.status_lbl.config(text="Running" if running else "Stopped")
        else:
            self.status_lbl.config(text="No Adapter")

    def open_keyboard(self, entry):
        if self.keyboard_lock:
            return
        if self.keyboard_popup and self.keyboard_popup.winfo_exists():
            self.keyboard_popup.destroy()

        def unlock():
            self.keyboard_lock = False

        self.keyboard_popup = KeyboardPopup(
            self.master, entry,
            on_close_callback=lambda: [
                self.master.focus_set(), setattr(self, 'keyboard_lock', True),
                self.master.after(500, unlock)
            ]
        )
