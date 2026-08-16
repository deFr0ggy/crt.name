# crt.name
CRT.NAME is the new entry into which allows the users to perform subdomain enumeration using Certificate Transparency records. The data is quite similar to what is provided by 'CRT.SH' domain. 

However, this repository is all about the scripts, aliases and a simple python script that allows you to perform the subdomain enumerations. 

The simplest command will be as below. 

```
curl -s "https://crt.name/v1/search?apex=<DOMAIN NAME>"| awk '{print $1}' | sort -u
```

## CRT_ENUM (Bash)

A lightweight bash wrapper around the `crt.name` API for quick subdomain enumeration from the command line.

### Usage

`./crt_enum.sh example.com` <br>
`./crt_enum.sh example.com -o domains.txt`


### Options

| Flag | Description |
|------|-------------|
| `domain` | Target domain, e.g. `example.com` (positional, required) |
| `-o`, `--output FILE` | Save discovered domains to `FILE` |
| `-h`, `--help` | Show usage and exit |

### Requirements

- `bash`
- `curl`
- `awk`
- `sort`

## Python Implementation

Similarly to the bash script, you can also utilize the Python3 script to achieve the same.

### Usage

`python3 crtenum.py example.com` <br>
`python3 crtenum.py example.com -o domains.txt` <br>
`python3 crtenum.py example.com -q`


If no domain is passed as an argument, the script will prompt for one interactively.

### Options

| Flag | Description |
|------|-------------|
| `domain` | Target domain, e.g. `example.com` (positional, optional — prompted if omitted) |
| `-o`, `--output FILE` | Save discovered domains to `FILE` |
| `-q`, `--quiet` | Only print discovered domains, no banner or summary output |
| `--cacert FILE` | Path to a custom/corporate CA bundle (`.pem`) — use this if you're behind a TLS-inspecting proxy |
| `--insecure` | Disable HTTPS certificate verification (last resort, not recommended) |

### Requirements

pip install certifi


`certifi` is optional but recommended — the script prefers certifi's CA bundle over the system default, which avoids most `CERTIFICATE_VERIFY_FAILED` errors caused by an incomplete or stale local trust store.
