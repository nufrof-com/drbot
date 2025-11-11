# Checking User Data Script Status

If `/var/log/user-data.log` doesn't exist, the user data script may not have run or failed early. Here's how to diagnose:

## Step 1: Check Cloud-Init Status

```bash
# Connect via SSM
aws ssm start-session --target <instance-id>

# Check cloud-init status
sudo cloud-init status
sudo cloud-init status --wait  # Wait for it to complete

# Check if cloud-init finished
sudo cat /var/lib/cloud/instance/boot-finished
```

## Step 2: Check Cloud-Init Logs

```bash
# Main cloud-init log
sudo cat /var/log/cloud-init.log | tail -100

# Cloud-init output (most important)
sudo cat /var/log/cloud-init-output.log | tail -100

# Check for errors
sudo grep -i error /var/log/cloud-init.log
sudo grep -i error /var/log/cloud-init-output.log
```

## Step 3: Check User Data Script Execution

```bash
# Check if user data was executed
sudo cat /var/lib/cloud/instance/user-data.txt

# Check user data script location
ls -la /var/lib/cloud/instances/*/scripts/

# Check if scripts ran
sudo cat /var/lib/cloud/instance/scripts/runcmd
```

## Step 4: Check What Actually Ran

```bash
# Check if directories were created
ls -la /opt/partybot

# Check if services exist
sudo systemctl list-unit-files | grep -E "ollama|drp-spokesbot|nginx"

# Check if packages were installed
which python3
which ollama
which nginx

# Check systemd services
sudo systemctl status ollama
sudo systemctl status drp-spokesbot
sudo systemctl status nginx
```

## Step 5: Re-run User Data Manually (If Needed)

If user data didn't run, you can execute it manually:

```bash
# Get the user data script
sudo cat /var/lib/cloud/instance/user-data.txt > /tmp/user-data.sh
chmod +x /tmp/user-data.sh

# Run it (this will reinstall/configure everything)
sudo /tmp/user-data.sh
```

## Common Issues

### Issue: User Data Script Not Running

**Symptoms:**
- No `/var/log/user-data.log`
- No `/opt/partybot` directory
- Services not installed

**Possible Causes:**
1. Cloud-init hasn't finished yet (wait 2-5 minutes after instance start)
2. User data script had a syntax error
3. Instance was created before user data was set

**Solution:**
```bash
# Check cloud-init status
sudo cloud-init status

# If it says "status: running" or "status: error", check logs
sudo tail -50 /var/log/cloud-init-output.log
```

### Issue: User Data Failed Early

**Symptoms:**
- `/var/log/user-data.log` exists but is short
- Script stopped partway through

**Solution:**
```bash
# Check the log
sudo cat /var/log/user-data.log

# Check cloud-init output for errors
sudo tail -100 /var/log/cloud-init-output.log | grep -i error
```

### Issue: Package Installation Failed

**Symptoms:**
- Log shows package installation errors
- Missing commands (python3, ollama, etc.)

**Solution:**
```bash
# Try installing manually
sudo yum update -y
sudo yum install -y python3 python3-pip python3-devel gcc git nginx

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sudo sh
```

## Quick Diagnostic Script

Run this to get a full status report:

```bash
cat << 'EOF' | sudo bash
echo "=== Cloud-Init Status ==="
cloud-init status
echo ""
echo "=== User Data Log Exists? ==="
[ -f /var/log/user-data.log ] && echo "YES" || echo "NO"
echo ""
echo "=== Last 20 lines of cloud-init-output.log ==="
tail -20 /var/log/cloud-init-output.log
echo ""
echo "=== Installed Packages ==="
which python3 ollama nginx || echo "Some packages missing"
echo ""
echo "=== Services Status ==="
systemctl list-units --type=service --state=running | grep -E "ollama|drp-spokesbot|nginx" || echo "Services not running"
echo ""
echo "=== Directory Check ==="
[ -d /opt/partybot ] && echo "/opt/partybot exists" || echo "/opt/partybot missing"
EOF
```

## Next Steps

1. **If user data never ran**: Check cloud-init status and logs
2. **If user data failed**: Check the error in cloud-init-output.log
3. **If user data is still running**: Wait a few more minutes
4. **If everything looks good but app isn't running**: Check application logs with `journalctl -u drp-spokesbot`

