import json
import os
from utils.cmd import run_cmd

CRED_FILE = '/home/minicp/wifi_credentials.json'

class WifiManager:
    def list_adapters(self) -> list[str]:
        out = run_cmd(['nmcli', '-t', '-f', 'DEVICE,TYPE', 'device'])
        return [line.split(':')[0]
                for line in out.splitlines()
                if line.endswith(':wifi')]

    def scan_networks(self, ifname: str) -> list[str]:
        out = run_cmd(
            ['nmcli', '-t', '-f', 'SSID', 'device', 'wifi', 'list', 'ifname', ifname],
            timeout=10
        )
        return sorted({ssid.strip() for ssid in out.splitlines() if ssid.strip()})

    def connect(self, ifname: str, ssid: str, psk: str) -> tuple[bool, str]:
        run_cmd(['nmcli', 'con', 'delete', ssid], timeout=5)
        out = run_cmd([
            'nmcli', 'con', 'add', 'type', 'wifi',
            'ifname', ifname, 'con-name', ssid, 'ssid', ssid,
            'wifi-sec.key-mgmt', 'wpa-psk', 'wifi-sec.psk', psk
        ], timeout=15)
        if "Error" in out or not out:
            return False, out

        out2 = run_cmd(['nmcli', 'con', 'up', 'id', ssid, 'ifname', ifname], timeout=15)
        if "Error" in out2:
            return False, out2

        self.save_credentials(ifname, ssid, psk)
        return True, ""

    def disconnect(self, ifname: str) -> None:
        active = self.get_active_connection(ifname)
        if active:
            run_cmd(['nmcli', 'con', 'down', 'id', active], timeout=5)

    def get_active_connection(self, ifname: str) -> str:
        out = run_cmd(['nmcli', '-t', '-f', 'NAME,DEVICE', 'con', 'show', '--active'])
        for line in out.splitlines():
            name, dev = line.split(':', 1)
            if dev == ifname:
                return name
        return ""

    def get_status(self) -> dict[str, dict]:
        status = {}
        for ifname in self.list_adapters():
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
                status[ifname] = {'role': role, 'ssid': ssid}
            else:
                status[ifname] = {'role': 'idle', 'ssid': ''}
        return status

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
