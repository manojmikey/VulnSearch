import re
import smart_reconnaissance
from pathlib import Path
import content_discovery


def check_domain(domain):
    """Validate that the input looks like a real domain (e.g. example.com)."""
    pattern = r'^([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$'
    if re.fullmatch(pattern, domain):
        print("✅ Entered a valid domain....")
        return True
    else:
        raise ValueError(
            f"Invalid domain: '{domain}'. "
            "Please enter a bare domain like 'example.com' (no https:// prefix)."
        )


def main():
    # ── Phase 1: Smart Reconnaissance ──────────────────────────────────── #
    try:
        domain_name = input("Enter the domain name you want to scan: ").strip()
        check_domain(domain_name)

        print("\n🔍 Phase 1: Smart Reconnaissance started...\n")
        result = smart_reconnaissance.smart_reconn(domain_name)

        if result['success']:
            print("\n✅ Phase 1 complete. Live sites discovered.")
            print("   Check these files for manual testing:")
            for p in result['path']:
                print(f"   → {p}")
        else:
            print("\n❌ Phase 1 failed: Reconnaissance did not produce results.")
            return

    except ValueError as e:
        print(f"❌ {e}")
        return
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user. Exiting.")
        return
    except Exception as e:
        print(f"❌ Unexpected error in Phase 1: {e}")
        return

    # ── Phase 2: Content Discovery ──────────────────────────────────────── #
    try:
        print("\n🔍 Phase 2: Content Discovery started...\n")

        live_sites = Path("live_sites.txt")
        if not live_sites.exists() or live_sites.stat().st_size == 0:
            raise FileNotFoundError(
                "'live_sites.txt' not found or is empty. Phase 1 may have failed."
            )

        content_discovery.intel_content_discovery(str(live_sites))
        print("\n✅ Phase 2: Content discovery completed.")

    except FileNotFoundError as e:
        print(f"❌ {e}")
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user during Phase 2. Partial results may exist.")
    except Exception as e:
        print(f"❌ Unexpected error in Phase 2: {e}")


if __name__ == "__main__":
    main()
