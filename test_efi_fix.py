#!/usr/bin/env python3
"""
Quick EFI Boot Fix Test Script
Tests if the new xorriso parameters create proper GPT partition table
"""

import subprocess
import os
import sys

def test_iso_partition_table(iso_path):
    """Test if ISO has GPT partition table"""
    print(f"🔍 Testing partition table structure of: {iso_path}")
    
    if not os.path.exists(iso_path):
        print(f"❌ ISO file not found: {iso_path}")
        return False
    
    try:
        # Test 1: Check with gdisk
        print("\n📊 Testing with gdisk...")
        result = subprocess.run(
            ["sudo", "gdisk", "-l", iso_path], 
            capture_output=True, text=True, timeout=10
        )
        
        output = result.stdout + result.stderr
        
        if "GPT: present" in output:
            print("✅ GPT partition table detected!")
            gpt_present = True
        elif "GPT: not present" in output:
            print("❌ GPT partition table missing")
            gpt_present = False
        else:
            print("⚠️ Could not determine GPT status")
            gpt_present = False
        
        # Test 2: Check for EFI boot catalog
        print("\n🔍 Testing EFI boot catalog...")
        hex_result = subprocess.run(
            ["hexdump", "-C", iso_path], 
            capture_output=True, text=True, timeout=5
        )
        
        if "91 ef" in hex_result.stdout:
            print("✅ EFI boot catalog entry found!")
            efi_catalog = True
        else:
            print("❌ EFI boot catalog entry missing")
            efi_catalog = False
        
        # Test 3: Check file system type
        print("\n💿 Testing ISO file system...")
        file_result = subprocess.run(
            ["file", iso_path], 
            capture_output=True, text=True
        )
        
        if "ISO 9660" in file_result.stdout:
            print("✅ Valid ISO 9660 file system")
            valid_iso = True
        else:
            print("❌ Invalid or corrupted ISO")
            valid_iso = False
        
        # Summary
        print("\n" + "="*50)
        print("EFI BOOT FIX TEST RESULTS:")
        print("="*50)
        print(f"GPT Partition Table: {'✅ PRESENT' if gpt_present else '❌ MISSING'}")
        print(f"EFI Boot Catalog:    {'✅ PRESENT' if efi_catalog else '❌ MISSING'}")
        print(f"Valid ISO Format:    {'✅ VALID' if valid_iso else '❌ INVALID'}")
        
        success = gpt_present and efi_catalog and valid_iso
        
        if success:
            print("\n🎉 SUCCESS: EFI boot should work!")
            print("💡 Test the ISO in VirtualBox with EFI enabled")
        else:
            print("\n⚠️ ISSUES DETECTED: EFI boot may fail")
            print("💡 Try running iso_builder.py v0.00.26 to rebuild")
        
        return success
        
    except subprocess.TimeoutExpired:
        print("❌ Test timed out")
        return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    print("🔧 EFI Boot Fix Test Script v0.00.26")
    print("=" * 50)
    
    # Look for INSTYAML ISO in current directory
    iso_candidates = [
        "instyaml-24.04.2-beta.iso",
        "instyaml-24.04.2.iso",
        "ubuntu-24.04.2-live-server-amd64.iso"
    ]
    
    iso_found = None
    for iso in iso_candidates:
        if os.path.exists(iso):
            iso_found = iso
            break
    
    if not iso_found:
        print("🔍 No ISO found automatically. Please specify ISO path:")
        iso_path = input("Enter ISO file path: ").strip()
        if not iso_path:
            print("❌ No ISO specified")
            return False
    else:
        iso_path = iso_found
    
    print(f"📀 Testing ISO: {iso_path}")
    
    # Check if running on Linux (required for tools)
    if os.name != 'posix':
        print("⚠️ This test requires Linux (for gdisk and hexdump)")
        return False
    
    # Check for required tools
    required_tools = ["gdisk", "hexdump", "file"]
    missing_tools = []
    
    for tool in required_tools:
        if not subprocess.run(["which", tool], capture_output=True).returncode == 0:
            missing_tools.append(tool)
    
    if missing_tools:
        print(f"❌ Missing required tools: {', '.join(missing_tools)}")
        print("💡 Install with: sudo apt install gdisk util-linux file")
        return False
    
    # Run the test
    return test_iso_partition_table(iso_path)

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Test cancelled by user")
        sys.exit(1)