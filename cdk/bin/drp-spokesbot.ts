#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { DrpSpokesbotStack } from '../lib/drp-spokesbot-stack';

const app = new cdk.App();

new DrpSpokesbotStack(app, 'DrpSpokesbotStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
  },
  description: 'Democratic Republican SpokesBot on EC2',
  // Uncomment and set these for automatic deployment:
  gitRepoUrl: 'https://github.com/nufrof-com/drbot.git',
  gitBranch: 'main',  // optional, defaults to 'main'
});

