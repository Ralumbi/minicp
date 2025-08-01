import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import subprocess
import threading
import time

def run_cmd(cmd, timeout=None):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=True)
        return result.stdout
    except subprocess.TimeoutExpired:
        return ''
    except subprocess.CalledProcessError as e:
        return e.stdout or e.stderr

class KeyboardPopup(tk.Toplevel):
    """
    A reusable on-screen mobile-style keyboard popup.
    """
    def __init__(self, master, target_entry, on_close_callback=None):
        super().__init__(master)
        self.title("Keyboard")
        self.geometry("480x240")
        self.resizable(False, False)
        self.target_entry = target_entry
        self.on_close_callback = on_close_callback
        self.input_var = tk.StringVar(value=target_entry.get())
        self.mode = 'lowercase'

        # Entry preview
        tk.Entry(self, textvariable=self.input_var, font=("Arial", 14)).pack(fill=tk.X, padx=5, pady=5)
        self.frame = tk.Frame(self)
        self.frame.pack()

        # Define layouts
        self.layouts = {
            'lowercase': [
                ['q','w','e','r','t','y','u','i','o','p'],
                ['a','s','d','f','g','h','j','k','l'],
                ['⇧','z','x','c','v','b','n','m','⌫'],
                ['123','@','.',' ','Enter','Close']
            ],
            'uppercase': [
                ['Q','W','E','R','T','Y','U','I','O','P'],
                ['A','S','D','F','G','H','J','K','L'],
                ['⇧','Z','X','C','V','B','N','M','⌫'],
                ['123','@','.',' ','Enter','Close']
            ],
            'symbols': [
                ['1','2','3','4','5','6','7','8','9','0'],
                ['!','@','#','$','%','^','&','*','(',')'],
                ['ABC','-','=','_','+','{','}',':','\'',"⌫"],
                ['"',',','.','<','>','/','?',' ','Enter','Close']
            ]
        }
        self.render()

    def render(self):
        # Clear old
        for w in self.frame.winfo_children():
            w.destroy()
        # Draw keys
        layout = self.layouts[self.mode]
        for row in layout:
            rowf = tk.Frame(self.frame)
            rowf.pack(fill=tk.X, pady=1)
            for key in row:
                btn = tk.Button(
                    rowf, text=key, font=("Arial", 12),
                    command=lambda k=key: self.on_key(k)
                )
                btn.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=1, pady=1)

    def on_key(self, key):
        if key == '⇧':
            self.mode = 'uppercase' if self.mode == 'lowercase' else 'lowercase'
            self.render()
        elif key == '123':
            self.mode = 'symbols'
            self.render()
        elif key == 'ABC':
            self.mode = 'lowercase'
            self.render()
        elif key == '⌫':
            self.input_var.set(self.input_var.get()[:-1])
        elif key == 'Enter':
            self.commit()
            self.close()
        elif key == 'Close':
            self.close()
        else:
            self.input_var.set(self.input_var.get() + key)

    def commit(self):
        self.target_entry.delete(0, tk.END)
        self.target_entry.insert(0, self.input_var.get())

    def close(self):
        if self.on_close_callback:
            self.on_close_callback()
        self.destroy()

