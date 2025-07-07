# INSTYAML - Ubuntu Server Auto-Installer

A system for creating lightweight, updateable Ubuntu Server installations using cloud-init and GitHub-hosted installer scripts.

## How It Works

1. **Modified ISO**: Ubuntu 24.04.2 Live Server ISO modified to include `autoinstall.yaml`
2. **Boot Process**: ISO boots and automatically runs the autoinstall YAML
3. **Network Setup**: YAML establishes network connectivity via DHCP
4. **Script Download**: Downloads `install.sh` from this GitHub repository
5. **Execution**: Runs the installer script to customize the OS

## Files

- `autoinstall.yaml` - Cloud-init configuration file (embed in ISO)
- `install.sh` - Installer script (hosted on GitHub, downloaded during install)

## Workflow

1. Create modified ISO with `autoinstall.yaml` embedded
2. Boot from ISO (VM or physical hardware)
3. Watch for test messages from `install.sh`
4. Edit `install.sh` in GitHub to update installer logic
5. Reboot same ISO to test updates

## Benefits

- ✅ Update installer logic without rebuilding ISOs
- ✅ End users create USB boot media once
- ✅ Rapid iteration and testing
- ✅ Internet-based updates

## Testing

The current `install.sh` displays test messages to verify:
- ISO boots correctly
- YAML executes
- Network connectivity works
- GitHub repository is accessible
- Remote script execution functions

Edit the message in `install.sh` and reboot to test the update mechanism.
