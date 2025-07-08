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

# Moved sudo check to after header display

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
    """Global cleanup function to clear sudo cache (silent for exit handler)"""
    if platform.system() == "Linux":
        try:
            subprocess.run(["sudo", "-k"], check=False)
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
        self.output_iso = "instyaml-24.04.2-beta.iso"
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
            
            # Add autoinstall to kernel parameters (try multiple patterns)
            original_content = content
            
            # Pattern 1: Standard casper boot
            content = content.replace(
                'linux /casper/vmlinuz',
                'linux /casper/vmlinuz autoinstall ds=nocloud-net\\;s=cd:/'
            )
            
            # Pattern 2: Alternative patterns
            if content == original_content:
                content = content.replace(
                    'linux\t/casper/vmlinuz',
                    'linux\t/casper/vmlinuz autoinstall ds=nocloud-net\\;s=cd:/'
                )
            
            # Pattern 3: Any vmlinuz reference
            if content == original_content:
                import re
                content = re.sub(
                    r'(linux\s+/casper/vmlinuz\S*)',
                    r'\1 autoinstall ds=nocloud-net\;s=cd:/',
                    content
                )
            
            with open(grub_cfg, 'w') as f:
                f.write(content)
            
            if content != original_content:
                print("✅ Modified GRUB configuration")
            else:
                print("⚠️ GRUB configuration unchanged - pattern not found")
                # Debug: show what patterns exist
                if 'vmlinuz' in original_content:
                    print("🔍 Found vmlinuz references in GRUB config")
                else:
                    print("🔍 No vmlinuz references found in GRUB config")
        
        return True
    
    def find_efi_image(self, extract_dir):
        """Check for EFI boot executables (Ubuntu 24.04.2 uses multiple EFI files)"""
        # Ubuntu 24.04.2 uses multiple EFI executables for full compatibility
        efi_dir = os.path.join(extract_dir, "EFI", "boot")
        
        if not os.path.exists(efi_dir):
            print("⚠️ No EFI directory found - EFI boot will be disabled")
            return False
        
        # Check for the three critical EFI files
        efi_files = {
            "bootx64.efi": "Primary EFI boot loader",
            "grubx64.efi": "GRUB EFI executable", 
            "mmx64.efi": "Memory test utility"
        }
        
        found_files = []
        missing_files = []
        
        for filename, description in efi_files.items():
            file_path = os.path.join(efi_dir, filename)
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                print(f"✅ Found {filename}: {description} ({file_size} bytes)")
                found_files.append(filename)
            else:
                print(f"⚠️ Missing {filename}: {description}")
                missing_files.append(filename)
        
        # bootx64.efi is critical for EFI boot
        if "bootx64.efi" in found_files:
            print(f"✅ EFI boot should work - found {len(found_files)}/3 EFI files")
            return True
        else:
            print("❌ Critical: bootx64.efi missing - EFI boot will fail")
            return False
    
    def handle_existing_iso(self):
        """Handle existing output ISO file"""
        if not os.path.exists(self.output_iso):
            return True  # No existing file, proceed
        
        # Always prompt for user choice - no automatic defaults
        
        print()  # Extra space before warning
        print(f"\033[1;31m⚠️ {self.output_iso} already exists\033[0m")  # Bold red warning
        while True:
            try:
                # For piped execution, redirect input to terminal
                import sys
                if not sys.stdin.isatty():
                    try:
                        sys.stdin = open('/dev/tty', 'r')
                    except (OSError, FileNotFoundError):
                        # Fallback for systems without /dev/tty (like Windows)
                        print("❌ Cannot get interactive input in piped mode")
                        print("💡 Run: python3 iso_builder.py (after downloading)")
                        return False
                
                choice = input("🤔 [O]verwrite, [B]ackup, [C]ancel? ").strip().upper()
                print()  # Blank line after user choice
                
                if choice == 'O':
                    print(f"🔄 Will overwrite {self.output_iso}")
                    return True
                    
                elif choice == 'B':
                    backup_name = f"{self.output_iso}.backup"
                    counter = 1
                    while os.path.exists(backup_name):
                        backup_name = f"{self.output_iso}.backup.{counter}"
                        counter += 1
                    
                    try:
                        shutil.move(self.output_iso, backup_name)
                        print(f"📦 Backed up existing ISO to: {backup_name}")
                        return True
                    except Exception as e:
                        print(f"❌ Failed to backup: {e}")
                        continue
                        
                elif choice == 'C':
                    print("❌ ISO creation cancelled by user")
                    return False
                    
                else:
                    print("Please enter O, B, or C")
                    
            except KeyboardInterrupt:
                print("\n❌ Cancelled by user")
                return False
            except EOFError:
                print("\n❌ No input available - cancelling")
                return False
    
    def create_iso(self, extract_dir, tool):
        """Create new ISO"""
        # Check for existing ISO and handle user choice
        if not self.handle_existing_iso():
            return False
        
        print(f"💿 Creating new ISO: {self.output_iso}")
        
        # Check for EFI boot support (Ubuntu 24.04.2 uses direct EFI executables)
        has_efi_support = self.find_efi_image(extract_dir)
        
        try:
            if self.is_windows:
                if "xorriso" in tool:
                    cmd = [
                        "xorriso.exe",
                        "-as", "mkisofs",
                        "-r", "-V", "Ubuntu 24.04.2 INSTYAML",
                        "-J", "-joliet-long",
                        "-cache-inodes",  # Ubuntu parameter for efficiency
                        "-b", "boot/grub/i386-pc/eltorito.img",
                        "-c", "boot.catalog",  # Boot catalog location (Ubuntu 24.04.2)
                        "-no-emul-boot",
                        "-boot-load-size", "4",
                        "-boot-info-table"
                    ]
                    
                    # Ubuntu 24.04.2 uses direct EFI executables - no El Torito EFI needed
                    # EFI boot is handled automatically by the EFI/boot/grubx64.efi file
                    # Just add GPT support for hybrid boot
                    if has_efi_support:
                        cmd.extend([
                            "-isohybrid-gpt-basdat"
                        ])
                    
                    # Add hybrid boot and partition support (Ubuntu parameters)
                    cmd.extend([
                        "-partition_offset", "16",  # Ubuntu uses this for hybrid boot
                        "-o", self.output_iso,
                        extract_dir
                    ])
                elif "oscdimg" in tool:
                    cmd = [
                        "oscdimg.exe",
                        "-n", "-m",
                        "-b", os.path.join(extract_dir, "boot", "grub", "i386-pc", "eltorito.img"),
                        extract_dir,
                        self.output_iso
                    ]
            else:
                # Linux - use xorriso in mkisofs compatibility mode (Ubuntu-compatible)
                if "xorriso" in tool:
                    cmd = [
                        tool, "-as", "mkisofs",
                        "-r", "-V", "Ubuntu 24.04.2 INSTYAML",
                        "-J", "-joliet-long",
                        "-cache-inodes",  # Ubuntu parameter for efficiency
                        "-b", "boot/grub/i386-pc/eltorito.img",
                        "-c", "boot.catalog",  # Boot catalog location (Ubuntu 24.04.2)
                        "-no-emul-boot",
                        "-boot-load-size", "4",
                        "-boot-info-table"
                    ]
                    
                    # Ubuntu 24.04.2 uses direct EFI executables - no El Torito EFI needed
                    # EFI boot is handled automatically by the EFI/boot/grubx64.efi file
                    # Just add GPT support for hybrid boot
                    if has_efi_support:
                        cmd.extend([
                            "-isohybrid-gpt-basdat"
                        ])
                    
                    # Add hybrid boot and partition support (Ubuntu parameters)
                    cmd.extend([
                        "-partition_offset", "16",  # Ubuntu uses this for hybrid boot
                        "-o", self.output_iso, 
                        extract_dir
                    ])
                    
                else:
                    # genisoimage or mkisofs (fallback - limited EFI support)
                    cmd = [
                        tool,
                        "-r", "-V", "Ubuntu 24.04.2 INSTYAML",
                        "-J", "-joliet-long",
                        "-b", "boot/grub/i386-pc/eltorito.img",
                        "-c", "boot.catalog",  # Boot catalog location (Ubuntu 24.04.2)
                        "-no-emul-boot",
                        "-boot-load-size", "4",
                        "-boot-info-table"
                    ]
                    
                    # Note: genisoimage has limited EFI support compared to xorriso
                    # EFI boot relies on direct EFI/boot/grubx64.efi executable
                    if has_efi_support:
                        print("⚠️ Using genisoimage - EFI boot support may be limited")
                    
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
                    if "MachoDrone/instyaml" in yaml_content:
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
                    has_autoinstall = "autoinstall" in grub_content
                    has_datasource = "ds=nocloud-net" in grub_content or "ds=nocloud" in grub_content
                    
                    if has_autoinstall and has_datasource:
                        print("✅ GRUB config contains autoinstall parameters")
                    elif has_autoinstall:
                        print("⚠️ GRUB config has autoinstall but missing datasource")
                    elif has_datasource:
                        print("⚠️ GRUB config has datasource but missing autoinstall")
                    else:
                        print("❌ GRUB config missing autoinstall parameters")
                        
                        # Debug: show what we found
                        if "vmlinuz" in grub_content:
                            print("🔍 Debug: Found vmlinuz in GRUB, but no autoinstall params")
                        else:
                            print("🔍 Debug: No vmlinuz found in GRUB config")
            else:
                print("⚠️ GRUB config not found")
            
            # Check 3: File count (rough verification)
            file_count = 0
            for root, dirs, files in os.walk(temp_mount):
                file_count += len(files)
            
            if file_count > 800:  # Modified ISO typically has ~871 files (down from ~1079)
                print(f"✅ File count looks good: {file_count} files")
            else:
                print(f"⚠️ Low file count: {file_count} files")
            
            # Check 4: EFI boot support (Ubuntu 24.04.2 uses multiple EFI files)
            efi_dir = os.path.join(temp_mount, "EFI", "boot")
            if os.path.exists(efi_dir):
                efi_files = ["bootx64.efi", "grubx64.efi", "mmx64.efi"]
                found_efi = []
                for efi_file in efi_files:
                    efi_path = os.path.join(efi_dir, efi_file)
                    if os.path.exists(efi_path):
                        efi_size = os.path.getsize(efi_path)
                        print(f"✅ Found {efi_file}: {efi_size} bytes")
                        found_efi.append(efi_file)
                
                if "bootx64.efi" in found_efi:
                    print(f"✅ EFI boot should work: {len(found_efi)}/3 EFI files present")
                else:
                    print("❌ Critical: bootx64.efi missing - EFI boot will fail")
            else:
                print("⚠️ EFI directory not found - EFI boot will fail")
            
            # Check 5: ISO size
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
    
    def cleanup_ancillary_files(self):
        """Remove temporary ancillary files created during ISO building"""
        files_to_remove = ["iso_builder.py", "autoinstall.yaml"]
        
        for filename in files_to_remove:
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                    print(f"🗑️ Removed {filename}")
                except Exception as e:
                    print(f"⚠️ Could not remove {filename}: {e}")
    
    def offer_cleanup_original_iso(self):
        """Offer to remove the original Ubuntu ISO to save space"""
        # Removed per user request - don't show space optimization suggestions
        pass
        
    def cleanup(self):
        """Clean up temporary files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                # Make sure all files are writable before deletion
                subprocess.run(["chmod", "-R", "u+w", self.temp_dir], check=False)
                shutil.rmtree(self.temp_dir)
                # Clear sudo credentials (silent - message shown in main output)
                if platform.system() == "Linux":
                    subprocess.run(["sudo", "-k"], check=False)
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
            
            # Clean up temporary files
            self.cleanup_ancillary_files()
            
            print("=" * 50)
            print(f"📀 {self.output_iso} is ready.")
            print("🧹 Removed temp files, exited sudo")
            print()
            print("🔥 Next steps:")
            print("1. Burn to USB with Rufus/dd")
            print("2. Boot and watch for GitHub-downloaded messages")
            print("3. Edit install.sh in GitHub to test updates")
            print()
            
            # Offer to remove original ISO
            self.offer_cleanup_original_iso()
            
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
    
    print()
    print()
    # NOSANA ASCII art in bold green
    DGREEN = '\033[0;32m'
    NC = '\033[0m'
    print(f"{DGREEN}               | \\ \\ \\  |{NC}")
    print(f"{DGREEN}               |  \\ \\ \\ |{NC}")
    print(f"{DGREEN}               | \\ \\ \\  |{NC}")
    print(f"{DGREEN}               |  \\_\\ \\_|{NC}")
    print()
    print(f"               {DGREEN}N O S A N A{NC}")
    print()
    print(f"{DGREEN}Building Ubuntu 24.04.2 with autoinstall YAML - v0.00.23{NC}")
    print("📅 Script Updated: 2025-01-08 17:45 UTC")
    print()
    
    # Check for sudo access on Linux
    if platform.system() == "Linux":
        print("🔑 This script needs sudo access to mount ISO files.")
        try:
            subprocess.run(["sudo", "-v"], check=True)
        except subprocess.CalledProcessError:
            print("❌ Sudo access required for ISO mounting")
            sys.exit(1)
        print()  # Extra space after sudo section
    
    # First, ensure Python dependencies are installed
    if not install_python_dependencies():
        print("❌ Failed to install Python dependencies")
        sys.exit(1)
    
    builder = ISOBuilder()
    success = builder.build()
    
    sys.exit(0 if success else 1)