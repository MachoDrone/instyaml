# EFI Boot Fix Research - Missing GPT Partition Table

## Problem Summary
- ✅ Legacy BIOS boot works perfectly
- ✅ EFI files (bootx64.efi, grubx64.efi, mmx64.efi) are present and identical
- ✅ EFI boot catalog entry (91 ef) is present in boot catalog
- ❌ GPT partition table missing ("GPT: not present")
- ❌ EFI boot fails in VirtualBox

## Root Cause
Ubuntu ISOs have both MBR and GPT partition tables (hybrid boot), while our custom ISO only has MBR. Modern UEFI firmware requires GPT for EFI boot.

## Current xorriso Parameters (v0.25)
```bash
xorriso -as mkisofs \
  -r -V "Ubuntu 24.04.2 INSTYAML" \
  -J -joliet-long \
  -cache-inodes \
  -b "boot/grub/i386-pc/eltorito.img" \
  -c "boot.catalog" \
  -no-emul-boot \
  -boot-load-size 4 \
  -boot-info-table \
  -eltorito-alt-boot \
  -e "EFI/boot/bootx64.efi" \
  -no-emul-boot \
  -isohybrid-gpt-basdat \
  -isohybrid-apm-hfsplus \
  -partition_offset 16 \
  -o output.iso input_dir
```

## Approach 1: Enhanced xorriso Parameters

Try these additional Ubuntu-compatible parameters:

```bash
xorriso -as mkisofs \
  -r -V "Ubuntu 24.04.2 INSTYAML" \
  -J -joliet-long \
  -cache-inodes \
  -b "boot/grub/i386-pc/eltorito.img" \
  -c "boot.catalog" \
  -no-emul-boot \
  -boot-load-size 4 \
  -boot-info-table \
  -eltorito-alt-boot \
  -e "EFI/boot/bootx64.efi" \
  -no-emul-boot \
  -isohybrid-gpt-basdat \
  -isohybrid-mbr /usr/lib/ISOLINUX/isohdpfx.bin \
  -partition_offset 16 \
  -partition_hd_cyl 1024 \
  -partition_sec_hd 32 \
  -partition_cyl_align off \
  -append_partition 2 0xef EFI/boot/bootx64.efi \
  -o output.iso input_dir
```

## Approach 2: Post-Processing with isohybrid

Create ISO normally, then add GPT:

```bash
# Step 1: Create ISO with basic xorriso
xorriso -as mkisofs [basic parameters] -o temp.iso input_dir

# Step 2: Add GPT partition table
isohybrid --uefi --mac temp.iso

# Step 3: Rename to final ISO
mv temp.iso final.iso
```

## Approach 3: Use grub-mkrescue

```bash
# Create minimal grub structure
mkdir -p iso/boot/grub
echo 'set default=0' > iso/boot/grub/grub.cfg

# Copy Ubuntu content
cp -r ubuntu_extract/* iso/

# Build with grub-mkrescue (automatically creates GPT)
grub-mkrescue --output=output.iso iso/
```

## Approach 4: Exact Ubuntu Parameters

Research shows Ubuntu uses these specific xorriso parameters:

```bash
xorriso -as mkisofs \
  -r -V "Ubuntu 24.04.2 LTS amd64" \
  -o output.iso \
  -J -joliet-long \
  -cache-inodes \
  -b isolinux/isolinux.bin \
  -c isolinux/boot.cat \
  -no-emul-boot \
  -boot-load-size 4 \
  -boot-info-table \
  -eltorito-alt-boot \
  -e boot/grub/efi.img \
  -no-emul-boot \
  -isohybrid-gpt-basdat \
  -isohybrid-mbr /usr/lib/ISOLINUX/isohdpfx.bin \
  input_dir
```

## Approach 5: Alternative EFI Image

Instead of pointing to bootx64.efi directly, create/use efi.img:

```bash
# Check if Ubuntu has efi.img
find ubuntu_extract -name "efi.img" -type f

# If found, use:
-e "boot/grub/efi.img"

# Instead of:
-e "EFI/boot/bootx64.efi"
```

## Testing Commands

### Check Current ISO Structure
```bash
# Check partition table
sudo gdisk -l custom.iso

# Check boot catalog
hexdump -C custom.iso | grep -A5 -B5 "91 ef"

# Mount and compare EFI files
sudo mount -o loop custom.iso /mnt/custom
sudo mount -o loop ubuntu.iso /mnt/ubuntu
md5sum /mnt/custom/EFI/boot/* /mnt/ubuntu/EFI/boot/*
```

### Test Each Approach
```bash
# Test in VirtualBox
# 1. Create VM with EFI enabled
# 2. Boot from ISO
# 3. Check if GRUB menu appears
# 4. Verify EFI boot process
```

## Implementation Priority

1. **Try Approach 1** (enhanced xorriso) - easiest to implement
2. **Try Approach 2** (post-processing) - if isohybrid supports it
3. **Research Ubuntu's exact method** - look at ubuntu build scripts
4. **Try Approach 4** (exact Ubuntu params) - if we find them
5. **Try Approach 3** (grub-mkrescue) - last resort, more complex

## Expected Outcome

After implementing the correct approach:
- `sudo gdisk -l custom.iso` should show "GPT: present"
- EFI boot should work in VirtualBox
- Legacy BIOS boot should still work (hybrid)

## Code Implementation

The fix should be implemented in `iso_builder.py` around line 450 in the `create_iso()` method, specifically in the EFI support section:

```python
if has_efi_support:
    cmd.extend([
        "-eltorito-alt-boot",
        "-e", "EFI/boot/bootx64.efi",  # or boot/grub/efi.img
        "-no-emul-boot",
        "-isohybrid-gpt-basdat",
        # ADD NEW PARAMETERS HERE
        "-isohybrid-mbr", "/usr/lib/ISOLINUX/isohdpfx.bin",
        "-append_partition", "2", "0xef", "EFI/boot/bootx64.efi"
    ])
```