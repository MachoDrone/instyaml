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
import signal
import atexit
from pathlib import Path

# Check for sudo access immediately on Linux
if platform.system() == "Linux":
    print("🔐 This script needs sudo access to mount ISO files.")
    try:
        subprocess.run(["sudo", "-v"], check=True)
        print("✅ Sudo access confirmed")
    except subprocess.CalledProcessError:
        print("❌ Sudo access required for ISO mounting")
        sys.exit(1)
    print()

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

def cleanup_sudo():
    """Global cleanup function to clear sudo cache"""
    if platform.system() == "Linux":
        try:
            subprocess.run(["sudo", "-k"], check=False)
            print("🔐 Cleared sudo credentials cache")
        except Exception:
            pass

def signal_handler(signum, frame):
    """Handle script interruption (Ctrl+C, etc.)"""
    print(f"\n⚠️ Script interrupted by signal {signum}")
    cleanup_sudo()
    sys.exit(1)

class ISOBuilder:
    def __init__(self):
        self.iso_url = "https://mirror.pilotfiber.com/ubuntu-iso/24.04.2/ubuntu-24.04.2-live-server-amd64.iso"
        self.iso_filename = "ubuntu-24.04.2-live-server-amd64.iso"
        self.yaml_url = "https://raw.githubusercontent.com/MachoDrone/instyaml/main/autoinstall.yaml"
        self.output_iso = "instyaml-ubuntu-24.04.2-autoinstall.iso"
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
    
    def find_efi_image(self, extract_dir):
        """Find the correct EFI boot image path"""
        possible_paths = [
            "boot/grub/efi.img",
            "EFI/boot/grubx64.efi", 
            "casper/vmlinuz",
            "boot/grub/x86_64-efi/core.efi"
        ]
        
        for path in possible_paths:
            full_path = os.path.join(extract_dir, path)
            if os.path.exists(full_path):
                print(f"✅ Found EFI image: {path}")
                return path
        
        print("⚠️ No EFI image found, using legacy boot only")
        return None
    
    def create_iso(self, extract_dir, tool):
        """Create new ISO"""
        print(f"💿 Creating new ISO: {self.output_iso}")
        
        # Find EFI boot image
        efi_image = self.find_efi_image(extract_dir)
        
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
                # Linux - use xorriso in mkisofs compatibility mode
                if "xorriso" in tool:
                    cmd = [
                        tool, "-as", "mkisofs",
                        "-r", "-V", "Ubuntu 24.04.2 INSTYAML",
                        "-J", "-joliet-long",
                        "-b", "boot/grub/i386-pc/eltorito.img",
                        "-no-emul-boot",
                        "-boot-load-size", "4",
                        "-boot-info-table"
                    ]
                    
                    # Add EFI boot if available
                    if efi_image:
                        cmd.extend([
                            "-eltorito-alt-boot",
                            "-e", efi_image,
                            "-no-emul-boot",
                            "-isohybrid-gpt-basdat"
                        ])
                    
                    cmd.extend(["-o", self.output_iso, extract_dir])
                    
                else:
                    # genisoimage or mkisofs
                    cmd = [
                        tool,
                        "-r", "-V", "Ubuntu 24.04.2 INSTYAML",
                        "-J", "-joliet-long",
                        "-b", "boot/grub/i386-pc/eltorito.img",
                        "-no-emul-boot",
                        "-boot-load-size", "4",
                        "-boot-info-table"
                    ]
                    
                    # Add EFI boot if available
                    if efi_image:
                        cmd.extend([
                            "-eltorito-alt-boot",
                            "-e", efi_image,
                            "-no-emul-boot"
                        ])
                    
                    cmd.extend(["-o", self.output_iso, extract_dir])
            
            subprocess.run(cmd, check=True)
            print(f"✅ Created {self.output_iso}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ ISO creation failed: {e}")
            return False
    
    def inspect_iso(self):
        """Verify the created ISO has our modifications"""
        if not os.path.exists(self.output_iso):
            print("❌ Cannot inspect - ISO file not found")
            return False
            
        print("🔍 Inspecting created ISO for modifications...")
        
        if self.is_windows:
            print("⚠️ ISO inspection not implemented for Windows yet")
            return True
            
        # Linux: Mount and inspect
        temp_mount = tempfile.mkdtemp(prefix="instyaml_inspect_")
        
        try:
            # Mount the created ISO
            subprocess.run(["sudo", "mount", "-o", "loop,ro", self.output_iso, temp_mount], check=True)
            
            # Check 1: autoinstall.yaml exists
            yaml_path = os.path.join(temp_mount, "autoinstall.yaml")
            if os.path.exists(yaml_path):
                print("✅ autoinstall.yaml found in ISO root")
                
                # Check YAML content
                with open(yaml_path, 'r') as f:
                    yaml_content = f.read()
                    if "github.com/MachoDrone/instyaml" in yaml_content:
                        print("✅ autoinstall.yaml contains GitHub URL")
                    else:
                        print("⚠️ autoinstall.yaml missing GitHub URL")
            else:
                print("❌ autoinstall.yaml NOT found in ISO root")
            
            # Check 2: GRUB config has autoinstall parameters
            grub_path = os.path.join(temp_mount, "boot", "grub", "grub.cfg")
            if os.path.exists(grub_path):
                with open(grub_path, 'r') as f:
                    grub_content = f.read()
                    if "autoinstall" in grub_content and "ds=nocloud-net" in grub_content:
                        print("✅ GRUB config contains autoinstall parameters")
                    else:
                        print("❌ GRUB config missing autoinstall parameters")
            else:
                print("⚠️ GRUB config not found")
            
            # Check 3: File count (rough verification)
            file_count = 0
            for root, dirs, files in os.walk(temp_mount):
                file_count += len(files)
            
            if file_count > 1000:  # Original Ubuntu ISO has ~1079 files
                print(f"✅ File count looks good: {file_count} files")
            else:
                print(f"⚠️ Low file count: {file_count} files")
            
            # Check 4: ISO size
            iso_size_gb = os.path.getsize(self.output_iso) / (1024*1024*1024)
            if iso_size_gb > 2.5:  # Should be ~3GB
                print(f"✅ ISO size looks good: {iso_size_gb:.1f} GB")
            else:
                print(f"⚠️ ISO size seems small: {iso_size_gb:.1f} GB")
            
            print("🎯 Inspection complete - ISO appears ready for testing!")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to mount ISO for inspection: {e}")
            return False
        except Exception as e:
            print(f"⚠️ Inspection error: {e}")
            return False
        finally:
            # Unmount
            try:
                subprocess.run(["sudo", "umount", temp_mount], check=False)
                os.rmdir(temp_mount)
            except:
                pass
    
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
            
            # Inspect the created ISO
            print()
            if not self.inspect_iso():
                print("⚠️ ISO inspection had issues - manual verification recommended")
            
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
    # Register cleanup handlers for unexpected exits
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    atexit.register(cleanup_sudo)  # Normal exit cleanup
    
    # Bold blue text for header (ANSI escape codes)
    BLUE_BOLD = '\033[1;34m'
    RESET = '\033[0m'
    
    print(f"{BLUE_BOLD}INSTYAML ISO Builder v0.08.00{RESET}")
    print(f"{BLUE_BOLD}Building Ubuntu 24.04.2 with autoinstall YAML{RESET}")
    print(f"{BLUE_BOLD}📅 Script Updated: 2025-07-07 17:50 UTC{RESET}")
    print(f"{BLUE_BOLD}🔗 https://github.com/MachoDrone/instyaml{RESET}")
    print()  # Extra space for easy finding
    
    # First, ensure Python dependencies are installed
    if not install_python_dependencies():
        print("❌ Failed to install Python dependencies")
        sys.exit(1)
    
    builder = ISOBuilder()
    success = builder.build()
    
    sys.exit(0 if success else 1)