# Growth checklist (manual action items)

Things the `growth-kit-v1` branch changed in code, paired with the
real-world actions they depend on. Code alone does nothing here - these
are the human steps.

## 1. Hero GIF

- [x] Script written: `scripts/record-hero-gif.sh`
- [ ] Install tools: `brew install ffmpeg gifski`
- [ ] Run a full agent on a visually interesting case (suggested:
      `test-cases/001-daily-life-food-uber-eats` or a calendar-booking
      one - end-to-end flows film better than data-entry ones)
- [ ] `./scripts/record-hero-gif.sh <case-dir> claude-opus-4-6`
- [ ] Review `static/hero.gif`. If the 15s window doesn't tell the
      story, re-run with `FROM=120 TO=135 ./scripts/record-hero-gif.sh ...`
- [ ] Embed in README above the subtitle: `<img src="static/hero.gif" alt="ClawBench agent demo" width="720">`
- [ ] Commit `static/hero.gif` + README change

## 2. Discord server

- [ ] Create Discord server "ClawBench" (see `docs/launch-playbook.md`
      for the channel list)
- [ ] Generate invite link
- [ ] Replace `https://discord.gg/clawbench` placeholder in both
      READMEs (`README.md` and `README.zh-CN.md`)
- [ ] Pin welcome message

The badge is live in both READMEs already - it will 404 until the
server exists. Worth leaving broken for a few days as motivation.

## 3. Codespaces

- [x] `.devcontainer/devcontainer.json` committed
- [ ] Open https://codespaces.new/reacher-z/ClawBench?quickstart=1
      yourself first, verify the `clawbench` command works inside the
      Codespace, take a screenshot for the launch post
- [ ] If Docker-in-Docker fails on the default 4GB machine, switch the
      badge URL to request a larger machine: `...&machine=standardLinux32gb`

## 4. HF Space leaderboard

- [x] Scaffold in `leaderboard/`
- [ ] `huggingface-cli login` with your HF account
- [ ] `huggingface-cli repo create clawbench-leaderboard --type space --space_sdk gradio`
- [ ] Copy CSVs: `cp -r eval-results leaderboard/`
- [ ] First push (see `leaderboard/README.md` for the git remote setup)
- [ ] Verify the Space renders at https://huggingface.co/spaces/<user>/clawbench-leaderboard
- [ ] Add a "Leaderboard" badge to both READMEs pointing at the Space URL

## 5. Launch

- [ ] Read `docs/launch-playbook.md`
- [ ] Pick a Tuesday/Wednesday
- [ ] Execute
