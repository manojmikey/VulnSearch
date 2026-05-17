import subprocess
import time
import re
from pathlib import Path


DEVNULL = subprocess.DEVNULL

# ── Tuneable constants ────────────────────────────────────────────────────────
KATANA_DEPTH      = 3    # reduce to 2 for very large targets (depth 5 times out on 300+ URLs)
KATANA_TIMEOUT    = 600  # seconds; increase if katana is cut short on slower machines
WAYBACK_TIMEOUT   = 300  # seconds per root domain
HTTPX_TIMEOUT     = 300  # seconds for the JS probe pass
ARJUN_TIMEOUT     = 300  # seconds
QUALITY_JS_LIMIT  = 100  # cap on JS targets sent to the quality list
# ─────────────────────────────────────────────────────────────────────────────


def _run(command, timeout=None, input_text=None):
    """
    Run a command silently. Returns CompletedProcess or None on failure.
    """
    try:
        result = subprocess.run(
            command,
            input=input_text,
            stdout=subprocess.PIPE,
            stderr=DEVNULL,
            text=True,
            timeout=timeout
        )
        return result
    except subprocess.TimeoutExpired:
        print(f"⏱  Timeout: {' '.join(command)}")
    except FileNotFoundError:
        print(f"❌ Tool not found: '{command[0]}'. Is it installed and in PATH?")
    except Exception as e:
        print(f"❌ Error running {command[0]}: {e}")
    return None


def _clean_ansi(text):
    """Strip ANSI color codes from a string."""
    return re.compile(r'\x1b\[[0-9;]*m').sub('', text)


def _extract_plain_urls(live_sites_path):
    """
    live_sites.txt from httpx looks like:
        https://example.com [200] [Title] [Tech]
    with ANSI color codes. Extracts just the plain URL (first token).
    """
    urls = []
    for line in Path(live_sites_path).read_text().splitlines():
        line = _clean_ansi(line).strip()
        if not line:
            continue
        url = line.split()[0]
        if url.startswith("http"):
            urls.append(url)
    return urls


def _extract_domains(urls):
    """Extract bare hostnames from a list of URLs."""
    domains = set()
    for url in urls:
        host = re.sub(r'^https?://', '', url)
        host = host.split('/')[0].split('?')[0].split(':')[0]
        if host:
            domains.add(host)
    return sorted(domains)


