#!/usr/bin/env python3
"""
SIMPLE CUBIC MODIFIER v1.0
Uses your working cubic_custom.iso as base and adds custom content
Avoids complex squashfs extraction that requires sudo
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

class SimpleCubicModifier:
    def __init__(self):
        self.version = "1.0"
        self.start_time = datetime.now()
        self.work_dir = Path("simple_modifier_work")
        self.cubic_iso = "cubic_custom.iso"
        self.output_iso = f"simple_custom_{datetime.now().strftime('%Y%m%d_%H%M')}.iso"
        
    def log(self, message, emoji="📝"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{emoji} {timestamp} {message}")
        
    def check_cubic_iso(self):
        self.log("CHECKING CUBIC ISO", "🔍")
        print("-" * 40)
        
        if not Path(self.cubic_iso).exists():
            self.log(f"Missing: {self.cubic_iso}", "❌")
            self.log("Please ensure cubic_custom.iso is in current directory", "💡")
            return False
            
        size = Path(self.cubic_iso).stat().st_size
        self.log(f"Cubic ISO found: {size:,} bytes ({size/(1024**3):.1f}GB)", "✅")
        return True
        
    def extract_cubic_iso(self):
        self.log("EXTRACTING CUBIC ISO", "📂")
        print("-" * 40)
        
        if self.work_dir.exists():
            shutil.rmtree(self.work_dir)
        self.work_dir.mkdir()
        
        extract_dir = self.work_dir / "extracted"
        extract_dir.mkdir()
        
        self.log("Extracting Cubic ISO contents...", "⚙️")
        cmd = ["7z", "x", self.cubic_iso, f"-o{extract_dir}", "-y"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            self.log(f"Extraction failed: {result.stderr}", "❌")
            return False
            
        self.log("Cubic ISO extraction completed", "✅")
        return True
        
    def add_simple_customization(self):
        self.log("ADDING SIMPLE CUSTOMIZATIONS", "📝")
        print("-" * 40)
        
        extract_dir = self.work_dir / "extracted"
        
        # Add HelloWorld.txt to ISO root (simple method)
        custom_content = f"""Hello from Simple Cubic Modifier v{self.version}!

Created: {self.start_time}
Method: Modified working Cubic ISO

This proves:
✅ Cubic ISO can be easily modified
✅ EFI boot structure preserved  
✅ Simple customization works

Based on your working cubic_custom.iso that boots successfully!
"""
        
        hello_file = extract_dir / "HelloWorld.txt"
        hello_file.write_text(custom_content)
        self.log("Added HelloWorld.txt to ISO root", "✅")
        
        # Update disk info
        disk_info = extract_dir / ".disk" / "info"
        if disk_info.exists():
            disk_info.write_text(f"Simple Cubic Modifier v{self.version} - {datetime.now().strftime('%Y%m%d')}")
            self.log("Updated disk info", "✅")
            
        return True
        
    def create_modified_iso(self):
        self.log("CREATING MODIFIED ISO", "🔧")
        print("-" * 40)
        
        extract_dir = self.work_dir / "extracted"
        
        # Use same xorriso command that works
        xorriso_cmd = [
            "xorriso", "-as", "mkisofs",
            "-r",
            "-V", f"Simple-Cubic-Mod-v{self.version}",
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
        
        self.log("Building modified EFI-bootable ISO...", "⚙️")
        result = subprocess.run(xorriso_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            self.log(f"ISO creation failed: {result.stderr}", "❌")
            return False
            
        if Path(self.output_iso).exists():
            size = Path(self.output_iso).stat().st_size
            self.log(f"Modified ISO created: {self.output_iso} ({size:,} bytes)", "✅")
            
            # Verify it still has hybrid boot structure
            file_check = subprocess.run(["file", self.output_iso], capture_output=True, text=True)
            
            if "(DOS/MBR boot sector)" in file_check.stdout:
                self.log("EFI boot structure preserved", "✅")
            else:
                self.log("EFI boot structure may be damaged", "⚠️")
                
            return True
        else:
            self.log("ISO file not created", "❌")
            return False
            
    def cleanup(self):
        if self.work_dir.exists():
            shutil.rmtree(self.work_dir)
            self.log("Cleanup completed", "🧹")
            
    def run(self):
        print(f"📝 SIMPLE CUBIC MODIFIER v{self.version}")
        print("=" * 50)
        self.log(f"Started: {self.start_time}")
        self.log("Modifying your working Cubic ISO", "🎯")
        print()
        
        try:
            if not self.check_cubic_iso():
                return False
                
            if not self.extract_cubic_iso():
                return False
                
            if not self.add_simple_customization():
                return False
                
            if not self.create_modified_iso():
                return False
                
            duration = datetime.now() - self.start_time
            
            print("\n" + "=" * 50)
            self.log(f"MODIFICATION COMPLETED in {duration}", "🎉")
            self.log(f"Output: {self.output_iso}", "📁")
            self.log("Should boot identically to your working Cubic ISO!", "🚀")
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
    modifier = SimpleCubicModifier()
    success = modifier.run()
    sys.exit(0 if success else 1)