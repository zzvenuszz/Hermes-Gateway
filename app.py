#!/usr/bin/env python3
"""
Hermes Gateway - Container Server Management Dashboard Orchestrator
Integrates Cockpit source code (https://github.com/cockpit-project/cockpit.git)
and 45Drives Cockpit Navigator File Manager
and serves the management dashboard inside Docker on port 7860.
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

COCKPIT_REPO = "https://github.com/cockpit-project/cockpit.git"
COCKPIT_SRC_DIR = "/opt/cockpit-src"
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
PORT = int(os.getenv("PORT", "7860"))

def setup_cockpit_repo():
    """Ensure Cockpit source repository is cloned and integrated."""
    logger.info(f"Checking Cockpit repository at {COCKPIT_SRC_DIR}...")
    if not os.path.exists(COCKPIT_SRC_DIR):
        logger.info(f"Cloning Cockpit source code from {COCKPIT_REPO}...")
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", COCKPIT_REPO, COCKPIT_SRC_DIR],
                check=True,
                capture_output=True,
                text=True
            )
            logger.info("Cockpit source code successfully cloned.")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to clone Cockpit repo: {e.stderr}. Proceeding with system package assets.")
    else:
        logger.info("Cockpit repository directory already present.")

def setup_cockpit_plugins():
    """Configure Cockpit plugins and file manager for container environment."""
    # 1. Remove incompatible cockpit-files if present
    files_dir = "/usr/share/cockpit/files"
    if os.path.exists(files_dir):
        shutil.rmtree(files_dir, ignore_errors=True)

    # 2. Patch systemd manifest: keep 'index' (Overview/System Info/Metrics/Terminal), remove ONLY 'services' menu
    sys_manifest = "/usr/share/cockpit/systemd/manifest.json"
    if os.path.exists(sys_manifest):
        try:
            with open(sys_manifest, "r") as f:
                data = json.load(f)
            if "menu" in data and "services" in data["menu"]:
                del data["menu"]["services"]
                logger.info("Removed broken Services menu from systemd manifest while preserving Overview & System Info.")
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
            logger.info("Cockpit Navigator configured as primary 'File Manager'.")
        except Exception as e:
            logger.warning(f"Could not update Navigator manifest: {e}")

def setup_container_user():
    """Create and configure container admin user for Cockpit access."""
    logger.info(f"Configuring container user '{ADMIN_USER}'...")
    
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

    # Ensure sudo without password inside container
    sudoers_file = f"/etc/sudoers.d/{ADMIN_USER}"
    with open(sudoers_file, "w") as f:
        f.write(f"{ADMIN_USER} ALL=(ALL) NOPASSWD:ALL\n")
    os.chmod(sudoers_file, 0o440)

def setup_ssh():
    """Setup SSH daemon inside container for Cockpit local bridge authentication."""
    logger.info("Setting up SSH daemon inside container...")
    os.makedirs("/run/sshd", exist_ok=True)
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
    subprocess.Popen(["/usr/sbin/sshd", "-D", "-e", "-p", "22"])
    logger.info("SSH daemon started on port 2222.")

def start_cockpit_ws():
    """Start Cockpit Web Service listening on 0.0.0.0:7860."""
    logger.info(f"Starting Cockpit Web Service on 0.0.0.0:{PORT}...")
    
    # Copy cockpit.conf if available
    conf_src = "/app/cockpit.conf"
    conf_dst = "/etc/cockpit/cockpit.conf"
    os.makedirs("/etc/cockpit", exist_ok=True)
    if os.path.exists(conf_src):
        subprocess.run(["cp", conf_src, conf_dst], check=False)

    cockpit_ws_bin = "/usr/lib/cockpit/cockpit-ws"
    if not os.path.exists(cockpit_ws_bin):
        cockpit_ws_bin = "cockpit-ws"

    cmd = [
        cockpit_ws_bin,
        "--no-tls",
        f"--port={PORT}",
        "--address=0.0.0.0"
    ]

    logger.info(f"Executing: {' '.join(cmd)}")
    process = subprocess.Popen(cmd)
    return process

def main():
    logger.info("=== Starting Hermes Gateway Container Server Manager ===")
    setup_cockpit_repo()
    setup_cockpit_plugins()
    setup_container_user()
    setup_ssh()
    
    proc = start_cockpit_ws()
    logger.info(f"Cockpit Server Management Dashboard active on port {PORT}.")
    logger.info(f"Default Login -> User: {ADMIN_USER} | Password: {ADMIN_PASSWORD}")
    
    try:
        proc.wait()
    except KeyboardInterrupt:
        logger.info("Shutting down services...")
        proc.terminate()

if __name__ == "__main__":
    main()
