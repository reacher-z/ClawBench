# Launch Playbook

How to execute a coordinated push the next time there's something worth
launching (new eval results, major feature, or just the v1 tag). This doc
exists because the star-growth research (see `docs/star-strategy.md`) showed
that 14/20 high-star dev-tool repos had one-day star spikes of 300+, and
those spikes trace back to coordinated launches - not to organic growth.

Treat this as a checklist to copy-paste from, not prose to read.

---

## T-7 days: prep

- [ ] Pick launch target (usually Tue or Wed, 8am PT - peak HN front-page window)
- [ ] Pin release tag; freeze feature merges
- [ ] Record hero GIF: `./scripts/record-hero-gif.sh <case> <model>` - must be under 6 MB
- [ ] Refresh leaderboard: run `clawbench batch` against latest frontier models, commit CSVs
- [ ] Update `leaderboard/` HF Space (see `leaderboard/README.md`)
- [ ] Draft HN post (below) - circulate to 2-3 friends for feedback
- [ ] Draft X thread (below) - pre-record failure clips (3-5, 10-15s each)
- [ ] Line up 5-10 people who will upvote in the first hour (no voting rings - just people who actually care)
- [ ] Newsletter pitches sent to TLDR AI, Ben's Bites, The Rundown 3-5 days before launch

## T-0: launch day

- [ ] 0745 PT: do one final check - build passes, `claw-bench doctor` green, Space loads
- [ ] 0800 PT: submit HN post - title under 80 chars, no clickbait prefixes
- [ ] 0805 PT: post X thread, pin to profile
- [ ] 0810 PT: post to r/LocalLLaMA and r/MachineLearning (mod-allowing)
- [ ] 0815 PT: cross-post to Hacker News Show HN via Discord/friends network
- [ ] First hour: reply to every HN comment within 5 min. This is the single biggest signal HN uses to decide front-page placement.
- [ ] Watch GitHub traffic tab - spike should hit ~1-2h after HN post

## T+1 to T+7: follow-through

- [ ] Reply to every issue opened within 24h
- [ ] Merge easy PRs fast (or comment with clear path forward)
- [ ] Post a "thanks for the response" summary on X showing star growth + notable PRs
- [ ] Save one or two particularly funny agent failures as short video clips for future retweets

---

## HN post draft

**Title:** Show HN: ClawBench – 153 everyday web tasks even GPT-5 fails

**Body:**

> We ran GPT-5, Claude Opus 4.6, Gemini, and three others against 153
> real-world web tasks - ordering food on Uber Eats, booking on Calendly,
> filling out Indeed applications, etc. The best one passed 62%. Several
> frontier models sit under 40%.
>
> ClawBench is open source. Everything runs in a container with Chrome +
> a recorded extension - you point it at a model and it gives you back a
> CSV of pass/fail per task with justifications.
>
> Why 153? We wanted coverage without death-by-variants: 15 categories
> (food, housing, jobs, email, calendars, health, pets, travel, ...) x
> ~10 tasks each. Live websites, not static snapshots. Tasks have real
> time limits.
>
> The failure modes are the fun part. Most agents die on:
> - CAPTCHAs they can't solve (especially claw-machine style ones)
> - multi-step flows where they lose track at step 4+
> - site-specific quirks (Uber's PerimeterX page, Indeed's cookie wall)
>
> Leaderboard: <HF Space URL>
> Repo: https://github.com/reacher-z/ClawBench
> Install: `pip install claw-bench` (or: open in Codespaces, one click)
>
> Happy to answer questions about the methodology, the scoring rubric,
> or why your favorite model isn't on the board yet (usually: we're
> still running it).

**Rationale:**
- Front-loads the number (153) and the punchline (best passes 62%)
- Ends with install instructions - people should be able to try it in the
  time it takes to read the comments
- Don't include GIF in HN body (HN doesn't render images); link to the
  HF Space which has the leaderboard + screenshots

---

## X failure-reel thread

Goal: one killer clip per tweet, 5 tweets max. People retweet funny
failures, not pass rates.

**Tweet 1 (hook):**
> I gave GPT-5, Claude Opus, and 4 other frontier models 153 real web
> chores. 
>
> Best one finished 62%. The rest? Chaos.
>
> [15s clip: agent repeatedly failing Uber Eats CAPTCHA]
>
> Open-source leaderboard below ↓

**Tweet 2:**
> The one that broke me: agent spent 4 minutes trying to solve a
> claw-machine CAPTCHA on Uber Eats. Got 11 of 12 wrong.
> [clip]

**Tweet 3:**
> Calendly booking looks trivial until an agent tries it. This one
> scheduled a meeting for 2027.
> [clip]

**Tweet 4:**
> Email is also not solved. Watch this agent send the draft to itself
> twice before realizing the "To" field was empty.
> [clip]

**Tweet 5 (CTA):**
> 153 tasks. 15 categories. Every pass/fail justified.
>
> Try it: pip install claw-bench
> Leaderboard: <link>
> Repo: <link>
>
> If you run a frontier model we haven't tested, open a PR with your
> CSV - we'll add it.

**Rationale:** the first clip is the most important asset you will ship
this year. Spend the time picking it.

---

## Newsletter pitches

Send 3-5 days before launch. Short. Include a hook + one metric + a link.

**TLDR AI** (tldr.tech/ai - Dan Ni, ~500K subscribers):
> Subject: ClawBench: frontier models fail 40% of everyday web tasks
>
> Hi Dan,
>
> Launching Tuesday: a 153-task benchmark for browser agents where even
> the best frontier model only passes 62%. Open source, `pip install
> claw-bench`, live leaderboard on HF Spaces.
>
> The fun part is the failure reel - CAPTCHAs, 4-step flows, and
> Perimeter X walls that break every model we tested. Happy to share an
> early look if useful.
>
> Repo: https://github.com/reacher-z/ClawBench

**Ben's Bites** (bensbites.com):
Same pitch, emphasize the "watch agents fail" angle - BB readers like
specific examples over abstract framings.

**The Rundown** (therundown.ai):
Lead with the leaderboard screenshot.

**Bonus targets:** Last Week in AI, Import AI (Jack Clark), The Neuron,
AI Breakfast, Etude AI. All take submissions via their contact form.

---

## Discord server setup (one-time)

- [ ] Create server at discord.com/developers, pick name "ClawBench"
- [ ] Channels: `#general`, `#help`, `#results`, `#contribute`, `#announcements`
- [ ] Turn on Community features (rules channel, announcement channel)
- [ ] Generate vanity invite: `discord.gg/clawbench` (requires boost level 3 - can start with regular invite and update README badge URL later)
- [ ] Update `discord.gg/clawbench` in both READMEs once the invite is real
- [ ] Pin a welcome message with: repo link, install command, leaderboard link, where to report bugs

The Discord badge in both READMEs currently points at `discord.gg/clawbench`
which is a placeholder. Fix before launch.

---

## Post-launch: what to measure

- Stars gained in first 48h (target: 500+)
- HN front-page time (target: 4+ hours on front page)
- HF Space unique visitors (target: 2000+ on launch day)
- PRs opened by external contributors in first week (target: 3+)
- Newsletter mentions (target: 2+)

If stars are below 200 at T+48h, the launch underperformed - usually
means HN title wasn't sharp enough or the GIF didn't work. Log lessons
in `docs/launches/YYYY-MM-DD.md` for next time.
