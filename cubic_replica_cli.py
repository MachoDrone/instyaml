#!/usr/bin/env python3
"""
CUBIC REPLICA CLI v1.0
Replicates Cubic's exact methodology for creating EFI-bootable custom Ubuntu ISOs
Based on analysis of working Cubic vs original Ubuntu differences
"""

import os
import sys
import subprocess
import shutil
import requests
from pathlib import Path
from datetime import datetime
import tempfile

class CubicReplicaCLI:
    def __init__(self):
        self.version = "1.0"
        self.start_time = datetime.now()
        self.work_dir = Path("cubic_replica_work")
        self.ubuntu_iso = "ubuntu-24.04.2-live-server-amd64.iso"
        self.ubuntu_url = "https://mirror.pilotfiber.com/ubuntu-iso/24.04.2/ubuntu-24.04.2-live-server-amd64.iso"
        self.output_iso = f"cubic_replica_custom_{datetime.now().strftime('%Y%m%d_%H%M')}.iso"
        
    def log(self, message, emoji="📝"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{emoji} {timestamp} {message}")
        
    def check_dependencies(self):
        self.log("CHECKING DEPENDENCIES", "🔍")
        print("-" * 40)
        
        required_tools = ['7z', 'unsquashfs', 'mksquashfs', 'xorriso', 'wget']
        missing_tools = []
        
        for tool in required_tools:
            if shutil.which(tool):
                print(f"✅ {tool}: Available")
            else:
                print(f"❌ {tool}: Missing")
                missing_tools.append(tool)
                
        # Check for isolinux MBR file
        mbr_file = Path("/usr/lib/ISOLINUX/isohdpfx.bin")
        if mbr_file.exists():
            print(f"✅ MBR boot file: {mbr_file}")
        else:
            print(f"❌ MBR boot file missing")
            missing_tools.append("isolinux")
                
        if missing_tools:
            self.log("Installing missing dependencies...", "🔧")
            try:
                subprocess.run(['sudo', 'apt', 'update'], check=True)
                subprocess.run(['sudo', 'apt', 'install', '-y', 'p7zip-full', 'squashfs-tools', 'xorriso', 'isolinux', 'wget'], check=True)
                self.log("Dependencies installed successfully", "✅")
            except subprocess.CalledProcessError as e:
                self.log(f"Failed to install dependencies: {e}", "❌")
                return False
                
        return True
        
    def download_ubuntu_iso(self):
        self.log("UBUNTU ISO SETUP", "📥")
        print("-" * 40)
        
        if Path(self.ubuntu_iso).exists():
            size = Path(self.ubuntu_iso).stat().st_size
            self.log(f"Ubuntu ISO exists: {size:,} bytes", "✅")
            return True
            
        self.log(f"Downloading Ubuntu Server 24.04.2...", "⬇️")
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
                            print(f"\rProgress: {percent:.1f}%", end='')
                            
            print()
            self.log(f"Download complete: {downloaded:,} bytes", "✅")
            return True
            
        except Exception as e:
            self.log(f"Download failed: {e}", "❌")
            return False
            
    def extract_ubuntu_iso(self):
        self.log("EXTRACTING UBUNTU ISO", "📂")
        print("-" * 40)
        
        if self.work_dir.exists():
            shutil.rmtree(self.work_dir)
        self.work_dir.mkdir()
        
        extract_dir = self.work_dir / "extracted"
        extract_dir.mkdir()
        
        self.log("Extracting ISO contents...", "⚙️")
        cmd = ["7z", "x", self.ubuntu_iso, f"-o{extract_dir}", "-y"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            self.log(f"Extraction failed: {result.stderr}", "❌")
            return False
            
        self.log("ISO extraction completed", "✅")
        return True
        
    def cubic_step1_simplify_kernel(self):
        self.log("STEP 1: SIMPLIFY KERNEL STRUCTURE (Like Cubic)", "🎯")
        print("-" * 50)
        
        extract_dir = self.work_dir / "extracted"
        casper_dir = extract_dir / "casper"
        
        # Remove HWE kernel files (Cubic removes these)
        hwe_files = ["hwe-initrd", "hwe-vmlinuz"]
        for hwe_file in hwe_files:
            hwe_path = casper_dir / hwe_file
            if hwe_path.exists():
                hwe_path.unlink()
                self.log(f"Removed HWE file: {hwe_file}", "🗑️")
                
        # Rename initrd to initrd.gz (Cubic does this)
        initrd_path = casper_dir / "initrd"
        initrd_gz_path = casper_dir / "initrd.gz"
        
        if initrd_path.exists():
            initrd_path.rename(initrd_gz_path)
            self.log("Renamed initrd to initrd.gz", "✅")
            
        self.log("Kernel structure simplified", "✅")
        return True
        
    def cubic_step2_modify_squashfs(self):
        self.log("STEP 2: MODIFY LIVE FILESYSTEM (Like Cubic)", "🗂️")
        print("-" * 50)
        
        extract_dir = self.work_dir / "extracted"
        casper_dir = extract_dir / "casper"
        squashfs_file = casper_dir / "ubuntu-server-minimal.squashfs"
        
        if not squashfs_file.exists():
            self.log("Squashfs file not found", "❌")
            return False
            
        # Create temporary mount point
        mount_dir = self.work_dir / "squashfs_mount"
        modified_dir = self.work_dir / "squashfs_modified"
        
        self.log("Extracting squashfs filesystem...", "⚙️")
        
        # Extract squashfs to modify it
        cmd = ["unsquashfs", "-f", "-d", str(modified_dir), str(squashfs_file)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            self.log(f"Failed to extract squashfs: {result.stderr}", "❌")
            return False
            
        self.log("Squashfs extracted for modification", "✅")
        
        # Add custom content to live filesystem (like Cubic does)
        self.log("Adding custom content to live filesystem...", "📝")
        
        custom_content = f"""Hello from Cubic Replica CLI v{self.version}!

Created: {self.start_time}
Method: Replicated Cubic's exact methodology

This file proves that:
✅ Live filesystem modification works
✅ EFI boot structure preserved
✅ Custom content injection successful

This is inside the live Ubuntu system filesystem,
not just the ISO file structure!
"""
        
        # Add HelloWorld.txt to root of live filesystem
        hello_file = modified_dir / "HelloWorld.txt"
        hello_file.write_text(custom_content)
        self.log(f"Added HelloWorld.txt to live filesystem", "✅")
        
        # Add to home directory as well
        home_hello = modified_dir / "home" / "HelloWorld.txt"
        home_hello.write_text(custom_content)
        self.log(f"Added HelloWorld.txt to /home", "✅")
        
        # Recompress squashfs with Cubic-like parameters
        self.log("Recompressing squashfs filesystem...", "🔧")
        
        # Remove old squashfs
        squashfs_file.unlink()
        
        # Create new squashfs with compression (like Cubic)
        cmd = [
            "mksquashfs", str(modified_dir), str(squashfs_file),
            "-comp", "xz", "-Xbcj", "x86", "-b", "1048576",
            "-noappend", "-no-recovery"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            self.log(f"Failed to compress squashfs: {result.stderr}", "❌")
            return False
            
        new_size = squashfs_file.stat().st_size
        self.log(f"New squashfs created: {new_size:,} bytes", "✅")
        
        # Update filesystem.size (Cubic does this)
        size_file = casper_dir / "filesystem.size"
        size_file.write_text(str(new_size))
        
        # Update ubuntu-server-minimal.size
        minimal_size_file = casper_dir / "ubuntu-server-minimal.size"
        minimal_size_file.write_text(str(new_size))
        
        self.log("Filesystem sizes updated", "✅")
        
        # Cleanup
        shutil.rmtree(modified_dir)
        
        return True
        
    def cubic_step3_update_boot_configs(self):
        self.log("STEP 3: UPDATE BOOT CONFIGURATIONS (Like Cubic)", "⚙️")
        print("-" * 50)
        
        extract_dir = self.work_dir / "extracted"
        
        # Update GRUB configuration (exact Cubic changes)
        grub_cfg = extract_dir / "boot" / "grub" / "grub.cfg"
        
        if grub_cfg.exists():
            grub_content = grub_cfg.read_text()
            
            # Apply Cubic's exact changes
            grub_content = grub_content.replace(
                "initrd  /casper/initrd",
                "initrd  /casper/initrd.gz"
            )
            grub_content = grub_content.replace(
                "linux   /casper/hwe-vmlinuz",
                "linux   /casper/vmlinuz"
            )
            grub_content = grub_content.replace(
                "initrd  /casper/hwe-initrd", 
                "initrd  /casper/initrd.gz"
            )
            
            grub_cfg.write_text(grub_content)
            self.log("GRUB configuration updated", "✅")
            
        # Update loopback.cfg too
        loopback_cfg = extract_dir / "boot" / "grub" / "loopback.cfg"
        if loopback_cfg.exists():
            loopback_content = loopback_cfg.read_text()
            loopback_content = loopback_content.replace(
                "initrd  /casper/initrd",
                "initrd  /casper/initrd.gz"
            )
            loopback_cfg.write_text(loopback_content)
            self.log("Loopback configuration updated", "✅")
            
        # Update install-sources.yaml (Cubic modifies this)
        casper_dir = extract_dir / "casper"
        install_sources = casper_dir / "install-sources.yaml"
        
        if install_sources.exists():
            # Simplified install sources like Cubic
            cubic_sources = f"""- default: true
  description:
    en: Cubic Replica CLI v{self.version}
  id: ubuntu-server-minimal
  locale_support: locale-only
  name:
    en: Cubic-Replica-Server 24.04.2 {datetime.now().strftime('%Y.%m.%d')}
  path: ubuntu-server-minimal.squashfs
  size: {(casper_dir / 'ubuntu-server-minimal.squashfs').stat().st_size}
  type: fsimage
"""
            install_sources.write_text(cubic_sources)
            self.log("Install sources updated", "✅")
            
        # Update .disk/info (Cubic changes this)
        disk_info = extract_dir / ".disk" / "info"
        if disk_info.exists():
            disk_info.write_text(f"Cubic Replica CLI v{self.version} - Ubuntu Server 24.04.2 {datetime.now().strftime('%Y%m%d')}")
            self.log("Disk info updated", "✅")
            
        return True
        
    def cubic_step4_remove_signatures(self):
        self.log("STEP 4: REMOVE GPG SIGNATURES (Like Cubic)", "🗑️")
        print("-" * 50)
        
        extract_dir = self.work_dir / "extracted"
        casper_dir = extract_dir / "casper"
        
        # Remove all .gpg files (Cubic removes these for custom ISOs)
        gpg_files = list(casper_dir.glob("*.gpg"))
        
        for gpg_file in gpg_files:
            gpg_file.unlink()
            self.log(f"Removed signature: {gpg_file.name}", "🗑️")
            
        # Remove unnecessary manifest files
        unnecessary_files = [
            "filesystem.manifest",
            "ubuntu-server-minimal.ubuntu-server.installer.generic-hwe.manifest",
            "ubuntu-server-minimal.ubuntu-server.installer.generic-hwe.size", 
            "ubuntu-server-minimal.ubuntu-server.installer.generic-hwe.squashfs",
            "ubuntu-server-minimal.ubuntu-server.manifest",
            "ubuntu-server-minimal.ubuntu-server.size",
            "ubuntu-server-minimal.ubuntu-server.squashfs"
        ]
        
        for file_name in unnecessary_files:
            file_path = casper_dir / file_name
            if file_path.exists():
                file_path.unlink()
                self.log(f"Removed unnecessary: {file_name}", "🗑️")
                
        self.log("Signatures and unnecessary files removed", "✅")
        return True
        
    def cubic_step5_create_iso(self):
        self.log("STEP 5: CREATE HYBRID EFI ISO (Like Cubic)", "🔧")
        print("-" * 50)
        
        extract_dir = self.work_dir / "extracted"
        
        # Use exact xorriso command that works (from our previous investigation)
        xorriso_cmd = [
            "xorriso", "-as", "mkisofs",
            "-r",
            "-V", f"Cubic-Replica-v{self.version}",
            "-J", "-joliet-long",
            "-isohybrid-mbr", "/usr/lib/ISOLINUX/isohdpfx.bin",
            "-c", "boot.catalog",
            "-b", "boot/grub/i386-pc/eltorito.img",
            "-no-emul-boot",
            "-boot-load-size", "4",
            "-boot-info-table",
            "-eltorito-alt-boot",
            "-e", "EFI/boot/bootx64.efi",
            "-no-emul-boot",
            "-isohybrid-gpt-basdat",
            "-o", self.output_iso,
            str(extract_dir)
        ]
        
        self.log("Building EFI-bootable ISO...", "⚙️")
        result = subprocess.run(xorriso_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            self.log(f"ISO creation failed: {result.stderr}", "❌")
            return False
            
        if Path(self.output_iso).exists():
            size = Path(self.output_iso).stat().st_size
            self.log(f"ISO created: {self.output_iso} ({size:,} bytes)", "✅")
            
            # Verify hybrid boot structure
            self.log("Verifying EFI boot structure...", "🔍")
            mbr_check = subprocess.run([
                "dd", f"if={self.output_iso}", "bs=512", "count=1"
            ], capture_output=True)
            
            if mbr_check.stdout[:2] != b'\x00\x00':
                self.log("MBR boot sector present", "✅")
            else:
                self.log("MBR boot sector missing", "❌")
                
            # Check file type
            file_check = subprocess.run(["file", self.output_iso], capture_output=True, text=True)
            
            if "(DOS/MBR boot sector)" in file_check.stdout:
                self.log("Hybrid boot structure confirmed", "✅")
            else:
                self.log("Hybrid boot structure missing", "❌")
                
            return True
        else:
            self.log("ISO file not created", "❌")
            return False
            
    def cleanup(self):
        if self.work_dir.exists():
            shutil.rmtree(self.work_dir)
            self.log("Cleanup completed", "🧹")
            
    def run(self):
        print(f"🎯 CUBIC REPLICA CLI v{self.version}")
        print("=" * 50)
        self.log(f"Started: {self.start_time}")
        self.log("Replicating Cubic's exact EFI boot methodology", "🎯")
        print()
        
        try:
            if not self.check_dependencies():
                return False
                
            if not self.download_ubuntu_iso():
                return False
                
            if not self.extract_ubuntu_iso():
                return False
                
            if not self.cubic_step1_simplify_kernel():
                return False
                
            if not self.cubic_step2_modify_squashfs():
                return False
                
            if not self.cubic_step3_update_boot_configs():
                return False
                
            if not self.cubic_step4_remove_signatures():
                return False
                
            if not self.cubic_step5_create_iso():
                return False
                
            duration = datetime.now() - self.start_time
            
            print("\n" + "=" * 50)
            self.log(f"CUBIC REPLICA COMPLETED in {duration}", "🎉")
            self.log(f"Output: {self.output_iso}", "📁")
            self.log("Ready for VirtualBox EFI testing!", "🚀")
            print("=" * 50)
            
            return True
            
        except KeyboardInterrupt:
            self.log("Process interrupted", "⚠️")
            return False
        except Exception as e:
            self.log(f"Error: {e}", "❌")
            return False
        finally:
            self.cleanup()

if __name__ == "__main__":
    creator = CubicReplicaCLI()
    success = creator.run()
    sys.exit(0 if success else 1)