# Open WebUI Setup

Complete configuration for running Open WebUI with pipelines, Ollama, and nginx HTTPS proxy on macOS.

## Prerequisites

- macOS (tested on M4 MacBook Pro)
- Docker Desktop
- Homebrew
- Ollama

## Quick Start

1. **Install dependencies**
   ```bash
   # Install Homebrew if not present
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   
   # Install nginx (NOT Caddy - Caddy has SSL issues)
   brew install nginx
   ```

2. **Set up API keys**
   ```bash
   mkdir -p ~/.api_keys
   cp api_keys.template ~/.api_keys/api_keys
   # Edit ~/.api_keys/api_keys and add your keys
   nano ~/.api_keys/api_keys
   ```

3. **Generate SSL certificate**
   ```bash
   mkdir -p ~/.ssl
   openssl req -x509 -newkey rsa:4096 -keyout ~/.ssl/key.pem -out ~/.ssl/cert.pem -days 365 -nodes -subj "/CN=macbook-pro.local"
   ```

4. **Configure nginx**
   ```bash
   cp nginx.conf /opt/homebrew/etc/nginx/nginx.conf
   ```

5. **Clone pipelines**
   ```bash
   git clone https://github.com/DonUsingGit/openwebui-pipelines.git ~/openwebui-pipelines
   ```

6. **Start services**
   ```bash
   # Start pipelines
   chmod +x pipelines-start.sh
   ./pipelines-start.sh
   
   # Start Open WebUI
   chmod +x open-webui-start.sh
   ./open-webui-start.sh
   
   # Start nginx for HTTPS
   brew services start nginx
   ```

7. **Set up auto-start**
   - Add Docker Desktop to Login Items
   - Add Ollama to Login Items
   - nginx auto-starts via brew services

## URLs

| URL | Use Case |
|-----|----------|
| https://macbook-pro.local | HTTPS with mic access (any device on network) |
| http://localhost:3000 | Local access with mic (Mac only) |
| http://macbook-pro.local:3000 | Network access without mic |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    macbook-pro.local                     │
├─────────────────────────────────────────────────────────┤
│  nginx (:443) ──HTTPS──> Open WebUI (:3000)             │
│                              │                           │
│                    ┌─────────┴─────────┐                │
│                    ▼                   ▼                │
│            Pipelines (:9099)     Ollama (:11434)        │
│            - Claude              - Local models         │
│            - ChatGPT             - gpt-oss:20b          │
│            - Gemini              - llama3.2             │
│            - Grok                - etc.                 │
│            - BodE                                       │
│            - DeepSeek                                   │
└─────────────────────────────────────────────────────────┘
```

## Text-to-Speech

Free local TTS configured with:
- **Engine**: Transformers (Local)
- **Voice**: cmu_us_clb_arctic
- **Cost**: Free

Configure in Admin Settings > Audio.

## Files

| File | Purpose |
|------|---------|
| open-webui-start.sh | Recreates Open WebUI container |
| pipelines-start.sh | Recreates Pipelines container |
| nginx.conf | nginx HTTPS proxy config |
| api_keys.template | Template for API keys |

## IMPORTANT: Why nginx instead of Caddy

Caddy had persistent SSL/TLS errors on this Mac:
- `error:1404B438:SSL routines:ST_CONNECT:tlsv1 alert internal error`
- Failed to install root certificate
- Multiple process conflicts

nginx works reliably with self-signed certs.

## Troubleshooting

### HTTPS shows 500 Internal Error
This is Open WebUI redirecting unauthenticated users. Solutions:
1. Accept the self-signed certificate warning first
2. Log in via https://macbook-pro.local/auth
3. The session cookie must be set over HTTPS

### Mic not working
Use https://macbook-pro.local (requires nginx running)

### Regenerate SSL certificate
```bash
openssl req -x509 -newkey rsa:4096 -keyout ~/.ssl/key.pem -out ~/.ssl/cert.pem -days 365 -nodes -subj "/CN=macbook-pro.local"
brew services restart nginx
```

### Linux network access
Add to /etc/hosts on Linux machine:
```
192.168.1.233 macbook-pro.local
```

## Related Repos

- Pipelines: https://github.com/DonUsingGit/openwebui-pipelines
