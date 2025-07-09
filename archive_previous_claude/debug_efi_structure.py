#!/usr/bin/env python3
"""
Debug EFI Structure - Compare Original vs Created ISO
Purpose: Find why EFI boot fails on our created ISO
"""

import subprocess
import tempfile
import shutil
from pathlib import Path

def analyze_iso_efi_structure(iso_path, label):
    """Analyze EFI structure of an ISO"""
    print(f"\n🔍 Analyzing {label}: {iso_path}")
    print("=" * 60)
    
    if not Path(iso_path).exists():
        print(f"❌ ISO not found: {iso_path}")
        return
    
    with tempfile.TemporaryDirectory() as temp_dir:
        extract_dir = Path(temp_dir) / "extracted"
        extract_dir.mkdir()
        
        # Extract ISO
        try:
            subprocess.run(["7z", "x", f"-o{extract_dir}", iso_path], 
                         check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print(f"❌ Failed to extract {iso_path}")
            return
        
        # Check EFI directory structure
        efi_dir = extract_dir / "EFI"
        if efi_dir.exists():
            print("✅ EFI directory found")
            
            # List EFI subdirectories
            for subdir in efi_dir.iterdir():
                if subdir.is_dir():
                    print(f"📁 EFI/{subdir.name}/")
                    for file in subdir.iterdir():
                        if file.is_file():
                            size = file.stat().st_size
                            print(f"   📄 {file.name} ({size:,} bytes)")
        else:
            print("❌ No EFI directory found")
        
        # Check boot directory structure
        boot_dir = extract_dir / "boot"
        if boot_dir.exists():
            print("\n✅ boot directory found")
            
            # Check grub subdirectories
            grub_dir = boot_dir / "grub"
            if grub_dir.exists():
                print("📁 boot/grub/")
                for subdir in grub_dir.iterdir():
                    if subdir.is_dir():
                        print(f"   📁 {subdir.name}/")
                        # Check for important boot files
                        for file in subdir.iterdir():
                            if file.suffix in ['.efi', '.img']:
                                size = file.stat().st_size
                                print(f"      📄 {file.name} ({size:,} bytes)")
        else:
            print("❌ No boot directory found")
        
        # Check for specific EFI boot files
        critical_files = [
            "EFI/boot/bootx64.efi",
            "EFI/ubuntu/shimx64.efi", 
            "EFI/ubuntu/grubx64.efi",
            "boot/grub/i386-pc/eltorito.img",
            "boot/grub/efi.img"
        ]
        
        print(f"\n🎯 Critical EFI Boot Files Check:")
        for file_path in critical_files:
            full_path = extract_dir / file_path
            if full_path.exists():
                size = full_path.stat().st_size
                print(f"✅ {file_path} ({size:,} bytes)")
            else:
                print(f"❌ {file_path} - MISSING")

def compare_xorriso_output():
    """Show the xorriso command we used"""
    print(f"\n🔧 Our xorriso Command:")
    print("-" * 40)
    cmd = """xorriso -as mkisofs \\
  -r \\
  -V "HelloEFI Ubuntu 24.04.2 Server" \\
  -J -joliet-long \\
  -b boot/grub/i386-pc/eltorito.img \\
  -c boot.catalog \\
  -no-emul-boot \\
  -boot-load-size 4 \\
  -boot-info-table \\
  -eltorito-alt-boot \\
  -e EFI/boot/bootx64.efi \\
  -no-emul-boot \\
  -isohybrid-gpt-basdat \\
  -partition_offset 16 \\
  -o helloefi.iso \\
  work/extracted"""
    print(cmd)

def main():
    print("🚨 EFI Boot Failure Debug Analysis")
    print("Purpose: Find why our ISO fails EFI boot")
    
    # Analyze original Ubuntu ISO
    analyze_iso_efi_structure("ubuntu-24.04.2-live-server-amd64.iso", "ORIGINAL Ubuntu")
    
    # Analyze our created ISO  
    analyze_iso_efi_structure("helloefi.iso", "OUR Created ISO")
    
    # Show our xorriso command
    compare_xorriso_output()
    
    print(f"\n🎯 FINDINGS SUMMARY:")
    print("1. Compare EFI structures above")
    print("2. Look for missing EFI boot files") 
    print("3. Check if shimx64.efi vs bootx64.efi difference")
    print("4. Verify xorriso parameters match Ubuntu's method")

if __name__ == "__main__":
    main()