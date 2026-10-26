#!/usr/bin/env python3
"""
EDITH Tactical AI OS - Kali Linux Native Bridge Daemon
Allows EDITH to execute commands, perform offensive/defensive assessments,
and access local system tools on your Kali Linux machine.
"""

import sys
import os
import time
import json
import socket
import platform
import subprocess
import argparse
import urllib.request
import urllib.error

VERSION = "1.0.0-kali"

KNOWN_TOOLS = [
    "nmap", "nikto", "sqlmap", "wireshark", "burpsuite",
    "hydra", "john", "hashcat", "aircrack-ng", "msfconsole",
    "gobuster", "dirb", "netdiscover", "arp-scan", "tshark"
]

def detect_tools():
    available = []
    for tool in KNOWN_TOOLS:
        ret = subprocess.call(["which", tool], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if ret == 0:
            available.append(tool)
    return available

def get_system_info():
    hostname = socket.gethostname()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = "127.0.0.1"

    os_release = "Kali Linux"
    if os.path.exists("/etc/os-release"):
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        os_release = line.split("=")[1].strip().strip('"')
                        break
        except Exception:
            pass

    return {
        "hostname": hostname,
        "osRelease": os_release,
        "kernel": platform.release(),
        "ipAddress": ip,
        "installedTools": detect_tools(),
    }

def main():
    parser = argparse.ArgumentParser(description="EDITH Kali Linux System Bridge Daemon")
    parser.add_argument("--server", default="http://localhost:3000", help="EDITH AI OS Server URL")
    parser.add_argument("--secret", default="edith-kali-secret", help="Authorization secret key")
    args = parser.parse_args()

    server_url = args.server.rstrip("/")
    agent_id = f"kali-{socket.gethostname()}-{int(time.time())}"

    print("=" * 60)
    print(" [EDITH] Kali Linux Bridge Daemon Initializing...")
    print(f" Target Server : {server_url}")
    print(f" Agent ID      : {agent_id}")
    print("=" * 60)

    sys_info = get_system_info()
    sys_info["agentId"] = agent_id

    # Register with server
    reg_payload = json.dumps(sys_info).encode("utf-8")
    try:
        req = urllib.request.Request(
            f"{server_url}/api/kali/register",
            data=reg_payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            print("[+] Successfully registered with EDITH AI OS!")
            print(f"[+] Detected {len(sys_info['installedTools'])} Kali tools: {', '.join(sys_info['installedTools'][:6])}...")
    except Exception as e:
        print(f"[-] Registration failed: {e}")
        print("[-] Ensure EDITH server is running and accessible.")
        sys.exit(1)

    print("[*] Listening for tactical commands from EDITH... Press Ctrl+C to stop.")

    last_heartbeat = 0

    while True:
        try:
            now = time.time()
            if now - last_heartbeat > 10:
                hb_req = urllib.request.Request(
                    f"{server_url}/api/kali/heartbeat",
                    data=json.dumps({"agentId": agent_id}).encode(),
                    headers={"Content-Type": "application/json"}
                )
                try:
                    urllib.request.urlopen(hb_req, timeout=5)
                except Exception:
                    pass
                last_heartbeat = now

            # Poll for queued command
            poll_req = urllib.request.Request(
                f"{server_url}/api/kali/poll?agentId={agent_id}",
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(poll_req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                job = data.get("job")
                if job:
                    job_id = job["id"]
                    cmd = job["command"]
                    print(f"\n[>] Executing command from EDITH: {cmd}")

                    try:
                        proc = subprocess.Popen(
                            cmd,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True,
                            executable="/bin/bash"
                        )
                        output, _ = proc.communicate(timeout=60)
                        exit_code = proc.returncode
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        output = "[ERROR] Command timed out after 60 seconds."
                        exit_code = 124
                    except Exception as err:
                        output = f"[ERROR] Failed to execute: {err}"
                        exit_code = 1

                    print(f"[<] Exit code: {exit_code} (Output length: {len(output)} bytes)")

                    # Report result back
                    res_payload = json.dumps({
                        "jobId": job_id,
                        "output": output,
                        "exitCode": exit_code
                    }).encode("utf-8")

                    res_req = urllib.request.Request(
                        f"{server_url}/api/kali/result",
                        data=res_payload,
                        headers={"Content-Type": "application/json"}
                    )
                    urllib.request.urlopen(res_req, timeout=10)

            time.sleep(1.5)
        except KeyboardInterrupt:
            print("\n[*] Stopping EDITH Kali Bridge Daemon. Goodbye Commander.")
            break
        except Exception as e:
            time.sleep(3)

if __name__ == "__main__":
    main()
