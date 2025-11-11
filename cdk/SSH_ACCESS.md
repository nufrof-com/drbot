# SSH Access to EC2 Instance

If you deployed without a key pair, you have two options:

## Option 1: AWS Systems Manager Session Manager (Recommended - No Key Needed)

The CDK stack already configured the instance with SSM permissions, so you can connect immediately:

### Prerequisites

1. **Install AWS CLI** (if not already installed):
   ```bash
   # macOS
   brew install awscli
   
   # Or download from: https://aws.amazon.com/cli/
   ```

2. **Install Session Manager Plugin**:
   ```bash
   # macOS
   brew install --cask session-manager-plugin
   
   # Or download from: https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html
   ```

3. **Configure AWS credentials** (if not already done):
   ```bash
   aws configure
   ```

### Connect via SSM

```bash
# Get the instance ID from CDK outputs or AWS Console
INSTANCE_ID=$(aws cloudformation describe-stacks \
  --stack-name DrpSpokesbotStack \
  --query 'Stacks[0].Outputs[?OutputKey==`InstanceId`].OutputValue' \
  --output text)

# Connect via SSM
aws ssm start-session --target $INSTANCE_ID
```

Or if you know the instance ID:
```bash
aws ssm start-session --target i-0123456789abcdef0
```

### Exit Session

Type `exit` or press `Ctrl+D` to disconnect.

---

## Option 2: Add a Key Pair to Existing Instance

### Step 1: Create a Key Pair

```bash
# Create a new key pair
aws ec2 create-key-pair \
  --key-name drp-spokesbot-key \
  --query 'KeyMaterial' \
  --output text > ~/.ssh/drp-spokesbot-key.pem

# Set proper permissions
chmod 400 ~/.ssh/drp-spokesbot-key.pem
```

### Step 2: Stop the Instance

```bash
# Get instance ID
INSTANCE_ID=$(aws cloudformation describe-stacks \
  --stack-name DrpSpokesbotStack \
  --query 'Stacks[0].Outputs[?OutputKey==`InstanceId`].OutputValue' \
  --output text)

# Stop instance
aws ec2 stop-instances --instance-ids $INSTANCE_ID

# Wait for it to stop
aws ec2 wait instance-stopped --instance-ids $INSTANCE_ID
```

### Step 3: Attach Key Pair

You can't directly attach a key pair to a running instance. You have two options:

#### Option A: Use EC2 Instance Connect (Temporary)

```bash
# Generate a temporary SSH key
aws ec2-instance-connect send-ssh-public-key \
  --instance-id $INSTANCE_ID \
  --availability-zone $(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].Placement.AvailabilityZone' \
    --output text) \
  --instance-os-user ec2-user \
  --ssh-public-key file://~/.ssh/id_rsa.pub
```

Then SSH normally (this is temporary, expires after 60 seconds).

#### Option B: Create New Instance with Key Pair

1. **Update CDK stack** to include key pair:
   ```typescript
   // In lib/drp-spokesbot-stack.ts
   keyName: 'drp-spokesbot-key',
   ```

2. **Redeploy**:
   ```bash
   cdk deploy
   ```

3. **SSH with key**:
   ```bash
   ssh -i ~/.ssh/drp-spokesbot-key.pem ec2-user@<public-ip>
   ```

---

## Option 3: Use EC2 Instance Connect (Quick Test)

AWS provides a browser-based SSH client:

1. Go to AWS Console → EC2 → Instances
2. Select your instance
3. Click "Connect" → "EC2 Instance Connect"
4. Click "Connect"

This works without a key pair but is only for quick access.

---

## Recommended Approach

**For immediate access**: Use Option 1 (SSM Session Manager) - it's already configured and works right away.

**For long-term access**: Use Option 2B (update CDK stack with key pair and redeploy) - gives you traditional SSH access.

