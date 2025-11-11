# Viewing User Data Logs

The user data script logs to multiple locations. Here's how to access them:

## Log Locations

### 1. Custom User Data Log (Recommended)
**Location:** `/var/log/user-data.log`

This is the log file we explicitly created in the user data script. It contains all output from the script.

### 2. Cloud-Init Output Log
**Location:** `/var/log/cloud-init-output.log`

Standard cloud-init log that captures all output from user data scripts.

### 3. Cloud-Init Log
**Location:** `/var/log/cloud-init.log`

Detailed cloud-init execution log with timestamps.

## How to View Logs

### Option 1: Via AWS Systems Manager (No SSH Key Needed)

```bash
# Get instance ID
INSTANCE_ID=$(aws cloudformation describe-stacks \
  --stack-name DrpSpokesbotStack \
  --query 'Stacks[0].Outputs[?OutputKey==`InstanceId`].OutputValue' \
  --output text)

# Connect via SSM
aws ssm start-session --target $INSTANCE_ID

# Once connected, view logs:
sudo tail -f /var/log/user-data.log
# or
sudo tail -f /var/log/cloud-init-output.log
```

### Option 2: Via SSH (If You Have Key Pair)

```bash
# SSH into instance
ssh -i your-key.pem ec2-user@<public-ip>

# View logs
sudo tail -f /var/log/user-data.log
sudo tail -f /var/log/cloud-init-output.log
sudo cat /var/log/cloud-init.log
```

### Option 3: One-Liner to View Latest Logs

```bash
# Get instance ID and view logs in one command
INSTANCE_ID=$(aws cloudformation describe-stacks \
  --stack-name DrpSpokesbotStack \
  --query 'Stacks[0].Outputs[?OutputKey==`InstanceId`].OutputValue' \
  --output text)

# View last 100 lines of user data log
aws ssm send-command \
  --instance-ids $INSTANCE_ID \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=["sudo tail -100 /var/log/user-data.log"]' \
  --query 'Command.CommandId' \
  --output text

# Then get the output (replace COMMAND_ID)
aws ssm get-command-invocation \
  --command-id COMMAND_ID \
  --instance-id $INSTANCE_ID
```

## Viewing Application Logs

After deployment, check application status:

```bash
# Via SSM
aws ssm start-session --target $INSTANCE_ID

# Then run:
sudo journalctl -u drp-spokesbot -f
sudo journalctl -u ollama -f
sudo systemctl status drp-spokesbot
sudo systemctl status ollama
```

## Quick Status Check

```bash
# Check if user data completed
aws ssm send-command \
  --instance-ids $INSTANCE_ID \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=["sudo tail -20 /var/log/user-data.log"]' \
  --output text | grep -A 20 "CommandId"
```

## What to Look For

In the logs, you should see:
- ✅ "Starting user data script at..."
- ✅ "Ollama is ready!"
- ✅ "Models are ready!" (if auto-deploying)
- ✅ "Application started successfully!"
- ✅ "User data script completed at..."

If you see errors, they'll be clearly marked in the log.

