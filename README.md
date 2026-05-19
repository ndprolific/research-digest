# 📚 Weekly Research Digest

A Python script that automatically fetches recent academic papers across online research methods, survey methodology, public opinion, and synthetic data — summarises them with Claude AI — and emails you a weekly digest every Monday morning.

Built and maintained by [@a-j-gordon](https://github.com/a-j-gordon).

---

## What it does

1. **Fetches** recent papers from 20+ sources including arXiv, SocArXiv, PsyArXiv, Public Opinion Quarterly, JSSAM, Behavior Research Methods, PNAS, Nature Human Behaviour, Pew Research, and more
2. **Summarises** them using Claude AI, filtering for relevance to your research areas and grouping by theme
3. **Emails** you a nicely formatted digest every Monday at 9am UK time

---

## Setup (one-time, ~15 minutes)

### 1. Get an Anthropic API key
- Go to [console.anthropic.com](https://console.anthropic.com)
- Sign up or log in
- Go to **API Keys** → **Create Key**
- Copy it somewhere safe

### 2. Get a Gmail App Password
You need this so the script can send email on your behalf. It is separate from your normal Gmail password and can be revoked at any time.

- Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
- You may need to enable 2-factor authentication first if you haven't already
- Create a new app password — call it something like "research digest"
- Copy the 16-character code it gives you

### 3. Fork this repo
- Click **Fork** at the top right of this page
- This creates your own copy of the repo under your GitHub account

### 4. Add your secrets
In your forked repo, go to **Settings** → **Secrets and variables** → **Actions** → **New repository secret** and add these four secrets:

| Secret name | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `EMAIL_FROM` | Your Gmail address |
| `EMAIL_TO` | The address to receive the digest (can be the same) |
| `EMAIL_PASS` | Your 16-character Gmail App Password |

> ⚠️ Never paste these values into the script itself — always use GitHub secrets.

### 5. Enable the workflow
- Go to the **Actions** tab in your repo
- Click **Weekly Digest**
- Click **Enable workflow** if prompted

### 6. Test it
- In the **Actions** tab, click **Weekly Digest** → **Run workflow** → **Run workflow**
- It should go green within a minute and you'll receive an email

From now on it runs automatically every Monday at 9am UK time (8am UTC). You don't need to do anything else.

---

## Customising topics

The research areas Claude looks for are defined in the prompt inside `summarise_papers()` in `weekly_digest.py`. Edit that section to add or change topics.

The list of feeds is in the `ALL_FEEDS` list near the top of the script. Add or remove RSS feed URLs there to change which journals and preprint servers are checked.

---

## Costs

- **GitHub Actions**: free (well within the free tier)
- **Anthropic API**: roughly $0.01–0.03 per run depending on how many papers are fetched

---

## Requirements

```
anthropic
feedparser
requests
```

Install with: `pip install anthropic feedparser requests`
