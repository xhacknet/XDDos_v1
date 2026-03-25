e = input(Fore.CYAN + "[?] Select: ").strip()

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
