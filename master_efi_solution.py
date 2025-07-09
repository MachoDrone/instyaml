#!/usr/bin/env python3
"""
Master EFI Solution - Complete Workflow with Version Control
PURPOSE: One script to rule them all - handles cache issues and complete workflow
VERSION: 2.0.0 - Master controller with self-version verification
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import urllib.request
import urllib.error

VERSION = "2.0.0"
SCRIPT_NAME = "master_efi_solution.py"
GITHUB_BASE = "https://raw.githubusercontent.com/MachoDrone/instyaml/cursor/read-and-verify-file-contents-eeeb"

# Expected script versions for validation
EXPECTED_VERSIONS = {
    "fix_corrupted_iso.py": "1.0.1",
    "complete_efi_solution.py": "1.0.2", 
    "boot_order_fix.py": "1.0.1"
}

class MasterEFISolution:
    def __init__(self):
        # Use ~/iso as working directory
        self.iso_dir = Path.home() / "iso"
        self.iso_dir.mkdir(exist_ok=True)
        os.chdir(self.iso_dir)
        
        self.ubuntu_iso = "ubuntu-24.04.2-live-server-amd64.iso"
        
    def show_header(self):
        """Show master script header with version info"""
        print("🚀 MASTER EFI SOLUTION - Complete Workflow")
        print("=" * 60)
        print(f"📋 MASTER SCRIPT: {SCRIPT_NAME} VERSION: {VERSION}")
        print(f"🕒 Execution time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📂 Working directory: {os.getcwd()}")
        print("🎯 Purpose: Create working EFI bootable Ubuntu ISO with HelloWorld.txt")
        print()
        
    def fetch_and_verify_script(self, script_name, expected_version):
        """Fetch script from GitHub and verify version"""
        print(f"📥 Fetching {script_name} (expected v{expected_version})...")
        
        url = f"{GITHUB_BASE}/{script_name}"
        
        try:
            # Add cache-busting timestamp
            cache_bust_url = f"{url}?cb={int(datetime.now().timestamp())}"
            response = urllib.request.urlopen(cache_bust_url)
            script_content = response.read().decode('utf-8')
            
            # Check if version matches
            if f'VERSION = "{expected_version}"' in script_content:
                print(f"✅ {script_name} v{expected_version} - VERSION VERIFIED")
                return script_content
            else:
                print(f"❌ {script_name} - VERSION MISMATCH or CACHED!")
                # Try to extract actual version
                for line in script_content.split('\n'):
                    if 'VERSION = ' in line and '"' in line:
                        actual_version = line.split('"')[1]
                        print(f"   Expected: {expected_version}, Got: {actual_version}")
                        break
                return None
                
        except urllib.error.URLError as e:
            print(f"❌ Failed to fetch {script_name}: {e}")
            return None
    
    def execute_script_content(self, script_content, script_name):
        """Execute script content directly"""
        print(f"\n🔧 EXECUTING: {script_name}")
        print("-" * 40)
        
        try:
            # Create a temporary file and execute it
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(script_content)
                temp_file.flush()
                
                # Execute the temporary script
                result = subprocess.run([sys.executable, temp_file.name], 
                                      cwd=self.iso_dir)
                
                # Clean up
                os.unlink(temp_file.name)
                
                if result.returncode == 0:
                    print(f"✅ {script_name} completed successfully")
                    return True
                else:
                    print(f"❌ {script_name} failed with exit code {result.returncode}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error executing {script_name}: {e}")
            return False
    
    def check_iso_status(self):
        """Check current ISO file status"""
        print("\n📊 CURRENT ISO STATUS:")
        print("-" * 30)
        
        if Path(self.ubuntu_iso).exists():
            size = Path(self.ubuntu_iso).stat().st_size
            size_gb = size / (1024**3)
            print(f"✅ Ubuntu ISO: {self.ubuntu_iso} ({size_gb:.2f} GB)")
            
            # Quick corruption check
            if size < 3000000000:  # Less than 3GB = likely corrupted
                print("⚠️  Ubuntu ISO appears corrupted (too small)")
                return False
            else:
                print("✅ Ubuntu ISO size looks correct")
                return True
        else:
            print(f"❌ Ubuntu ISO not found: {self.ubuntu_iso}")
            return False
    
    def show_created_isos(self):
        """Show all ISOs created during the process"""
        print("\n📁 CREATED ISO FILES:")
        print("-" * 30)
        
        iso_patterns = [
            ("helloefi.iso", "Standard EFI fix"),
            ("helloefi_minimal.iso", "Minimal Ubuntu parameters"),
            ("helloefi_exact.iso", "Exact Ubuntu sequence"),
            ("helloefi_grub_priority.iso", "grubx64.efi priority"),
            ("helloefi_ubuntu_params.iso", "Ubuntu build parameters")
        ]
        
        created_isos = []
        for iso_name, description in iso_patterns:
            if Path(iso_name).exists():
                size = Path(iso_name).stat().st_size / (1024**3)
                created_isos.append(iso_name)
                print(f"✅ {iso_name} ({size:.1f} GB) - {description}")
        
        if not created_isos:
            print("❌ No custom ISOs found")
            return False
        
        print(f"\n🧪 TEST INSTRUCTIONS:")
        print("1. Test each ISO in VirtualBox with EFI enabled")
        print("2. Look for SHORTER boot error messages (like original Ubuntu)")
        print("3. Verify HelloWorld.txt exists after boot")
        print("\n🎯 Priority testing order:")
        for i, iso in enumerate(created_isos[:3], 1):
            print(f"{i}. {iso}")
        
        return True
    
    def run_complete_workflow(self):
        """Execute the complete EFI solution workflow"""
        print("🔄 EXECUTING COMPLETE WORKFLOW:")
        print("=" * 40)
        
        # Step 1: Check/Fix ISO corruption
        print("\n📋 STEP 1: ISO Integrity Check & Fix")
        iso_script = self.fetch_and_verify_script("fix_corrupted_iso.py", 
                                                 EXPECTED_VERSIONS["fix_corrupted_iso.py"])
        if not iso_script:
            print("❌ Cannot proceed - failed to get ISO fix script")
            return False
        
        if not self.execute_script_content(iso_script, "fix_corrupted_iso.py"):
            print("❌ ISO fix failed")
            return False
        
        # Step 2: Complete EFI solution
        print("\n📋 STEP 2: Complete EFI Solution")
        efi_script = self.fetch_and_verify_script("complete_efi_solution.py",
                                                 EXPECTED_VERSIONS["complete_efi_solution.py"])
        if not efi_script:
            print("❌ Cannot proceed - failed to get EFI solution script")
            return False
            
        if not self.execute_script_content(efi_script, "complete_efi_solution.py"):
            print("❌ EFI solution failed")
            return False
        
        # Step 3: Boot order fix (multiple ISOs)
        print("\n📋 STEP 3: Boot Order Fix (Multiple Test ISOs)")
        boot_script = self.fetch_and_verify_script("boot_order_fix.py",
                                                  EXPECTED_VERSIONS["boot_order_fix.py"])
        if not boot_script:
            print("⚠️  Boot order fix script unavailable - continuing...")
        else:
            self.execute_script_content(boot_script, "boot_order_fix.py")
        
        return True
    
    def run(self):
        """Main execution flow"""
        self.show_header()
        
        # Check if we're in the right place
        print("🔍 ENVIRONMENT CHECK:")
        print("-" * 25)
        print(f"✅ Working directory: {self.iso_dir}")
        print(f"✅ Current user: {os.environ.get('USER', 'unknown')}")
        print(f"✅ Python version: {sys.version.split()[0]}")
        
        # Check current ISO status
        iso_ok = self.check_iso_status()
        
        # Run complete workflow
        if self.run_complete_workflow():
            print("\n🎉 MASTER WORKFLOW COMPLETED!")
            print("=" * 40)
            
            # Show final results
            self.show_created_isos()
            
            print("\n🎯 NEXT STEPS:")
            print("1. Test the created ISOs in VirtualBox with EFI enabled")
            print("2. Compare boot error messages with original Ubuntu")
            print("3. Look for the ISO with SHORTER error messages")
            print("4. Verify HelloWorld.txt exists in working ISO")
            
            print(f"\n✅ All files created in: {self.iso_dir}")
            return True
        else:
            print("\n❌ MASTER WORKFLOW FAILED!")
            print("Check the error messages above for details")
            return False

if __name__ == "__main__":
    master = MasterEFISolution()
    success = master.run()
    sys.exit(0 if success else 1)