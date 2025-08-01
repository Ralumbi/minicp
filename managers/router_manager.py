import json
import os
from utils.cmd import run_cmd

CRED_FILE = '/home/minicp/ap_credentials.json'

class RouterManager:
    def start_ap(self, ifname: str, ssid: str, psk: str) -> tuple[bool, str]:
        conn_name = f"Hotspot_{ifname}"
        run_cmd(['nmcli', 'con', 'delete', conn_name], timeout=5)
        out = run_cmd([
            'nmcli', 'device', 'wifi', 'hotspot',
            'ifname', ifname,
            'con-name', conn_name,
            'ssid', ssid,
            'password', psk
        ], timeout=15)
        if "Error" in out:
            return False, out

        self.save_credentials(ifname, ssid, psk)
        return True, ""

    def stop_ap(self, ifname: str) -> None:
        conn_name = f"Hotspot_{ifname}"
        run_cmd(['nmcli', 'con', 'down', conn_name], timeout=5)
        run_cmd(['nmcli', 'con', 'delete', conn_name], timeout=5)

    def is_running(self, ifname: str) -> bool:
        conn_name = f"Hotspot_{ifname}"
        out = run_cmd(['nmcli', '-t', '-f', 'NAME,DEVICE', 'con', 'show', '--active'])
        return any(
            line.split(':', 1)[0] == conn_name and line.split(':', 1)[1] == ifname
            for line in out.splitlines()
        )

    def _load_credentials(self) -> dict:
        if os.path.exists(CRED_FILE):
            with open(CRED_FILE, 'r') as f:
                return json.load(f)
        return {}

    def _save_credentials(self, data: dict):
        os.makedirs(os.path.dirname(CRED_FILE), exist_ok=True)
        with open(CRED_FILE, 'w') as f:
            json.dump(data, f)

    def save_credentials(self, ifname: str, ssid: str, psk: str):
        creds = self._load_credentials()
        creds[ifname] = {'ssid': ssid, 'psk': psk}
        self._save_credentials(creds)

    def load_credentials(self, ifname: str) -> tuple[str, str]:
        creds = self._load_credentials()
        return (
            creds.get(ifname, {}).get('ssid', ''),
            creds.get(ifname, {}).get('psk', '')
        )