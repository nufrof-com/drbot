# DRP SpokesBot CDK Deployment

This CDK stack automates the deployment of the Democratic Republican SpokesBot to AWS EC2.

## Prerequisites

1. **AWS CLI** configured with credentials
2. **Node.js** 18+ installed
3. **AWS CDK CLI** installed: `npm install -g aws-cdk`
4. **TypeScript** (installed via npm)

## Setup

### 1. Install Dependencies

```bash
cd cdk
npm install
```

### 2. Bootstrap CDK (First Time Only)

```bash
cdk bootstrap
```

### 3. Configure Stack

Edit `bin/drp-spokesbot.ts` to customize:
- Region
- Account ID

Edit `lib/drp-spokesbot-stack.ts` to customize:
- Instance type (default: t3.medium)
- Key pair name
- VPC settings

## Deployment

### Deploy Stack

```bash
# Synthesize CloudFormation template
cdk synth

# Preview changes
cdk diff

# Deploy
cdk deploy
```

### Customize Instance Type

```bash
# Deploy with custom instance type
cdk deploy --context instanceType=t3.large
```

Or edit `lib/drp-spokesbot-stack.ts`:

```typescript
const instanceType = ec2.InstanceType.of(
  ec2.InstanceClass.T3,
  ec2.InstanceSize.LARGE  // Change from MEDIUM
);
```

### Specify Key Pair

```bash
# Deploy with key pair name
cdk deploy --context keyPairName=my-key-pair
```

Or edit `lib/drp-spokesbot-stack.ts`:

```typescript
keyName: 'my-key-pair',  // Add your key pair name
```

## Post-Deployment

After deployment, you'll need to:

1. **SSH into the instance** (use the output SSH command)
2. **Clone your repository**:
   ```bash
   cd /opt/partybot
   git clone https://github.com/yourusername/partybot.git .
   ```
3. **Install Python dependencies**:
   ```bash
   /opt/partybot/venv/bin/pip install -r requirements.txt
   ```
4. **Verify Ollama is running**:
   ```bash
   systemctl status ollama
   ollama list  # Should show qwen3:0.6b and qwen3-embedding:0.6b
   ```
5. **Start the application**:
   ```bash
   systemctl start drp-spokesbot
   ```
6. **Check logs**:
   ```bash
   journalctl -u drp-spokesbot -f
   ```

## Alternative: Automated Deployment

For automated deployment, consider:

1. **AWS CodeDeploy** - Deploy from S3 or GitHub
2. **GitHub Actions** - CI/CD pipeline
3. **AWS Systems Manager** - Run commands remotely
4. **User Data Script** - Modify to clone repo automatically

### Example: Auto-deploy from GitHub

Modify the user data script in `lib/drp-spokesbot-stack.ts`:

```bash
# Clone repository
cd /opt/partybot
git clone https://github.com/yourusername/partybot.git .
/opt/partybot/venv/bin/pip install -r requirements.txt
systemctl start drp-spokesbot
```

## Destroy Stack

```bash
cdk destroy
```

## Useful Commands

```bash
# Compile TypeScript
npm run build

# Watch for changes and compile
npm run watch

# Run tests
npm test

# CDK commands
cdk synth          # Synthesize CloudFormation template
cdk diff           # Compare deployed stack with current state
cdk deploy         # Deploy this stack to your default AWS account/region
cdk destroy        # Destroy stack
cdk ls             # List all stacks
```

## Stack Outputs

After deployment, the stack outputs:
- **InstanceId**: EC2 instance ID
- **PublicIp**: Public IP address
- **PublicDnsName**: Public DNS name
- **SshCommand**: SSH command to connect
- **AppUrl**: Application URL

## Cost Optimization

- Use **t3.medium** for development (minimum recommended)
- Use **Reserved Instances** for production (save up to 72%)
- Consider **Spot Instances** for non-critical workloads
- Use **Auto Scaling** to scale down during off-hours

## Security Notes

1. **SSH Access**: Currently allows SSH from anywhere. Restrict in production:
   ```typescript
   securityGroup.addIngressRule(
     ec2.Peer.ipv4('YOUR_IP/32'),  // Replace with your IP
     ec2.Port.tcp(22),
     'Allow SSH from my IP'
   );
   ```

2. **Key Pair**: Make sure you have the key pair created in EC2 console

3. **HTTPS**: Set up SSL certificates (Let's Encrypt) after deployment

## Troubleshooting

### Instance not accessible

```bash
# Check instance status
aws ec2 describe-instances --instance-ids <instance-id>

# Check security group
aws ec2 describe-security-groups --group-ids <sg-id>
```

### Application not starting

```bash
# SSH into instance
ssh -i your-key.pem ec2-user@<public-ip>

# Check services
sudo systemctl status ollama
sudo systemctl status drp-spokesbot
sudo systemctl status nginx

# Check application logs
journalctl -u drp-spokesbot -n 50
journalctl -u ollama -n 50

# Check if Ollama models are available
ollama list
```

### CDK Deployment Fails

```bash
# Check AWS credentials
aws sts get-caller-identity

# Check CDK bootstrap
cdk bootstrap

# Check CloudFormation events
aws cloudformation describe-stack-events --stack-name DrpSpokesbotStack
```

