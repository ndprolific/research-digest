"""
Weekly Research Digest
======================
Fetches recent papers on online research methods, public opinion & polling,
and survey methodology from preprint servers and journals, summarises them
with Claude, and emails you a digest.

SETUP (one-time):
  pip install anthropic feedparser requests

TO AUTOMATE (run every Monday morning):
  - Mac/Linux: cron job  →  0 8 * * 1 python /path/to/weekly_digest.py
  - Anywhere:  GitHub Actions (free) — see comment at the bottom
"""

import os
import smtplib
import feedparser
import anthropic
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta, timezone

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
EMAIL_FROM        = os.environ.get("EMAIL_FROM")
EMAIL_TO          = os.environ.get("EMAIL_TO")
EMAIL_PASS        = os.environ.get("EMAIL_PASS")

# ─────────────────────────────────────────────
# SOURCES
# ─────────────────────────────────────────────

ALL_FEEDS = [

    # ── PREPRINT SERVERS ──────────────────────────────────────────────────

    # arXiv: Statistics - Methodology & Applications
    "https://rss.arxiv.org/rss/stat.ME",
    "https://rss.arxiv.org/rss/stat.AP",

    # SocArXiv — social sciences preprints (polling, political science, sociology)
    "https://osf.io/preprints/socarxiv/feed/",

    # PsyArXiv — psychology preprints (attitudes, opinion, behaviour)
    "https://osf.io/preprints/psyarxiv/feed/",

    # ── CORE JOURNALS — PUBLIC OPINION & SURVEY METHODS ──────────────────

    # Public Opinion Quarterly (POQ)
    "https://academic.oup.com/rss/site_6317/advanceAccess_6317.xml",

    # International Journal of Public Opinion Research (IJPOR)
    "https://academic.oup.com/rss/site_6316/advanceAccess_6316.xml",

    # Journal of Survey Statistics and Methodology (JSSAM)
    "https://academic.oup.com/rss/site_6318/advanceAccess_6318.xml",

    # Survey Practice — open access, applied
    "https://www.surveypractice.org/gateway/rss/",

    # ── CORE JOURNALS — METHODS & BEHAVIOUR ──────────────────────────────

    # Behavior Research Methods (Springer)
    "https://link.springer.com/search.rss?facet-journal-id=13428&channel-name=Behavior+Research+Methods",

    # Psychological Methods (APA)
    "https://www.apa.org/pubs/journals/rss/met.xml",

    # ── HIGH-IMPACT GENERAL SCIENCE ───────────────────────────────────────

    # PNAS — Social Science topic feed
    "https://www.pnas.org/action/showFeed?type=topic&feed=rss&jc=pnas&topicCode=100",

    # PNAS — Psychological and Cognitive Sciences topic feed
    "https://www.pnas.org/action/showFeed?type=topic&feed=rss&jc=pnas&topicCode=82",

    # Nature Human Behaviour
    "https://www.nature.com/nathumbehav.rss",

    # ── DIGITAL & COMPUTATIONAL METHODS ──────────────────────────────────

    # Social Science Computer Review (Sage)
    "https://journals.sagepub.com/action/showFeed?ui=0&mi=ehikzz&ai=2b4&jc=sscb&type=etoc&feed=rss",

    # International Journal of Social Research Methodology (Taylor & Francis)
    "https://www.tandfonline.com/action/showFeed?type=etoc&feed=rss&jc=tsrm20",

    # Field Methods (Sage)
    "https://journals.sagepub.com/action/showFeed?ui=0&mi=ehikzz&ai=2b4&jc=fmxa&type=etoc&feed=rss",

    # Political Communication (Taylor & Francis)
    "https://www.tandfonline.com/action/showFeed?type=etoc&feed=rss&jc=upcp20",

    # Journal of Information Technology & Politics (Taylor & Francis)
    "https://www.tandfonline.com/action/showFeed?type=etoc&feed=rss&jc=witp20",

    # ── RESEARCH ORGANISATIONS ────────────────────────────────────────────

    # Pew Research Center
    "https://www.pewresearch.org/feed/",

    # AAPOR
    "https://www.aapor.org/feed/",

]

MAX_PER_FEED  = 10
DAYS_LOOKBACK = 30

# ─────────────────────────────────────────────
# FETCH PAPERS
# ─────────────────────────────────────────────

def fetch_papers(feeds, days=30, limit=10):
    papers = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    for url in feeds:
        try:
            feed = feedparser.parse(url)
            count = 0
            for entry in feed.entries:
                if count >= limit:
                    break
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                if published and published < cutoff:
                    continue
                papers.append({
                    "title":   entry.get("title", "No title").strip(),
                    "summary": entry.get("summary", entry.get("description", ""))[:600],
                    "link":    entry.get("link", ""),
                    "source":  feed.feed.get("title", url),
                    "date":    published.strftime("%d %b %Y") if published else "Unknown",
                })
                count += 1
        except Exception as e:
            print(f"⚠️  Could not fetch {url}: {e}")

    return papers

