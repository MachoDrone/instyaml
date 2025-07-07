#!/usr/bin/env python3
"""
INSTYAML ISO Builder
Downloads Ubuntu 24.04.2 ISO, adds autoinstall YAML, and creates bootable ISO
Works on Windows and Linux
"""

import os
import sys
import platform
import subprocess
import tempfile
import shutil
import requests
from pathlib import Path
import urllib.request

class ISOBuilder:
    def __init__(self):
        self.iso_url = "https://mirror.pilotfiber.com/ubuntu-iso/24.04.2/ubuntu-24.04.2-live-server-amd64.iso"
        self.iso_filename = "ubuntu-24.04.2-live-server-amd64.iso"
        self.yaml_url = "https://raw.githubusercontent.com/MachoDrone/instyaml/main/autoinstall.yaml"
        self.output_iso = "ubuntu-24.04.2-instyaml-amd64.iso"
        self.temp_dir = None
        self.is_windows = platform.system() == "Windows"
        
    def check_dependencies(self):
        """Check if required tools are available"""
        print("🔍 Checking dependencies...")
        
        if self.is_windows:
            # Check for xorriso or oscdimg
            tools = ["xorriso.exe", "oscdimg.exe"]
            for tool in tools:
                if shutil.which(tool):
                    print(f"✅ Found {tool}")
                    return tool
            
            print("❌ Missing ISO creation tools")
            print("Install xorriso or Windows ADK (oscdimg)")
            print("Recommendation: Download xorriso for Windows")
            return None
        else:
            # Linux: check for xorriso, genisoimage, or mkisofs
            tools = ["xorriso", "genisoimage", "mkisofs"]
            for tool in tools:
                if shutil.which(tool):
                    print(f"✅ Found {tool}")
                    return tool
            
            print("❌ Missing ISO creation tools")
            print("Install with: sudo apt install xorriso genisoimage")
            return None
    
    def download_iso(self):
        """Download Ubuntu ISO if not present"""
        if os.path.exists(self.iso_filename):
            print(f"✅ {self.iso_filename} already exists")
            return True
        
        print(f"📥 Downloading {self.iso_filename}...")
        print(f"From: {self.iso_url}")
        
        try:
            # Download with progress
            response = requests.get(self.iso_url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(self.iso_filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r📥 Progress: {percent:.1f}%", end='', flush=True)
            
            print(f"\n✅ Downloaded {self.iso_filename}")
            return True
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return False
    
    def download_yaml(self):
        """Download autoinstall YAML from GitHub"""
        print("📥 Downloading autoinstall.yaml from GitHub...")
        
        try:
            response = requests.get(self.yaml_url)
            response.raise_for_status()
            
            with open("autoinstall.yaml", 'w') as f:
                f.write(response.text)
            
            print("✅ Downloaded autoinstall.yaml")
            return True
            
        except Exception as e:
            print(f"❌ Failed to download YAML: {e}")
            return False
    
    def extract_iso(self, tool):
        """Extract ISO contents"""
        print("📂 Extracting ISO contents...")
        
        self.temp_dir = tempfile.mkdtemp(prefix="instyaml_")
        extract_dir = os.path.join(self.temp_dir, "iso_extract")
        os.makedirs(extract_dir)
        
        try:
            if self.is_windows:
                # Windows: Use 7zip or mount
                if shutil.which("7z.exe"):
                    cmd = ["7z.exe", "x", self.iso_filename, f"-o{extract_dir}"]
                    subprocess.run(cmd, check=True)
                else:
                    print("❌ Need 7zip to extract ISO on Windows")
                    return False
            else:
                # Linux: Mount and copy
                mount_point = os.path.join(self.temp_dir, "iso_mount")
                os.makedirs(mount_point)
                
                # Mount ISO
                subprocess.run(["sudo", "mount", "-o", "loop", self.iso_filename, mount_point], check=True)
                
                # Copy contents
                subprocess.run(["cp", "-rT", mount_point, extract_dir], check=True)
                
                # Unmount
                subprocess.run(["sudo", "umount", mount_point], check=True)
            
            print(f"✅ Extracted to {extract_dir}")
            return extract_dir
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Extraction failed: {e}")
            return None
    
    def modify_iso(self, extract_dir):
        """Add autoinstall YAML and modify boot configuration"""
        print("🔧 Modifying ISO...")
        
        # Copy autoinstall.yaml to root of ISO
        yaml_dest = os.path.join(extract_dir, "autoinstall.yaml")
        shutil.copy("autoinstall.yaml", yaml_dest)
        print("✅ Added autoinstall.yaml to ISO")
        
        # Modify grub.cfg to enable autoinstall
        grub_cfg = os.path.join(extract_dir, "boot", "grub", "grub.cfg")
        
        if os.path.exists(grub_cfg):
            print("🔧 Modifying GRUB configuration...")
            
            with open(grub_cfg, 'r') as f:
                content = f.read()
            
            # Add autoinstall to kernel parameters
            content = content.replace(
                'linux /casper/vmlinuz',
                'linux /casper/vmlinuz autoinstall ds=nocloud-net\\;s=cd:/'
            )
            
            with open(grub_cfg, 'w') as f:
                f.write(content)
            
            print("✅ Modified GRUB configuration")
        
        return True
    
    def create_iso(self, extract_dir, tool):
        """Create new ISO"""
        print(f"💿 Creating new ISO: {self.output_iso}")
        
        try:
            if self.is_windows:
                if "xorriso" in tool:
                    cmd = [
                        "xorriso.exe",
                        "-as", "mkisofs",
                        "-r", "-V", "Ubuntu 24.04.2 INSTYAML",
                        "-J", "-joliet-long",
                        "-b", "boot/grub/i386-pc/eltorito.img",
                        "-no-emul-boot",
                        "-boot-load-size", "4",
                        "-boot-info-table",
                        "-eltorito-alt-boot",
                        "-e", "boot/grub/efi.img",
                        "-no-emul-boot",
                        "-isohybrid-gpt-basdat",
                        "-o", self.output_iso,
                        extract_dir
                    ]
                elif "oscdimg" in tool:
                    cmd = [
                        "oscdimg.exe",
                        "-n", "-m",
                        "-b", os.path.join(extract_dir, "boot", "grub", "i386-pc", "eltorito.img"),
                        extract_dir,
                        self.output_iso
                    ]
            else:
                # Linux
                cmd = [
                    tool,
                    "-r", "-V", "Ubuntu 24.04.2 INSTYAML",
                    "-J", "-joliet-long",
                    "-b", "boot/grub/i386-pc/eltorito.img",
                    "-no-emul-boot",
                    "-boot-load-size", "4",
                    "-boot-info-table",
                    "-eltorito-alt-boot",
                    "-e", "boot/grub/efi.img",
                    "-no-emul-boot",
                    "-isohybrid-gpt-basdat",
                    "-o", self.output_iso,
                    extract_dir
                ]
            
            subprocess.run(cmd, check=True)
            print(f"✅ Created {self.output_iso}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ ISO creation failed: {e}")
            return False
    
    def cleanup(self):
        """Clean up temporary files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            print("🧹 Cleaned up temporary files")
    
    def build(self):
        """Main build process"""
        print("🚀 INSTYAML ISO Builder Starting...")
        print("=" * 50)
        
        try:
            # Check dependencies
            tool = self.check_dependencies()
            if not tool:
                return False
            
            # Download ISO
            if not self.download_iso():
                return False
            
            # Download YAML
            if not self.download_yaml():
                return False
            
            # Extract ISO
            extract_dir = self.extract_iso(tool)
            if not extract_dir:
                return False
            
            # Modify ISO
            if not self.modify_iso(extract_dir):
                return False
            
            # Create new ISO
            if not self.create_iso(extract_dir, tool):
                return False
            
            print("=" * 50)
            print("🎉 SUCCESS! Your INSTYAML ISO is ready:")
            print(f"📀 {self.output_iso}")
            print(f"📏 Size: {os.path.getsize(self.output_iso) / (1024*1024*1024):.1f} GB")
            print("\n🔥 Next steps:")
            print("1. Burn to USB with Rufus/dd")
            print("2. Boot and watch for GitHub-downloaded messages")
            print("3. Edit install.sh in GitHub to test updates")
            
            return True
            
        except Exception as e:
            print(f"❌ Build failed: {e}")
            return False
        
        finally:
            self.cleanup()

if __name__ == "__main__":
    print("INSTYAML ISO Builder")
    print("Building Ubuntu 24.04.2 with autoinstall YAML")
    print()
    
    builder = ISOBuilder()
    success = builder.build()
    
    sys.exit(0 if success else 1)