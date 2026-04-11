# Synthetic User Profile

Every ClawBench run gets its own synthetic identity: a dummy user (Alex Green), a disposable email address, and a resume PDF. The agent is instructed to read these files whenever it needs personal details for form filling, sign-up, checkout, job applications, or similar.

The goal is to let agents exercise real sign-up and form flows **without** using real human data and without polluting real accounts across runs.

## `/my-info/` layout

Each container has a `/my-info/` directory mounted read-only with:

```
/my-info/
  alex_green_personal_info.json    # Full profile (contact, address, education, work, etc.)
  email_credentials.json           # Fresh disposable email + password + login URL
  alex_green_resume.pdf            # Resume with the fresh email injected into the header
  <extra_info files>               # Any files declared in task.json's extra_info array
```

The agent instruction prompt explicitly lists the three core files so the agent knows they exist without needing to `ls` first; `ls` is still available for discovering `extra_info` files.

## Alex Green

The base profile lives at [`shared/alex_green_personal_info.json`](../shared/alex_green_personal_info.json) and covers contact info, address, education, work history, and more. The `online_accounts` section is **stripped** before the file is mounted into the container, so the agent cannot reuse pre-existing account credentials — every run starts from zero.

The `contact.email` field is overwritten per run with the freshly provisioned disposable email.

## Disposable email lifecycle

For each run, the test driver calls the [PurelyMail API](https://news.purelymail.com/api/index.html#/User) to create and later delete a single-use email account. Details:

| Aspect         | Value                                                                                       |
| -------------- | ------------------------------------------------------------------------------------------- |
| Username       | `cb<12-hex-chars>` (e.g., `cb92784dc43fb0`)                                                 |
| Domain         | `PURELY_MAIL_DOMAIN` from `.env`                                                            |
| Password       | `secrets.token_urlsafe(16)` — 22 characters                                                 |
| Lifetime       | Created just before the container starts; deleted after the container exits                |
| Cleanup        | Guaranteed via `try/finally` in `test-driver/run.py`, even if the test case fails           |

The email and password land in `/my-info/email_credentials.json` alongside the login URL (the PurelyMail webmail) so the agent can open the inbox to receive verification codes.

The email is also injected into both `alex_green_personal_info.json` (`contact.email`) and `alex_green_resume.pdf` (header) so every place the agent might look for "my email" returns the same value.

## Resume PDF

The resume is generated from [`test-driver/resume_template.json`](../test-driver/resume_template.json) by [`test-driver/generate_resume_pdf.py`](../test-driver/generate_resume_pdf.py) using `fpdf2`. The generator reads the template, injects the fresh disposable email into the header, and writes `alex_green_resume.pdf`.

To preview a resume locally:

```bash
cd test-driver && uv run generate_resume_pdf.py [output.pdf]
```

## Where to add per-test-case files

If your test case needs something specific in `/my-info/` (e.g., a project brief, a spreadsheet the agent must upload), list it in the test case's `task.json` under `extra_info`:

```json
{
  "extra_info": [
    {
      "path": "extra_info/project_brief.pdf",
      "description": "Project brief for the consulting task — the agent should reference this when filling in the inquiry form."
    }
  ]
}
```

The file must exist in the test case directory. The driver copies it into the temporary `/my-info/` directory and injects the description into the agent prompt as `project_brief.pdf: <description>`.

See [`../CONTRIBUTING.md`](../CONTRIBUTING.md) for the full test-case authoring workflow.

## Source templates

| File                                                | Role                                          |
| --------------------------------------------------- | --------------------------------------------- |
| [`shared/alex_green_personal_info.json`](../shared/alex_green_personal_info.json) | Base profile for Alex Green                   |
| [`test-driver/resume_template.json`](../test-driver/resume_template.json) | PDF resume template                           |
| `test-driver/generate_resume_pdf.py`                | PDF generator (fpdf2)                         |
| `test-driver/run.py`                                | Runtime assembly of `/my-info/`               |
