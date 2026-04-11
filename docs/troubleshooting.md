# Troubleshooting

If a run is failing, start here. Each section follows **Symptom → Cause → Fix**. For anything not covered, open an issue with the relevant log files attached.

## 1. Chrome CDP not ready after 30 seconds

**Symptom.** Container exits quickly. `interception.json` reports `"stop_reason": "chrome_cdp_timeout"`. Nothing in `actions.jsonl`.

**Cause.** Chromium failed to start before the entrypoint's health-check loop gave up. Usually: OOM, missing GPU libraries, an unwritable profile directory, or a stealth-flag incompatibility with the installed Chrome version.

**Fix.**

- Check container logs: `docker logs <container>` (the name is printed by the driver) or `podman logs <container>`.
- Rebuild without the layer cache: `docker build --no-cache -t clawbench .` — catches transient apt mirror issues.
- Confirm you have at least 4 GB of free RAM on the host. Chromium + Xvfb + ffmpeg together need room.
- Verify `libegl1` and `libgbm1` are installed by the Dockerfile (they are required for `--use-gl=angle --use-angle=swiftshader`). If you customized the Dockerfile, don't remove them.
- As a last resort, add `--shell` to enter the container and run `chromium --version && chromium --no-sandbox --headless=new` by hand to see the error.

## 2. Podman rootless build fails on `apt-get install`

**Symptom.** `podman build` errors out during the `apt-get install` step with permission/ownership errors (`chown: invalid user`, `dpkg-statoverride`, or similar).

**Cause.** Rootless Podman uses user namespaces; some APT post-install scripts try to `chown` to users that don't exist inside the namespace.

**Fix.**

