# python lib imports

# third party imports
from tkinter import ttk
import tkinter as tk

# local imports
from managers.wifi_manager import WifiManager
from managers.router_manager import RouterManager
from managers.bluetooth_manager import BluetoothManager
from ui.overview_frame import OverviewFrame
from ui.wifi_frame import WifiManagerFrame
from ui.router_frame import RouterSetupFrame
from ui.bluetooth_frame import BluetoothManagerFrame
# from ui.usb_frame import UsbManagerFrame

class MainApp:
    def __init__(self):
        self.wifi_mgr   = WifiManager(ifname="wlan0")  # Onboard for client
        self.router_mgr = RouterManager(ifname="wlan1")  # PHREEZE for AP
        self.bt_mgr     = BluetoothManager()

        self.root = tk.Tk()
        self.root.title("MiniCP - Raspberry Pi")
        self.root.geometry("480x320")
        self.root.attributes('-fullscreen', False)  # Fullscreen for 480x320 touch display

        nb = ttk.Notebook(self.root)
        nb.pack(fill=tk.BOTH, expand=True)

        nb.add(OverviewFrame(nb, self),        text="Overview")
        nb.add(WifiManagerFrame(nb, self),     text="Wi‑Fi")
        nb.add(RouterSetupFrame(nb, self),     text="Router")
        nb.add(BluetoothManagerFrame(nb, self), text="Bluetooth")
        # nb.add(UsbManagerFrame(nb, self),      text="USB")

        self.root.mainloop()

if __name__ == "__main__":
    MainApp()
