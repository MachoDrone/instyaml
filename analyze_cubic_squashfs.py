#!/usr/bin/env python3
"""
CUBIC SQUASHFS ANALYZER
Extracts and compares Ubuntu original vs Cubic's working squashfs
to determine exactly what Cubic does differently
"""

import os
import subprocess
import shutil
from pathlib import Path
import hashlib

def run_cmd(cmd, description):
    print(f"🔧 {description}...")
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if result.returncode != 0:
        print(f"❌ Failed: {result.stderr}")
        return False
    return True

def get_dir_info(path):
    """Get directory size and file count"""
    result = subprocess.run(['du', '-sb', str(path)], capture_output=True, text=True)
    size = int(result.stdout.split()[0]) if result.returncode == 0 else 0
    
    result = subprocess.run(['find', str(path), '-type', 'f'], capture_output=True, text=True)
    file_count = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
    
    return size, file_count

def main():
    print("🔍 CUBIC SQUASHFS CONTENT ANALYZER")
    print("=" * 50)
    
    # Paths
    ubuntu_iso = "ubuntu-24.04.2-live-server-amd64.iso"
    cubic_iso = "cubic_custom.iso"  # User's working Cubic ISO
    
    work_dir = Path("squashfs_analysis")
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir()
    
    ubuntu_extract = work_dir / "ubuntu_extracted"
    cubic_extract = work_dir / "cubic_extracted"
    ubuntu_squashfs_extract = work_dir / "ubuntu_squashfs"
    cubic_squashfs_extract = work_dir / "cubic_squashfs"
    
    # Extract Ubuntu ISO
    print("\n📂 EXTRACTING UBUNTU ISO...")
    ubuntu_extract.mkdir()
    if not run_cmd(f"7z x {ubuntu_iso} -o{ubuntu_extract} -y", "Ubuntu ISO extraction"):
        return
    
    # Find Ubuntu squashfs
    ubuntu_squashfs = ubuntu_extract / "casper" / "ubuntu-server-minimal.squashfs"
    if not ubuntu_squashfs.exists():
        print("❌ Ubuntu squashfs not found")
        return
        
    ubuntu_size = ubuntu_squashfs.stat().st_size
    print(f"✅ Ubuntu squashfs: {ubuntu_size:,} bytes")
    
    # Check if Cubic ISO exists
    if not Path(cubic_iso).exists():
        print(f"❌ Cubic ISO not found: {cubic_iso}")
        print("   Please ensure the working Cubic ISO is in current directory")
        return
    
    # Extract Cubic ISO  
    print("\n📂 EXTRACTING CUBIC ISO...")
    cubic_extract.mkdir()
    if not run_cmd(f"7z x {cubic_iso} -o{cubic_extract} -y", "Cubic ISO extraction"):
        return
        
    # Find Cubic squashfs
    cubic_squashfs = cubic_extract / "casper" / "ubuntu-server-minimal.squashfs"
    if not cubic_squashfs.exists():
        print("❌ Cubic squashfs not found")
        return
        
    cubic_size = cubic_squashfs.stat().st_size  
    print(f"✅ Cubic squashfs: {cubic_size:,} bytes")
    
    print(f"\n📊 SIZE COMPARISON:")
    print(f"   Ubuntu: {ubuntu_size:,} bytes")
    print(f"   Cubic:  {cubic_size:,} bytes")
    print(f"   Diff:   {cubic_size - ubuntu_size:,} bytes ({((cubic_size/ubuntu_size)-1)*100:.1f}% larger)")
    
    # Extract both squashfs filesystems
    print("\n🗂️ EXTRACTING SQUASHFS CONTENTS...")
    ubuntu_squashfs_extract.mkdir()
    cubic_squashfs_extract.mkdir()
    
    if not run_cmd(f"sudo unsquashfs -f -d {ubuntu_squashfs_extract} {ubuntu_squashfs}", "Ubuntu squashfs"):
        return
        
    if not run_cmd(f"sudo unsquashfs -f -d {cubic_squashfs_extract} {cubic_squashfs}", "Cubic squashfs"):
        return
    
    # Analyze extracted content
    print("\n📈 CONTENT ANALYSIS:")
    
    ubuntu_content_size, ubuntu_files = get_dir_info(ubuntu_squashfs_extract)
    cubic_content_size, cubic_files = get_dir_info(cubic_squashfs_extract)
    
    print(f"   Ubuntu content: {ubuntu_content_size:,} bytes, {ubuntu_files:,} files")
    print(f"   Cubic content:  {cubic_content_size:,} bytes, {cubic_files:,} files")
    print(f"   Content diff:   {cubic_content_size - ubuntu_content_size:,} bytes, {cubic_files - ubuntu_files:,} files")
    
    # Find differences in directory structure
    print("\n🔍 FINDING CONTENT DIFFERENCES...")
    
    # Get file lists
    run_cmd(f"find {ubuntu_squashfs_extract} -type f | sort > ubuntu_files.txt", "Ubuntu file list")
    run_cmd(f"find {cubic_squashfs_extract} -type f | sort > cubic_files.txt", "Cubic file list")
    
    # Compare file lists
    run_cmd("diff ubuntu_files.txt cubic_files.txt > file_differences.txt", "File differences")
    
    # Check for added/removed files
    result = subprocess.run(['wc', '-l', 'file_differences.txt'], capture_output=True, text=True)
    diff_lines = int(result.stdout.split()[0]) if result.returncode == 0 else 0
    
    if diff_lines > 0:
        print(f"✅ Found {diff_lines} file differences")
        print("📄 Showing first 20 differences:")
        subprocess.run(['head', '-20', 'file_differences.txt'])
    else:
        print("⚠️ No file differences found")
    
    # Check package differences
    print("\n📦 CHECKING INSTALLED PACKAGES...")
    
    ubuntu_packages = ubuntu_squashfs_extract / "var/lib/dpkg/status"
    cubic_packages = cubic_squashfs_extract / "var/lib/dpkg/status"
    
    if ubuntu_packages.exists() and cubic_packages.exists():
        run_cmd(f"grep '^Package:' {ubuntu_packages} | sort > ubuntu_packages.txt", "Ubuntu packages")
        run_cmd(f"grep '^Package:' {cubic_packages} | sort > cubic_packages.txt", "Cubic packages")
        run_cmd("diff ubuntu_packages.txt cubic_packages.txt > package_differences.txt", "Package differences")
        
        result = subprocess.run(['wc', '-l', 'package_differences.txt'], capture_output=True, text=True)
        pkg_diff_lines = int(result.stdout.split()[0]) if result.returncode == 0 else 0
        
        if pkg_diff_lines > 0:
            print(f"✅ Found {pkg_diff_lines} package differences")
            print("📦 Showing package differences:")
            subprocess.run(['head', '-20', 'package_differences.txt'])
        else:
            print("⚠️ No package differences found")
    
    # Check compression ratios
    print(f"\n🗜️ COMPRESSION ANALYSIS:")
    ubuntu_ratio = ubuntu_size / ubuntu_content_size if ubuntu_content_size > 0 else 0
    cubic_ratio = cubic_size / cubic_content_size if cubic_content_size > 0 else 0
    
    print(f"   Ubuntu compression: {ubuntu_ratio:.3f} ({ubuntu_content_size:,} → {ubuntu_size:,})")
    print(f"   Cubic compression:  {cubic_ratio:.3f} ({cubic_content_size:,} → {cubic_size:,})")
    
    if cubic_ratio > ubuntu_ratio:
        print("   🔍 Cubic uses LESS compression (preserves more content)")
    elif cubic_ratio < ubuntu_ratio:
        print("   🔍 Cubic uses MORE compression")
    else:
        print("   🔍 Same compression ratio")
    
    print(f"\n📋 SUMMARY:")
    print(f"   The key to Cubic's {cubic_size:,} byte squashfs:")
    if cubic_content_size > ubuntu_content_size:
        print(f"   1. Added {cubic_content_size - ubuntu_content_size:,} bytes of content")
    if cubic_files > ubuntu_files:
        print(f"   2. Added {cubic_files - ubuntu_files:,} files")
    print(f"   3. Used compression ratio of {cubic_ratio:.3f}")
    
    print(f"\n📁 Analysis files created:")
    print(f"   - file_differences.txt")
    print(f"   - package_differences.txt") 
    print(f"   - ubuntu_files.txt")
    print(f"   - cubic_files.txt")
    
    print(f"\n🎯 TO FIX THE SCRIPT:")
    print(f"   Review the differences to see what Cubic adds/changes")
    print(f"   Update compression settings to match Cubic's ratio")

if __name__ == "__main__":
    main()