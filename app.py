#!/usr/bin/env python3
"""
Hermes Gateway - Container Server Management Dashboard Orchestrator
Serves Cockpit management dashboard inside Docker on port 7860.
"""

import os
import sys
import time
import json
import shutil
import subprocess
import threading
import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("HermesGateway")

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
PORT = int(os.getenv("PORT", "7860"))

def setup_cockpit_plugins():
    """Configure Cockpit plugins and file manager for container environment."""
    logger.info("Configuring Cockpit plugins...")
    
    # 1. Remove incompatible cockpit-files if present
    files_dir = "/usr/share/cockpit/files"
    if os.path.exists(files_dir):
        shutil.rmtree(files_dir, ignore_errors=True)

    # 2. Patch systemd manifest: keep 'index', remove 'services' menu
    sys_manifest = "/usr/share/cockpit/systemd/manifest.json"
    if os.path.exists(sys_manifest):
        try:
            with open(sys_manifest, "r") as f:
                data = json.load(f)
            if "menu" in data and "services" in data["menu"]:
                del data["menu"]["services"]
                logger.info("Removed Services menu from systemd manifest.")
            with open(sys_manifest, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.warning(f"Could not update systemd manifest: {e}")

    # 3. Configure Cockpit Navigator menu label
    nav_manifest = "/usr/share/cockpit/navigator/manifest.json"
    if os.path.exists(nav_manifest):
        try:
            with open(nav_manifest, "r") as f:
                data = json.load(f)
            if "menu" in data and "navigator" in data["menu"]:
                data["menu"]["navigator"]["label"] = "File Manager"
                data["menu"]["navigator"]["order"] = 10
            with open(nav_manifest, "w") as f:
                json.dump(data, f, indent=4)
            logger.info("Cockpit Navigator configured as 'File Manager'.")
        except Exception as e:
            logger.warning(f"Could not update Navigator manifest: {e}")

def setup_container_user():
    """Create and configure container admin user for Cockpit access."""
    logger.info(f"Configuring container user '{ADMIN_USER}'...")
    try:
        # Create user if not exists
        res = subprocess.run(["id", ADMIN_USER], capture_output=True)
        if res.returncode != 0:
            subprocess.run(["useradd", "-m", "-s", "/bin/bash", "-G", "sudo", ADMIN_USER], check=False)
            logger.info(f"User '{ADMIN_USER}' created.")

        # Set password
        chpasswd_input = f"{ADMIN_USER}:{ADMIN_PASSWORD}\n"
        p = subprocess.Popen(["chpasswd"], stdin=subprocess.PIPE, text=True)
        p.communicate(input=chpasswd_input)
        logger.info(f"Password set for '{ADMIN_USER}'.")

        # Ensure sudoers file
        sudoers_file = f"/etc/sudoers.d/{ADMIN_USER}"
        os.makedirs("/etc/sudoers.d", exist_ok=True)
        with open(sudoers_file, "w") as f:
            f.write(f"{ADMIN_USER} ALL=(ALL) NOPASSWD:ALL\n")
        os.chmod(sudoers_file, 0o440)
    except Exception as e:
        logger.warning(f"Container user setup warning (bypassed if build-time created): {e}")

def setup_ssh():
    """Setup SSH daemon inside container for Cockpit local bridge authentication."""
    logger.info("Setting up SSH daemon inside container...")
    os.makedirs("/run/sshd", exist_ok=True)
    os.makedirs("/var/run/sshd", exist_ok=True)
    subprocess.run(["ssh-keygen", "-A"], capture_output=True)
    
    # Configure sshd_config for container access
    ssh_config = """
Port 22
PermitRootLogin yes
PasswordAuthentication yes
KbdInteractiveAuthentication yes
UsePAM yes
X11Forwarding no
PrintMotd no
"""
    os.makedirs("/etc/ssh/sshd_config.d", exist_ok=True)
    with open("/etc/ssh/sshd_config.d/cockpit.conf", "w") as f:
        f.write(ssh_config)
    
    # Start sshd
    try:
        subprocess.Popen(["/usr/sbin/sshd", "-D", "-e", "-p", "22"])
        logger.info("SSH daemon started on port 22.")
    except Exception as e:
        logger.error(f"Failed to start SSH daemon: {e}")

def start_cockpit_ws():
    """Start Cockpit Web Service listening on 0.0.0.0:PORT."""
    logger.info(f"Starting Cockpit Web Service on 0.0.0.0:{PORT}...")
    
    conf_src = "/app/cockpit.conf"
    conf_dst = "/etc/cockpit/cockpit.conf"
    os.makedirs("/etc/cockpit", exist_ok=True)
    if os.path.exists(conf_src):
        shutil.copy(conf_src, conf_dst)

    cockpit_ws_bin = "/usr/lib/cockpit/cockpit-ws"
    if not os.path.exists(cockpit_ws_bin):
        cockpit_ws_bin = shutil.which("cockpit-ws") or "cockpit-ws"

    cmd = [
        cockpit_ws_bin,
        "--no-tls",
        "-p", str(PORT)
    ]

    logger.info(f"Executing: {' '.join(cmd)}")
    return subprocess.Popen(cmd)

def main():
    logger.info("=== Starting Hermes Gateway Container Server Manager ===")
    setup_cockpit_plugins()
    setup_container_user()
    setup_ssh()
    
    while True:
        proc = start_cockpit_ws()
        logger.info(f"Cockpit Management Dashboard running on port 7860.")
        logger.info(f"Default Login -> User: {ADMIN_USER} | Password: {ADMIN_PASSWORD}")
        
        try:
            exit_code = proc.wait()
            logger.warning(f"cockpit-ws process exited with code {exit_code}. Restarting in 3 seconds...")
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            proc.terminate()
            break
        time.sleep(3)

if __name__ == "__main__":
    main()
