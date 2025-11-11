import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';

export interface DrpSpokesbotStackProps extends cdk.StackProps {
  instanceType?: ec2.InstanceType;
  keyPairName?: string;
  domainName?: string;
  /** Git repository URL to automatically deploy (e.g., https://github.com/username/partybot.git) */
  gitRepoUrl?: string;
  /** Git branch to deploy (default: main) */
  gitBranch?: string;
}

export class DrpSpokesbotStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: DrpSpokesbotStackProps) {
    super(scope, id, props);

    // VPC - Use default VPC or create new one
    const vpc = ec2.Vpc.fromLookup(this, 'VPC', {
      isDefault: true,
    });

    // Security Group
    const securityGroup = new ec2.SecurityGroup(this, 'SpokesbotSecurityGroup', {
      vpc,
      description: 'Security group for DRP SpokesBot',
      allowAllOutbound: true,
    });

    // Allow SSH from anywhere (restrict in production!)
    securityGroup.addIngressRule(
      ec2.Peer.anyIpv4(),
      ec2.Port.tcp(22),
      'Allow SSH'
    );

    // Allow HTTP
    securityGroup.addIngressRule(
      ec2.Peer.anyIpv4(),
      ec2.Port.tcp(80),
      'Allow HTTP'
    );

    // Allow HTTPS
    securityGroup.addIngressRule(
      ec2.Peer.anyIpv4(),
      ec2.Port.tcp(443),
      'Allow HTTPS'
    );

