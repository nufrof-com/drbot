# Automatic Deployment with CDK

The CDK stack now supports **fully automatic deployment** - no manual steps required!

## How It Works

When you provide a `gitRepoUrl` in the CDK stack props, the user data script will:
1. Install all dependencies (Python, Ollama, Nginx)
2. Clone your git repository
3. Install Python dependencies
4. Wait for Ollama models to be ready
5. Start the application automatically

## Usage

### Option 1: Edit `bin/drp-spokesbot.ts`

```typescript
new DrpSpokesbotStack(app, 'DrpSpokesbotStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
  },
  description: 'Democratic Republican SpokesBot on EC2',
  gitRepoUrl: 'https://github.com/yourusername/partybot.git',
  gitBranch: 'main',  // optional, defaults to 'main'
});
```

### Option 2: Use CDK Context

```bash
cdk deploy \
  --context gitRepoUrl=https://github.com/yourusername/partybot.git \
  --context gitBranch=main
```

### Option 3: Use Environment Variables

```bash
export GIT_REPO_URL=https://github.com/yourusername/partybot.git
export GIT_BRANCH=main
cdk deploy
```

(You'd need to modify `bin/drp-spokesbot.ts` to read these)

## What Happens

1. **CDK deploys** the stack
2. **EC2 instance starts** and runs user data script
3. **Dependencies install** (Python, Ollama, Nginx)
4. **Code clones** from your git repository
5. **Dependencies install** (pip packages)
6. **Models download** (if not already present)
7. **Application starts** automatically
8. **You're done!** Just wait 5-10 minutes and visit the AppUrl

## Monitoring

Check deployment progress:

```bash
# Get instance ID
INSTANCE_ID=$(aws cloudformation describe-stacks \
  --stack-name DrpSpokesbotStack \
  --query 'Stacks[0].Outputs[?OutputKey==`InstanceId`].OutputValue' \
  --output text)

# Connect via SSM
aws ssm start-session --target $INSTANCE_ID

# Check user data logs
sudo tail -f /var/log/user-data.log

# Check application logs
sudo journalctl -u drp-spokesbot -f
```

## Private Repositories

For private repositories, you have a few options:

### Option 1: Use SSH with Deploy Key

1. Generate an SSH key pair
2. Add the public key as a deploy key in GitHub/GitLab
3. Store the private key in AWS Systems Manager Parameter Store
4. Modify user data script to retrieve and use the key

### Option 2: Use GitHub Personal Access Token

1. Create a GitHub Personal Access Token
2. Store it in AWS Secrets Manager
3. Modify user data script to retrieve and use it:
   ```bash
   git clone https://<token>@github.com/username/repo.git
   ```

### Option 3: Use AWS CodeDeploy

For more complex scenarios, consider using AWS CodeDeploy which has built-in support for private repositories.

## Troubleshooting

### Deployment Failed

Check logs:
```bash
sudo cat /var/log/user-data.log
sudo journalctl -u drp-spokesbot -n 50
```

### Models Not Ready

The script waits up to 5 minutes for models. If they're not ready:
```bash
sudo -u ollama ollama pull qwen3:0.6b
sudo -u ollama ollama pull qwen3-embedding:0.6b
sudo systemctl restart drp-spokesbot
```

### Application Not Starting

Check service status:
```bash
sudo systemctl status drp-spokesbot
sudo systemctl status ollama
sudo systemctl status nginx
```

## Benefits

✅ **Zero manual steps** - everything happens automatically  
✅ **Reproducible** - same deployment every time  
✅ **Fast** - no waiting for manual commands  
✅ **Version controlled** - deployment config in CDK code  
✅ **Easy updates** - just redeploy with new code

