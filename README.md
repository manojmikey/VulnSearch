# 🔍 project-vulnsearch

An automated reconnaissance and content discovery pipeline for bug bounty hunters and penetration testers. Given a target domain, it chains together industry-standard tools to enumerate subdomains, probe live hosts, crawl endpoints, and extract parameters — all with a single command.

---

## 🚀 What It Does

| Phase | Description |
|-------|-------------|
| **Phase 1 — Smart Reconnaissance** | Subdomain enumeration via `subfinder` + `assetfinder`, DNS resolution via `dnsx`, live host probing via `httpx` |
| **Phase 2 — Content Discovery** | Historical URL mining via `waybackurls`, deep crawl via `katana`, JS file probing via `httpx`, parameter discovery via `arjun` |

---

## 📋 Prerequisites

### Python
- Python 3.8+

### External Tools (must be installed and in `$PATH`)

| Tool | Install |
|------|---------|
| [subfinder](https://github.com/projectdiscovery/subfinder) | `go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest` |
| [assetfinder](https://github.com/tomnomnom/assetfinder) | `go install github.com/tomnomnom/assetfinder@latest` |
| [dnsx](https://github.com/projectdiscovery/dnsx) | `go install github.com/projectdiscovery/dnsx/cmd/dnsx@latest` |
| [httpx](https://github.com/projectdiscovery/httpx) | `go install github.com/projectdiscovery/httpx/cmd/httpx@latest` |
| [waybackurls](https://github.com/tomnomnom/waybackurls) | `go install github.com/tomnomnom/waybackurls@latest` |
| [katana](https://github.com/projectdiscovery/katana) | `go install github.com/projectdiscovery/katana/cmd/katana@latest` |
| [arjun](https://github.com/s0md3v/Arjun) | `pip install arjun` |

> **Tip:** All Go-based tools require Go 1.21+. Make sure `$GOPATH/bin` is in your `$PATH`.

---

## 📦 Installation

```bash
git clone https://github.com/yourusername/project-vulnsearch.git
cd project-vulnsearch
```

No Python dependencies beyond the standard library are required.

---

## ⚙️ Usage

```bash
python3 main.py
```

You will be prompted to enter the target domain:

```
Enter the domain name you want to scan: example.com
```

The tool validates the domain format before proceeding. Use bare domains only — no `https://` prefix:

```
✅  example.com          ← correct
❌  https://example.com  ← incorrect
```

---

## 📁 Output Files

After a full run, the following files are created in your working directory:

| File | Contents |
|------|----------|
| `subfinder.txt` | Raw subdomains from subfinder |
| `amass.txt` | Raw subdomains from assetfinder |
| `all_subs.txt` | Combined, deduplicated subdomain list |
| `resolved_subs.txt` | DNS-resolved subdomains (raw dnsx output) |
| `clean_subs.txt` | Clean hostnames extracted from dnsx output |
| `live_sites.txt` | Live hosts with status codes and tech stack |
| `clean_live_urls.txt` | Plain URLs extracted from live_sites.txt |
| `live_domains.txt` | All live domains (one per line) |
| `urls.txt` | Historical URLs from the Wayback Machine |
| `live_js.txt` | Live JS files returning HTTP 200 |
| `katana_urls.txt` | URLs discovered by the katana crawler |
| `params.txt` | URLs containing query parameters |
| `arjun_results.txt` | Discovered parameters per endpoint |
| `quality_js.txt` | Top 100 deduplicated JS targets |

---

## ⚠️ Known Limitations & Expected Behaviours

These are not bugs — they are expected behaviours based on real-world testing against large targets.

### No JS files found (`live_js.txt` / `quality_js.txt` empty)
The JS probe (Phase 2, Step 2) looks for `.js` URLs inside `urls.txt`, which is populated by `waybackurls`. If the Wayback Machine has no `.js` entries indexed for the target, this step is skipped automatically. This is expected on some targets and is **not a bug**.

### katana timeout / no results
By default, katana crawls with depth `3` and a 600-second timeout. On large targets with 300+ live URLs, this can still time out. If you see:
```
⏱  Timeout: katana ...
katana returned no results.
```
Open `content_discovery.py` and reduce `KATANA_DEPTH` (e.g. from `3` to `2`) at the top of the file:
```python
KATANA_DEPTH = 2   # lower = faster, less thorough
```

### arjun non-zero exit code
arjun frequently exits with a non-zero return code **even when it successfully finds parameters**. The warning in the output is expected:
```
⚠️  arjun exited with non-zero code (this is normal — check arjun_results.txt manually)
```
Always inspect `arjun_results.txt` directly regardless of the exit message.

### `quality_js.txt` empty
This file is built from JS URLs found in both `urls.txt` (waybackurls) and `katana_urls.txt` (katana). If both are empty of JS entries, `quality_js.txt` will be empty too. This is downstream of the two points above.

---

## 🛠️ Tuning Parameters

You can adjust these constants at the top of `content_discovery.py` to tune performance vs. thoroughness:

| Constant | Default | Description |
|----------|---------|-------------|
| `KATANA_DEPTH` | `3` | Crawl depth — reduce to `2` for large targets |
| `KATANA_TIMEOUT` | `600` | Seconds before katana is killed |
| `WAYBACK_TIMEOUT` | `300` | Seconds per root domain for waybackurls |
| `HTTPX_TIMEOUT` | `300` | Seconds for JS probing pass |
| `ARJUN_TIMEOUT` | `300` | Seconds for arjun parameter discovery |
| `QUALITY_JS_LIMIT` | `100` | Max JS URLs written to quality_js.txt |

---

## 🗂️ Project Structure

```
project-vulnsearch/
├── main.py                   # Entry point — orchestrates Phase 1 & 2
├── smart_reconnaissance.py   # Phase 1: subdomain enum, DNS resolution, live probing
├── content_discovery.py      # Phase 2: URL mining, crawling, param discovery
└── README.md
```

---

## 🔐 Legal Disclaimer

This tool is intended for **authorized security testing only**. Only run it against domains you own or have explicit written permission to test. Unauthorized scanning may violate the Computer Fraud and Abuse Act (CFAA) and equivalent laws in your jurisdiction.

---

## 🤝 Contributing

Pull requests are welcome. For major changes, open an issue first to discuss what you'd like to change.

---

## 📄 License

MIT
