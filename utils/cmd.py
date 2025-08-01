import subprocess

def run_cmd(cmd, timeout=None):
    """Run a shell command safely, return stdout or combined stderr, never hang."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True
        )
        return result.stdout
    except subprocess.TimeoutExpired:
        return ""
    except subprocess.CalledProcessError as e:
        return (e.stdout or "") + (e.stderr or "")
