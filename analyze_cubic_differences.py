#!/usr/bin/env python3
"""
CUBIC DIFFERENCE ANALYZER v1.0
Analyzes differences between working Cubic ISO and original Ubuntu ISO
to understand what makes EFI boot successful
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

class CubicAnalyzer:
    def __init__(self):
        self.cubic_iso = "cubic_custom.iso"
        self.ubuntu_iso = "ubuntu_original.iso" 
        self.work_dir = Path("cubic_analysis")
        self.start_time = datetime.now()
        
    def log(self, message, emoji="📝"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{emoji} {timestamp} {message}")
        
    def check_isos_exist(self):
        self.log("CHECKING ISO FILES", "🔍")
        print("-" * 40)
        
        if not Path(self.cubic_iso).exists():
            self.log(f"Missing: {self.cubic_iso}", "❌")
            return False
            
        if not Path(self.ubuntu_iso).exists():
            self.log(f"Missing: {self.ubuntu_iso}", "❌") 
            return False
            
        cubic_size = Path(self.cubic_iso).stat().st_size
        ubuntu_size = Path(self.ubuntu_iso).stat().st_size
        
        self.log(f"Cubic ISO: {cubic_size:,} bytes ({cubic_size/(1024**3):.1f}GB)", "✅")
        self.log(f"Ubuntu ISO: {ubuntu_size:,} bytes ({ubuntu_size/(1024**3):.1f}GB)", "✅")
        
        return True
        
    def extract_isos(self):
        self.log("EXTRACTING ISOS FOR COMPARISON", "📂")
        print("-" * 40)
        
        if self.work_dir.exists():
            shutil.rmtree(self.work_dir)
        self.work_dir.mkdir()
        
        cubic_dir = self.work_dir / "cubic"
        ubuntu_dir = self.work_dir / "ubuntu"
        
        # Extract both ISOs
        for iso_file, extract_dir in [(self.cubic_iso, cubic_dir), (self.ubuntu_iso, ubuntu_dir)]:
            self.log(f"Extracting {iso_file}...", "⚙️")
            extract_dir.mkdir()
            
            cmd = ["7z", "x", iso_file, f"-o{extract_dir}", "-y"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.log(f"Failed to extract {iso_file}: {result.stderr}", "❌")
                return False
                
        self.log("Both ISOs extracted successfully", "✅")
        return True
        
    def compare_file_structures(self):
        self.log("COMPARING FILE STRUCTURES", "🔍")
        print("-" * 40)
        
        cubic_dir = self.work_dir / "cubic"
        ubuntu_dir = self.work_dir / "ubuntu"
        
        # Get file lists
        self.log("Analyzing file differences...", "📊")
        
        cmd = ["diff", "-r", "--brief", str(ubuntu_dir), str(cubic_dir)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.stdout:
            self.log("FILE DIFFERENCES FOUND:", "🎯")
            print(result.stdout)
        else:
            self.log("No file structure differences found", "ℹ️")
            
        return True
        
    def analyze_casper_directory(self):
        self.log("ANALYZING CASPER DIRECTORIES", "🎯")
        print("-" * 40)
        
        cubic_casper = self.work_dir / "cubic" / "casper"
        ubuntu_casper = self.work_dir / "ubuntu" / "casper"
        
        for name, casper_dir in [("Ubuntu", ubuntu_casper), ("Cubic", cubic_casper)]:
            if casper_dir.exists():
                self.log(f"{name} Casper contents:", "📋")
                cmd = ["ls", "-la", str(casper_dir)]
                result = subprocess.run(cmd, capture_output=True, text=True)
                print(result.stdout)
            else:
                self.log(f"{name} has no casper directory", "⚠️")
                
        # Check for differences in casper files
        if cubic_casper.exists() and ubuntu_casper.exists():
            cmd = ["diff", "-r", str(ubuntu_casper), str(cubic_casper)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.stdout:
                self.log("CASPER DIFFERENCES:", "🎯")
                print(result.stdout[:2000])  # Limit output
            else:
                self.log("Casper directories are identical", "ℹ️")
                
        return True
        
    def analyze_boot_configs(self):
        self.log("ANALYZING BOOT CONFIGURATIONS", "⚙️")
        print("-" * 40)
        
        # Check grub.cfg differences
        ubuntu_grub = self.work_dir / "ubuntu" / "boot" / "grub" / "grub.cfg"
        cubic_grub = self.work_dir / "cubic" / "boot" / "grub" / "grub.cfg"
        
        if ubuntu_grub.exists() and cubic_grub.exists():
            cmd = ["diff", "-u", str(ubuntu_grub), str(cubic_grub)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.stdout:
                self.log("GRUB CONFIG DIFFERENCES:", "🎯")
                print(result.stdout[:1500])  # Limit output
            else:
                self.log("GRUB configs are identical", "ℹ️")
        else:
            self.log("Missing grub.cfg files", "⚠️")
            
        return True
        
    def analyze_squashfs_differences(self):
        self.log("ANALYZING SQUASHFS FILESYSTEMS", "🗂️")
        print("-" * 40)
        
        ubuntu_squash = self.work_dir / "ubuntu" / "casper" / "filesystem.squashfs"
        cubic_squash = self.work_dir / "cubic" / "casper" / "filesystem.squashfs"
        
        for name, squash_file in [("Ubuntu", ubuntu_squash), ("Cubic", cubic_squash)]:
            if squash_file.exists():
                size = squash_file.stat().st_size
                self.log(f"{name} squashfs: {size:,} bytes ({size/(1024**2):.1f}MB)", "📊")
                
                # Try to list contents briefly
                cmd = ["unsquashfs", "-ll", str(squash_file)]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    lines = result.stdout.split('\n')[:10]  # First 10 lines
                    self.log(f"{name} squashfs contents (first 10 entries):", "📋")
                    for line in lines:
                        if line.strip():
                            print(f"  {line}")
                else:
                    self.log(f"Could not analyze {name} squashfs", "⚠️")
            else:
                self.log(f"{name} has no squashfs file", "❌")
                
        return True
        
    def analyze_efi_structure(self):
        self.log("ANALYZING EFI STRUCTURES", "🔧")
        print("-" * 40)
        
        for name, base_dir in [("Ubuntu", self.work_dir / "ubuntu"), ("Cubic", self.work_dir / "cubic")]:
            efi_dir = base_dir / "EFI" / "boot"
            
            if efi_dir.exists():
                self.log(f"{name} EFI/boot contents:", "📋")
                cmd = ["ls", "-la", str(efi_dir)]
                result = subprocess.run(cmd, capture_output=True, text=True)
                print(result.stdout)
            else:
                self.log(f"{name} has no EFI/boot directory", "⚠️")
                
        return True
        
    def generate_summary(self):
        self.log("GENERATING ANALYSIS SUMMARY", "📋")
        print("-" * 50)
        
        duration = datetime.now() - self.start_time
        
        summary = f"""