def intel_content_discovery(file_path):

    # ------------------------------------------------------------------ #
    # Pre-step: Clean live_sites.txt — extract plain URLs
    # ------------------------------------------------------------------ #
    print("🧹 Cleaning live_sites.txt (stripping ANSI, extracting URLs)...")
    plain_urls = _extract_plain_urls(file_path)

    if not plain_urls:
        print("❌ No valid URLs found in live_sites.txt. Aborting Phase 2.")
        return

    Path("clean_live_urls.txt").write_text('\n'.join(plain_urls) + '\n')
    print(f"✅ {len(plain_urls)} clean URLs extracted → clean_live_urls.txt")

    all_domains = _extract_domains(plain_urls)
    Path("live_domains.txt").write_text('\n'.join(all_domains) + '\n')
    print(f"✅ {len(all_domains)} domains extracted → live_domains.txt")

    # Only use root domains for waybackurls — querying every subdomain is wasteful
    # (Wayback Machine already indexes all subdomains under the root)
    root_domains = sorted(set(
        '.'.join(d.split('.')[-2:]) for d in all_domains
    ))
    print(f"   Using {len(root_domains)} root domain(s) for waybackurls: {root_domains}")

    # ------------------------------------------------------------------ #
    # Step 1: Waybackurls — fetch historical URLs
    # NOTE: Runs only on root domains, not every subdomain.
    # Querying all subdomains individually (e.g. 303 × 60s) would take hours.
    # ------------------------------------------------------------------ #
    print("\n📡 Initiating waybackurls...")
    wstart = time.time()
    all_wayback_urls = set()
    try:
        for root in root_domains:
            print(f"   Fetching wayback URLs for: {root}")
            result = _run(["waybackurls", root], timeout=WAYBACK_TIMEOUT)
            if result and result.stdout.strip():
                found = [l.strip() for l in result.stdout.splitlines() if l.strip()]
                all_wayback_urls.update(found)
                print(f"   ✅ {len(found)} URLs fetched for {root}")
            else:
                print(f"   ⚠️  No results for {root}")

    except KeyboardInterrupt:
        print(f"\n⚠️  waybackurls interrupted — saving {len(all_wayback_urls)} URLs collected so far...")
    except Exception as e:
        print(f"❌ waybackurls error: {e}")
    finally:
        if all_wayback_urls:
            existing = set()
            if Path("urls.txt").exists():
                existing = set(Path("urls.txt").read_text().splitlines())
            new_urls = all_wayback_urls - existing
            with open("urls.txt", "a") as f:
                f.write('\n'.join(sorted(new_urls)) + '\n')
            print(f"✅ waybackurls done in {time.time() - wstart:.2f}s — "
                  f"{len(new_urls)} new URLs saved → urls.txt")
        else:
            print("⚠️  waybackurls returned no results — urls.txt will be empty.")

    # ------------------------------------------------------------------ #
    # Step 2: Extract live JS files via httpx
    # NOTE: This step depends on urls.txt containing .js URLs from waybackurls.
    # If the target has no .js entries in the Wayback Machine, this is skipped.
    # That is expected behaviour, not a bug.
    # ------------------------------------------------------------------ #
    print("\n🔍 Probing JS files with httpx...")
    hstart = time.time()
    try:
        urls_content = Path("urls.txt").read_text() if Path("urls.txt").exists() else ""
        js_urls = [l for l in urls_content.splitlines() if l.strip().endswith(".js")]

        if not js_urls:
            print("⚠️  No .js URLs found in urls.txt — skipping JS probe.")
            print("   ℹ️  This is normal if the Wayback Machine has no JS entries for this target.")
        else:
            js_input = '\n'.join(js_urls) + '\n'
            result = _run(["httpx", "-silent", "-mc", "200"], input_text=js_input, timeout=HTTPX_TIMEOUT)
            if result and result.stdout.strip():
                Path("live_js.txt").write_text(result.stdout)
                count = len(result.stdout.strip().splitlines())
                print(f"✅ JS probing done in {time.time() - hstart:.2f}s — "
                      f"{count} live JS files → live_js.txt")
            else:
                print("⚠️  No live JS files found.")

    except Exception as e:
        print(f"❌ JS probing failed: {e}")

    # ------------------------------------------------------------------ #
    # Step 3: Katana — deep crawl
    # NOTE: katana uses -list flag and does NOT read from stdin.
    # KNOWN ISSUE: On large targets (300+ URLs) with depth 5, katana may time out.
    # If you see a timeout here, reduce KATANA_DEPTH at the top of this file.
    # ------------------------------------------------------------------ #
    print(f"\n🕷️  Initiating katana crawler (depth={KATANA_DEPTH})...")
    kstart = time.time()
    try:
        result = _run(
            ["katana", "-list", "clean_live_urls.txt",
             "-jc", "-aff", "-d", str(KATANA_DEPTH), "-f", "qurl", "-silent"],
            timeout=KATANA_TIMEOUT
        )
        if result and result.stdout.strip():
            katana_urls = sorted(set(result.stdout.strip().splitlines()))
            Path("katana_urls.txt").write_text('\n'.join(katana_urls) + '\n')
            print(f"✅ katana done in {time.time() - kstart:.2f}s — "
                  f"{len(katana_urls)} URLs → katana_urls.txt")
        else:
            print("⚠️  katana returned no results.")
            print("   ℹ️  If it timed out, try reducing KATANA_DEPTH or KATANA_TIMEOUT in this file.")

    except Exception as e:
        print(f"❌ katana step failed: {e}")

    # ------------------------------------------------------------------ #
    # Step 4: Arjun — parameter discovery
    # NOTE: arjun frequently exits with a non-zero code even when it finds results.
    # The warning below is expected — always check arjun_results.txt manually.
    # ------------------------------------------------------------------ #
    print("\n🔧 Initiating arjun (extracting param URLs from urls.txt)...")
    a2start = time.time()
    try:
        urls_content = Path("urls.txt").read_text() if Path("urls.txt").exists() else ""
        param_urls = sorted(set(
            line.strip() for line in urls_content.splitlines()
            if '?' in line and line.strip()
        ))

        if not param_urls:
            print("⚠️  No URLs with query params found in urls.txt — skipping arjun.")
        else:
            Path("params.txt").write_text('\n'.join(param_urls) + '\n')
            print(f"   {len(param_urls)} param URLs written → params.txt")

            proc2 = subprocess.Popen(
                ["arjun", "-i", "params.txt", "-o", "arjun_results.txt",
                 "-t", "50", "--passive", "--disable-redirects", "--timeout", "5", "--stable"],
                stdout=DEVNULL, stderr=DEVNULL
            )
            proc2.communicate(timeout=ARJUN_TIMEOUT)
            if proc2.returncode == 0:
                print(f"✅ arjun done in {time.time() - a2start:.2f}s → arjun_results.txt")
            else:
                # arjun commonly exits non-zero even with valid results — check the file
                print(f"⚠️  arjun exited with non-zero code (this is normal — check arjun_results.txt manually).")

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError, KeyboardInterrupt, Exception) as e:
        print(f"❌ arjun failed: {e}")

    # ------------------------------------------------------------------ #
    # Step 5: Build quality JS target list (merge wayback + katana JS)
    # NOTE: This will be empty if both waybackurls and katana found no .js URLs.
    # ------------------------------------------------------------------ #
    print("\n🗂️  Building quality JS target list...")
    try:
        js_sources = []
        for fname in ["urls.txt", "katana_urls.txt"]:
            if Path(fname).exists():
                js_sources += [
                    l.strip() for l in Path(fname).read_text().splitlines()
                    if l.strip().endswith(".js")
                ]

        if js_sources:
            quality = sorted(set(js_sources))[:QUALITY_JS_LIMIT]
            Path("quality_js.txt").write_text('\n'.join(quality) + '\n')
            print(f"✅ {len(quality)} JS targets → quality_js.txt")
        else:
            print("⚠️  No JS URLs found in urls.txt or katana_urls.txt — quality_js.txt will be empty.")
            print("   ℹ️  This is expected if the target has no historical JS in Wayback and katana timed out.")

    except Exception as e:
        print(f"❌ JS quality list failed: {e}")

    # ------------------------------------------------------------------ #
    # Final summary
    # ------------------------------------------------------------------ #
    print("\n📁 Output files generated:")
    files = [
        "clean_live_urls.txt", "live_domains.txt", "urls.txt",
        "live_js.txt", "katana_urls.txt", "params.txt",
        "arjun_results.txt", "quality_js.txt"
    ]
    for fname in files:
        p = Path(fname)
        if p.exists() and p.stat().st_size > 0:
            lines = len(p.read_text().splitlines())
            print(f"   ✅ {fname} ({lines} lines, {p.stat().st_size} bytes)")
        else:
            print(f"   ⚠️  {fname} — missing or empty")
