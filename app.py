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

class MainApp:
    def __init__(self):
        self.wifi_mgr   = WifiManager()
        self.router_mgr = RouterManager()
        self.bt_mgr     = BluetoothManager()

        self.root = tk.Tk()
        self.root.title("MiniCP - Raspberry Pi")
        self.root.geometry("480x320")

        nb = ttk.Notebook(self.root)
        nb.pack(fill=tk.BOTH, expand=True)

        nb.add(OverviewFrame(nb, self),        text="Overview")
        nb.add(WifiManagerFrame(nb, self),     text="Wi‑Fi")
        nb.add(RouterSetupFrame(nb, self),     text="Router")
        nb.add(BluetoothManagerFrame(nb, self), text="Bluetooth")

        self.root.mainloop()

if __name__ == "__main__":
    MainApp()
