 or we are the latest version
    verify_user()

    # Main loop
    while True:
        print_header("XDDOS v1 - MAIN MENU")
        print(Fore.CYAN + "1. Free Version")
        print("2. Paid Version")
        print("3. Exit")
        main_choice = input(Fore.CYAN + "\n[?] Select: ").strip()

        if main_choice == "1":
            free_version()
        elif main_choice == "2":
            paid_version()
        elif main_choice == "3":
            clear_screen()
            print(Fore.GREEN + "[*] Goodbye!")
            sys.exit(0)
        else:
            print(Fore.RED + "[!] Invalid option.")
            time.sleep(1)

if __name__ == "__main__":
    try:
        # Show disclaimer once at the very beginning
        clear_screen()
        print(Fore.RED + Style.BRIGHT + """
    ╔══════════════════════════════════════════════════════╗
    ║  ⚠️  DISCLAIMER  ⚠️                                 ║
    ║  This tool is for EDUCATIONAL PURPOSES ONLY.        ║
    ║  You may ONLY test websites you own or have         ║
    ║  explicit permission to test.                       ║
    ║  Misuse is illegal and unethical. The author is     ║
    ║  not responsible for any damage.                    ║
    ╚══════════════════════════════════════════════════════╝
        """)
        confirm = input(Fore.CYAN + "Do you understand and agree? (y/n): ").strip().lower()
        if confirm != 'y':
            print(Fore.RED + "[!] Exiting.")
            sys.exit(0)
        main()
    except KeyboardInterrupt:
        clear_screen()
        print(Fore.YELLOW + "\n[!] Interrupted. Exiting.")
        sys.exit(0)