CUBIC SUCCESS ANALYSIS SUMMARY
=============================
Analysis Duration: {duration}
Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Key Findings:
1. File structure comparison completed
2. Casper directory analysis completed  
3. Boot configuration comparison completed
4. SquashFS filesystem analysis completed
5. EFI structure verification completed

Next Steps:
- Review above differences to understand Cubic's modifications
- Focus on squashfs and casper differences for CLI script development
- Identify minimal changes needed for EFI boot success

Files analyzed:
- {self.cubic_iso} (Cubic custom ISO)
- {self.ubuntu_iso} (Original Ubuntu ISO)
"""
        
        print(summary)
        
        # Save summary to file
        summary_file = "cubic_analysis_summary.txt"
        with open(summary_file, 'w') as f:
            f.write(summary)
            
        self.log(f"Summary saved to {summary_file}", "💾")
        
    def cleanup(self):
        if self.work_dir.exists():
            shutil.rmtree(self.work_dir)
            self.log("Cleanup completed", "🧹")
            
    def run(self):
        print(f"🔍 CUBIC DIFFERENCE ANALYZER v1.0")
        print("=" * 50)
        self.log(f"Started: {self.start_time}")
        print()
        
        try:
            if not self.check_isos_exist():
                return False
                
            if not self.extract_isos():
                return False
                
            self.compare_file_structures()
            self.analyze_casper_directory()
            self.analyze_boot_configs()
            self.analyze_squashfs_differences()
            self.analyze_efi_structure()
            self.generate_summary()
            
            self.log("Analysis completed successfully", "✅")
            return True
            
        except KeyboardInterrupt:
            self.log("Analysis interrupted", "⚠️")
            return False
        except Exception as e:
            self.log(f"Analysis error: {e}", "❌")
            return False
        finally:
            self.cleanup()

if __name__ == "__main__":
    analyzer = CubicAnalyzer()
    success = analyzer.run()
    sys.exit(0 if success else 1)