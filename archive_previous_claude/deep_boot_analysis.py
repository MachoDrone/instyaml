#!/usr/bin/env python3
"""
Deep Boot Analysis - Find the Missing EFI Boot Component
Purpose: Compare original vs created ISO boot structures in detail
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

class DeepBootAnalysis:
    def __init__(self):
        # Use ~/iso as working directory
        self.iso_dir = Path.home() / "iso"
        self.iso_dir.mkdir(exist_ok=True)
        os.chdir(self.iso_dir)
        
        self.ubuntu_iso = "ubuntu-24.04.2-live-server-amd64.iso"
        self.our_iso = "helloefi.iso"
        
    def analyze_boot_catalog(self, iso_path, label):
        """Analyze the boot catalog in detail"""
        print(f"\n🔍 Analyzing BOOT CATALOG: {label}")
        print("=" * 50)
        
        try:
            # Use isoinfo to examine boot catalog
            result = subprocess.run([
                "isoinfo", "-d", "-i", iso_path
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("📋 ISO Boot Information:")
                for line in result.stdout.split('\n'):
                    if any(keyword in line.lower() for keyword in ['boot', 'catalog', 'sector', 'el torito']):
                        print(f"   {line.strip()}")
            else:
                print("❌ isoinfo failed, trying alternative...")
                
        except FileNotFoundError:
            print("⚠️ isoinfo not available, using 7z...")
            
        # Alternative: Check boot catalog with 7z
        try:
            result = subprocess.run([
                "7z", "l", iso_path, "boot.catalog"
            ], capture_output=True, text=True)
            
            if "boot.catalog" in result.stdout:
                print("✅ boot.catalog found")
                # Extract and examine boot catalog
                with tempfile.TemporaryDirectory() as temp_dir:
                    subprocess.run([
                        "7z", "e", f"-o{temp_dir}", iso_path, "boot.catalog"
                    ], capture_output=True)
                    
                    catalog_file = Path(temp_dir) / "boot.catalog"
                    if catalog_file.exists():
                        size = catalog_file.stat().st_size
                        print(f"📊 boot.catalog size: {size} bytes")
            else:
                print("❌ boot.catalog not found")
                
        except subprocess.CalledProcessError:
            print("❌ Failed to analyze boot catalog")
    
    def compare_efi_directories(self):
        """Compare EFI directories between original and our ISO"""
        print(f"\n🔍 COMPARING EFI DIRECTORIES")
        print("=" * 50)
        
        for iso_name, label in [(self.ubuntu_iso, "ORIGINAL"), (self.our_iso, "OUR ISO")]:
            if not Path(iso_name).exists():
                print(f"❌ {label}: {iso_name} not found")
                continue
                
            print(f"\n📁 {label} EFI Structure:")
            try:
                result = subprocess.run([
                    "7z", "l", iso_name, "EFI/*"
                ], capture_output=True, text=True)
                
                # Parse and show EFI files
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'EFI' in line and ('.efi' in line or 'boot' in line.lower()):
                        parts = line.split()
                        if len(parts) >= 6:
                            size = parts[3]
                            filename = parts[-1]
                            print(f"   📄 {filename} ({size} bytes)")
                            
            except subprocess.CalledProcessError:
                print(f"❌ Failed to analyze {label}")
    
    def check_missing_boot_components(self):
        """Check for missing boot components that might be causing failure"""
        print(f"\n🔍 CHECKING FOR MISSING BOOT COMPONENTS")
        print("=" * 50)
        
        # List of critical boot files to check
        critical_files = [
            "EFI/boot/bootx64.efi",
            "EFI/boot/grubx64.efi", 
            "EFI/boot/mmx64.efi",
            "EFI/ubuntu/shimx64.efi",
            "EFI/ubuntu/grubx64.efi",
            "boot/grub/i386-pc/eltorito.img",
            "boot/grub/efi.img",
            "boot.catalog",
            ".disk/info"
        ]
        
        for iso_name, label in [(self.ubuntu_iso, "ORIGINAL"), (self.our_iso, "OUR ISO")]:
            if not Path(iso_name).exists():
                continue
                
            print(f"\n📋 {label} Critical Files:")
            for file_path in critical_files:
                try:
                    result = subprocess.run([
                        "7z", "l", iso_name, file_path
                    ], capture_output=True, text=True)
                    
                    if file_path in result.stdout:
                        print(f"✅ {file_path}")
                    else:
                        print(f"❌ {file_path} - MISSING")
                        
                except subprocess.CalledProcessError:
                    print(f"❌ {file_path} - ERROR")
    
    def create_fixed_iso_with_ubuntu_params(self):
        """Create ISO using Ubuntu's exact xorriso parameters"""
        print(f"\n🔧 CREATING ISO WITH UBUNTU'S EXACT PARAMETERS")
        print("=" * 50)
        
        # Extract Ubuntu ISO to analyze
        extract_dir = self.iso_dir / "ubuntu_extract"
        if extract_dir.exists():
            shutil.rmtree(extract_dir)
        extract_dir.mkdir()
        
        print("📂 Extracting Ubuntu ISO for analysis...")
        try:
            subprocess.run([
                "7z", "x", f"-o{extract_dir}", self.ubuntu_iso
            ], check=True)
            
            # Inject HelloWorld.txt
            hello_file = extract_dir / "HelloWorld.txt"
            hello_file.write_text("Hello World - Ubuntu Parameter Test!")
            
            # Try Ubuntu's exact xorriso command structure
            # Based on research of Ubuntu's official build process
            ubuntu_xorriso_cmd = [
                "xorriso", "-as", "mkisofs",
                "-r",
                "-checksum_algorithm_iso", "md5,sha1",
                "-V", "Ubuntu-Server 24.04.2 HelloWorld",
                "-o", "helloefi_ubuntu_params.iso",
                "-J", "-joliet-long",
                "-cache-inodes",
                "-b", "boot/grub/i386-pc/eltorito.img",
                "-c", "boot.catalog",
                "-no-emul-boot",
                "-boot-load-size", "4", 
                "-boot-info-table",
                "-eltorito-alt-boot",
                "-e", "EFI/boot/bootx64.efi",  # Try bootx64.efi like Ubuntu
                "-no-emul-boot",
                "-isohybrid-gpt-basdat",
                "-isohybrid-apm-hfsplus",
                str(extract_dir)
            ]
            
            print("🏗️ Creating ISO with Ubuntu parameters...")
            print(" ".join(ubuntu_xorriso_cmd))
            
            result = subprocess.run(ubuntu_xorriso_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Ubuntu parameters ISO created successfully")
                iso_size = Path("helloefi_ubuntu_params.iso").stat().st_size / (1024*1024*1024)
                print(f"📊 Output: helloefi_ubuntu_params.iso ({iso_size:.1f} GB)")
                return True
            else:
                print("❌ Ubuntu parameters failed, trying shimx64.efi...")
                print("STDERR:", result.stderr)
                return self.try_shim_approach(extract_dir)
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed: {e}")
            return False
    
    def try_shim_approach(self, extract_dir):
        """Try using shimx64.efi approach"""
        print("🔄 Trying shimx64.efi approach...")
        
        # Check if shimx64.efi exists
        shim_file = extract_dir / "EFI" / "ubuntu" / "shimx64.efi"
        if shim_file.exists():
            print("✅ Found shimx64.efi, trying shim approach...")
            
            shim_xorriso_cmd = [
                "xorriso", "-as", "mkisofs",
                "-r",
                "-V", "Ubuntu-Server 24.04.2 Shim",
                "-o", "helloefi_shim.iso",
                "-J", "-joliet-long",
                "-b", "boot/grub/i386-pc/eltorito.img",
                "-c", "boot.catalog",
                "-no-emul-boot",
                "-boot-load-size", "4",
                "-boot-info-table", 
                "-eltorito-alt-boot",
                "-e", "EFI/ubuntu/shimx64.efi",  # Use shimx64.efi
                "-no-emul-boot",
                "-isohybrid-gpt-basdat",
                str(extract_dir)
            ]
            
            result = subprocess.run(shim_xorriso_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Shim approach ISO created successfully")
                return True
            else:
                print("❌ Shim approach also failed")
                return False
        else:
            print("❌ shimx64.efi not found")
            return False
    
    def provide_test_instructions(self):
        """Provide comprehensive testing instructions"""
        print(f"\n🧪 TESTING INSTRUCTIONS")
        print("=" * 50)
        
        iso_files = []
        for iso_name in ["helloefi.iso", "helloefi_ubuntu_params.iso", "helloefi_shim.iso"]:
            if Path(iso_name).exists():
                iso_files.append(iso_name)
        
        print(f"📁 ISO files to test: {', '.join(iso_files)}")
        print("\n🖥️ Test each ISO in VirtualBox with EFI enabled:")
        print("1. Try helloefi.iso (our grubx64.efi approach)")
        print("2. Try helloefi_ubuntu_params.iso (Ubuntu's exact parameters)")
        print("3. Try helloefi_shim.iso (shimx64.efi approach)")
        print("\n🎯 Look for which one gets past the Boot0003/0002/0001 failures")
    
    def run(self):
        """Main execution flow"""
        print("🚀 Deep Boot Analysis - Find Missing EFI Component")
        print("=" * 60)
        print(f"📂 Working in: {os.getcwd()}")
        
        # Check if we have both ISOs
        if not Path(self.ubuntu_iso).exists():
            print(f"❌ Original Ubuntu ISO not found: {self.ubuntu_iso}")
            return False
            
        if not Path(self.our_iso).exists():
            print(f"❌ Our ISO not found: {self.our_iso}")
            print("🔧 Run the complete EFI solution first")
            return False
        
        # Deep analysis
        self.analyze_boot_catalog(self.ubuntu_iso, "ORIGINAL Ubuntu")
        self.analyze_boot_catalog(self.our_iso, "OUR helloefi.iso")
        
        self.compare_efi_directories()
        self.check_missing_boot_components()
        
        # Try different approaches
        self.create_fixed_iso_with_ubuntu_params()
        
        self.provide_test_instructions()
        
        print("\n🎯 GOAL: Find which ISO boots past the Boot0003/0002/0001 errors")
        return True

if __name__ == "__main__":
    analyzer = DeepBootAnalysis()
    success = analyzer.run()
    sys.exit(0 if success else 1)