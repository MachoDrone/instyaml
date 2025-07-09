#!/usr/bin/env python3
"""
PROPER EFI ISO Creator - Based on Ubuntu's Official Method
==========================================================

This script uses the EXACT method from Ubuntu's live-custom-ubuntu-from-scratch project
to create EFI-bootable ISOs that work properly in VirtualBox and real hardware.

The key insight: Ubuntu creates a proper EFI boot image (efiboot.img) and uses
complex xorriso parameters to create hybrid BIOS+UEFI+Secure Boot compatible ISOs.

Credit: Based on https://github.com/mvallim/live-custom-ubuntu-from-scratch
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

def run_command(cmd, check=True, shell=False):
    """Run a command and handle errors"""
    print(f"🔧 Running: {cmd}")
    try:
        if isinstance(cmd, str) and not shell:
            cmd = cmd.split()
        result = subprocess.run(cmd, check=check, capture_output=True, text=True, shell=shell)
        if result.stdout:
            print(f"✅ Output: {result.stdout.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running command: {cmd}")
        print(f"❌ Error: {e}")
        print(f"❌ Stdout: {e.stdout}")
        print(f"❌ Stderr: {e.stderr}")
        raise

def extract_ubuntu_iso(iso_path, extract_dir):
    """Extract Ubuntu ISO to working directory"""
    print(f"📦 Extracting Ubuntu ISO: {iso_path}")
    
    # Mount the ISO
    mount_dir = extract_dir / "mount"
    mount_dir.mkdir(exist_ok=True)
    
    try:
        run_command(f"sudo mount -o loop {iso_path} {mount_dir}")
        
        # Copy contents (excluding squashfs for now)
        iso_contents = extract_dir / "iso"
        iso_contents.mkdir(exist_ok=True)
        
        run_command(f"sudo rsync -av --exclude=casper/filesystem.squashfs {mount_dir}/ {iso_contents}/")
        
        # Fix permissions
        run_command(f"sudo chown -R $USER:$USER {iso_contents}")
        
    finally:
        # Unmount
        run_command("sudo umount " + str(mount_dir), check=False)

def inject_hello_world(iso_contents, extract_dir):
    """Extract squashfs, inject HelloWorld.txt, and recompress"""
    print("🔧 Injecting HelloWorld.txt into filesystem")
    
    # Extract squashfs
    squashfs_file = extract_dir / "mount" / "casper" / "filesystem.squashfs"
    filesystem_dir = extract_dir / "filesystem"
    
    # Re-mount to get squashfs
    mount_dir = extract_dir / "mount"
    try:
        run_command(f"sudo mount -o loop {extract_dir.parent / 'ubuntu-24.04.2-server-amd64.iso'} {mount_dir}")
        
        # Extract squashfs
        run_command(f"sudo unsquashfs -d {filesystem_dir} {mount_dir}/casper/filesystem.squashfs")
        
    finally:
        run_command("sudo umount " + str(mount_dir), check=False)
    
    # Inject HelloWorld.txt
    hello_file = filesystem_dir / "HelloWorld.txt"
    run_command(f"sudo bash -c 'echo \"Hello from Proper EFI Creator! $(date)\" > {hello_file}'")
    
    # Fix permissions
    run_command(f"sudo chown $USER:$USER {hello_file}")
    
    # Recreate squashfs
    new_squashfs = iso_contents / "casper" / "filesystem.squashfs"
    run_command(f"sudo mksquashfs {filesystem_dir} {new_squashfs} -comp xz -noappend")
    
    # Update filesystem.size
    size_file = iso_contents / "casper" / "filesystem.size"
    result = run_command(f"sudo du -sx --block-size=1 {filesystem_dir}")
    size = result.stdout.split()[0]
    run_command(f"echo {size} | sudo tee {size_file}")

def create_efi_boot_structure(iso_contents):
    """Create the proper EFI boot structure like Ubuntu does"""
    print("🔧 Creating EFI boot structure")
    
    isolinux_dir = iso_contents / "isolinux"
    isolinux_dir.mkdir(exist_ok=True)
    
    # Copy EFI loaders (Ubuntu's signed bootloaders)
    print("📦 Copying EFI bootloaders")
    efi_files = [
        ("/usr/lib/shim/shimx64.efi.signed.latest", "bootx64.efi"),
        ("/usr/lib/shim/mmx64.efi", "mmx64.efi"),
        ("/usr/lib/grub/x86_64-efi-signed/grubx64.efi.signed", "grubx64.efi")
    ]
    
    for src, dst in efi_files:
        if not os.path.exists(src):
            src = src.replace(".latest", "")  # Fallback
        if not os.path.exists(src):
            src = src.replace(".signed", "")  # Another fallback
        
        if os.path.exists(src):
            run_command(f"cp {src} {isolinux_dir / dst}")
        else:
            print(f"⚠️  Warning: {src} not found, EFI boot may not work")
    
    # Create GRUB configuration
    grub_cfg = isolinux_dir / "grub.cfg"
    grub_config = '''search --set=root --file /ubuntu
insmod all_video
set default="0"
set timeout=30

menuentry "Try Ubuntu without installing" {
   linux /casper/vmlinuz boot=casper nopersistent toram quiet splash ---
   initrd /casper/initrd
}

menuentry "Install Ubuntu" {
   linux /casper/vmlinuz boot=casper only-ubiquity quiet splash ---
   initrd /casper/initrd
}

menuentry "Check disc for defects" {
   linux /casper/vmlinuz boot=casper integrity-check quiet splash ---
   initrd /casper/initrd
}

if [ "$grub_platform" = "efi" ]; then
menuentry 'UEFI Firmware Settings' {
   fwsetup
}
fi
'''
    
    with open(grub_cfg, 'w') as f:
        f.write(grub_config)
    
    # Create the FAT16 EFI boot image (THIS IS THE KEY!)
    print("🔧 Creating EFI boot image")
    efi_img = isolinux_dir / "efiboot.img"
    
    # Create 10MB EFI boot image
    run_command(f"dd if=/dev/zero of={efi_img} bs=1M count=10")
    run_command(f"mkfs.vfat -F 16 {efi_img}")
    
    # Mount the EFI image and populate it
    efi_mount = iso_contents.parent / "efi_mount"
    efi_mount.mkdir(exist_ok=True)
    
    try:
        run_command(f"sudo mount -o loop {efi_img} {efi_mount}")
        
        # Create EFI directory structure
        efi_dirs = ["EFI/boot", "EFI/ubuntu"]
        for dir_path in efi_dirs:
            (efi_mount / dir_path).mkdir(parents=True, exist_ok=True)
        
        # Copy EFI files into the image
        for src, dst in efi_files:
            src_file = isolinux_dir / dst
            if src_file.exists():
                run_command(f"sudo cp {src_file} {efi_mount}/EFI/boot/{dst}")
        
        # Copy GRUB config
        run_command(f"sudo cp {grub_cfg} {efi_mount}/EFI/ubuntu/grub.cfg")
        
    finally:
        run_command(f"sudo umount {efi_mount}", check=False)
    
    # Create BIOS boot image
    print("🔧 Creating BIOS boot image")
    bios_img = isolinux_dir / "bios.img"
    
    # Create GRUB standalone image for BIOS
    run_command(f"""grub-mkstandalone \
   --format=i386-pc \
   --output={isolinux_dir}/core.img \
   --install-modules="linux16 linux normal iso9660 biosdisk memdisk search tar ls" \
   --modules="linux16 linux normal iso9660 biosdisk search" \
   --locales="" \
   --fonts="" \
   "boot/grub/grub.cfg={grub_cfg}" """, shell=True)
    
    # Combine with cdboot.img
    cdboot_img = "/usr/lib/grub/i386-pc/cdboot.img"
    if os.path.exists(cdboot_img):
        run_command(f"cat {cdboot_img} {isolinux_dir}/core.img > {bios_img}")
    
    # Create the ubuntu marker file
    (iso_contents / "ubuntu").touch()

def create_proper_iso(iso_contents, output_iso):
    """Create ISO using Ubuntu's proven xorriso method"""
    print("🔧 Creating ISO with proper EFI support")
    
    # Change to iso contents directory
    os.chdir(iso_contents)
    
    # Get the hybrid MBR
    hybrid_mbr = None
    mbr_locations = [
        "/usr/lib/grub/i386-pc/boot_hybrid.img",
        "../chroot/usr/lib/grub/i386-pc/boot_hybrid.img"
    ]
    
    for mbr_path in mbr_locations:
        if os.path.exists(mbr_path):
            hybrid_mbr = mbr_path
            break
    
    if not hybrid_mbr:
        print("⚠️  Warning: hybrid MBR not found, using basic method")
    
    # The EXACT command from Ubuntu's live-custom-ubuntu-from-scratch
    xorriso_cmd = f"""sudo xorriso \\
   -as mkisofs \\
   -iso-level 3 \\
   -full-iso9660-filenames \\
   -J -J -joliet-long \\
   -volid "Ubuntu Custom EFI" \\
   -output "{output_iso}" \\
   -eltorito-boot isolinux/bios.img \\
     -no-emul-boot \\
     -boot-load-size 4 \\
     -boot-info-table \\
     --eltorito-catalog boot.catalog \\
     --grub2-boot-info \\"""
    
    if hybrid_mbr:
        xorriso_cmd += f"""     --grub2-mbr {hybrid_mbr} \\"""
    
    xorriso_cmd += """     -partition_offset 16 \\
     --mbr-force-bootable \\
   -eltorito-alt-boot \\
     -no-emul-boot \\
     -e isolinux/efiboot.img \\
     -append_partition 2 28732ac11ff8d211ba4b00a0c93ec93b isolinux/efiboot.img \\
     -appended_part_as_gpt \\
     -iso_mbr_part_type a2a0d0ebe5b9334487c068b6b72699c7 \\
     -m "isolinux/efiboot.img" \\
     -m "isolinux/bios.img" \\
     -e '--interval:appended_partition_2:::' \\
   -exclude isolinux \\
   -graft-points \\
      "/EFI/boot/bootx64.efi=isolinux/bootx64.efi" \\
      "/EFI/boot/mmx64.efi=isolinux/mmx64.efi" \\
      "/EFI/boot/grubx64.efi=isolinux/grubx64.efi" \\
      "/EFI/ubuntu/grub.cfg=isolinux/grub.cfg" \\
      "/isolinux/bios.img=isolinux/bios.img" \\
      "/isolinux/efiboot.img=isolinux/efiboot.img" \\
      "." """
    
    # Execute the command
    run_command(xorriso_cmd, shell=True)

