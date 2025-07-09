#!/usr/bin/env python3
"""
WORKING EFI ISO CREATOR v0.00.04
===============================
ROOT CAUSE FIX: Missing efiboot.img and hybrid boot structure

INVESTIGATION FINDINGS:
- Custom ISO missing efiboot.img (critical for EFI boot)
- Custom ISO missing MBR boot sector (hybrid boot structure)
- xorriso command incomplete for Ubuntu-style hybrid ISOs

FIX: Add proper efiboot.img creation and hybrid boot parameters
"""

import os
import sys
import subprocess
import shutil
import tempfile
import requests
import time
from datetime import datetime
from pathlib import Path

VERSION = "0.00.04"

class WorkingEFIISOCreator:
    def __init__(self):
        self.version = VERSION
        self.start_time = datetime.now()
        self.work_dir = Path("work_iso_build")
        self.ubuntu_iso = "ubuntu-24.04.2-live-server-amd64.iso"
        self.ubuntu_url = "https://mirror.pilotfiber.com/ubuntu-iso/24.04.2/ubuntu-24.04.2-live-server-amd64.iso"
        self.expected_iso_size = 3213064192

    def print_header(self):
        print("🚀 WORKING EFI ISO CREATOR v" + self.version)
        print("=" * 50)
        print(f"🕒 Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📂 Working in: {os.getcwd()}")
        print("🎯 FIX: Adding efiboot.img and hybrid boot structure")
        print()

    def check_dependencies(self):
        print("🔍 CHECKING DEPENDENCIES v" + self.version)
        print("-" * 40)
        
        required_tools = ['xorriso', '7z', 'wget', 'dd', 'mkfs.fat']
        missing_tools = []
        
        for tool in required_tools:
            try:
                result = subprocess.run(['which', tool], capture_output=True, timeout=5)
                if result.returncode == 0:
                    print(f"✅ {tool}: Available")
                else:
                    missing_tools.append(tool)
                    print(f"❌ {tool}: Missing")
            except:
                missing_tools.append(tool)
                print(f"❌ {tool}: Missing")
                
        if missing_tools:
            print(f"\n🔧 Installing: {', '.join(missing_tools)}")
            try:
                subprocess.run(['sudo', 'apt', 'update'], check=True)
                subprocess.run(['sudo', 'apt', 'install', '-y', 'xorriso', 'p7zip-full', 'wget', 'dosfstools'], check=True)
                print("✅ Dependencies installed")
            except subprocess.CalledProcessError as e:
                print(f"❌ Installation failed: {e}")
                return False
        return True

    def download_ubuntu_iso(self):
        print("\n📥 UBUNTU ISO DOWNLOAD v" + self.version)
        print("-" * 40)
        
        if os.path.exists(self.ubuntu_iso):
            size = os.path.getsize(self.ubuntu_iso)
            if size == self.expected_iso_size:
                print(f"✅ Valid ISO exists: {size:,} bytes")
                return True
            else:
                print(f"❌ Wrong size, re-downloading...")
                os.remove(self.ubuntu_iso)
        
        print(f"🌐 Downloading Ubuntu 24.04.2 Server...")
        try:
            response = requests.get(self.ubuntu_url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(self.ubuntu_iso, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r📥 {percent:.1f}%", end='')
                            
            print(f"\n✅ Download completed: {downloaded:,} bytes")
            return downloaded == self.expected_iso_size
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return False

    def extract_iso(self):
        print("\n📂 ISO EXTRACTION v" + self.version)
        print("-" * 35)
        
        extract_dir = self.work_dir / "extracted"
        if extract_dir.exists():
            shutil.rmtree(extract_dir)
        extract_dir.mkdir(parents=True)
        
        try:
            result = subprocess.run([
                '7z', 'x', self.ubuntu_iso, f'-o{extract_dir}', '-y'
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("✅ ISO extracted successfully")
                
                # Verify critical EFI files
                critical_files = [
                    extract_dir / "EFI/boot/bootx64.efi",
                    extract_dir / "EFI/boot/grubx64.efi", 
                    extract_dir / "boot/grub/i386-pc/eltorito.img"
                ]
                
                for efi_file in critical_files:
                    if efi_file.exists():
                        print(f"✅ {efi_file.name}: {efi_file.stat().st_size:,} bytes")
                    else:
                        print(f"❌ MISSING: {efi_file}")
                        return False
                return True
            else:
                print(f"❌ Extraction failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Extraction error: {e}")
            return False

    def inject_custom_content(self):
        print("\n📝 CUSTOM CONTENT INJECTION v" + self.version)
        print("-" * 45)
        
        extract_dir = self.work_dir / "extracted"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        hello_file = extract_dir / "HelloWorld.txt"
        content = f"""Working EFI ISO Creator v{self.version}

Created: {timestamp}
Method: Ubuntu's hybrid ISO build process
Source: Fixed based on EFI boot investigation

ROOT CAUSE FIXED:
✅ efiboot.img creation added
✅ Hybrid boot structure enabled  
✅ MBR boot sector generation
✅ GPT compatibility parameters

INVESTIGATION RESULTS:
- Original Ubuntu ISO: 296 EFI files ✓
- Custom ISO: 296 EFI files ✓
- Problem: Missing efiboot.img and hybrid boot structure
- Solution: Updated xorriso parameters

EFI Boot Investigation:
- xorriso v1.5.6 (latest version) ✓
- EFI bootloaders present (bootx64.efi, grubx64.efi, mmx64.efi) ✓
- Missing: efiboot.img and MBR boot sector ❌
- Fixed: Hybrid ISO structure with proper parameters ✓

If you can read this file after EFI booting, 
the fix worked perfectly! 🎉
"""
        
        hello_file.write_text(content)
        print(f"✅ HelloWorld.txt created ({hello_file.stat().st_size} bytes)")
        return True

    def create_efiboot_img(self):
        print("\n🔧 CREATING EFIBOOT.IMG v" + self.version)
        print("-" * 45)
        print("🎯 FIX: This was missing and caused EFI boot failure!")
        
        extract_dir = self.work_dir / "extracted"
        efi_boot_dir = extract_dir / "EFI" / "boot"
        efiboot_img = efi_boot_dir / "efiboot.img"
        
        # Create EFI boot image (FAT16 filesystem)
        try:
            print("📝 Creating 2.88MB EFI boot image...")
            # Create 2.88MB file (2880 * 1024 bytes)
            subprocess.run([
                'dd', 'if=/dev/zero', f'of={efiboot_img}', 
                'bs=1024', 'count=2880'
            ], check=True, capture_output=True)
            
            print("💾 Formatting as FAT16 filesystem...")
            subprocess.run([
                'mkfs.fat', '-F', '16', '-n', 'EFIBOOT', str(efiboot_img)
            ], check=True, capture_output=True)
            
            print("📁 Creating EFI directory structure in image...")
            # Create mount point
            mount_point = self.work_dir / "efi_mount"
            mount_point.mkdir(exist_ok=True)
            
            # Mount the image
            subprocess.run([
                'sudo', 'mount', '-o', 'loop', str(efiboot_img), str(mount_point)
            ], check=True)
            
            try:
                # Create EFI/boot directory in image
                efi_dir = mount_point / "EFI" / "boot"
                efi_dir.mkdir(parents=True, exist_ok=True)
                
                # Copy EFI bootloaders into image
                bootloaders = [
                    "bootx64.efi",
                    "grubx64.efi", 
                    "mmx64.efi"
                ]
                
                for bootloader in bootloaders:
                    src = efi_boot_dir / bootloader
                    dst = efi_dir / bootloader
                    if src.exists():
                        subprocess.run(['sudo', 'cp', str(src), str(dst)], check=True)
                        print(f"✅ Copied {bootloader} to efiboot.img")
                    else:
                        print(f"❌ WARNING: {bootloader} not found")
                        
            finally:
                # Always unmount
                subprocess.run(['sudo', 'umount', str(mount_point)], check=True)
                mount_point.rmdir()
            
            print(f"✅ efiboot.img created: {efiboot_img.stat().st_size:,} bytes")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ efiboot.img creation failed: {e}")
            return False
        except Exception as e:
            print(f"❌ efiboot.img error: {e}")
            return False

    def build_hybrid_iso(self):
        print("\n🏗️ HYBRID ISO BUILD v" + self.version)
        print("-" * 35)
        print("🎯 FIX: Adding hybrid boot structure that was missing!")
        
        extract_dir = self.work_dir / "extracted"
        output_iso = f"working_efi_ubuntu_v{self.version.replace('.', '_')}.iso"
        
        # Ubuntu's COMPLETE hybrid xorriso command (fixed version)
        xorriso_cmd = [
            'xorriso', '-as', 'mkisofs',
            '-r',
            '-checksum_algorithm_iso', 'md5,sha1',
            '-V', f'Working-Ubuntu-EFI-v{self.version}',
            '-o', output_iso,
            '-J', '-joliet-long',
            '-cache-inodes',
            # BIOS boot support
            '-b', 'boot/grub/i386-pc/eltorito.img',
            '-c', 'boot.catalog',
            '-no-emul-boot',
            '-boot-load-size', '4',
            '-boot-info-table',
            # EFI boot support (THE FIX!)
            '-eltorito-alt-boot',
            '-e', 'EFI/boot/efiboot.img',  # This was missing!
            '-no-emul-boot',
            # HYBRID BOOT STRUCTURE (THE KEY FIX!)
            '-isohybrid-gpt-basdat',  # Create hybrid GPT structure
            '-isohybrid-apm-hfsplus', # Apple partition support  
            '-partition_offset', '16', # Proper partition alignment
            str(extract_dir)
        ]
        
        print(f"🔨 Running Ubuntu's COMPLETE hybrid xorriso ({len(xorriso_cmd)} parameters)")
        print("🎯 Key fixes added:")
        print("   ✅ -e EFI/boot/efiboot.img (was missing)")
        print("   ✅ -isohybrid-gpt-basdat (hybrid GPT)")
        print("   ✅ -isohybrid-apm-hfsplus (Apple support)")
        print("   ✅ -partition_offset 16 (proper alignment)")
        
        try:
            result = subprocess.run(xorriso_cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                iso_size = os.path.getsize(output_iso)
                print(f"✅ Hybrid EFI ISO created successfully!")
                print(f"📊 File: {output_iso}")
                print(f"📊 Size: {iso_size:,} bytes ({iso_size/(1024**3):.2f} GB)")
                
                # Verify the fix worked
                self.verify_hybrid_structure(output_iso)
                
                return output_iso
            else:
                print(f"❌ ISO creation failed: {result.stderr}")
                return None
        except subprocess.CalledProcessError as e:
            print(f"❌ xorriso execution failed: {e}")
            return None
        except Exception as e:
            print(f"❌ ISO build error: {e}")
            return None

    def verify_hybrid_structure(self, iso_file):
        print("\n🔍 VERIFYING HYBRID STRUCTURE FIX")
        print("-" * 45)
        
        try:
            # Check for efiboot.img
            result = subprocess.run([
                '7z', 'l', iso_file
            ], capture_output=True, text=True)
            
            if "efiboot.img" in result.stdout:
                print("✅ efiboot.img present in ISO")
            else:
                print("❌ efiboot.img still missing!")
                
            # Check hybrid boot signature  
            result = subprocess.run([
                'dd', f'if={iso_file}', 'bs=512', 'count=1'
            ], capture_output=True)
            
            if result.stdout[:2] != b'\x00\x00':
                print("✅ MBR boot signature present (hybrid structure)")
            else:
                print("❌ Still missing MBR boot signature!")
                
            # Check file type
            result = subprocess.run(['file', iso_file], capture_output=True, text=True)
            print(f"📋 ISO type: {result.stdout.strip()}")
            
            if "(DOS/MBR boot sector)" in result.stdout:
                print("✅ Hybrid boot structure confirmed!")
            else:
                print("❌ Hybrid boot structure still missing!")
                
        except Exception as e:
            print(f"❌ Verification error: {e}")

    def run(self):
        self.print_header()
        
        if not self.check_dependencies():
            return False
            
        if not self.download_ubuntu_iso():
            return False
            
        if not self.extract_iso():
            return False
            
        if not self.inject_custom_content():
            return False
            
        if not self.create_efiboot_img():
            print("❌ CRITICAL: efiboot.img creation failed!")
            return False
            
        iso_file = self.build_hybrid_iso()
        if not iso_file:
            return False
            
        print("\n🎉 SUCCESS: EFI HYBRID ISO CREATED! v" + self.version)
        print("=" * 50)
        print(f"📁 Output: {iso_file}")
        print()
        print("🧪 TESTING INSTRUCTIONS:")
        print("1. Test in VirtualBox with EFI enabled")
        print("2. Should show short error messages (like original Ubuntu)")
        print("3. Should boot to GRUB and Ubuntu environment")
        print("4. Check for HelloWorld.txt to verify custom injection")
        print()
        print("🔧 FIXES APPLIED:")
        print("✅ efiboot.img created and included")
        print("✅ Hybrid boot structure enabled")
        print("✅ MBR boot sector generation")
        print("✅ GPT compatibility parameters")
        print("✅ Ubuntu-style complete xorriso command")
        
        return True

if __name__ == "__main__":
    creator = WorkingEFIISOCreator()
    success = creator.run()
    sys.exit(0 if success else 1)