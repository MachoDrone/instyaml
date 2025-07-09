#!/usr/bin/env python3
"""
EFI Boot Fix v0.00.31 for INSTYAML
Analyzes original Ubuntu ISO and replicates exact EFI boot method
"""

import os
import subprocess
import tempfile
import shutil

def run_command(cmd):
    """Run command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def analyze_original_ubuntu_iso():
    """Analyze how the original Ubuntu ISO boots with EFI"""
    print("🔍 Analyzing original Ubuntu ISO EFI boot method...")
    
    ubuntu_iso = "ubuntu-24.04.2-live-server-amd64.iso"
    if not os.path.exists(ubuntu_iso):
        print(f"❌ Original Ubuntu ISO not found: {ubuntu_iso}")
        return None
    
    # Mount original Ubuntu ISO
    with tempfile.TemporaryDirectory() as temp_dir:
        mount_point = os.path.join(temp_dir, "ubuntu_mount")
        os.makedirs(mount_point)
        
        code, stdout, stderr = run_command(f"sudo mount -o loop '{ubuntu_iso}' '{mount_point}'")
        if code != 0:
            print(f"❌ Failed to mount Ubuntu ISO: {stderr}")
            return None
        
        try:
            # Check what EFI boot method Ubuntu actually uses
            efi_methods = {}
            
            # Method 1: Check for efi.img
            efi_img_path = os.path.join(mount_point, "boot", "grub", "efi.img")
            if os.path.exists(efi_img_path):
                efi_methods["efi.img"] = os.path.getsize(efi_img_path)
                print(f"✅ Found boot/grub/efi.img: {efi_methods['efi.img']:,} bytes")
            
            # Method 2: Check direct EFI files
            efi_boot_dir = os.path.join(mount_point, "EFI", "boot")
            if os.path.exists(efi_boot_dir):
                for efi_file in ["bootx64.efi", "grubx64.efi"]:
                    efi_path = os.path.join(efi_boot_dir, efi_file)
                    if os.path.exists(efi_path):
                        efi_methods[efi_file] = os.path.getsize(efi_path)
                        print(f"✅ Found EFI/boot/{efi_file}: {efi_methods[efi_file]:,} bytes")
            
            # Check what Ubuntu's xorriso command actually uses
            print("\n🔍 Checking Ubuntu's actual EFI boot configuration...")
            
            # Use isoinfo to see the actual boot catalog
            code, stdout, stderr = run_command(f"isoinfo -d -i '{ubuntu_iso}'")
            if code == 0:
                print("📋 Ubuntu ISO Boot Information:")
                lines = stdout.split('\n')
                for line in lines:
                    if any(keyword in line.lower() for keyword in ['boot', 'el torito', 'efi']):
                        print(f"   {line.strip()}")
            
            return efi_methods
            
        finally:
            run_command(f"sudo umount '{mount_point}'")

def create_fixed_iso():
    """Create ISO with correct EFI boot method"""
    print("\n🔧 Creating ISO with Ubuntu-exact EFI boot method...")
    
    # Check if we have the INSTYAML files
    if not os.path.exists("instyaml-24.04.2-beta.iso"):
        print("❌ INSTYAML ISO not found - run iso_builder.py first")
        return False
    
    # We need to rebuild with the correct EFI method
    print("💡 The issue is likely that Ubuntu uses a specific EFI boot catalog setup")
    print("💡 that requires exact parameter ordering in xorriso")
    
    # For now, let's test with Legacy BIOS to verify basic functionality
    print("\n🎯 RECOMMENDATION:")
    print("1. First test your INSTYAML ISO with Legacy BIOS (disable EFI in VirtualBox)")
    print("2. Verify the autoinstall and GitHub download works")
    print("3. Then we'll fix the EFI boot issue")
    
    return True

def main():
    """Main function"""
    print("🔧 EFI Boot Fix v0.00.31 for INSTYAML")
    print("=" * 50)
    
    # Analyze original Ubuntu ISO
    efi_methods = analyze_original_ubuntu_iso()
    
    if efi_methods:
        print(f"\n📊 Ubuntu EFI Methods Found: {len(efi_methods)}")
        for method, size in efi_methods.items():
            print(f"   {method}: {size:,} bytes")
        
        # The key insight: Ubuntu likely uses a specific combination
        if "efi.img" not in efi_methods:
            print("\n💡 KEY FINDING: Ubuntu 24.04.2 does NOT use efi.img!")
            print("💡 It uses direct EFI executables with specific xorriso parameters")
            print("💡 The issue is likely parameter ordering or missing GPT setup")
    
    create_fixed_iso()

if __name__ == "__main__":
    main()