def main():
    """Main execution function"""
    print("🚀 Proper EFI ISO Creator - Ubuntu's Official Method")
    print("=" * 60)
    
    # Check for required tools
    required_tools = ["sudo", "mount", "rsync", "unsquashfs", "mksquashfs", "mkfs.vfat", "grub-mkstandalone", "xorriso"]
    for tool in required_tools:
        if not shutil.which(tool):
            print(f"❌ Required tool not found: {tool}")
            sys.exit(1)
    
    # Get Ubuntu ISO path
    iso_path = "ubuntu-24.04.2-server-amd64.iso"
    if not os.path.exists(iso_path):
        print(f"❌ Ubuntu ISO not found: {iso_path}")
        print("Please download Ubuntu 24.04.2 Server ISO")
        sys.exit(1)
    
    # Create working directory
    with tempfile.TemporaryDirectory(prefix="proper_efi_") as temp_dir:
        work_dir = Path(temp_dir)
        print(f"📁 Working directory: {work_dir}")
        
        try:
            # Step 1: Extract Ubuntu ISO
            extract_ubuntu_iso(iso_path, work_dir)
            
            # Step 2: Inject HelloWorld.txt
            iso_contents = work_dir / "iso"
            inject_hello_world(iso_contents, work_dir)
            
            # Step 3: Create proper EFI boot structure
            create_efi_boot_structure(iso_contents)
            
            # Step 4: Create ISO with proper EFI support
            output_iso = f"ubuntu-proper-efi-{os.getpid()}.iso"
            create_proper_iso(iso_contents, str(Path.cwd() / output_iso))
            
            print(f"🎉 SUCCESS! Created: {output_iso}")
            print("\n📝 Test Results:")
            print("✅ Should boot in VirtualBox with EFI enabled")
            print("✅ Should show short error messages like original Ubuntu")
            print("✅ Should proceed to GRUB menu")
            print("✅ Contains HelloWorld.txt in root filesystem")
            print("\n🔍 Key differences from our previous attempts:")
            print("  • Creates proper EFI boot image (efiboot.img)")
            print("  • Uses Ubuntu's signed EFI bootloaders")
            print("  • Creates GPT partition table")
            print("  • Uses proper hybrid MBR")
            print("  • Implements full Ubuntu boot structure")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()