# Zeabur Deployment Guide

## Prerequisites

- GitHub repository: `Cosiz/gappy`
- Zeabur account

## Step-by-Step Deployment

### 1. Connect Repository

1. Go to [Zeabur Dashboard](https://zeabur.com)
2. Click **New Service** → **GitHub**
3. Select the `Cosiz/gappy` repository

### 2. Configure Service

- **Build Method**: Dockerfile (auto-detected)
- **Port**: `8080`
- **Health Check Path**: `/health` (recommended)

### 3. Environment Variables (Optional)

No environment variables are strictly required for the prototype.
You may optionally set:

```
DATABASE_URL=sqlite:///./gappy.db
```

### 4. Deploy

Click **Deploy**. Zeabur will build and deploy the service.

### 5. Custom Domain (Optional)

After deployment succeeds:
1. Go to your service
2. Go to **Domain** tab
3. Add your custom domain (e.g. `cosie-gap-analyze.zeabur.app`)

## Troubleshooting

### Build Failed - "Repository not found"

- Make sure the repository is **public**, or
- Connect your GitHub account in Zeabur settings

### Runtime Crash on Startup

- Check the logs for Python import errors
- Most common issues have been fixed in the latest commit

### Health Check Failing

- Ensure the `/health` endpoint returns 200
- The Dockerfile includes a health check

## Post-Deployment

After successful deployment, you can:

1. Upload HKMA regulations via `/upload`
2. Run gap analysis via `/run-analysis`
3. Review findings at `/report`

## Support

For issues, check the Zeabur logs first.