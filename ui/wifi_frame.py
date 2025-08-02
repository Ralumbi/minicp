import tkinter as tk
from tkinter import ttk, messagebox
from ui.keyboard import KeyboardPopup

class WifiManagerFrame(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.keyboard_popup = None
        self.keyboard_lock = False
        self.build_ui()

    def build_ui(self):
        # Adapter selector
        tk.Label(self, text="Adapter:", font=(None, 10)).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.iface_var = tk.StringVar()
        self.iface_cb = ttk.Combobox(self, textvariable=self.iface_var, state="readonly", font=(None, 10))
        self.iface_cb.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        tk.Button(self, text="Refresh", command=self.refresh_ifaces, font=(None, 10), width=10, height=2)\
            .grid(row=0, column=2, sticky="ew", padx=5, pady=5)

        self.refresh_ifaces()

        # Scan button and list
        tk.Button(self, text="Scan", command=self.scan, font=(None, 10), width=10, height=2)\
            .grid(row=1, column=0, padx=5, pady=5)
        self.lst = tk.Listbox(self, height=4, font=(None, 10))
        self.lst.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        self.lst.bind('<<ListboxSelect>>', self.on_select)  # Bind selection event

        # SSID & PSK entries
        tk.Label(self, text="SSID:", font=(None, 10)).grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.ssid_entry = tk.Entry(self, font=(None, 10))
        self.ssid_entry.grid(row=3, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        self.ssid_entry.bind('<FocusIn>', lambda e: self.open_keyboard(self.ssid_entry))

        tk.Label(self, text="Password:", font=(None, 10)).grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.psk_entry = tk.Entry(self, show="*", font=(None, 10))
        self.psk_entry.grid(row=4, column=1, sticky="ew", padx=5, pady=5)
        self.psk_entry.bind('<FocusIn>', lambda e: self.open_keyboard(self.psk_entry))

        tk.Button(self, text="Connect", bg="green", fg="white", command=self._connect, font=(None, 10), width=10, height=2)\
            .grid(row=4, column=2, padx=5, pady=5)
        tk.Button(self, text="Disconnect", command=lambda: self.app.wifi_mgr.disconnect(self.iface_var.get()), font=(None, 12), width=10, height=2)\
            .grid(row=5, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

        for c in range(3):
            self.grid_columnconfigure(c, weight=1)

    def refresh_ifaces(self):
        adapters = self.app.wifi_mgr.list_adapters()
        self.iface_cb['values'] = adapters
        if adapters:
            self.iface_var.set(adapters[0])
        else:
            self.iface_var.set('')

    def scan(self):
        self.lst.delete(0, tk.END)
        ifname = self.iface_var.get()
        if not ifname:
            messagebox.showwarning("No Adapter", "Please select a Wi-Fi adapter.")
            return
        nets = self.app.wifi_mgr.scan_networks(ifname)
        for net in nets:
            self.lst.insert(tk.END, f"{net['ssid']} ({net['signal']}%)")

    def on_select(self, event):
        """Autofill SSID when a network is selected from the list."""
        if not self.lst.curselection():
            return
        selected_index = self.lst.curselection()[0]
        ssid = self.lst.get(selected_index).split(' (')[0]  # Extract SSID before '('
        self.ssid_entry.delete(0, tk.END)
        self.ssid_entry.insert(0, ssid)

    def _connect(self):
        ssid = self.ssid_entry.get().strip()
        psk = self.psk_entry.get().strip()
        ifname = self.iface_var.get()
        if not ifname:
            messagebox.showwarning("No Adapter", "Please select an adapter.")
            return
        ok, msg = self.app.wifi_mgr.connect(ifname, ssid, psk)
        if not ok:
            messagebox.showerror("Wi‑Fi Error", msg)
        else:
            messagebox.showinfo("Wi‑Fi", f"Connected to {ssid}")

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
