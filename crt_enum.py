#!/usr/bin/env python3

import argparse
import json
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request

class Colors:
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

def banner():
    print(f"""
{Colors.CYAN}{Colors.BOLD}

    ▄▖▄▖▄▖  ▖ ▖▄▖▖  ▖▄▖
    ▌ ▙▘▐   ▛▖▌▌▌▛▖▞▌▙▖
    ▙▖▌▌▐ ▄▖▌▝▌▛▌▌▝ ▌▙▖
                   
    CRT_NAME Domain Enumerator - @KamranSaifullahKhan
    https://linkedin.com/in/KamranSaifullah
    https://x.com/deFr0ggy
{Colors.RESET}
""")

def normalize_domain(domain: str) -> str:
    domain = domain.strip().lower()

    if "://" in domain:
        parsed = urllib.parse.urlparse(domain)
        domain = parsed.netloc

    domain = domain.split("/")[0]
    domain = domain.split(":")[0]
    domain = domain.removeprefix("*.")
    domain = domain.strip(".")

    return domain


def is_valid_domain(domain: str) -> bool:
    if not domain:
        return False

    pattern = r"^(?=.{1,253}$)(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"

    return bool(re.match(pattern, domain))


def build_ssl_context(insecure: bool = False, cacert: str | None = None) -> ssl.SSLContext:

    if insecure:
        print(
            f"{Colors.YELLOW}[!] HTTPS certificate "
            f"verification disabled{Colors.RESET}"
        )
        return ssl._create_unverified_context()

    if cacert:
        return ssl.create_default_context(cafile=cacert)

    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def fetch_crt_data(
    domain: str,
    insecure: bool = False,
    cacert: str | None = None
) -> str:

    url = (
        "https://crt.name/v1/search?apex="
        + urllib.parse.quote(domain, safe="")
    )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "CRT-Domain-Enumerator/1.0"
        },
    )

    ssl_context = build_ssl_context(insecure=insecure, cacert=cacert)

    with urllib.request.urlopen(
        request,
        timeout=30,
        context=ssl_context
    ) as response:
        return response.read().decode("utf-8")


def extract_domains(data: str, domain: str) -> set[str]:

    domains = set()

    try:
        parsed = json.loads(data)

        def extract(value):
            if isinstance(value, str):
                matches = re.findall(
                    r"(?:\*\.)?(?:[a-zA-Z0-9-]+\.)+"
                    r"[a-zA-Z]{2,}",
                    value
                )
                for item in matches:
                    domains.add(item)
            elif isinstance(value, list):
                for item in value:
                    extract(item)
            elif isinstance(value, dict):
                for item in value.values():
                    extract(item)

        extract(parsed)

    except json.JSONDecodeError:
        for line in data.splitlines():
            line = line.strip()
            if not line:
                continue
            first_field = line.split()[0]
            domains.add(first_field)

    cleaned = set()
    suffix = "." + domain

    for item in domains:
        item = item.strip().lower()
        item = item.removeprefix("*.")
        item = item.strip(".")
        item = re.sub(r"^https?://", "", item)
        item = item.split("/")[0]

        if item == domain or item.endswith(suffix):
            cleaned.add(item)

    return cleaned


def save_results(domains: list[str], filename: str):
    try:
        with open(filename, "w", encoding="utf-8") as output:
            for domain in domains:
                output.write(domain + "\n")
    except OSError as error:
        print(
            f"{Colors.RED}"
            f"[!] Unable to write output file: {error}"
            f"{Colors.RESET}"
        )
        return False
    return True


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Enumerate domains/subdomains using "
            "Certificate Transparency logs."
        )
    )

    parser.add_argument("domain", nargs="?", help="Target domain, e.g. example.com")
    parser.add_argument("-o", "--output", metavar="FILE", help="Save discovered domains to FILE")
    parser.add_argument("--insecure", action="store_true", help="Disable HTTPS certificate verification (last resort - use --cacert instead if possible)")
    parser.add_argument("--cacert", metavar="FILE", help="Path to a custom/corporate CA bundle (.pem) to trust, e.g. for TLS-inspecting proxies")
    parser.add_argument("-q", "--quiet", action="store_true", help="Only print discovered domains")

    args = parser.parse_args()

    if not args.quiet:
        banner()

    domain = args.domain

    if not domain:
        try:
            domain = input(f"{Colors.YELLOW}[?] Enter domain: {Colors.RESET}")
        except KeyboardInterrupt:
            print()
            sys.exit(0)

    domain = normalize_domain(domain)

    if not is_valid_domain(domain):
        print(f"{Colors.RED}[!] Invalid domain: {domain}{Colors.RESET}")
        sys.exit(1)

    if not args.quiet:
        print(f"{Colors.CYAN}[+] Target: {Colors.RESET}{domain}")
        print(f"{Colors.CYAN}[+] Querying Certificate Transparency logs...{Colors.RESET}\n")

    try:
        data = fetch_crt_data(domain, insecure=args.insecure, cacert=args.cacert)
    except urllib.error.HTTPError as error:
        print(f"{Colors.RED}[!] HTTP error: {error.code} {error.reason}{Colors.RESET}")
        sys.exit(1)
    except urllib.error.URLError as error:
        reason = error.reason
        if isinstance(reason, ssl.SSLCertVerificationError) or (
            isinstance(reason, ssl.SSLError) and "CERTIFICATE_VERIFY_FAILED" in str(reason)
        ):
            print(f"{Colors.RED}[!] SSL certificate verification failed: {reason}{Colors.RESET}")
            print(
                f"{Colors.YELLOW}[!] This usually means either your local CA "
                f"bundle is missing/stale, or you're behind a TLS-inspecting "
                f"proxy (common on corporate networks).{Colors.RESET}"
            )
            print(
                f"{Colors.YELLOW}    - Try: pip install certifi{Colors.RESET}"
            )
            print(
                f"{Colors.YELLOW}    - If on a corporate proxy: "
                f"--cacert /path/to/corp-root-ca.pem{Colors.RESET}"
            )
            print(
                f"{Colors.YELLOW}    - Last resort (not recommended): "
                f"--insecure{Colors.RESET}"
            )
        else:
            print(f"{Colors.RED}[!] Connection error: {reason}{Colors.RESET}")
        sys.exit(1)
    except Exception as error:
        print(f"{Colors.RED}[!] Error: {error}{Colors.RESET}")
        sys.exit(1)

    domains = extract_domains(data, domain)

    if not domains:
        print(f"{Colors.YELLOW}[!] No domains found.{Colors.RESET}")
        sys.exit(0)

    sorted_domains = sorted(domains, key=lambda x: (x.count("."), x))

    for subdomain in sorted_domains:
        if args.quiet:
            print(subdomain)
        else:
            print(f"{Colors.GREEN}[+] {subdomain}{Colors.RESET}")

    if args.output:
        success = save_results(sorted_domains, args.output)
        if success and not args.quiet:
            print(f"\n{Colors.GREEN}[+] Results saved to: {args.output}{Colors.RESET}")

    if not args.quiet:
        print(f"\n{Colors.CYAN}{Colors.BOLD}[+] Found {len(sorted_domains)} unique domain(s).{Colors.RESET}")


if __name__ == "__main__":
    main()