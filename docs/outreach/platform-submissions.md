# Academic / research platform submissions

## Key finding: Papers with Code is DEAD

PwC shut down 24-25 July 2025. All paperswithcode.com URLs now redirect to huggingface.co/papers/trending. Benchmark/task/paper submission is no longer possible. Use HF Community Evals instead.

## 1. Hugging Face Daily Papers

URL: https://huggingface.co/papers/2604.08523

Steps:
1. Log in to HF.
2. Visit https://huggingface.co/papers → search `2604.08523`. If not indexed, click "Index this paper".
3. On the paper page: "Claim authorship" (needs matching affiliation email).
4. For Daily Papers (AK-curated): Submit button on https://huggingface.co/papers requires at least one already-indexed paper to your HF account.
5. Link the ClawBench Space/dataset from Space settings → "Paper".

Timing: indexing <1min; Daily Papers pickup same-day if submitted morning PT and AK picks it.

## 2. HF Community Evals (de-facto PwC replacement)

URL: https://github.com/huggingface/community-evals + https://huggingface.co/docs/hub/eval-results

Steps:
1. Create ClawBench dataset repo on HF.
2. Follow community-evals README to register leaderboard schema.
3. For each of 7 evaluated models: PR on that model's repo adding `.eval_results/clawbench.yaml` with scores. Community-provided PRs appear immediately; no model-author approval needed.

## 3. HF Collections to ask to be added to

| Collection | Owner | URL |
|---|---|---|
| Awesome Computer Use Agents | ranpox | https://huggingface.co/collections/ranpox/awesome-computer-use-agents-675272db99b478caa1034283 |
| GUI Agents | m-ric (HF staff) | https://huggingface.co/collections/m-ric/gui-agents-67cc9f6ea029f09af73caff8 |
| Agent Benchmarks | akseljoonas | https://huggingface.co/collections/akseljoonas/agent-benchmarks |
| Web Agents with World Models | LangAGI-Lab | https://huggingface.co/collections/LangAGI-Lab/web-agents-with-world-models-66d2cecfc79195150389693d |
| Screen Agents | shivramanna | https://huggingface.co/collections/shivramanna/screen-agents-6720042f5a5841b762cb48a6 |

## 4. OpenCompass / HELM / BIG-Bench / LMArena

- **OpenCompass**: PR against github.com/open-compass/opencompass, add dataset module under `opencompass/datasets/`. Also email `opencompass@pjlab.org.cn`. Chinese audience skew, active merging.
- **HELM**: PR against github.com/stanford-crfm/helm following `docs/adding_new_scenarios.md`. Stanford CRFM merges.
- **BIG-Bench**: Dormant post-BBH. Low priority.
- **LMArena**: Does not accept external benchmarks. Not applicable.

## 5. Auto-indexed platforms (no action needed)

- **alphaXiv** — auto-mirrors arXiv. Replace `arxiv` → `alphaxiv` in URL. Optional: seed one substantive comment on the paper page.
- **Scholar Inbox** — auto-pulls arXiv daily.
- **Elicit** — indexes arXiv within ~24h.
- **ResearchRabbit** — pulls from Semantic Scholar.
- **arXiv Sanity Lite** — auto-pulls arXiv cs.* daily.

## 6. Semantic Scholar — claim author page

Auto-ingests arXiv within 24–72h. Claim flow:
1. Search your name → open author profile.
2. Click "Claim Author Page".
3. Submit email (preferably matching one referenced in papers) + ORCID.
4. Moderated, 1–5 day approval.

URL: https://www.semanticscholar.org/faq#claim-author-page

## 7. Conference submission windows (author awareness)

- **NeurIPS 2026 Evaluations & Datasets Track** (renamed from D&B)
  - Abstract: May 4, 2026 AoE
  - Full paper: May 6, 2026 AoE
  - URL: https://neurips.cc/Conferences/2026/CallForEvaluationsDatasets
  - Three weeks away — actionable.
- **ICLR 2027 workshops** — CFP typically November 2026. Watch for Lifelong Agents, MemAgents, Agents-in-the-Wild tracks.
- **ACL 2026 GEM Workshop** — deadline passed.
- **KDD 2026 D&B Track** — https://kdd2026.kdd.org/datasets-and-benchmarks-track-call-for-papers/

## Priority order

1. HF paper page claim + HF Daily Papers submission + Collection asks
2. alphaXiv discussion seed
3. Semantic Scholar author claim (one-time, compounds citations)
4. HF Community Evals PRs
5. NeurIPS 2026 E&D submission (May 4-6 deadline, actionable now)
6. OpenCompass dataset PR (high-signal for Chinese audience)
7. HELM scenario PR (long-tail credibility)
