#!/usr/bin/env python3
"""
EFI Boot Diagnostic Tool for INSTYAML v0.00.30
Analyzes ISO structure to identify EFI boot issues
"""

import os
import subprocess
import tempfile
import sys
from pathlib import Path

def run_command(cmd, capture_output=True):
    """Run command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=capture_output, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def check_iso_structure(iso_path):
    """Analyze ISO structure for EFI boot compatibility"""
    print(f"🔍 Analyzing ISO structure: {iso_path}")
    
    if not os.path.exists(iso_path):
        print(f"❌ ISO file not found: {iso_path}")
        return False
    
    # Check basic file info
    code, stdout, stderr = run_command(f"file '{iso_path}'")
    print(f"📁 File type: {stdout.strip()}")
    
    # Check ISO size
    size = os.path.getsize(iso_path)
    print(f"📏 Size: {size:,} bytes ({size/1024/1024/1024:.2f} GB)")
    
    # Mount and analyze
    with tempfile.TemporaryDirectory() as temp_dir:
        mount_point = os.path.join(temp_dir, "iso_mount")
        os.makedirs(mount_point)
        
        print(f"📂 Mounting ISO to analyze structure...")
        code, stdout, stderr = run_command(f"sudo mount -o loop '{iso_path}' '{mount_point}'")
        
        if code != 0:
            print(f"❌ Failed to mount ISO: {stderr}")
            return False
        
        try:
            analyze_efi_structure(mount_point)
            analyze_boot_structure(mount_point)
            
        finally:
            # Unmount
            run_command(f"sudo umount '{mount_point}'")
    
    return True

def analyze_efi_structure(mount_point):
    """Analyze EFI directory structure"""
    print("\n🔧 EFI Structure Analysis:")
    
    efi_path = os.path.join(mount_point, "EFI")
    if not os.path.exists(efi_path):
        print("❌ No EFI directory found!")
        return
    
    print("✅ EFI directory exists")
    
    # Check EFI/boot directory
    efi_boot_path = os.path.join(efi_path, "boot")
    if not os.path.exists(efi_boot_path):
        print("❌ No EFI/boot directory found!")
        return
    
    print("✅ EFI/boot directory exists")
    
    # Check critical EFI files
    efi_files = {
        "bootx64.efi": "Primary EFI boot loader",
        "grubx64.efi": "GRUB EFI executable", 
        "mmx64.efi": "Memory test utility"
    }
    
    for filename, description in efi_files.items():
        filepath = os.path.join(efi_boot_path, filename)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"✅ {filename}: {description} ({size:,} bytes)")
        else:
            print(f"❌ {filename}: Missing!")

def analyze_boot_structure(mount_point):
    """Analyze boot directory structure"""
    print("\n🔧 Boot Structure Analysis:")
    
    boot_path = os.path.join(mount_point, "boot")
    if not os.path.exists(boot_path):
        print("❌ No boot directory found!")
        return
    
    print("✅ boot directory exists")
    
    # Check for GRUB
    grub_path = os.path.join(boot_path, "grub")
    if os.path.exists(grub_path):
        print("✅ boot/grub directory exists")
        
        # Check for efi.img (Ubuntu's preferred EFI method)
        efi_img_path = os.path.join(grub_path, "efi.img")
        if os.path.exists(efi_img_path):
            size = os.path.getsize(efi_img_path)
            print(f"✅ boot/grub/efi.img exists ({size:,} bytes)")
        else:
            print("⚠️ boot/grub/efi.img not found (Ubuntu's preferred EFI method)")
        
        # Check eltorito.img
        eltorito_path = os.path.join(grub_path, "i386-pc", "eltorito.img")
        if os.path.exists(eltorito_path):
            print("✅ boot/grub/i386-pc/eltorito.img exists (Legacy BIOS)")
        else:
            print("❌ eltorito.img missing!")

def check_iso_boot_info(iso_path):
    """Check ISO boot information using isoinfo"""
    print("\n🔧 ISO Boot Information:")
    
    # Check if isoinfo is available
    code, stdout, stderr = run_command("which isoinfo")
    if code != 0:
        print("⚠️ isoinfo not available (install genisoimage package)")
        return
    
    # Get boot catalog info
    code, stdout, stderr = run_command(f"isoinfo -d -i '{iso_path}'")
    if code == 0:
        lines = stdout.split('\n')
        for line in lines:
            if 'boot' in line.lower() or 'el torito' in line.lower():
                print(f"📋 {line.strip()}")
    
    # Check for El Torito boot catalog
    code, stdout, stderr = run_command(f"isoinfo -R -l -i '{iso_path}' | grep -i 'boot.catalog'")
    if code == 0:
        print("✅ Boot catalog found")
    else:
        print("❌ Boot catalog not found")

def test_virtualbox_compatibility():
    """Test VirtualBox EFI compatibility"""
    print("\n🔧 VirtualBox EFI Compatibility Check:")
    
    # Check if VirtualBox is available
    code, stdout, stderr = run_command("which VBoxManage")
    if code != 0:
        print("⚠️ VirtualBox not available for testing")
        return
    
    print("✅ VirtualBox available")
    
    # Get VirtualBox version
    code, stdout, stderr = run_command("VBoxManage --version")
    if code == 0:
        print(f"📋 VirtualBox version: {stdout.strip()}")

def main():
    """Main diagnostic function"""
    print("🔧 EFI Boot Diagnostic Tool for INSTYAML v0.00.30")
    print("=" * 60)
    
    # Look for ISO in common locations
    iso_locations = [
        "~/iso/instyaml-24.04.2-beta.iso",
        "./instyaml-24.04.2-beta.iso",
        "instyaml-24.04.2-beta.iso"
    ]
    
    iso_path = None
    for location in iso_locations:
        expanded_path = os.path.expanduser(location)
        if os.path.exists(expanded_path):
            iso_path = expanded_path
            break
    
    if not iso_path:
        print("❌ INSTYAML ISO not found in common locations")
        print("Please specify the path to your instyaml-24.04.2-beta.iso file")
        if len(sys.argv) > 1:
            iso_path = sys.argv[1]
        else:
            return
    
    print(f"🎯 Found ISO: {iso_path}")
    
    # Run diagnostics
    if check_iso_structure(iso_path):
        check_iso_boot_info(iso_path)
        test_virtualbox_compatibility()
        
        print("\n" + "=" * 60)
        print("🎯 DIAGNOSTIC SUMMARY:")
        print("If EFI files are present but VirtualBox still fails to boot:")
        print("1. Try Legacy BIOS mode first to verify basic functionality")
        print("2. Check VirtualBox EFI settings (System → Enable EFI)")
        print("3. Ensure VM has enough memory (2GB+ recommended)")
        print("4. Try different VirtualBox storage controller types")
        print("5. Check if Secure Boot is disabled in VM settings")

if __name__ == "__main__":
    main()