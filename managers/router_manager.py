import json
import os
import logging
import time
from utils.cmd import run_cmd

# Use current user's home directory
HOME_DIR = os.path.expanduser("~")
LOG_FILE = os.path.join(HOME_DIR, ".config/minicp/router_manager.log")
CRED_FILE = os.path.join(HOME_DIR, ".config/minicp/ap_credentials.json")

# Setup logging
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s: %(message)s')

class RouterManager:
    def __init__(self, ifname: str = "wlan1"):
        self.ifname = ifname

    def start_ap(self, ifname: str, ssid: str, psk: str, band: str = 'bg', channel: int = None) -> tuple[bool, str]:
        logging.info(f"Starting AP on {ifname} with SSID {ssid}")
        if not ssid:
            logging.error("SSID cannot be empty")
            return False, "SSID cannot be empty"
        if len(psk) < 8:
            logging.error("Password too short")
            return False, "Password must be at least 8 characters"
        conn_name = f"Hotspot_{ifname}"
        run_cmd(['nmcli', 'con', 'delete', conn_name], timeout=5)

        if band == 'a':
            channel = channel or 36  # Default to channel 36 for 5GHz
        else:
            band = 'bg'
            channel = channel or 6   # Default to channel 6 for 2.4GHz

        out = run_cmd([
            'nmcli', 'con', 'add', 'type', 'wifi', 'ifname', ifname,
            'con-name', conn_name, 'ssid', ssid,
            'autoconnect', 'yes', 'wifi-sec.key-mgmt', 'wpa-psk',
            'wifi-sec.psk', psk, 'wifi.mode', 'ap',
            'wifi.band', band, 'wifi.channel', str(channel),
            'ipv4.method', 'shared', 'ipv4.addresses', '192.168.4.1/24'
        ], timeout=15)

        if "Error" in out or not out:
            logging.error(f"AP setup failed: {out}")
            return False, out
        out2 = run_cmd(['nmcli', 'con', 'up', conn_name], timeout=15)
        if "Error" in out2:
            logging.error(f"AP activation failed: {out2}")
            return False, out2
        self.save_credentials(ifname, ssid, psk)
        self.enable_internet_sharing(ifname)
        logging.info("AP started successfully")
        return True, ""

    def stop_ap(self, ifname: str = None) -> None:
        ifname = ifname or self.ifname
        logging.info(f"Stopping AP on {ifname}")
        conn_name = f"Hotspot_{ifname}"
        run_cmd(['nmcli', 'con', 'down', conn_name], timeout=5)
        run_cmd(['nmcli', 'con', 'delete', conn_name], timeout=5)
        logging.info("AP stopped")

    def is_running(self, ifname: str = None) -> bool:
        ifname = ifname or self.ifname
        conn_name = f"Hotspot_{ifname}"
        out = run_cmd(['nmcli', '-t', '-f', 'NAME,DEVICE', 'con', 'show', '--active'])
        running = any(
            line.split(':', 1)[0] == conn_name and line.split(':', 1)[1] == ifname
            for line in out.splitlines()
        )
        logging.debug(f"AP running check for {ifname}: {running}")
        return running

    def list_connected_devices(self, ifname: str = None) -> list[dict]:
        ifname = ifname or self.ifname
        logging.debug(f"Listing devices on {ifname}")
        out = run_cmd(['arp', '-n', '-i', ifname])
        devices = []
        for line in out.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 3:
                devices.append({'ip': parts[0], 'mac': parts[2]})
        logging.debug(f"Found devices: {devices}")
        return devices

    def enable_internet_sharing(self, ifname: str, client_ifname: str = "wlan0"):
        logging.info(f"Enabling internet sharing from {client_ifname} to {ifname}")
        run_cmd(['sysctl', '-w', 'net.ipv4.ip_forward=1'])
        run_cmd(['iptables', '-t', 'nat', '-A', 'POSTROUTING', '-o', client_ifname, '-j', 'MASQUERADE'])
        run_cmd(['iptables', '-A', 'FORWARD', '-i', ifname, '-o', client_ifname, '-j', 'ACCEPT'])
        run_cmd(['iptables', '-A', 'FORWARD', '-i', client_ifname, '-o', ifname, '-m', 'state', '--state', 'RELATED,ESTABLISHED', '-j', 'ACCEPT'])
        run_cmd(['sh', '-c', 'iptables-save > /etc/iptables/rules.v4'])

    def _load_credentials(self) -> dict:
        logging.debug(f"Loading credentials from {CRED_FILE}")
        if os.path.exists(CRED_FILE):
            try:
                with open(CRED_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Failed to load credentials: {e}")
                return {}
        return {}

    def _save_credentials(self, data: dict):
        logging.debug(f"Saving credentials to {CRED_FILE}: {data}")
        try:
            os.makedirs(os.path.dirname(CRED_FILE), exist_ok=True)
            with open(CRED_FILE, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logging.error(f"Failed to save credentials: {e}")

    def save_credentials(self, ifname: str, ssid: str, psk: str):
        logging.info(f"Saving credentials for {ifname}, SSID: {ssid}")
        creds = self._load_credentials()
        creds[ifname] = {'ssid': ssid, 'psk': psk}
        self._save_credentials(creds)

    def load_credentials(self, ifname: str) -> tuple[str, str]:
        creds = self._load_credentials()
        return (
            creds.get(ifname, {}).get('ssid', ''),
            creds.get(ifname, {}).get('psk', '')
        )

    def monitor(self):
        while True:
            if not self.is_running():
                ssid, psk = self.load_credentials(self.ifname)
                if ssid and psk:
                    logging.info(f"Restarting AP {ssid} on {self.ifname}")
                    self.start_ap(self.ifname, ssid, psk)
            time.sleep(60)