class OverviewFrame(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.build_ui()
        self.update_status()

    def build_ui(self):
        tk.Label(self, text="Device Status", font=("Arial", 12, "bold")).pack(pady=5)
        self.device_frame = tk.Frame(self)
        self.device_frame.pack(fill=tk.BOTH, expand=True)

    def update_status(self):
        # Clear existing widgets
        for widget in self.device_frame.winfo_children():
            widget.destroy()

        # Wi-Fi devices
        tk.Label(self.device_frame, text="Wi-Fi Devices", font=("Arial", 10, "bold")).pack(pady=5)
        status = self.app.get_device_status()
        for device, info in status.items():
            frame = tk.Frame(self.device_frame)
            frame.pack(fill=tk.X, pady=2)
            tk.Label(frame, text=f"{device}: {info['role']}").pack(side=tk.LEFT)
            if info['role'] == 'client':
                tk.Label(frame, text=f"Connected to {info['ssid']}").pack(side=tk.LEFT, padx=10)
                tk.Button(frame, text="Disconnect", command=lambda d=device: self.app.wifi_tab.disconnect_wifi(d)).pack(side=tk.RIGHT)
            elif info['role'] == 'ap':
                tk.Label(frame, text=f"AP: {info['ssid']}").pack(side=tk.LEFT, padx=10)
                tk.Button(frame, text="Stop AP", command=lambda d=device: self.app.router_tab.stop_ap(d)).pack(side=tk.RIGHT)

        # Bluetooth devices
        tk.Label(self.device_frame, text="Bluetooth Devices", font=("Arial", 10, "bold")).pack(pady=5)
        paired_devices = self.app.get_paired_bluetooth_devices()
        for device in paired_devices:
            mac = device['mac']
            name = device['name']
            connected = self.app.get_bluetooth_connection_status(mac)
            status_text = f"{name} ({mac}): {'Connected' if connected else 'Disconnected'}"
            tk.Label(self.device_frame, text=status_text).pack()

        # Schedule next update
        self.after(5000, self.update_status)

class WifiManagerFrame(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.keyboard_popup = None
        self.keyboard_lock = False
        self.wifi_device = tk.StringVar(value="wlan0")  # Default device
        self.available_devices = self.get_wifi_devices()  # Initial device list
        self.build_ui()

    def build_ui(self):
        # Current connection display
        tk.Label(self, text="Connected:", font=("Arial", 9)).grid(row=0, column=0, sticky="w", padx=5)
        self.current_conn_label = tk.Label(self, text="None", font=("Arial", 9), wraplength=200)
        self.current_conn_label.grid(row=0, column=1, columnspan=2, sticky="w", padx=5)
        self.device_label = tk.Label(self, text="", font=("Arial", 8), fg="gray")
        self.device_label.grid(row=1, column=1, columnspan=2, sticky="w", padx=5)
        self.update_current_connection()

        # Wi-Fi device selection
        tk.Label(self, text="Wi-Fi Device:", font=("Arial", 8)).grid(row=2, column=0, sticky="w", padx=5)
        self.device_combobox = ttk.Combobox(self, textvariable=self.wifi_device, values=self.available_devices, state="readonly", font=("Arial", 8))
        self.device_combobox.grid(row=2, column=1, columnspan=2, padx=5, pady=2, sticky="ew")
        self.device_combobox.bind("<FocusIn>", self.refresh_devices)
        if not self.available_devices:
            self.wifi_device.set("No Wi-Fi devices found")
            self.device_combobox.config(state="disabled")

        # Network list
        tk.Label(self, text="Available Networks", font=("Arial", 9, "bold")).grid(row=3, column=0, columnspan=3, pady=2)
        self.networks_listbox = tk.Listbox(self, height=4, font=("Arial", 8))
        self.networks_listbox.grid(row=4, column=0, columnspan=3, padx=5, pady=2, sticky="ew")

        # Scan and Disconnect buttons
        tk.Button(self, text="Scan", font=("Arial", 8), command=self.scan_networks).grid(row=5, column=0, padx=3, pady=2, sticky="ew")
        tk.Button(self, text="Disconnect", font=("Arial", 8), command=lambda: self.disconnect_wifi(self.wifi_device.get())).grid(row=5, column=1, padx=3, pady=2, sticky="ew")

        # SSID entry
        tk.Label(self, text="SSID", font=("Arial", 8)).grid(row=6, column=0, pady=(5, 0), sticky="w")
        self.ssid_entry = tk.Entry(self, font=("Arial", 10))
        self.ssid_entry.grid(row=7, column=0, columnspan=3, padx=5, pady=2, sticky="ew")
        self.ssid_entry.bind("<FocusIn>", lambda e: self.open_keyboard(self.ssid_entry))

        # Password entry and Connect button
        tk.Label(self, text="Password", font=("Arial", 8)).grid(row=8, column=0, pady=(5, 0), sticky="w")
        self.pass_entry = tk.Entry(self, font=("Arial", 10), show="*")
        self.pass_entry.grid(row=9, column=0, columnspan=2, padx=5, pady=2, sticky="ew")
        tk.Button(self, text="Connect", bg="green", fg="white", font=("Arial", 9), command=self.connect_wifi).grid(row=9, column=2, padx=3, pady=2, sticky="ew")
        self.pass_entry.bind("<FocusIn>", lambda e: self.open_keyboard(self.pass_entry))

        # Configure grid weights for resizing
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)

    def get_wifi_devices(self):
        try:
            out = subprocess.check_output(['nmcli', '-t', '-f', 'DEVICE,TYPE', 'device']).decode()
            devices = []
            for line in out.splitlines():
                device, typ = line.split(':')
                if typ == 'wifi':
                    devices.append(device)
            return devices
        except Exception:
            return []

    def refresh_devices(self, event):
        current_device = self.wifi_device.get()
        new_devices = self.get_wifi_devices()
        if new_devices != self.available_devices or not new_devices:
            self.available_devices = new_devices
            self.device_combobox['values'] = self.available_devices
            if not self.available_devices:
                self.wifi_device.set("No Wi-Fi devices found")
                self.device_combobox.config(state="disabled")
            else:
                self.device_combobox.config(state="readonly")
                if current_device in self.available_devices:
                    self.wifi_device.set(current_device)
                else:
                    self.wifi_device.set(self.available_devices[0])

    def scan_networks(self):
        self.networks_listbox.delete(0, tk.END)
        device = self.wifi_device.get()
        if not device or device == "No Wi-Fi devices found":
            messagebox.showwarning("Device Error", "Please select a valid Wi-Fi device.")
            return
        try:
            out = subprocess.check_output([
                'nmcli', '-t', '-f', 'SSID', 'device', 'wifi', 'list', 'ifname', device
            ]).decode()
            ssids = sorted({l.strip() for l in out.splitlines() if l.strip()})
            for ssid in ssids:
                self.networks_listbox.insert(tk.END, ssid)
            self.update_current_connection()
        except Exception as e:
            messagebox.showerror("Scan Error", str(e))

    def connect_wifi(self):
        device = self.wifi_device.get()
        status = self.app.get_device_status()
        if device in status and status[device]['role'] == 'ap':
            messagebox.showinfo("Info", f"Device {device} is in AP mode. Connecting will deactivate it.")
        ssid = self.ssid_entry.get().strip()
        pwd = self.pass_entry.get().strip()
        if not ssid:
            messagebox.showwarning("Input", "SSID required")
            return
        if not device or device == "No Wi-Fi devices found":
            messagebox.showwarning("Device Error", "Please select a valid Wi-Fi device.")
            return
        try:
            conn_check = subprocess.run(
                ['nmcli', 'con', 'show', ssid],
                capture_output=True, text=True
            )
            if conn_check.returncode == 0:
                subprocess.run(['nmcli', 'con', 'delete', ssid], check=True)
            subprocess.run([
                'nmcli', 'con', 'add', 'type', 'wifi',
                'ifname', device, 'con-name', ssid, 'ssid', ssid,
                'wifi-sec.key-mgmt', 'wpa-psk', 'wifi-sec.psk', pwd
            ], check=True)
            subprocess.run(['nmcli', 'con', 'up', 'id', ssid, 'ifname', device], check=True)
            messagebox.showinfo("Wi-Fi", f"Connected to {ssid}")
            self.update_current_connection()
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else "Connection failed. Check SSID, password, or Wi-Fi adapter."
            messagebox.showerror("Connect Error", error_msg)

    def disconnect_wifi(self, device=None):
        if device is None:
            device = self.wifi_device.get()
        active_conn, _ = self.get_active_connection_for_device(device)
        if active_conn:
            subprocess.run(['nmcli', 'con', 'down', 'id', active_conn], check=True)
            messagebox.showinfo("Wi-Fi", f"Disconnected from {active_conn} on {device}")
        self.update_current_connection()

    def get_active_connection_for_device(self, device):
        try:
            out = subprocess.check_output(['nmcli', '-t', '-f', 'NAME,DEVICE', 'con', 'show', '--active']).decode()
            for line in out.splitlines():
                name, dev = line.split(':')
                if dev == device:
                    return name, device
        except Exception:
            pass
        return '', ''

    def update_current_connection(self):
        device = self.wifi_device.get()
        active_conn, active_device = self.get_active_connection_for_device(device)
        if active_conn:
            self.current_conn_label.config(text=active_conn)
            self.device_label.config(text=f"Device: {active_device}")
        else:
            self.current_conn_label.config(text="None")
            self.device_label.config(text="")

    def open_keyboard(self, entry):
        if self.keyboard_lock:
            return
        if self.keyboard_popup and self.keyboard_popup.winfo_exists():
            self.keyboard_popup.destroy()
        def unlock(): self.keyboard_lock = False
        self.keyboard_popup = KeyboardPopup(
            self.master, entry,
            on_close_callback=lambda: [
                self.master.focus_set(), setattr(self, 'keyboard_lock', True),
                self.master.after(500, unlock)
            ]
        )

class RouterSetupFrame(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.keyboard_popup = None
        self.keyboard_lock = False
        self.ap_device = tk.StringVar(value="")  # Selected device for AP
        self.available_devices = self.get_wifi_devices()  # Initial device list
        self.build_ui()

    def build_ui(self):
        # Current AP status
        tk.Label(self, text="Access Point:", font=("Arial", 9)).grid(row=0, column=0, sticky="w", padx=5)
        self.ap_status_label = tk.Label(self, text="Stopped", font=("Arial", 9), wraplength=200)
        self.ap_status_label.grid(row=0, column=1, columnspan=2, sticky="w", padx=5)

        # Wi-Fi device selection
        tk.Label(self, text="Wi-Fi Device:", font=("Arial", 8)).grid(row=1, column=0, sticky="w", padx=5)
        self.device_combobox = ttk.Combobox(self, textvariable=self.ap_device, values=self.available_devices, state="readonly", font=("Arial", 8))
        self.device_combobox.grid(row=1, column=1, columnspan=2, padx=5, pady=2, sticky="ew")
        self.device_combobox.bind("<FocusIn>", self.refresh_devices)

        # SSID entry
        tk.Label(self, text="SSID", font=("Arial", 8)).grid(row=2, column=0, pady=(5, 0), sticky="w")
        self.ssid_entry = tk.Entry(self, font=("Arial", 10))
        self.ssid_entry.grid(row=3, column=0, columnspan=3, padx=5, pady=2, sticky="ew")
        self.ssid_entry.bind("<FocusIn>", lambda e: self.open_keyboard(self.ssid_entry))

        # Password entry
        tk.Label(self, text="Password", font=("Arial", 8)).grid(row=4, column=0, pady=(5, 0), sticky="w")
        self.pass_entry = tk.Entry(self, font=("Arial", 10), show="*")
        self.pass_entry.grid(row=5, column=0, columnspan=2, padx=5, pady=2, sticky="ew")
        self.pass_entry.bind("<FocusIn>", lambda e: self.open_keyboard(self.pass_entry))

        # Start and Stop buttons
        tk.Button(self, text="Start AP", bg="green", fg="white", font=("Arial", 9), command=self.start_ap).grid(row=5, column=2, padx=3, pady=2, sticky="ew")
        tk.Button(self, text="Stop AP", bg="red", fg="white", font=("Arial", 9), command=lambda: self.stop_ap(self.ap_device.get())).grid(row=6, column=0, columnspan=3, padx=5, pady=2, sticky="ew")

        # Configure grid weights
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)

    def get_wifi_devices(self):
        try:
            out = subprocess.check_output(['nmcli', '-t', '-f', 'DEVICE,TYPE', 'device']).decode()
            devices = []
            for line in out.splitlines():
                device, typ = line.split(':')
                if typ == 'wifi':
                    devices.append(device)
            return devices
        except Exception:
            return []

    def refresh_devices(self, event):
        current_device = self.ap_device.get()
        new_devices = self.get_wifi_devices()
        self.device_combobox['values'] = new_devices
        if new_devices:
            if current_device in new_devices:
                self.ap_device.set(current_device)
            else:
                self.ap_device.set(new_devices[0])
        else:
            self.ap_device.set("No Wi-Fi devices available")
            self.device_combobox.config(state="disabled")

    def start_ap(self):
        device = self.ap_device.get()
        status = self.app.get_device_status()
        if device in status and status[device]['role'] == 'client':
            messagebox.showinfo("Info", f"Device {device} is connected to a network. Starting AP will disconnect it.")
        ssid = self.ssid_entry.get().strip()
        pwd = self.pass_entry.get().strip()
        if not device or device == "No Wi-Fi devices available":
            messagebox.showwarning("Device Error", "Please select a valid Wi-Fi device.")
            return
        if not ssid or not pwd:
            messagebox.showwarning("Input Error", "SSID and Password are required.")
            return
        try:
            ap_conn_name = f"AP_{device}"
            subprocess.run(['nmcli', 'con', 'delete', ap_conn_name], check=False)
            subprocess.run(['nmcli', 'device', 'wifi', 'hotspot', 'ifname', device, 'con-name', ap_conn_name, 'ssid', ssid, 'password', pwd], check=True)
            messagebox.showinfo("Access Point", f"Started AP on {device} with SSID {ssid}")
            self.update_ap_status()
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to start AP: {e}")

    def stop_ap(self, device=None):
        if device is None:
            device = self.ap_device.get()
        ap_conn_name = f"AP_{device}"
        try:
            subprocess.run(['nmcli', 'con', 'down', ap_conn_name], check=True)
            subprocess.run(['nmcli', 'con', 'delete', ap_conn_name], check=True)
            messagebox.showinfo("Access Point", f"Stopped AP on {device}")
            self.update_ap_status()
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to stop AP: {e}")

    def update_ap_status(self):
        device = self.ap_device.get()
        ap_conn_name = f"AP_{device}"
        try:
            out = subprocess.check_output(['nmcli', '-t', '-f', 'NAME,DEVICE', 'con', 'show', '--active']).decode()
            for line in out.splitlines():
                name, dev = line.split(':')
                if name == ap_conn_name and dev == device:
                    self.ap_status_label.config(text=f"Running on {device}")
                    return
        except Exception:
            pass
        self.ap_status_label.config(text="Stopped")

    def open_keyboard(self, entry):
        if self.keyboard_lock:
            return
        if self.keyboard_popup and self.keyboard_popup.winfo_exists():
            self.keyboard_popup.destroy()
        def unlock(): self.keyboard_lock = False
        self.keyboard_popup = KeyboardPopup(
            self.master, entry,
            on_close_callback=lambda: [
                self.master.focus_set(), setattr(self, 'keyboard_lock', True),
                self.master.after(500, unlock)
            ]
        )

class BluetoothManagerFrame(tk.Frame):
    """Optimized bluetooth scanning with timeout"""
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.build_ui()

    def build_ui(self):
        self.devices_listbox = tk.Listbox(self, height=6, font=(None,8))
        self.devices_listbox.grid(row=0, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        tk.Button(self, text="Scan", command=self.scan_devices).grid(row=1, column=0)
        tk.Button(self, text="Pair", command=self.pair_device).grid(row=1, column=1)
        tk.Button(self, text="Connect", command=self.connect_device).grid(row=2, column=0)
        tk.Button(self, text="Disconnect", command=self.disconnect_device).grid(row=2, column=1)
        tk.Button(self, text="Remove", command=self.remove_device).grid(row=2, column=2)
        for i in range(3): self.grid_columnconfigure(i, weight=1)

    def scan_devices(self):
        self.devices_listbox.delete(0, tk.END)
        self.devices_listbox.insert(tk.END, "Scanning...")
        threading.Thread(target=self._scan_thread, daemon=True).start()

    def _scan_thread(self):
        # use timeout for scan on
        run_cmd(['timeout','5','bluetoothctl','scan','on'])
        run_cmd(['bluetoothctl','scan','off'])
        out = run_cmd(['bluetoothctl','devices'])
        devices = []
        for line in out.splitlines():
            if line.startswith('Device '):
                parts = line.split(' ',2)
                if len(parts)==3: devices.append(f"{parts[2]} ({parts[1]})")
        self.app.root.after(0, lambda: self._update_devices_list(devices))

    def _update_devices_list(self, devices):
        self.devices_listbox.delete(0, tk.END)
        for d in devices: self.devices_listbox.insert(tk.END, d)

    def pair_device(self):
        selected = self.devices_listbox.curselection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a device.")
            return
        device_str = self.devices_listbox.get(selected[0])
        mac = device_str.split('(')[1].split(')')[0]
        try:
            subprocess.run(['bluetoothctl', 'pair', mac], check=True)
            messagebox.showinfo("Bluetooth", f"Paired with {mac}")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Pair Error", str(e))

    def connect_device(self):
        selected = self.devices_listbox.curselection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a device.")
            return
        device_str = self.devices_listbox.get(selected[0])
        mac = device_str.split('(')[1].split(')')[0]
        try:
            subprocess.run(['bluetoothctl', 'connect', mac], check=True)
            messagebox.showinfo("Bluetooth", f"Connected to {mac}")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Connect Error", str(e))

    def disconnect_device(self):
        selected = self.devices_listbox.curselection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a device.")
            return
        device_str = self.devices_listbox.get(selected[0])
        mac = device_str.split('(')[1].split(')')[0]
        try:
            subprocess.run(['bluetoothctl', 'disconnect', mac], check=True)
            messagebox.showinfo("Bluetooth", f"Disconnected from {mac}")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Disconnect Error", str(e))

    def remove_device(self):
        selected = self.devices_listbox.curselection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a device.")
            return
        device_str = self.devices_listbox.get(selected[0])
        mac = device_str.split('(')[1].split(')')[0]
        try:
            subprocess.run(['bluetoothctl', 'remove', mac], check=True)
            messagebox.showinfo("Bluetooth", f"Removed {mac}")
            # Refresh the list
            self.scan_devices()
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Remove Error", str(e))

class MainApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Portable Pi Utility")
        self.root.geometry("480x320")
        self.build()
        self.root.mainloop()

    def build(self):
        nb = ttk.Notebook(self.root)
        nb.pack(fill=tk.BOTH, expand=True)

        self.overview_tab = OverviewFrame(nb, self)
        nb.add(self.overview_tab, text="Overview")

        self.wifi_tab = WifiManagerFrame(nb, self)
        nb.add(self.wifi_tab, text="Wi-Fi")

        self.router_tab = RouterSetupFrame(nb, self)
        nb.add(self.router_tab, text="Router")

        self.bluetooth_tab = BluetoothManagerFrame(nb, self)
        nb.add(self.bluetooth_tab, text="Bluetooth")

    def get_device_status(self):
        devices = []
        out = subprocess.check_output(['nmcli', '-t', '-f', 'DEVICE,TYPE', 'device']).decode().splitlines()
        for line in out:
            device, typ = line.split(':')
            if typ == 'wifi':
                devices.append(device)

        status = {}
        for device in devices:
            out = subprocess.check_output(['nmcli', '-t', '-f', 'GENERAL.STATE,GENERAL.CONNECTION', 'device', 'show', device]).decode().splitlines()
            state = connection = ''
            for line in out:
                if line.startswith('GENERAL.STATE:'):
                    state = line.split(':')[1].strip()
                elif line.startswith('GENERAL.CONNECTION:'):
                    connection = line.split(':')[1].strip()

            if state == '100 (connected)' and connection:
                details = subprocess.check_output(['nmcli', '-f', '802-11-wireless.mode,802-11-wireless.ssid', 'con', 'show', connection]).decode().splitlines()
                mode = ssid = ''
                for line in details:
                    if line.startswith('802-11-wireless.mode:'):
                        mode = line.split(':')[1].strip()
                    elif line.startswith('802-11-wireless.ssid:'):
                        ssid = line.split(':')[1].strip()
                status[device] = {'role': 'client' if mode == 'infrastructure' else 'ap', 'ssid': ssid}
            else:
                status[device] = {'role': 'idle'}
        return status

    def get_paired_bluetooth_devices(self):
        try:
            out = subprocess.check_output(['bluetoothctl', 'paired-devices']).decode().splitlines()
            devices = []
            for line in out:
                if line.startswith('Device '):
                    parts = line.split(' ', 2)
                    if len(parts) == 3:
                        mac = parts[1]
                        name = parts[2]
                        devices.append({'mac': mac, 'name': name})
            return devices
        except Exception:
            return []

    def get_bluetooth_connection_status(self, mac):
        try:
            out = subprocess.check_output(['bluetoothctl', 'info', mac]).decode()
            for line in out.splitlines():
                if line.strip().startswith('Connected:'):
                    status = line.split(':')[1].strip()
                    return status == 'yes'
            return False
        except Exception:
            return False

if __name__ == '__main__':
    MainApp()