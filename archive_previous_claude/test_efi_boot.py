#!/usr/bin/env python3
"""
EFI Boot Test Script
Purpose: Test if helloefi.iso boots correctly with EFI firmware
"""

import subprocess
import sys
from pathlib import Path

def test_qemu_efi():
    """Test EFI boot using QEMU"""
    iso_file = "helloefi.iso"
    
    if not Path(iso_file).exists():
        print(f"❌ ISO file {iso_file} not found")
        return False
    
    print("🧪 Testing EFI boot with QEMU...")
    print("This will open a VM window - check if:")
    print("1. GRUB loads correctly")
    print("2. Ubuntu boots without EFI errors") 
    print("3. HelloWorld.txt is accessible")
    
    qemu_cmd = [
        "qemu-system-x86_64",
        "-bios", "/usr/share/ovmf/OVMF.fd",  # EFI firmware
        "-cdrom", iso_file,
        "-m", "2048",
        "-enable-kvm",
        "-display", "gtk"
    ]
    
    try:
        print(f"Running: {' '.join(qemu_cmd)}")
        subprocess.run(qemu_cmd)
        return True
    except FileNotFoundError:
        print("❌ QEMU not found. Install with: sudo apt install qemu-system-x86_64 ovmf")
        return False
    except subprocess.CalledProcessError as e:
        print(f"❌ QEMU failed: {e}")
        return False

def test_virtualbox():
    """Instructions for VirtualBox testing"""
    print("🧪 VirtualBox EFI Test Instructions:")
    print("1. Create new VM with:")
    print("   - Type: Linux")
    print("   - Version: Ubuntu (64-bit)")
    print("   - Memory: 2048MB+")
    print("   - Enable EFI: System > Motherboard > Enable EFI")
    print("2. Mount helloefi.iso as CD/DVD")
    print("3. Boot and verify:")
    print("   ✅ GRUB menu appears")
    print("   ✅ Ubuntu boots normally")
    print("   ✅ HelloWorld.txt exists on desktop/filesystem")
    
def main():
    print("🚀 EFI Boot Testing")
    print("=" * 30)
    
    choice = input("Choose test method:\n1. QEMU (automated)\n2. VirtualBox (manual)\nChoice (1/2): ")
    
    if choice == "1":
        test_qemu_efi()
    elif choice == "2":
        test_virtualbox()
    else:
        print("Invalid choice")
        return False
        
    return True

if __name__ == "__main__":
    main()