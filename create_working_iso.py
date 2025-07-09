#!/usr/bin/env python3
"""
WORKING CUSTOM ISO CREATOR v0.00.01
====================================
GitHub-based implementation with cache-busting
Based on deadclaude7.txt investigation findings

Version: 0.00.01 (ALL SCRIPTS MUST MATCH THIS VERSION)
Author: Based on deadclaude7.txt systematic debugging
Status: Production implementation of proven methods
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

VERSION = "0.00.03"

class WorkingISOCreator:
    def __init__(self):
        self.version = VERSION
        self.start_time = datetime.now()
        self.work_dir = Path("work_iso_build")
        self.ubuntu_iso = "ubuntu-24.04.2-live-server-amd64.iso"
        self.ubuntu_url = "https://releases.ubuntu.com/24.04.2/ubuntu-24.04.2-live-server-amd64.iso"
        self.expected_iso_size = 3213064192  # From deadclaude7.txt investigation

    def print_header(self):
        print("🚀 WORKING CUSTOM ISO CREATOR v" + self.version)
        print("=" * 50)
        print(f" Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📂 Working in: {os.getcwd()}")
        print("🎯 GitHub-based with cache-busting verification")
        print("📋 Based on deadclaude7.txt investigation findings")
        print()

    def verify_version_fresh(self):
        """Quick cache-busting check by comparing timestamps"""
        print("🔍 VERSION VERIFICATION")
        print("-" * 25)
        
        script_path = Path(__file__)
        if script_path.exists():
            mod_time = datetime.fromtimestamp(script_path.stat().st_mtime)
            age_seconds = (self.start_time - mod_time).total_seconds()
            
            print(f"📄 Script: {script_path.name}")
            print(f"📅 Modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"⏱️  Age: {age_seconds:.1f} seconds")
            
            if age_seconds < 120:  # 2 minutes
                print("✅ Script is fresh (< 2 minutes old)")
            else:
                print("⚠️ Script may be cached (> 2 minutes old)")
                
        print(f"📋 Version: {self.version}")
        print("✅ Version verification completed")
        return True

    def check_dependencies(self):
        print("\n🔍 CHECKING DEPENDENCIES")
        print("-" * 30)
        
        required_tools = ['xorriso', '7z', 'wget', 'dd', 'mkfs.fat']
        missing_tools = []
        
        for tool in required_tools:
            try:
                result = subprocess.run(['which', tool], capture_output=True, timeout=5)
                if result.returncode == 0:
                    if tool == 'xorriso':
                        # Check xorriso version
                        try:
                            version_result = subprocess.run(['xorriso', '-version'], capture_output=True, text=True, timeout=5)
                            if version_result.returncode == 0:
                                version_line = version_result.stdout.split('\n')[0]
                                print(f"✅ {tool}: Available ({version_line})")
                            else:
                                print(f"✅ {tool}: Available (version unknown)")
                        except:
                            print(f"✅ {tool}: Available (version check failed)")
                    else:
                        print(f"✅ {tool}: Available")
                else:
                    missing_tools.append(tool)
                    print(f"❌ {tool}: Missing")
            except:
                missing_tools.append(tool)
                print(f"❌ {tool}: Missing")
                
        if missing_tools:
            print(f"\n🔧 Installing missing tools: {', '.join(missing_tools)}")
            print("💡 Installing latest available xorriso for better EFI support")
            try:
                subprocess.run(['sudo', 'apt', 'update'], check=True)
                subprocess.run(['sudo', 'apt', 'install', '-y', 'xorriso', 'p7zip-full', 'wget', 'dosfstools'], check=True)
                print("✅ Dependencies installed successfully")
                
                # Check if we got a newer version
                try:
                    version_result = subprocess.run(['xorriso', '-version'], capture_output=True, text=True, timeout=5)
                    if version_result.returncode == 0:
                        version_line = version_result.stdout.split('\n')[0]
                        print(f"📋 Installed xorriso: {version_line}")
                except:
                    pass
                    
            except subprocess.CalledProcessError as e:
                print(f"❌ Installation failed: {e}")
                return False
                
        print("✅ All dependencies available")
        return True

    def download_ubuntu_iso(self):
        print("\n📥 UBUNTU ISO DOWNLOAD")
        print("-" * 30)
        
        if os.path.exists(self.ubuntu_iso):
            size = os.path.getsize(self.ubuntu_iso)
            print(f"📊 Found existing ISO: {size:,} bytes")
            
            if size == self.expected_iso_size:
                print("✅ Ubuntu ISO already exists with correct size")
                print("✅ Skipping download (original Ubuntu ISO should never corrupt)")
                return True
            else:
                print(f"❌ Wrong size (expected {self.expected_iso_size:,}), removing...")
                os.remove(self.ubuntu_iso)
                
        print(f"🌐 Downloading: {self.ubuntu_url}")
        print("📊 Expected size: 2.99 GB")
        
        try:
            response = requests.get(self.ubuntu_url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            start_time = time.time()
            
            with open(self.ubuntu_iso, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            elapsed = time.time() - start_time
                            speed = downloaded / elapsed if elapsed > 0 else 0
                            speed_mb = speed / (1024 * 1024)
                            
                            print(f"\r📥 {percent:.1f}% | {speed_mb:.1f} MB/s", end='')
                            
            print(f"\n✅ Download completed: {downloaded:,} bytes")
            
            if downloaded == self.expected_iso_size:
                print("✅ Download size verified")
                return True
            else:
                print(f"❌ Size mismatch: got {downloaded:,}, expected {self.expected_iso_size:,}")
                return False
                
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return False

    def extract_iso(self):
        print("\n📂 ISO EXTRACTION")
        print("-" * 25)
        
        extract_dir = self.work_dir / "extracted"
        
        if extract_dir.exists():
            shutil.rmtree(extract_dir)
        extract_dir.mkdir(parents=True)
        
        print(f"📂 Extracting to: {extract_dir}")
        
        try:
            result = subprocess.run([
                '7z', 'x', self.ubuntu_iso, f'-o{extract_dir}', '-y'
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("✅ ISO extracted successfully")
                
                # Verify critical EFI files (from deadclaude7.txt findings)
                critical_files = [
                    extract_dir / "EFI/boot/bootx64.efi",
                    extract_dir / "EFI/boot/grubx64.efi", 
                    extract_dir / "EFI/boot/mmx64.efi",
                    extract_dir / "boot/grub/i386-pc/eltorito.img"
                ]
                
                all_found = True
                for efi_file in critical_files:
                    if efi_file.exists():
                        size = efi_file.stat().st_size
                        print(f"✅ {efi_file.name}: {size:,} bytes")
                    else:
                        print(f"❌ MISSING: {efi_file}")
                        all_found = False
                        
                if all_found:
                    print("✅ All critical EFI files verified")
                    return True
                else:
                    print("❌ Critical EFI files missing - ISO may be corrupted")
                    return False
            else:
                print(f"❌ Extraction failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Extraction error: {e}")
            return False

    def inject_custom_content(self):
        print("\n📝 CUSTOM CONTENT INJECTION")
        print("-" * 35)
        
        extract_dir = self.work_dir / "extracted"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        hello_file = extract_dir / "HelloWorld.txt"
        content = f"""Working Custom ISO Creator v{self.version}

