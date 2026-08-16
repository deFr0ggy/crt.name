#!/usr/bin/env bash
# Kamran Saifullah Khan

set -u

CYAN='\033[96m'
BOLD='\033[1m'
RESET='\033[0m'

banner() {
    printf "%b" "${CYAN}${BOLD}"
    cat << 'EOF'
    ▄▖▄▖▄▖  ▖ ▖▄▖▖  ▖▄▖
    ▌ ▙▘▐   ▛▖▌▌▌▛▖▞▌▙▖
    ▙▖▌▌▐ ▄▖▌▝▌▛▌▌▝ ▌▙▖

    CRT_NAME Domain Enumerator - @KamranSaifullahKhan
    https://linkedin.com/in/KamranSaifullah
    https://x.com/deFr0ggy
EOF
    printf "%b\n" "${RESET}"
}

usage() {
    echo "Usage: $0 <domain> [-o output_file]"
    echo
    echo "Examples:"
    echo "  $0 example.com"
    echo "  $0 example.com -o domains.txt"
    exit 1
}

DOMAIN=""
OUTPUT_FILE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -o|--output)
            [[ $# -lt 2 ]] && usage
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        -*)
            echo "[!] Unknown option: $1"
            usage
            ;;
        *)
            if [[ -z "$DOMAIN" ]]; then
                DOMAIN="$1"
            else
                echo "[!] Multiple domains specified."
                usage
            fi
            shift
            ;;
    esac
done

[[ -z "$DOMAIN" ]] && usage

banner

DOMAIN="${DOMAIN#http://}"
DOMAIN="${DOMAIN#https://}"
DOMAIN="${DOMAIN%%/*}"

echo "[+] Searching Certificate Transparency logs for: $DOMAIN"
echo

if [[ -n "$OUTPUT_FILE" ]]; then
    : > "$OUTPUT_FILE"
fi

curl -fsSL "https://crt.name/v1/search?apex=${DOMAIN}" |
    awk '{print $1}' |
    sort -u |
    while IFS= read -r subdomain; do

        [[ -z "$subdomain" ]] && continue

        echo "$subdomain"

        if [[ -n "$OUTPUT_FILE" ]]; then
            echo "$subdomain" >> "$OUTPUT_FILE"
        fi
    done

if [[ -n "$OUTPUT_FILE" ]]; then
    echo
    echo "[+] Results saved to: $OUTPUT_FILE"
fi