# ─────────────────────────────────────────────
# SUMMARISE WITH CLAUDE
# ─────────────────────────────────────────────

def summarise_papers(papers, api_key):
    if not papers:
        return "<p>No new papers found this week.</p>"

    client = anthropic.Anthropic(api_key=api_key)

    paper_text = ""
    for i, p in enumerate(papers, 1):
        paper_text += f"\n[{i}] {p['title']}\nSource: {p['source']} | {p['date']}\nURL: {p['link']}\nAbstract: {p['summary']}\n"

    prompt = f"""You are a research curator for a researcher working across the following areas:

- Online research methodologies and the use of crowdsourced or online samples for research
- Data quality in online and crowdsourced samples (e.g. attention, satisficing, bots, fraud)
- Public opinion, polling, and political attitudes
- Survey methodology (design, mode effects, non-response, weighting, questionnaire design)
- Synthetic data generation, validation, and applications (including use cases in market research, social science, and survey research)
- Computational and digital social science methods
- Validity and utility of online samples compared to probability samples

From the {len(papers)} papers below, please:
1. Select the 8-12 most relevant and interesting ones. Cast a wide net — include papers that
   partially touch on these areas or offer methodological insights applicable to them, not just
   papers squarely in the field.
2. Group them into 2-3 thematic sections with clear headings (e.g. "Online Samples & Data Quality",
   "Survey Methods & Design", "Synthetic Data", "Public Opinion & Polling").
3. For each paper write 2-3 sentences: what it does, and why it matters for this researcher's work.
4. Format your response as clean HTML using <h2>, <h3>, <p>, <a> tags. Make titles clickable links.
5. End with a one-paragraph "Editor's Pick" highlighting the single most interesting or useful paper.

Papers:
{paper_text}

Return only the HTML content (no <html> or <body> tags), no markdown.
"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text

# ─────────────────────────────────────────────
# BUILD & SEND EMAIL
# ─────────────────────────────────────────────

def send_email(html_body, from_addr, to_addr, password):
    week = datetime.now().strftime("%d %b %Y")
    subject = f"📚 Weekly Research Digest — {week}"

    full_html = f"""
    <html><body style="font-family: Georgia, serif; max-width: 680px; margin: 0 auto; color: #222;">
      <div style="background:#1a3a5c; color:white; padding:20px 30px; border-radius:6px 6px 0 0;">
        <h1 style="margin:0; font-size:22px;">📚 Weekly Research Digest</h1>
        <p style="margin:4px 0 0; opacity:0.8; font-size:14px;">Week of {week} · Online Methods, Polling & Survey Research</p>
      </div>
      <div style="padding:24px 30px; background:#fafafa; border:1px solid #ddd; border-top:none; border-radius:0 0 6px 6px;">
        {html_body}
      </div>
      <p style="font-size:12px; color:#999; text-align:center; margin-top:16px;">
        Generated by your weekly_digest.py script · <a href="https://console.anthropic.com">Anthropic Console</a>
      </p>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = from_addr
    msg["To"]      = to_addr
    msg.attach(MIMEText(full_html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(from_addr, password)
        server.sendmail(from_addr, to_addr, msg.as_string())

    print(f"✅ Digest sent to {to_addr}")

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("🔍 Fetching papers...")
    papers = fetch_papers(ALL_FEEDS, days=DAYS_LOOKBACK, limit=MAX_PER_FEED)
    print(f"   Found {len(papers)} items")

    print("🤖 Summarising with Claude...")
    digest_html = summarise_papers(papers, ANTHROPIC_API_KEY)

    print("📧 Sending email...")
    send_email(digest_html, EMAIL_FROM, EMAIL_TO, EMAIL_PASS)


# ─────────────────────────────────────────────
# GITHUB ACTIONS AUTOMATION (optional)
# ─────────────────────────────────────────────
#
# Runs every Monday at 8am UTC for free — no computer needed.
#
# 1. Push this file to a GitHub repo
# 2. Create .github/workflows/digest.yml containing:
#
# name: Weekly Digest
# on:
#   schedule:
#     - cron: '0 8 * * 1'
#   workflow_dispatch:
# jobs:
#   run-digest:
#     runs-on: ubuntu-latest
#     steps:
#       - uses: actions/checkout@v3
#       - uses: actions/setup-python@v4
#         with: { python-version: '3.11' }
#       - run: pip install anthropic feedparser requests
#       - run: python weekly_digest.py
#         env:
#           ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
#           EMAIL_FROM:        ${{ secrets.EMAIL_FROM }}
#           EMAIL_TO:          ${{ secrets.EMAIL_TO }}
#           EMAIL_PASS:        ${{ secrets.EMAIL_PASS }}
#
# 3. Add your secrets under repo Settings → Secrets and variables → Actions
