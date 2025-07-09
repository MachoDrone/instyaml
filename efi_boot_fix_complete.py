#!/usr/bin/env python3
"""
Complete EFI Boot Fix v0.00.31 for INSTYAML
Downloads Ubuntu ISO if needed and creates EFI-fixed version
"""

import os
import subprocess
import tempfile
import shutil
import sys

def download_ubuntu_iso():
    """Download Ubuntu 24.04.2 Server ISO if not present"""
    iso_filename = "ubuntu-24.04.2-live-server-amd64.iso"
    
    if os.path.exists(iso_filename):
        print(f"✅ Found existing {iso_filename}")
        return True
    
    print(f"📥 Downloading {iso_filename}...")
    print("⏳ This may take several minutes...")
    
    # Ubuntu 24.04.2 Server ISO URL
    iso_url = "https://releases.ubuntu.com/24.04.2/ubuntu-24.04.2-live-server-amd64.iso"
    
    try:
        # Download with wget showing progress
        subprocess.run([
            "wget", "-c", "--progress=bar", 
            "-O", iso_filename, iso_url
        ], check=True)
        
        print(f"✅ Downloaded {iso_filename}")
        return True
        
    except subprocess.CalledProcessError:
        print(f"❌ Failed to download {iso_filename}")
        print("💡 You can manually download it from:")
        print(f"   {iso_url}")
        return False

def create_efi_fixed_iso():
    """Create ISO with proper dual boot catalog (Legacy + EFI)"""
    print("🔧 Creating EFI-Fixed INSTYAML ISO v0.00.31")
    print("=" * 50)
    
    # Download Ubuntu ISO if needed
    if not download_ubuntu_iso():
        return False
    
    print("📂 Extracting Ubuntu ISO for EFI fix...")
    
    # Create temp directory
    with tempfile.TemporaryDirectory(prefix="instyaml_efi_fix_") as temp_dir:
        mount_point = os.path.join(temp_dir, "iso_mount")
        extract_dir = os.path.join(temp_dir, "iso_extract")
        os.makedirs(mount_point)
        
        # Mount Ubuntu ISO
        subprocess.run(["sudo", "mount", "-o", "loop", "ubuntu-24.04.2-live-server-amd64.iso", mount_point], check=True)
        
        try:
            # Copy all files using rsync to handle symlinks properly
            print("📂 Copying ISO contents (handling symlinks)...")
            subprocess.run([
                "rsync", "-av", "--exclude=ubuntu", f"{mount_point}/", extract_dir
            ], check=True)
            
            # Download autoinstall.yaml from correct branch
            print("📥 Downloading autoinstall.yaml...")
            subprocess.run([
                "curl", "-s", "-o", os.path.join(extract_dir, "autoinstall.yaml"),
                "https://raw.githubusercontent.com/MachoDrone/instyaml/cursor/thoroughly-read-specified-text-files-99d8/autoinstall.yaml"
            ], check=True)
            
            # Modify GRUB config
            grub_cfg_path = os.path.join(extract_dir, "boot", "grub", "grub.cfg")
            if os.path.exists(grub_cfg_path):
                with open(grub_cfg_path, 'r') as f:
                    grub_content = f.read()
                
                # Add autoinstall parameters to all vmlinuz lines
                modified_content = grub_content.replace(
                    'linux	/casper/vmlinuz',
                    'linux	/casper/vmlinuz autoinstall ds=nocloud-net\\;s=file:///cdrom/'
                ).replace(
                    'linux	/casper/hwe-vmlinuz',
                    'linux	/casper/hwe-vmlinuz autoinstall ds=nocloud-net\\;s=file:///cdrom/'
                )
                
                with open(grub_cfg_path, 'w') as f:
                    f.write(modified_content)
                
                print("✅ Modified GRUB configuration")
            
            # Create ISO with PROPER dual boot catalog
            print("💿 Creating EFI-Fixed ISO with dual boot catalog...")
            
            cmd = [
                "xorriso", "-as", "mkisofs",
                "-r", "-V", "Ubuntu 24.04.2 INSTYAML EFI-FIXED",
                "-J", "-joliet-long",
                "-cache-inodes",
                
                # Legacy BIOS boot (first catalog entry)
                "-b", "boot/grub/i386-pc/eltorito.img",
                "-c", "boot.catalog",
                "-no-emul-boot",
                "-boot-load-size", "4",
                "-boot-info-table",
                
                # EFI boot (second catalog entry) - THE MISSING PIECE!
                "-eltorito-alt-boot",
                "-e", "EFI/boot/bootx64.efi",
                "-no-emul-boot",
                
                # GPT and hybrid boot support
                "-isohybrid-gpt-basdat",
                "-partition_offset", "16",
                "-partition_hd_cyl", "255",
                "-partition_sec_hd", "32", 
                "-partition_cyl_align", "off",
                
                # Output
                "-o", "instyaml-24.04.2-efi-fixed.iso",
                extract_dir
            ]
            
            print("🔧 xorriso command with dual boot catalog:")
            print("   Legacy BIOS: boot/grub/i386-pc/eltorito.img")
            print("   EFI Boot:    EFI/boot/bootx64.efi (via -eltorito-alt-boot)")
            print()
            
            subprocess.run(cmd, check=True)
            
            print("✅ Created instyaml-24.04.2-efi-fixed.iso")
            print()
            print("🎯 KEY CHANGES IN EFI-FIXED VERSION:")
            print("✅ Added -eltorito-alt-boot (creates second boot catalog entry)")
            print("✅ Proper EFI boot catalog entry for VirtualBox")
            print("✅ Both Legacy BIOS and EFI should now work")
            print()
            print("🧪 TEST INSTRUCTIONS:")
            print("1. Test Legacy BIOS first (disable EFI in VirtualBox)")
            print("2. Test EFI mode (enable EFI in VirtualBox)")
            print("3. Both should boot to Ubuntu installer with autoinstall")
            
            return True
            
        finally:
            subprocess.run(["sudo", "umount", mount_point], check=False)

def main():
    """Main function"""
    # Check for required tools
    required_tools = ["wget", "curl", "xorriso", "rsync"]
    missing_tools = []
    
    for tool in required_tools:
        if subprocess.run(["which", tool], capture_output=True).returncode != 0:
            missing_tools.append(tool)
    
    if missing_tools:
        print(f"❌ Missing required tools: {', '.join(missing_tools)}")
        print("💡 Install with: sudo apt update && sudo apt install -y " + " ".join(missing_tools))
        return
    
    if create_efi_fixed_iso():
        print("\n🎉 EFI-Fixed ISO created successfully!")
        print("📀 File: instyaml-24.04.2-efi-fixed.iso")
        print("🔥 This should fix the VirtualBox EFI boot issue!")
        print()
        print("🎯 NEXT STEPS:")
        print("1. Mount instyaml-24.04.2-efi-fixed.iso in VirtualBox")
        print("2. Test with Legacy BIOS first")
        print("3. Test with EFI enabled")
        print("4. Watch your revolutionary INSTYAML system work!")
        print()
        print("📊 FILE SIZES:")
        if os.path.exists("instyaml-24.04.2-efi-fixed.iso"):
            size = os.path.getsize("instyaml-24.04.2-efi-fixed.iso")
            print(f"   instyaml-24.04.2-efi-fixed.iso: {size:,} bytes ({size/1024/1024:.1f} MB)")
    else:
        print("\n❌ Failed to create EFI-fixed ISO")

if __name__ == "__main__":
    main()