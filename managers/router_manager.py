import json
import os
import logging
from utils.cmd import run_cmd

# Setup logging
logging.basicConfig(filename='/home/minicp/.config/minicp/router_manager.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s: %(message)s')

CRED_FILE = '/home/minicp/.config/minicp/ap_credentials.json'

class RouterManager:
    def __init__(self, ifname: str = "wlan1"):
        self.ifname = ifname

    def start_ap(self, ssid: str, psk: str, channel: int = 6) -> tuple[bool, str]:
        logging.info(f"Starting AP on {self.ifname} with SSID {ssid}")
        if not ssid:
            logging.error("SSID cannot be empty")
            return False, "SSID cannot be empty"
        if len(psk) < 8:
            logging.error("Password too short")
            return False, "Password must be at least 8 characters"
        conn_name = f"Hotspot_{self.ifname}"
        run_cmd(['nmcli', 'con', 'delete', conn_name], timeout=5)
        out = run_cmd([
            'nmcli', 'con', 'add', 'type', 'wifi', 'ifname', self.ifname,
            'con-name', conn_name, 'ssid', ssid,
            'autoconnect', 'yes', 'wifi-sec.key-mgmt', 'wpa-psk',
            'wifi-sec.psk', psk, 'wifi.mode', 'ap',
            'wifi.channel', str(channel),
            'ipv4.method', 'shared', 'ipv4.addresses', '192.168.4.1/24'
        ], timeout=15)
        if "Error" in out or not out:
            logging.error(f"AP setup failed: {out}")
            return False, out
        out2 = run_cmd(['nmcli', 'con', 'up', conn_name], timeout=15)
        if "Error" in out2:
            logging.error(f"AP activation failed: {out2}")
            return False, out2
        self.save_credentials(self.ifname, ssid, psk)
        self.enable_internet_sharing()
        logging.info("AP started successfully")
        return True, ""

    def stop_ap(self) -> None:
        logging.info(f"Stopping AP on {self.ifname}")
        conn_name = f"Hotspot_{self.ifname}"
        run_cmd(['nmcli', 'con', 'down', conn_name], timeout=5)
        run_cmd(['nmcli', 'con', 'delete', conn_name], timeout=5)
        logging.info("AP stopped")

    def is_running(self) -> bool:
        conn_name = f"Hotspot_{self.ifname}"
        out = run_cmd(['nmcli', '-t', '-f', 'NAME,DEVICE', 'con', 'show', '--active'])
        running = any(
            line.split(':', 1)[0] == conn_name and line.split(':', 1)[1] == self.ifname
            for line in out.splitlines()
        )
        logging.debug(f"AP running check for {self.ifname}: {running}")
        return running

    def list_connected_devices(self) -> list[dict]:
        logging.debug(f"Listing devices on {self.ifname}")
        out = run_cmd(['arp', '-n', '-i', self.ifname])
        devices = []
        for line in out.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 3:
                devices.append({'ip': parts[0], 'mac': parts[2]})
        logging.debug(f"Found devices: {devices}")
        return devices

    def enable_internet_sharing(self, client_ifname: str = "wlan0"):
        logging.info(f"Enabling internet sharing from {client_ifname} to {self.ifname}")
        run_cmd(['sysctl', '-w', 'net.ipv4.ip_forward=1'])
        run_cmd(['iptables', '-t', 'nat', '-A', 'POSTROUTING', '-o', client_ifname, '-j', 'MASQUERADE'])
        run_cmd(['iptables', '-A', 'FORWARD', '-i', self.ifname, '-o', client_ifname, '-j', 'ACCEPT'])
        run_cmd(['iptables', '-A', 'FORWARD', '-i', client_ifname, '-o', self.ifname, '-m', 'state', '--state', 'RELATED,ESTABLISHED', '-j', 'ACCEPT'])
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
