# Installation

This guide walks you from a clean machine to a running ClawBench benchmark. Total time is about 15 minutes the first time (most of it is the container build and the PurelyMail account setup).

## 1. System Requirements

| Item              | Minimum                              | Recommended                     |
| ----------------- | ------------------------------------ | ------------------------------- |
| RAM               | 4 GB free                            | 8 GB+ (batch mode)              |
| Disk              | 5 GB (image + one run)               | 20 GB+                          |
| CPU               | 2 cores                              | 4+ cores                        |
| OS                | Linux x86_64, macOS (Docker Desktop) | Linux x86_64                    |
| Container runtime | Docker 24+ or Podman 4+              | Podman (rootless, no sudo)      |
| Python            | 3.11+                                | 3.12                            |

macOS works via Docker Desktop or `podman machine`. Windows is untested — WSL2 should work but you will need to forward ports 6080 (human mode) and build the image from inside the WSL filesystem.

## 2. Install Docker or Podman

ClawBench auto-detects whichever is available. Podman (rootless) is preferred on Linux because it does not require sudo.

### Linux — Podman (recommended)

```bash
# Debian/Ubuntu
sudo apt-get install -y podman slirp4netns fuse-overlayfs

# Fedora
sudo dnf install -y podman

# Arch
sudo pacman -S podman slirp4netns fuse-overlayfs
```

### Linux — Docker

```bash
# Debian/Ubuntu
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"
# log out and back in so the group change takes effect
```

### macOS

```bash
brew install --cask docker           # Docker Desktop
# or
brew install podman && podman machine init && podman machine start
```

## 3. Install `uv`

ClawBench uses [uv](https://docs.astral.sh/uv/) to manage Python dependencies. No venv fiddling required.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 4. Create a PurelyMail Account

ClawBench provisions a fresh disposable email for **every run** (and deletes it afterward). This requires a [PurelyMail](https://purelymail.com/) account with a domain you control.

1. Sign up at <https://purelymail.com/> (paid — roughly $10/year for unlimited aliases).
2. **Add and verify a domain** you own in the PurelyMail dashboard. Any cheap `.xyz` or `.top` domain from a registrar works; you just need to set the MX records PurelyMail shows you.
3. Go to **Account → API Access** and generate an API key.
4. Copy the key into `.env` (see step 7 below).

If you don't want to provision real emails, you can still use **human mode** for debugging — it does not hit the PurelyMail API. But agent mode always requires valid PurelyMail credentials.

## 5. Get a Model API Key

Pick one provider to start. OpenRouter has a free tier and covers most open-weight models without provider-specific setup.

| Provider    | Portal                                                          | `api_type` to use        | Notes                                        |
| ----------- | --------------------------------------------------------------- | ------------------------ | -------------------------------------------- |
| OpenRouter  | <https://openrouter.ai/keys>                                    | `openai-completions`     | Unified gateway; free tier for many models   |
| Anthropic   | <https://console.anthropic.com/settings/keys>                   | `anthropic-messages`     | Claude models                                |
| OpenAI      | <https://platform.openai.com/api-keys>                          | `openai-responses`       | GPT models                                   |
| Google      | <https://aistudio.google.com/apikey>                            | `google-generative-ai`   | Gemini models                                |

You will paste the key into `models/models.yaml` in step 8.

## 6. Clone ClawBench

```bash
git clone https://github.com/reacher-z/clawbench.git
cd clawbench
```

## 7. Configure `.env`

```bash
cp .env.example .env
$EDITOR .env
```

Fill in:

```
PURELY_MAIL_API_KEY="<your 40+ char key>"
PURELY_MAIL_DOMAIN="clawbench.example.com"
```

HuggingFace upload variables are optional — leave them commented unless you want runs auto-uploaded to a dataset repo.

## 8. Configure at Least One Model

```bash
cp models/models.example.yaml models/models.yaml
$EDITOR models/models.yaml
```

Replace the placeholder API key in the `qwen3.5-397b-a17b` block, or uncomment one of the Anthropic / OpenAI / Gemini blocks and fill it in. See [`models/model.schema.json`](../models/model.schema.json) for the full field reference.

## 9. Build the Container Image

The test driver will build the image for you on the first run, but you can also build it manually:

```bash
# Docker
docker build -t clawbench .

# Podman (rootless, no sudo)
podman build -t clawbench .

# Force a specific engine
CONTAINER_ENGINE=podman docker build -t clawbench .
```

Expected time: 3–5 minutes (cold); subsequent builds use the layer cache. Final image size: ~3 GB.

## 10. Verify

```bash
./run.sh
```

You should see the interactive TUI with four options: Single run, Batch run, Human mode, Configure models. From there, pick **Human mode** and any test case (e.g., `001-daily-life-food-uber-eats`) — this exercises the full pipeline without burning API credits and opens a noVNC URL you can use to drive Chrome in your browser.

If something fails, see [`troubleshooting.md`](troubleshooting.md).

## Ports

| Port | Service         | Purpose                                          |
| ---- | --------------- | ------------------------------------------------ |
| 7878 | FastAPI server  | Action/screenshot API, session control (container-internal) |
| 9223 | CDP via `socat` | Playwright/DevTools connection to Chromium (container-external) |
| 6080 | noVNC           | Human mode browser UI (host `localhost:6080`)    |