- Install `slirp4netns` and `fuse-overlayfs` on the host (see [`installation.md`](installation.md#linux--podman-recommended)).
- On macOS, use `podman machine init && podman machine start` before building.
- Force Docker for the build step: `CONTAINER_ENGINE=docker docker build -t clawbench .` (the runtime image is portable — you can build with Docker and run with Podman).

## 3. PurelyMail API 401 / 403 on email creation

**Symptom.** `test-driver/run.py` exits early with an HTTP 401 or 403 from `inbox.purelymail.com`.

**Cause.** The `PURELY_MAIL_API_KEY` or `PURELY_MAIL_DOMAIN` in `.env` is wrong: the placeholder was never replaced, the key was revoked, or the domain isn't actually added to the PurelyMail account.

**Fix.**

1. Open the PurelyMail dashboard. Confirm the domain shows as active with valid MX records.
2. Go to **Account → API Access**. If the key looks unfamiliar, regenerate it.
3. Update `.env` and run again.
4. Full walkthrough: [`installation.md#4-create-a-purelymail-account`](installation.md#4-create-a-purelymail-account).

## 4. `models/models.yaml` not found

**Symptom.** The TUI or `run.py` errors with "`models/models.yaml` not found" or similar.

**Cause.** You ran the tool before copying the example.

**Fix.**

```bash
cp models/models.example.yaml models/models.yaml
$EDITOR models/models.yaml
```

Replace the placeholder `api_key` with your real key. See [`installation.md#8-configure-at-least-one-model`](installation.md#8-configure-at-least-one-model).

## 5. OpenClaw gateway dies on startup

**Symptom.** Container exits with `"stop_reason": "gateway_failed"`. `data/gateway.log` has an error.

**Cause.** Usually one of:

- Malformed `~/.openclaw/openclaw.json` (rare — only if you hand-edited it or the setup script got a bad env var).
- Invalid API key (wrong format for the `api_type`).
- Unreachable `base_url` (wrong URL, or the provider is down).
- A provider regression or an OpenClaw upstream bump broke the pinned version.

**Fix.**

1. `cat` the gateway log from the output directory: `cat test-output/.../data/gateway.log`.
2. Verify `base_url` and `api_type` match the provider's documented format (see [`installation.md#5-get-a-model-api-key`](installation.md#5-get-a-model-api-key)).
3. Verify key format: Anthropic = `sk-ant-...`, OpenAI = `sk-...`, Google = `AIza...`, OpenRouter = `sk-or-v1-...`.
4. Try the same `base_url` and key from a `curl` probe on the host to confirm network reachability.

## 6. Chrome extension fails to load

**Symptom.** `actions.jsonl` is empty even though Chromium is running. No DOM events being captured.

**Cause.** Chromium didn't pick up the `--load-extension` path, or the extension manifest failed to parse, or the profile directory isn't writable.

**Fix.**

- Check the Chromium logs inside the container: `docker exec <container> cat /tmp/chromium.log` (while the container is still running).
- Validate the manifest: `jq . chrome-extension/manifest.json`.
- Confirm `chrome-extension/` was copied into the image — `docker run --rm clawbench ls /app/chrome-extension` should list `manifest.json`, `background.js`, `content.js`, `stealth.js`.
- If you customized the Dockerfile, make sure the `COPY chrome-extension ...` step is still present.

## 7. OpenClaw browser tool cannot connect to Chromium

**Symptom.** `agent-messages.jsonl` shows the agent trying to take actions but the browser tool errors out, or no browser tool calls appear at all. `actions.jsonl` is empty despite the agent reasoning correctly.

**Cause.** The upstream OpenClaw bug tracked as [openclaw/openclaw#47879](https://github.com/openclaw/openclaw/issues/47879): the `existing-session` driver hardcodes `--autoConnect` instead of honoring the `cdpUrl` from the browser profile config. ClawBench works around this by `sed`-patching the OpenClaw dist files in the Dockerfile. If someone bumped the pinned version without re-applying the patch — or if the patch target path changed upstream — the workaround no longer runs and the browser tool can't reach Chromium on port 9222.

**Fix.**

1. Confirm the patch is still applied inside the image:

   ```bash
   docker run --rm clawbench grep -r "browserUrl.*127.0.0.1:9222" /usr/local/lib/node_modules/openclaw/dist || echo "PATCH MISSING"
   ```

2. If the patch is missing, check the Dockerfile for the `sed` line that replaces `"--autoConnect"` with `"--browserUrl","http://127.0.0.1:9222"`. Confirm `openclaw` is pinned to `v2026.3.13`.
3. Full background and the sed command are in [`openclaw_integration.md#the-v2026313-browser-patch`](openclaw_integration.md#the-v2026313-browser-patch).

## 8. Agent produces zero actions (`agent_idle`)

**Symptom.** `interception.json` reports `"stop_reason": "agent_idle"`. `actions.jsonl` is empty or nearly empty. `agent-messages.jsonl` shows the model returning little or no output.

**Cause.** Common reasons:

- Content filter on the provider side rejected the system/user prompt.
- Rate-limit or quota error — the model call 429'd.
- Model returned empty `thinking`/`text` with no tool calls (some models do this when `thinking_level` is too high for a short task).
- The browser tool is broken (see issue #7 above).

**Fix.**

1. Inspect `data/agent-messages.jsonl` — look for HTTP errors, refusals, or empty messages.
2. Check the gateway log: `cat data/gateway.log`.
3. Lower `thinking_level` in `models/models.yaml` (e.g., `medium` → `low`).
4. Check your provider's dashboard for rate-limit events.
5. Try a different model to rule out provider-specific issues.

## 9. HuggingFace upload fails

**Symptom.** Run finishes successfully but the upload step errors. Log shows a `huggingface_hub` traceback.

**Cause.** Usually:

- `HF_TOKEN` is invalid or missing the `write` scope.
- `HF_REPO_ID` points to a repo that doesn't exist.
- `huggingface_hub` isn't installed (shouldn't happen with `uv`, but possible on heavily customized setups).

**Fix.**

1. Regenerate the token at <https://huggingface.co/settings/tokens> with **Write** scope.
2. Create the dataset repo at <https://huggingface.co/new-dataset> before running.
3. Pass `--no-upload` to the test driver to skip upload for one-off runs.
4. Or remove `HF_TOKEN` / `HF_REPO_ID` from `.env` to disable uploads globally.

## 10. Podman rootless cannot bind port 6080 (human mode)

**Symptom.** Human mode fails to start with a "permission denied" on port 6080, or the noVNC URL never becomes reachable.

**Cause.** Rootless Podman can't bind unprivileged ports below the distro's configured threshold.

**Fix.**

- Lower the unprivileged port range:
  ```bash
  sudo sysctl net.ipv4.ip_unprivileged_port_start=80
  ```
- Or remap 6080 to an allowed port when running the container (edit `test-driver/run.py`'s `docker_run_human` to use a different host port).
- On macOS, `podman machine` handles port forwarding differently — restart the machine if host-side binding fails.

## Still stuck?

- Read the gateway log: `test-output/.../data/gateway.log`
- Read the agent log (if present): `test-output/.../data/agent.log`
- Read the stop reason: `cat test-output/.../data/interception.json`
- Read the full architecture doc for context on what each component does: [`architecture.md`](architecture.md)
- Open an issue with: the command you ran, the container engine + version, the contents of `interception.json` and `run-meta.json`, and the last 100 lines of the relevant log.
