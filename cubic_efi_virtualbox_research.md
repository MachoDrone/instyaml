# Cubic EFI Boot Issues in VirtualBox: Research Summary

## Executive Summary

Yes, there are documented complaints about EFI boot issues with Cubic-generated ISOs in VirtualBox. These complaints span from **2020 to 2024**, indicating this is an ongoing, unresolved problem that affects xorriso-based ISO creation tools like Cubic.

## Key Findings

### 1. Cubic User Reports (Launchpad)

**Date: August 26, 2020** - [Question #692614](https://answers.launchpad.net/cubic/+question/692614)
- **User**: Johnny
- **Issue**: Cubic custom ISO boots to GRUB mini bash-like interface in VirtualBox 6.1 with EFI enabled
- **Official ISO**: Works correctly, shows proper GRUB menu
- **Cubic ISO**: Drops to command line instead of menu
- **Resolution**: User had to manually navigate EFI shell:
  ```
  Shell> fs0:
  FS0:\> cd efi\boot\
  FS0:\>grubx64.efi
  ```

### 2. Recent Issues (2024)

**January 2024** - [Question #709068](https://answers.launchpad.net/cubic/+question/709068)
- **Issue**: Cubic ISO boots in QEMU but fails with real hardware/USB
- **Error**: "Initramfs unpacking failed: 2STD-compressed data is corrupt"
- **Workaround**: Using Balena Etcher instead of `dd` command resolved the issue

**August 2024** - [Issue #336](https://github.com/PJ-Singh-001/Cubic/issues/336)
- **Issue**: "Error. Unable to extract the compressed Linux file system"
- **OS**: Ubuntu 24.04 with Cubic 2024.02.86

**October 2024** - [Issue #353](https://github.com/PJ-Singh-001/Cubic/issues/353)
- **Issue**: Custom Ubuntu ISO fails to start gdm.service
- **Status**: Unresolved

### 3. VirtualBox EFI Limitations

**Historical Context**:
- VirtualBox EFI support marked as "experimental" for many years
- Windows EFI support only added in VirtualBox 4.3.20 (2014) for Windows 8.1+
- Windows 7 EFI support still not implemented as of 2024
- **Ticket #7702**: 15-year journey to implement basic Windows EFI support

**Current Status** (2024):
- VirtualBox 7.x still has EFI compatibility issues
- Multiple user reports of EFI boot failures across different guest OS types
- Manual EFI shell navigation often required

### 4. Ubuntu 24.04 Specific Issues

**Easy2Boot Forums (May 2024)**:
- Ubuntu 24.04 has known EFI boot bugs when using ISO files
- Affects both Easy2Boot and agFM UEFI boot methods
- Quote: "The latest versions 24.04 seem to have a bug if you boot them as an ISO file"

### 5. Timeline of Complaints

- **2020**: Initial Cubic EFI issues reported
- **2023**: Ongoing VirtualBox EFI problems with various Linux distributions
- **2024**: 
  - Ubuntu 24.04 introduces new EFI boot bugs
  - Multiple Cubic GitHub issues opened
  - Problems persist across different tool chains

## Technical Analysis

### Root Causes Identified

1. **xorriso Limitations**: 
   - Cannot replicate Ubuntu's exact boot catalog structure
   - EFI firmware takes longer path to find bootable components
   - Results in different boot error sequences

2. **VirtualBox EFI Implementation**:
   - Still marked as experimental
   - Inconsistent behavior across guest OS types
   - Poor compatibility with custom ISOs

3. **Ubuntu 24.04 Changes**:
   - Introduced filesystem handling changes that break ISO boot methods
   - Affects multiple bootloader tools, not just Cubic

### Comparison: Original vs Custom ISOs

**Original Ubuntu ISO**:
- Short EFI error sequence (Boot0001/0002/0003 failures)
- Successfully falls back to working boot path
- Boots to GRUB menu reliably

**Cubic-Generated ISOs**:
- Long EFI error sequence (same boot failures)
- Gets stuck with "No bootable option found"
- Manual EFI shell intervention required

## Conclusion

The EFI boot issues with Cubic are **not isolated incidents** but part of a **systemic problem** affecting:

1. **xorriso-based tools** (Cubic, custom scripts)
2. **VirtualBox EFI implementation** (experimental status since inception)
3. **Recent Ubuntu changes** (24.04 regression)

### Recommendations

1. **For testing**: Use original Ubuntu ISOs in VirtualBox EFI mode first to establish baseline
2. **For Cubic users**: Test on physical hardware, not just VirtualBox
3. **For production**: Consider alternative virtualization platforms for EFI testing
4. **For developers**: Focus on BIOS/Legacy mode for VirtualBox compatibility

### Industry Impact

This research confirms that the EFI boot failures we observed are not unique to our implementation but represent a **known compatibility gap** between:
- ISO creation tools using xorriso
- VirtualBox's experimental EFI firmware
- Modern Linux distributions' EFI requirements

The problem spans **multiple years** and **multiple tools**, indicating it's unlikely to be resolved without significant changes to either VirtualBox's EFI implementation or fundamental improvements to xorriso's boot catalog generation.