# AWS EC2 Setup

This folder contains a production starter for running VU-Chatbot on an AWS EC2 Linux instance.

## Files
- `ec2-user-data.sh`: bootstrap script for a fresh EC2 instance (installs Docker, git, compose plugin)
- `setup-instance.sh`: clones/updates repo and starts services with Docker Compose
- `docker-compose.ec2.yml`: production compose file
- `.env.ec2.example`: environment template

## 1) Launch EC2
- Use Amazon Linux 2023 (x86_64)
- Open inbound rules:
  - TCP 22 from your IP
  - TCP 80 from 0.0.0.0/0
  - TCP 443 from 0.0.0.0/0 (if using TLS)
  - Optional: TCP 8000 from your IP for direct app debugging

## 2) Bootstrap instance
Option A: Paste `ec2-user-data.sh` into EC2 User Data at launch.

Option B: Run manually after SSH:
```bash
chmod +x deploy/aws/ec2-user-data.sh
./deploy/aws/ec2-user-data.sh
exit
```
Then SSH again (to apply Docker group).

## 3) Deploy app
```bash
chmod +x deploy/aws/setup-instance.sh
./deploy/aws/setup-instance.sh <your_repo_url>
```

On first run, the script creates `.env.ec2` and exits so you can add secrets.

## 4) Configure environment
```bash
nano /opt/vu-chatbot/deploy/aws/.env.ec2
```
Set all required values (AWS, JWT, IBM keys), then run setup again:
```bash
/opt/vu-chatbot/deploy/aws/setup-instance.sh <your_repo_url>
```

## 5) Verify
```bash
docker compose -f /opt/vu-chatbot/deploy/aws/docker-compose.ec2.yml ps
curl http://localhost:8000/health
```

If Nginx is active, test:
```bash
curl http://localhost/health
```

## Optional TLS
Place certificate files under `/opt/vu-chatbot/ssl` and adjust `nginx.conf` paths if needed.
