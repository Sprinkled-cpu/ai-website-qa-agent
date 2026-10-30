import subprocess
import re
import time
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def run_tunnel():
    cmd = [
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=NUL",
        "-o", "ServerAliveInterval=15",
        "-o", "ServerAliveCountMax=120",
        "-R", "80:127.0.0.1:8000",
        "nokey@localhost.run"
    ]

    while True:
        try:
            print("Starting persistent SSH tunnel with keep-alive heartbeat...", flush=True)
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1
            )

            current_url = None

            for line in proc.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()
                match = re.search(r"https://[a-zA-Z0-9\-\.]+\.lhr\.life", line)
                if match:
                    current_url = match.group(0)
                    print(f"\n==========================================", flush=True)
                    print(f"ACTIVE PUBLIC URL: {current_url}", flush=True)
                    print(f"==========================================\n", flush=True)
                    with open("live_url.txt", "w", encoding="utf-8") as f:
                        f.write(current_url.strip())

            proc.wait()
            print("Tunnel connection dropped. Reconnecting in 3 seconds...", flush=True)
            time.sleep(3)
        except Exception as e:
            print(f"Tunnel runner exception: {e}. Retrying in 5 seconds...", flush=True)
            time.sleep(5)

if __name__ == "__main__":
    run_tunnel()
