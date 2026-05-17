import subprocess
from pathlib import Path
import time
import re


DEVNULL = subprocess.DEVNULL


def _run(command, timeout=None, capture_output=True):
    """
    Helper to run a subprocess command cleanly.
    Suppresses stdout/stderr from CLI. Returns CompletedProcess or None on failure.
    """
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE if capture_output else DEVNULL,
            stderr=DEVNULL,
            text=True,
            timeout=timeout
        )
        return result
    except subprocess.TimeoutExpired:
        print(f"⏱  Timeout expired for: {' '.join(command)}")
    except FileNotFoundError:
        print(f"❌ Tool not found: '{command[0]}'. Is it installed and in PATH?")
    except Exception as e:
        print(f"❌ Unexpected error running {command[0]}: {e}")
    return None


def _clean_dnsx_output(resolved_path):
    """
    dnsx -resp produces lines like:
        sub.domain.com [A] [1.2.3.4]   <- with ANSI color codes around each part

    httpx needs plain hostnames only, one per line.
    This strips ANSI codes and extracts just the hostname (first token).
    Returns count of unique hostnames written to clean_subs.txt.
    """
    ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    cleaned_hosts = set()

    for line in Path(resolved_path).read_text().splitlines():
        line = ansi_escape.sub('', line).strip()
        if not line:
            continue
        hostname = line.split()[0]
        cleaned_hosts.add(hostname)

    if cleaned_hosts:
        Path("clean_subs.txt").write_text('\n'.join(sorted(cleaned_hosts)) + '\n')

    return len(cleaned_hosts)


def proceed():
    """
    Step 2: Combine subfinder + amass output, resolve with dnsx, clean, probe with httpx.
    """
    subfinder_exists = Path("subfinder.txt").exists() and Path("subfinder.txt").stat().st_size > 0
    amass_exists = Path("amass.txt").exists() and Path("amass.txt").stat().st_size > 0

    if not subfinder_exists and not amass_exists:
        print("❌ Neither subfinder.txt nor amass.txt found. Cannot proceed.")
        return {'success': False, 'path': []}

    # Combine whichever files exist
    print("📂 Combining subdomain enumeration output...")
    combined = set()
    for fname in ["subfinder.txt", "amass.txt"]:
        p = Path(fname)
        if p.exists() and p.stat().st_size > 0:
            combined.update(p.read_text().splitlines())

    combined = sorted(line.strip() for line in combined if line.strip())
    Path("all_subs.txt").write_text('\n'.join(combined) + '\n')
    print(f"✅ {len(combined)} unique subdomains → all_subs.txt")

    # Run dnsx to resolve subdomains
    print("🌐 Initiating dnsx for DNS resolution...")
    dstart = time.time()
    dnsx_result = _run(["dnsx", "-l", "all_subs.txt", "-resp", "-silent"])

    if dnsx_result and dnsx_result.returncode == 0 and dnsx_result.stdout.strip():
        Path("resolved_subs.txt").write_text(dnsx_result.stdout)
        count = len(dnsx_result.stdout.strip().splitlines())
        print(f"✅ dnsx completed in {time.time() - dstart:.2f}s — {count} resolved → resolved_subs.txt")
    else:
        print("❌ dnsx produced no output or failed.")
        return {'success': False, 'path': []}

    resolved = Path("resolved_subs.txt")
    if not resolved.exists() or resolved.stat().st_size == 0:
        print("❌ resolved_subs.txt is empty after dnsx.")
        return {'success': False, 'path': []}

    # Clean dnsx output
    print("🧹 Cleaning dnsx output (stripping ANSI codes, extracting hostnames)...")
    count = _clean_dnsx_output("resolved_subs.txt")

    if count == 0:
        print("❌ No hostnames found after cleaning resolved_subs.txt.")
        return {'success': False, 'path': []}

    print(f"✅ {count} unique hostnames extracted → clean_subs.txt")

    # Run httpx on the cleaned hostname list
    print("🌍 Initiating httpx for live site probing...")
    hstart = time.time()
    httpx_result = _run(
        ["httpx", "-list", "clean_subs.txt", "-silent", "-title", "-status-code", "-tech-detect"],
        timeout=300
    )

    if httpx_result and httpx_result.returncode == 0 and httpx_result.stdout.strip():
        Path("live_sites.txt").write_text(httpx_result.stdout)
        live_count = len(httpx_result.stdout.strip().splitlines())
        print(f"✅ httpx completed in {time.time() - hstart:.2f}s — {live_count} live sites → live_sites.txt")
    else:
        print("❌ httpx produced no output or failed.")
        return {'success': False, 'path': []}

    live = Path("live_sites.txt")
    if not live.exists() or live.stat().st_size == 0:
        print("❌ live_sites.txt is empty after httpx.")
        return {'success': False, 'path': []}

    return {'success': True, 'path': [live]}


def smart_reconn(domain):
    """
    Step 1: Run subfinder and assetfinder for subdomain enumeration.
    """

    # Subfinder
    print(f"🔎 Initiating subfinder for: {domain}")
    sstart = time.time()
    subfinder_result = _run(["subfinder", "-d", domain, "-silent", "-all"], timeout=300)

    if subfinder_result and subfinder_result.returncode == 0 and subfinder_result.stdout.strip():
        lines = subfinder_result.stdout.strip().splitlines()
        Path("subfinder.txt").write_text(subfinder_result.stdout)
        print(f"✅ subfinder completed in {time.time() - sstart:.2f}s — {len(lines)} subdomains found")
    else:
        print("⚠️  subfinder produced no output or failed.")

    # Assetfinder
    print(f"🔎 Initiating assetfinder for: {domain}")
    astart = time.time()
    amass_result = _run(["assetfinder", "--subs-only", domain], timeout=600)

    if amass_result and amass_result.returncode == 0 and amass_result.stdout.strip():
        lines = amass_result.stdout.strip().splitlines()
        Path("amass.txt").write_text(amass_result.stdout)
        print(f"✅ assetfinder completed in {time.time() - astart:.2f}s — {len(lines)} subdomains found")
    else:
        print("⚠️  assetfinder produced no output or failed.")

    # Validate at least one output file exists
    paths = [
        p for p in [Path("subfinder.txt"), Path("amass.txt")]
        if p.exists() and p.stat().st_size > 0
    ]

    if not paths:
        print("❌ Both subfinder and assetfinder produced no results. Aborting.")
        return {'success': False, 'path': []}

    print(f"📄 Found {len(paths)} output file(s): {[str(p) for p in paths]}")
    return proceed()
