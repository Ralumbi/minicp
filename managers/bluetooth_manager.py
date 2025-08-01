from utils.cmd import run_cmd
import subprocess

class BluetoothManager:
    def _btctl(self, commands: list[str], timeout: int = 10) -> str:
        """
        Run a sequence of bluetoothctl commands in a single session, return combined output.
        """
        proc = subprocess.Popen(
            ['bluetoothctl'], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True
        )
        # send commands then exit
        cmd_str = "\n".join(commands) + "\nexit\n"
        out, err = proc.communicate(cmd_str, timeout=timeout)
        return (out or '') + (err or '')

    def scan(self, duration: int = 10) -> list[tuple[str,str]]:
        # Ensure powered on and agent ready
        run_cmd(['bluetoothctl', 'power', 'on'], timeout=5)
        # Perform scan inside single btctl session
        out = self._btctl([
            'agent on',
            'default-agent',
            'scan on'
        ], timeout=duration)
        # turn off scan
        run_cmd(['bluetoothctl', 'scan', 'off'], timeout=5)

        devices = []
        for line in out.splitlines():
            line = line.strip()
            if line.startswith('Device '):
                parts = line.split(' ', 2)
                mac = parts[1]
                name = parts[2] if len(parts) == 3 else '<unknown>'
                devices.append((mac, name))
        return devices

    def pair(self, mac: str) -> tuple[bool,str]:
        cmds = [
            'agent on',
            'default-agent',
            f'pair {mac}',
            f'trust {mac}'
        ]
        out = self._btctl(cmds, timeout=15)
        if 'Pairing successful' in out or 'already paired' in out:
            return True, ''
        return False, out.strip()

    def connect(self, mac: str) -> tuple[bool,str]:
        """
        Connect to a paired device; handle profile errors.
        """
        out = self._btctl([f'connect {mac}'], timeout=10)
        # Profile unavailable error
        if 'br-connection-profile-unavailable' in out:
            msg = (
                'Connection failed: A2DP profile unavailable. '
                'Install/configure bluealsa or pulseaudio with A2DP support.'
            )
            return False, msg
        # Success indicator
        if 'Connection successful' in out or 'Connected: yes' in out:
            return True, ''
        # Fallback: query info
        info = run_cmd(['bluetoothctl', 'info', mac], timeout=5)
        if 'Connected: yes' in info:
            return True, ''
        return False, (out + '\n' + info).strip()

    def disconnect(self, mac: str) -> tuple[bool,str]:
        out = self._btctl([f'disconnect {mac}'], timeout=5)
        if 'Successful disconnected' in out or 'Disconnected: yes' in out:
            return True, ''
        return False, out.strip()

    def remove(self, mac: str) -> tuple[bool,str]:
        out = self._btctl([f'remove {mac}'], timeout=5)
        if 'Device has been removed' in out:
            return True, ''
        return False, out.strip()

    def get_paired(self) -> list[tuple[str,str]]:
        out = run_cmd(['bluetoothctl', 'paired-devices'], timeout=5)
        paired = []
        for line in out.splitlines():
            if line.startswith('Device '):
                parts = line.split(' ', 2)
                mac = parts[1]
                name = parts[2] if len(parts) == 3 else '<unknown>'
                paired.append((mac, name))
        return paired

    def is_connected(self, mac: str) -> bool:
        out = run_cmd(['bluetoothctl', 'info', mac], timeout=5)
        for line in out.splitlines():
            if line.strip().startswith('Connected:'):
                return line.split(':',1)[1].strip() == 'yes'
        return False