    // IAM Role for EC2 instance
    const role = new iam.Role(this, 'SpokesbotInstanceRole', {
      assumedBy: new iam.ServicePrincipal('ec2.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonSSMManagedInstanceCore'),
      ],
    });

    // User data script to install everything directly on EC2
    const userData = ec2.UserData.forLinux();
    userData.addCommands(
      '#!/bin/bash',
      'set -euxo pipefail',
      '',
      '# Log everything to a file for debugging',
      'exec > >(tee /var/log/user-data.log)',
      'exec 2>&1',
      'echo "Starting user data script at $(date)"',
      '',
      '# Update system',
      'yum update -y',
      '',
      '# Install Python 3 and dependencies',
      '# Note: curl is already installed as curl-minimal on Amazon Linux 2023',
      'yum install -y python3 python3-pip python3-devel gcc git || { echo "Package installation failed"; exit 1; }',
      '',
      '# Install Ollama',
      'if ! command -v ollama &> /dev/null; then',
      '  curl -fsSL https://ollama.com/install.sh | sh || { echo "Ollama installation failed"; exit 1; }',
      'else',
      '  echo "Ollama already installed"',
      'fi',
      '',
      '# Install Nginx',
      'yum install -y nginx',
      '',
      '# Create app directory',
      'mkdir -p /opt/partybot',
      'chown ec2-user:ec2-user /opt/partybot',
      '',
      '# Create Python virtual environment',
      'python3 -m venv /opt/partybot/venv',
      '',
      '# Create systemd service for Ollama',
      'cat > /etc/systemd/system/ollama.service << EOF',
      '[Unit]',
      'Description=Ollama Service',
      'After=network.target',
      '',
      '[Service]',
      'Type=simple',
      'User=ollama',
      'Group=ollama',
      'ExecStart=/usr/local/bin/ollama serve',
      'Restart=always',
      'RestartSec=3',
      '',
      '[Install]',
      'WantedBy=multi-user.target',
      'EOF',
      '',
      '# Create systemd service for FastAPI app',
      'cat > /etc/systemd/system/drp-spokesbot.service << EOF',
      '[Unit]',
      'Description=DRP SpokesBot FastAPI Application',
      'After=network.target ollama.service',
      'Requires=ollama.service',
      '',
      '[Service]',
      'Type=simple',
      'User=ec2-user',
      'Group=ec2-user',
      'WorkingDirectory=/opt/partybot',
      'Environment="PATH=/opt/partybot/venv/bin:/usr/local/bin:/usr/bin:/bin"',
      'Environment="OLLAMA_BASE_URL=http://localhost:11434"',
      'ExecStart=/opt/partybot/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000',
      'Restart=always',
      'RestartSec=3',
      '',
      '[Install]',
      'WantedBy=multi-user.target',
      'EOF',
      '',
      '# Configure Nginx reverse proxy',
      'cat > /etc/nginx/conf.d/partybot.conf << EOF',
      'server {',
      '    listen 80;',
      '    server_name _;',
      '',
      '    client_max_body_size 10M;',
      '',
      '    location / {',
      '        proxy_pass http://127.0.0.1:8000;',
      '        proxy_set_header Host $host;',
      '        proxy_set_header X-Real-IP $remote_addr;',
      '        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;',
      '        proxy_set_header X-Forwarded-Proto $scheme;',
      '        proxy_read_timeout 300s;',
      '        proxy_connect_timeout 75s;',
      '    }',
      '}',
      'EOF',
      '',
      '# Enable and start services',
      'systemctl daemon-reload',
      'systemctl enable ollama',
      'systemctl enable nginx',
      'systemctl enable drp-spokesbot',
      '',
      '# Start Ollama',
      'systemctl start ollama',
      '',
      '# Wait for Ollama to be ready',
      'sleep 10',
      'for i in {1..30}; do',
      '  if curl -f http://localhost:11434/api/tags > /dev/null 2>&1; then',
      '    echo "Ollama is ready!"',
      '    break',
      '  fi',
      '  sleep 2',
      'done',
      '',
      '# Pull required models (non-blocking)',
      'su - ollama -c "ollama pull qwen3:0.6b" || echo "Model pull will continue in background"',
      'su - ollama -c "ollama pull qwen3-embedding:0.6b" || echo "Model pull will continue in background"',
      '',
      '# Start Nginx',
      'systemctl start nginx',
      '',
      '# Auto-deploy application if git repo is provided',
    );
    
    // Add git clone and deployment if repo URL is provided
    if (props?.gitRepoUrl) {
      const gitBranch = props.gitBranch || 'main';
      userData.addCommands(
        '',
        'echo "Auto-deploying from git repository..."',
        'cd /opt/partybot',
        '',
        '# Clone repository',
        `git clone -b ${gitBranch} ${props.gitRepoUrl} . || { echo "Git clone failed"; exit 1; }`,
        '',
        '# Install Python dependencies',
        '/opt/partybot/venv/bin/pip install --upgrade pip || echo "pip upgrade failed, continuing..."',
        '/opt/partybot/venv/bin/pip install -r requirements.txt || { echo "pip install failed"; exit 1; }',
        '',
        '# Wait for Ollama models to be ready (with timeout)',
        'echo "Waiting for Ollama models..."',
        'MODEL_READY=0',
        'for i in {1..60}; do',
        '  if su - ollama -c "ollama list" 2>/dev/null | grep -q "qwen3:0.6b" && su - ollama -c "ollama list" 2>/dev/null | grep -q "qwen3-embedding:0.6b"; then',
        '    echo "Models are ready!"',
        '    MODEL_READY=1',
        '    break',
        '  fi',
        '  if [ $((i % 10)) -eq 0 ]; then',
        '    echo "Waiting for models... ($i/60)"',
        '    # Try pulling models again if they\'re not ready',
        '    su - ollama -c "ollama pull qwen3:0.6b" || true',
        '    su - ollama -c "ollama pull qwen3-embedding:0.6b" || true',
        '  fi',
        '  sleep 5',
        'done',
        '',
        'if [ $MODEL_READY -eq 0 ]; then',
        '  echo "WARNING: Models not ready after 5 minutes, starting app anyway"',
        'fi',
        '',
        '# Start the application',
        'echo "Starting application..."',
        'systemctl start drp-spokesbot || { echo "Failed to start application"; exit 1; }',
        '',
        '# Wait a bit and check if app is running',
        'sleep 5',
        'if systemctl is-active --quiet drp-spokesbot; then',
        '  echo "Application started successfully!"',
        'else',
        '  echo "WARNING: Application may not be running. Check logs with: journalctl -u drp-spokesbot"',
        'fi',
        '',
        'echo "User data script completed at $(date)"',
      );
    } else {
      userData.addCommands(
        '',
        'echo "No git repository provided. Manual deployment required:"',
        'echo "  1. cd /opt/partybot"',
        'echo "  2. git clone <your-repo-url> ."',
        'echo "  3. /opt/partybot/venv/bin/pip install -r requirements.txt"',
        'echo "  4. systemctl start drp-spokesbot"',
        '',
        'echo "User data script completed at $(date)"',
      );
    }

    // EC2 Instance
    const instanceType = props?.instanceType || ec2.InstanceType.of(
      ec2.InstanceClass.T3,
      ec2.InstanceSize.MEDIUM
    );

    const instance = new ec2.Instance(this, 'SpokesbotInstance', {
      vpc,
      instanceType,
      machineImage: ec2.MachineImage.latestAmazonLinux2023({
        cpuType: ec2.AmazonLinuxCpuType.X86_64,
      }),
      // Or use Ubuntu:
      // machineImage: ec2.MachineImage.lookup({
      //   name: 'ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*',
      // }),
      securityGroup,
      role,
      userData,
      keyName: props?.keyPairName,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PUBLIC,
      },
    });

    // Outputs
    new cdk.CfnOutput(this, 'InstanceId', {
      value: instance.instanceId,
      description: 'EC2 Instance ID',
    });

    new cdk.CfnOutput(this, 'PublicIp', {
      value: instance.instancePublicIp,
      description: 'Public IP address',
    });

    new cdk.CfnOutput(this, 'PublicDnsName', {
      value: instance.instancePublicDnsName,
      description: 'Public DNS name',
    });

    new cdk.CfnOutput(this, 'SshCommand', {
      value: props?.keyPairName 
        ? `ssh -i ${props.keyPairName}.pem ec2-user@${instance.instancePublicIp}`
        : `ssh ec2-user@${instance.instancePublicIp}`,
      description: 'SSH command to connect',
    });

    new cdk.CfnOutput(this, 'AppUrl', {
      value: `http://${instance.instancePublicIp}`,
      description: 'Application URL',
    });

    if (props?.gitRepoUrl) {
      new cdk.CfnOutput(this, 'DeploymentStatus', {
        value: 'Application is being automatically deployed from git repository. Check logs: sudo journalctl -u drp-spokesbot -f',
        description: 'Auto-deployment status',
      });
    } else {
      new cdk.CfnOutput(this, 'DeploymentInstructions', {
        value: `SSH to instance, then run:
1. cd /opt/partybot
2. git clone https://github.com/yourusername/partybot.git .
3. /opt/partybot/venv/bin/pip install -r requirements.txt
4. systemctl start drp-spokesbot

Or set gitRepoUrl in CDK props for automatic deployment.`,
        description: 'Post-deployment steps',
      });
    }
  }
}

