import tkinter as tk
from tkinter import messagebox
import os
import subprocess
import re

class UsbManagerFrame(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.keyboard_popup = None
        self.keyboard_lock = False
        self.mount_point = "/home/caleb/minicp/usb_mount"
        self.build_ui()

    def build_ui(self):
        # Title
        tk.Label(self, text="USB Manager", font=("Arial", 12, "bold")).pack(pady=5)

        # USB device list
        tk.Label(self, text="Available USB Devices:", font=("Arial", 10)).pack(pady=5)
        self.usb_list = tk.Listbox(self, height=4, font=("Arial", 10))
        self.usb_list.pack(fill=tk.X, padx=5, pady=5)
        self.usb_list.bind('<<ListboxSelect>>', self.on_select)
        tk.Button(self, text="Refresh", command=self.refresh_usb, font=("Arial", 10), width=10, height=1)\
            .pack(pady=5)

        # Mount status
        tk.Label(self, text="Mount Status:", font=("Arial", 10)).pack(pady=5)
        self.status_label = tk.Label(self, text="No device mounted", font=("Arial", 10))
        self.status_label.pack(pady=5)

        # Mount/Unmount buttons
        button_frame = tk.Frame(self)
        button_frame.pack(pady=5)

        tk.Button(button_frame, text="Mount", command=self.mount_usb, font=("Arial", 10), width=10, height=1)\
            .pack(side="left", padx=5)

        tk.Button(button_frame, text="Unmount", command=self.unmount_usb, font=("Arial", 10), width=10, height=1)\
            .pack(side="left", padx=5)
        

        self.refresh_usb()

    def refresh_usb(self):
        self.usb_list.delete(0, tk.END)
        usb_devices = self.get_usb_devices()
        for dev in usb_devices:
            self.usb_list.insert(tk.END, f"{dev['dev']} - {dev['label'] or 'No Label'}")

    def get_usb_devices(self):
        devices = []
        try:
            output = subprocess.check_output(["lsblk", "-o", "NAME,LABEL,TYPE,MOUNTPOINT", "-J"]).decode()
            data = eval(output)  # Parse JSON-like output
            for dev in data['blockdevices']:
                if dev['type'] == 'disk' and any(p['type'] == 'part' for p in dev.get('children', [])):
                    for part in dev.get('children', []):
                        if not part.get('mountpoint') and 'usb' in dev.get('name', '').lower():
                            devices.append({
                                'dev': f"/dev/{part['name']}",
                                'label': part.get('label', '')
                            })
        except Exception as e:
            print(f"Error detecting USB devices: {e}")
        return devices

    def on_select(self, event):
        """Update status when a device is selected."""
        if not self.usb_list.curselection():
            return
        selected_index = self.usb_list.curselection()[0]
        device = self.get_usb_devices()[selected_index]
        self.status_label.config(text=f"Selected: {device['dev']} - {device['label'] or 'No Label'}")

    def mount_usb(self):
        if not self.usb_list.curselection():
            messagebox.showwarning("No Selection", "Please select a USB device.")
            return
        selected_index = self.usb_list.curselection()[0]
        device = self.get_usb_devices()[selected_index]['dev']

        # Create mount point if it doesn't exist
        os.makedirs(self.mount_point, exist_ok=True)

        # Check if already mounted
        if os.path.ismount(self.mount_point):
            messagebox.showwarning("Mount Error", "A device is already mounted. Unmount first.")
            return

        try:
            # Attempt to mount with default filesystem (e.g., vfat, ntfs, ext4)
            subprocess.run(["mount", device, self.mount_point], check=True)
            # Set permissions for caleb user
            subprocess.run(["chown", "-R", "caleb:caleb", self.mount_point], check=True)
            messagebox.showinfo("Mount Success", f"Mounted {device} to {self.mount_point}")
            self.status_label.config(text=f"Mounted: {device} to {self.mount_point}")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Mount Error", f"Failed to mount {device}: {e}")
            if os.path.ismount(self.mount_point):
                subprocess.run(["umount", self.mount_point], check=False)

    def unmount_usb(self):
        if not os.path.ismount(self.mount_point):
            messagebox.showwarning("Unmount Error", "No device is mounted.")
            return
        try:
            subprocess.run(["umount", self.mount_point], check=True)
            self.status_label.config(text="No device mounted")
            messagebox.showinfo("Unmount Success", f"Unmounted {self.mount_point}")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Unmount Error", f"Failed to unmount: {e}")