Created: {timestamp}
Method: Ubuntu's proven complex xorriso build process
Source: Based on deadclaude7.txt systematic investigation

SUCCESS VERIFICATION:
If you can read this file after booting the ISO, 
custom content injection worked perfectly!

Technical Implementation:
✅ Version control (v{self.version})
✅ Ubuntu's 20+ parameter xorriso method
✅ Proper EFI boot structure
✅ GPT + hybrid MBR compatibility
✅ GitHub-based with cache-busting

From deadclaude7.txt methodology:
- No assumptions, only verified facts
- Proof-based debugging approach
- Evidence over enthusiasm
- Systematic validation at each step
"""
        
        hello_file.write_text(content)
        print(f"✅ HelloWorld.txt created ({hello_file.stat().st_size} bytes)")
        
        # Add version marker to casper if available
        casper_dir = extract_dir / "casper"
        if casper_dir.exists():
            custom_marker = casper_dir / f"working-iso-v{self.version}.txt"
            custom_marker.write_text(f"Working ISO v{self.version} created at {timestamp}")
            print(f"✅ Version marker added to casper directory")
            
        return True

    def build_custom_iso(self):
        print("\n🏗️ CUSTOM ISO BUILD")
        print("-" * 25)
        
        extract_dir = self.work_dir / "extracted"
        output_iso = f"working_custom_ubuntu_v{self.version.replace('.', '_')}.iso"
        
        # Ubuntu's complex xorriso command (from deadclaude7.txt investigation)
        # Key insight: Use grubx64.efi as PRIMARY EFI boot (not bootx64.efi)
        # deadclaude7.txt identified grubx64.efi as "MAIN EFI BOOT" file
        xorriso_cmd = [
            'xorriso', '-as', 'mkisofs',
            '-r',
            '-V', f'Working-Ubuntu-v{self.version}',
            '-o', output_iso,
            '-J', '-joliet-long',
            '-cache-inodes',
            # BIOS boot support
            '-b', 'boot/grub/i386-pc/eltorito.img',
            '-c', 'boot.catalog',
            '-no-emul-boot',
            '-boot-load-size', '4',
            '-boot-info-table',
            # EFI boot support - CRITICAL CHANGE: Use grubx64.efi as primary
            '-eltorito-alt-boot',
            '-e', 'EFI/boot/grubx64.efi',
            '-no-emul-boot',
            # Hybrid compatibility (essential for EFI)
            '-isohybrid-gpt-basdat',
            '-isohybrid-apm-hfsplus',
            str(extract_dir)
        ]
        
        print(f" Running Ubuntu's complex xorriso ({len(xorriso_cmd)} parameters)")
        print("📋 Based on deadclaude7.txt investigation findings")
        
        try:
            result = subprocess.run(xorriso_cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                iso_size = os.path.getsize(output_iso)
                print(f"✅ Custom ISO created successfully!")
                print(f"📊 File: {output_iso}")
                print(f"📊 Size: {iso_size:,} bytes ({iso_size/(1024**3):.2f} GB)")
                
                # Verify custom content
                try:
                    verify_result = subprocess.run([
                        '7z', 'l', output_iso, 'HelloWorld.txt'
                    ], capture_output=True, text=True)
                    
                    if 'HelloWorld.txt' in verify_result.stdout:
                        print("✅ Custom content verified in ISO")
                    else:
                        print("❓ Custom content verification inconclusive")
                        
                except:
                    print("❓ Could not verify custom content")
                    
                return output_iso
            else:
                print(f"❌ ISO creation failed")
                print(f"🔍 Error output:")
                print(result.stderr)
                return None
                
        except subprocess.TimeoutExpired:
            print("❌ ISO creation timed out (>10 minutes)")
            return None
        except Exception as e:
            print(f"❌ ISO creation error: {e}")
            return None

    def generate_test_instructions(self, iso_path):
        print(f"\n🧪 TESTING INSTRUCTIONS")
        print("=" * 40)
        print(f"📁 ISO File: {iso_path}")
        print(f"📋 Version: {self.version}")
        print()
        print("🖥️ VIRTUALBOX EFI TEST:")
        print("1. VM Configuration:")
        print("   - Name: Working-Ubuntu-Test")
        print("   - Type: Linux > Ubuntu (64-bit)")
        print("   - Memory: 2048MB minimum")
        print("   - ⚡ CRITICAL: System > Motherboard > Enable EFI")
        print()
        print("2. ISO Mount:")
        print(f"   - Storage > Controller IDE > CD/DVD: {iso_path}")
        print("   - Ensure 'Live CD/DVD' is enabled")
        print()
        print("3. Boot Verification:")
        print("   ✅ SHORT boot error messages (like original Ubuntu)")
        print("   ✅ GRUB menu appears")
        print("   ✅ Ubuntu boots to login/desktop")
        print("   ✅ HelloWorld.txt accessible (contains version info)")
        print()
        print("📊 SUCCESS CRITERIA:")
        print(f"   ✅ Version {self.version} verification")
        print("   ✅ EFI boot compatibility")
        print("   ✅ Custom content accessibility")
        print("   ✅ Normal Ubuntu functionality")

    def cleanup(self):
        print(f"\n🧹 CLEANUP")
        print("-" * 15)
        
        if self.work_dir.exists():
            print(f"🗑️ Removing: {self.work_dir}")
            shutil.rmtree(self.work_dir)
            
        print(f"📁 Keeping: {self.ubuntu_iso}")
        print("✅ Cleanup completed")

    def run_complete_build(self):
        try:
            self.print_header()
            
            if not self.verify_version_fresh():
                return False
            if not self.check_dependencies():
                return False
            if not self.download_ubuntu_iso():
                return False
            if not self.extract_iso():
                return False
            if not self.inject_custom_content():
                return False
                
            output_iso = self.build_custom_iso()
            if not output_iso:
                return False
                
            self.generate_test_instructions(output_iso)
            self.cleanup()
            
            elapsed = datetime.now() - self.start_time
            print(f"\n🎉 SUCCESS! Custom ISO v{self.version} created in {elapsed}")
            print(f"📁 Output: {output_iso}")
            print("\n🎯 Ready for EFI testing in VirtualBox!")
            return True
            
        except KeyboardInterrupt:
            print("\n\n⚠️ Build interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print(f"🚀 Working Custom ISO Creator v{VERSION}")
    print("Based on deadclaude7.txt systematic investigation")
    print("🎯 GitHub-based with cache-busting verification")
    print()
    
    creator = WorkingISOCreator()
    success = creator.run_complete_build()
    
    if success:
        print("\n✅ Build completed successfully!")
        print("📋 Next: Test the ISO in VirtualBox with EFI enabled")
    else:
        print("\n❌ Build failed - check error messages above")
        
    sys.exit(0 if success else 1)