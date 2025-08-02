import json
import os
import logging
import time
from utils.cmd import run_cmd

# Use current user's home directory
HOME_DIR = os.path.expanduser("~")
LOG_FILE = os.path.join(HOME_DIR, ".config/minicp/wifi_manager.log")
CRED_FILE = os.path.join(HOME_DIR, ".config/minicp/wifi_credentials.json")

# Setup logging
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s: %(message)s')

class WifiManager:
    def __init__(self, ifname: str = "wlan0"):
        self.ifname = ifname

    def list_adapters(self) -> list[str]:
        out = run_cmd(['nmcli', '-t', '-f', 'DEVICE,TYPE', 'device'])
        adapters = [line.split(':')[0] for line in out.splitlines() if line.endswith(':wifi')]
        logging.debug(f"Found adapters: {adapters}")
        return adapters

    def scan_networks(self, ifname: str = None) -> list[dict]:
        ifname = ifname or self.ifname
        logging.info(f"Scanning networks on {ifname}")
        out = run_cmd(
            ['nmcli', '-t', '-f', 'SSID,SIGNAL,SECURITY', 'device', 'wifi', 'list', 'ifname', ifname],
            timeout=10
        )
        networks = []
        for line in out.splitlines():
            if line.strip():
                parts = line.split(':')
                if len(parts) >= 3:
                    networks.append({
                        'ssid': parts[0].strip(),
                        'signal': int(parts[1]) if parts[1].isdigit() else 0,
                        'security': parts[2].strip()
                    })
        logging.debug(f"Found networks: {networks}")
        return sorted(networks, key=lambda x: x['signal'], reverse=True)

    def connect(self, ifname: str, ssid: str, psk: str) -> tuple[bool, str]:
        logging.info(f"Connecting to SSID {ssid} on {ifname}")
        if not ssid:
            logging.error("SSID cannot be empty")
            return False, "SSID cannot be empty"
        if len(psk) < 8:
            logging.error("Password too short")
            return False, "Password must be at least 8 characters"
        run_cmd(['nmcli', 'con', 'delete', ssid], timeout=5)
        out = run_cmd([
            'nmcli', 'con', 'add', 'type', 'wifi',
            'ifname', ifname, 'con-name', ssid, 'ssid', ssid,
            'wifi-sec.key-mgmt', 'wpa-psk', 'wifi-sec.psk', psk
        ], timeout=15)
        if "Error" in out or not out:
            logging.error(f"Connection add failed: {out}")
            return False, out

        out2 = run_cmd(['nmcli', 'con', 'up', 'id', ssid, 'ifname', ifname], timeout=15)
        if "Error" in out2:
            logging.error(f"Connection up failed: {out2}")
            return False, out2

        self.save_credentials(ifname, ssid, psk)
        logging.info("Connection successful")
        return True, ""

    def disconnect(self, ifname: str = None) -> None:
        ifname = ifname or self.ifname
        logging.info(f"Disconnecting from {ifname}")
        active = self.get_active_connection(ifname)
        if active:
            run_cmd(['nmcli', 'con', 'down', 'id', active], timeout=5)
            logging.info(f"Disconnected from {active}")

    def get_active_connection(self, ifname: str = None) -> str:
        ifname = ifname or self.ifname
        out = run_cmd(['nmcli', '-t', '-f', 'NAME,DEVICE', 'con', 'show', '--active'])
        for line in out.splitlines():
            name, dev = line.split(':', 1)
            if dev == ifname:
                logging.debug(f"Active connection on {ifname}: {name}")
                return name
        return ""

    def get_status(self, ifname: str = None) -> dict:
        ifname = ifname or self.ifname
        conn = self.get_active_connection(ifname)
        if conn:
            details = run_cmd(['nmcli', '-t', '-f', '802-11-wireless.mode,802-11-wireless.ssid', 'con', 'show', conn])
            mode = ssid = ""
            for line in details.splitlines():
                if line.startswith('802-11-wireless.mode:'):
                    mode = line.split(':', 1)[1]
                elif line.startswith('802-11-wireless.ssid:'):
                    ssid = line.split(':', 1)[1]
            role = 'client' if 'infrastructure' in mode else 'ap'
            logging.debug(f"Status for {ifname}: role={role}, ssid={ssid}")
            return {'role': role, 'ssid': ssid}
        logging.debug(f"Status for {ifname}: idle")
        return {'role': 'idle', 'ssid': ''}

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
            status = self.get_status()
            if status['role'] == 'idle':
                ssid, psk = self.load_credentials(self.ifname)
                if ssid and psk:
                    logging.info(f"Reconnecting to {ssid} on {self.ifname}")
                    self.connect(self.ifname, ssid, psk)
            time.sleep(60)
