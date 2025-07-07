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
import urllib.request
import zipfile
from pathlib import Path

def install_python_dependencies():
    """Auto-install required Python packages"""
    print("🔍 Checking Python dependencies...")
    
    try:
        import requests
        print("✅ requests already installed")
        return True
    except ImportError:
        print("📦 Installing requests package...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
            print("✅ Successfully installed requests")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install requests: {e}")
            print("Please install manually: pip install requests")
            return False

class ISOBuilder:
    def __init__(self):
        self.iso_url = "https://mirror.pilotfiber.com/ubuntu-iso/24.04.2/ubuntu-24.04.2-live-server-amd64.iso"
        self.iso_filename = "ubuntu-24.04.2-live-server-amd64.iso"
        self.yaml_url = "https://raw.githubusercontent.com/MachoDrone/instyaml/main/autoinstall.yaml"
        self.output_iso = "ubuntu-24.04.2-instyaml-amd64.iso"
        self.temp_dir = None
        self.is_windows = platform.system() == "Windows"
        
    def download_portable_tool(self, url, filename):
        """Download portable tool for Windows"""
        print(f"📥 Downloading {filename}...")
        try:
            urllib.request.urlretrieve(url, filename)
            print(f"✅ Downloaded {filename}")
            return True
        except Exception as e:
            print(f"❌ Failed to download {filename}: {e}")
            return False
    
    def install_windows_dependencies(self):
        """Install portable tools for Windows"""
        print("🔧 Installing Windows dependencies...")
        
        # Check for xorriso first
        if os.path.exists("xorriso.exe"):
            print("✅ xorriso.exe already available")
            return "xorriso.exe"
        
        if shutil.which("xorriso.exe"):
            print("✅ xorriso.exe found in PATH")
            return "xorriso.exe"
        
        # Download portable xorriso
        xorriso_url = "https://www.gnu.org/software/xorriso/xorriso-1.5.6.win32.zip"
        print("📦 Downloading portable xorriso...")
        
        try:
            # Download xorriso zip
            zip_file = "xorriso.zip"
            urllib.request.urlretrieve(xorriso_url, zip_file)
            print("✅ Downloaded xorriso.zip")
            
            # Extract xorriso.exe
            print("📂 Extracting xorriso.exe...")
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                # Look for xorriso.exe in the zip
                for file_info in zip_ref.filelist:
                    if file_info.filename.endswith('xorriso.exe'):
                        # Extract just this file to current directory
                        file_info.filename = 'xorriso.exe'
                        zip_ref.extract(file_info, '.')
                        print("✅ Extracted xorriso.exe")
                        
                        # Clean up zip file
                        os.remove(zip_file)
                        return "xorriso.exe"
                
                print("❌ xorriso.exe not found in zip file")
                return None
            
        except Exception as e:
            print(f"❌ Failed to setup xorriso: {e}")
            print("Please install manually:")
            print("1. Download xorriso from https://www.gnu.org/software/xorriso/")
            print("2. Place xorriso.exe in this script's folder")
            return None
    
    def install_linux_dependencies(self):
        """Auto-install Linux dependencies"""
        print("🔧 Installing Linux dependencies...")
        
        # Check what's already available
        tools = ["xorriso", "genisoimage", "mkisofs"]
        for tool in tools:
            if shutil.which(tool):
                print(f"✅ {tool} already installed")
                return tool
        
        # Try to install xorriso and genisoimage
        print("📦 Installing xorriso and genisoimage...")
        try:
            subprocess.check_call(["sudo", "apt", "update"])
            subprocess.check_call(["sudo", "apt", "install", "-y", "xorriso", "genisoimage"])
            
            # Check what got installed
            for tool in tools:
                if shutil.which(tool):
                    print(f"✅ Successfully installed {tool}")
                    return tool
            
            print("❌ Installation completed but tools not found in PATH")
            return None
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            print("Please install manually:")
            print("sudo apt install xorriso genisoimage")
            return None
    
    def check_dependencies(self):
        """Check and install required tools"""
        print("🔍 Checking system dependencies...")
        
        if self.is_windows:
            return self.install_windows_dependencies()
        else:
            return self.install_linux_dependencies()
    
    def download_iso(self):
        """Download Ubuntu ISO if not present"""
        if os.path.exists(self.iso_filename):
            print(f"✅ {self.iso_filename} already exists")
            return True
        
        print(f"📥 Downloading {self.iso_filename}...")
        print(f"From: {self.iso_url}")
        
        try:
            # Import requests (should be installed by now)
            import requests
            
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
            import requests
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
                
                # Make copied files writable
                subprocess.run(["chmod", "-R", "u+w", extract_dir], check=True)
            
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
            try:
                # Make sure all files are writable before deletion
                subprocess.run(["chmod", "-R", "u+w", self.temp_dir], check=False)
                shutil.rmtree(self.temp_dir)
                print("🧹 Cleaned up temporary files")
            except Exception as e:
                print(f"⚠️ Cleanup warning: {e}")
                print("Some temporary files may remain in /tmp/")
    
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
    # Bold blue text for header (ANSI escape codes)
    BLUE_BOLD = '\033[1;34m'
    RESET = '\033[0m'
    
    print(f"{BLUE_BOLD}INSTYAML ISO Builder v0.3{RESET}")
    print(f"{BLUE_BOLD}Building Ubuntu 24.04.2 with autoinstall YAML{RESET}")
    print(f"{BLUE_BOLD}📅 Script Updated: 2025-07-07 17:00 UTC{RESET}")
    print(f"{BLUE_BOLD}🔗 https://github.com/MachoDrone/instyaml{RESET}")
    print()  # Extra space for easy finding
    
    # Check if we're on Linux and will need sudo
    if platform.system() == "Linux":
        print("🔐 This script needs sudo access to mount ISO files.")
        print("Please enter your password when prompted...")
        
        # Test sudo access early
        try:
            subprocess.run(["sudo", "-v"], check=True)
            print("✅ Sudo access confirmed")
        except subprocess.CalledProcessError:
            print("❌ Sudo access required for ISO mounting")
            sys.exit(1)
        print()
    
    # First, ensure Python dependencies are installed
    if not install_python_dependencies():
        print("❌ Failed to install Python dependencies")
        sys.exit(1)
    
    builder = ISOBuilder()
    success = builder.build()
    
    sys.exit(0 if success else 1)