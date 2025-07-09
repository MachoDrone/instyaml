#!/usr/bin/env python3
"""
Version Check - Verify Script Versions and Cache Status
PURPOSE: Ensure we're running latest versions, not cached ones
VERSION: 1.0.0
"""
import sys
from datetime import datetime

VERSION = "1.0.0"
SCRIPT_NAME = "version_check.py"

def main():
    print("🔍 Version Check - Cache Buster Verification")
    print("=" * 50)
    print(f"📋 SCRIPT: {SCRIPT_NAME} VERSION: {VERSION}")
    print(f"🕒 Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    print("✅ If you see this version number, the script is NOT cached!")
    print("")
    print("🎯 Expected versions:")
    print("  - version_check.py: 1.0.0")
    print("  - boot_order_fix.py: 1.0.1") 
    print("  - complete_efi_solution.py: 1.0.2")
    print("  - fix_corrupted_iso.py: 1.0.1")
    print("")
    print("🚨 If you see different versions, you may have cache issues!")

if __name__ == "__main__":
    main()