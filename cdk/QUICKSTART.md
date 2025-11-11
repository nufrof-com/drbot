# Quick Start - CDK Deployment

## One-Time Setup

```bash
# 1. Install AWS CDK globally
npm install -g aws-cdk

# 2. Navigate to CDK directory
cd cdk

# 3. Install dependencies
npm install

# 4. Bootstrap CDK (first time only, per account/region)
cdk bootstrap
```

## Deploy

```bash
# 1. Preview what will be created
cdk diff

# 2. Deploy the stack
cdk deploy

# 3. Note the outputs (InstanceId, PublicIp, AppUrl)
```

## Post-Deployment Steps

After CDK creates the EC2 instance:

```bash
# 1. SSH into the instance (use the SSH command from outputs)
ssh -i your-key.pem ec2-user@<public-ip>

# 2. Clone your repository
cd /opt/partybot
git clone https://github.com/yourusername/partybot.git .

# 3. Install Python dependencies
/opt/partybot/venv/bin/pip install -r requirements.txt

# 4. Verify Ollama is running and models are pulled
systemctl status ollama
ollama list  # Should show qwen3:0.6b and qwen3-embedding:0.6b

# 5. Start the application
systemctl start drp-spokesbot

# 6. Check logs
journalctl -u drp-spokesbot -f
journalctl -u ollama -f
```

## Access Your App

Open the AppUrl from the CDK outputs in your browser:
```
http://<public-ip>
```

## Destroy

```bash
cdk destroy
```

## Customization

### Change Instance Type

Edit `lib/drp-spokesbot-stack.ts`:
```typescript
const instanceType = ec2.InstanceType.of(
  ec2.InstanceClass.T3,
  ec2.InstanceSize.LARGE  // Change from MEDIUM
);
```

### Add Key Pair

Edit `lib/drp-spokesbot-stack.ts`:
```typescript
keyName: 'your-key-pair-name',
```

### Auto-deploy from GitHub

Edit the user data script in `lib/drp-spokesbot-stack.ts` to automatically clone and start:
```bash
# Add after creating venv:
cd /opt/partybot
git clone https://github.com/yourusername/partybot.git .
/opt/partybot/venv/bin/pip install -r requirements.txt
systemctl start drp-spokesbot
```

