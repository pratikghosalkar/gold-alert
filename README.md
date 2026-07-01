# 🪙 Gold Rate Alert System — Pune

Automatically checks the **exact Pune gold rate** every 10 minutes and sends you a **WhatsApp + Email alert** when the price drops below your threshold.

- ✅ Exact Pune 22K & 24K rates (scraped from Jos Alukkas Online)
- ✅ WhatsApp notification via CallMeBot (free)
- ✅ Email notification via Gmail
- ✅ Runs every 10 minutes during market hours (Mon–Sat)
- ✅ 100% free using GitHub Actions
- ✅ No server needed

---

## 🚀 Setup Guide (10 minutes)

### Step 1 — Fork / Create this Repository

1. Go to [github.com](https://github.com) and sign in (or create a free account)
2. Click **"New repository"**, name it `gold-alert`
3. Upload all these files as-is

---

### Step 2 — Set Up CallMeBot (WhatsApp)

1. Save this number in your phone contacts: **+34 644 44 74 48**
2. Open WhatsApp, send this exact message to that number:
   ```
   I allow callmebot to send me messages
   ```
3. You'll receive a reply with your **API key** (looks like: `1234567`)
4. Note down your API key

---

### Step 3 — Set Up Gmail App Password (Email)

> If you don't want email alerts, skip this step.

1. Go to your Google Account → **Security**
2. Enable **2-Step Verification** (if not already)
3. Go to **App Passwords** → Select app: "Mail" → Select device: "Other"
4. Type "Gold Alert" → Click **Generate**
5. Copy the 16-character password shown (e.g. `abcd efgh ijkl mnop`)

---

### Step 4 — Add GitHub Secrets

1. Open your repository on GitHub
2. Go to **Settings → Secrets and variables → Actions**
3. Click **"New repository secret"** and add each of these:

| Secret Name | Value | Example |
|---|---|---|
| `THRESHOLD_22K` | Your 22K alert price (₹/gram) | `7200` |
| `THRESHOLD_24K` | Your 24K alert price (₹/gram) | `7850` |
| `WHATSAPP_NUMBER` | Your number with country code, no + | `919876543210` |
| `CALLMEBOT_API_KEY` | API key from CallMeBot | `1234567` |
| `EMAIL_SENDER` | Your Gmail address | `yourname@gmail.com` |
| `EMAIL_PASSWORD` | Gmail App Password (no spaces) | `abcdefghijklmnop` |
| `EMAIL_RECEIVER` | Where to receive alerts | `yourname@gmail.com` |

> 💡 **Tip**: Set `THRESHOLD_22K` slightly above today's rate initially to test that alerts work.

---

### Step 5 — Test It Manually

1. Go to your repository → **Actions** tab
2. Click **"Gold Rate Alert — Pune"** workflow
3. Click **"Run workflow"** → **"Run workflow"** (green button)
4. Watch the logs — you should see the rates printed
5. Check your WhatsApp and email!

---

## ⏰ Schedule

The workflow runs **every 10 minutes**, 7 days a week:

| Day | Hours (IST) |
|---|---|
| Monday – Sunday | 9:00 AM – 9:00 PM |

> To change frequency, edit `.github/workflows/gold_alert.yml` and modify the cron expression.
> For every 5 minutes, replace the 3 cron lines with:
> ```yaml
> - cron: "30-59/5 3 * * *"
> - cron: "*/5 4-14 * * *"
> - cron: "0,5,10,15,20,25,30 15 * * *"
> ```

---

## 📱 What the Alert Looks Like

**WhatsApp:**
```
🪙 Gold Rate Alert — Pune (15 May 2025, 10:30 AM)

✅ 22K Gold ₹7150/g has dropped below your threshold of ₹7200/g

Current Rates:
  22K → ₹7150/gram
  24K → ₹7800/gram

Act fast — rates change quickly!
```

**Email:** Same content, nicely formatted in HTML with gold styling.

---

## 🔧 Customization

### Change check frequency
Edit `gold_alert.yml`, change `*/10` to `*/5` for every 5 minutes:
```yaml
- cron: "*/5 3-11 * * 1-5"
```

### Only check one purity
Set the unused threshold secret to `0` — alerts for that purity will be skipped.

### Check only 22K
Set `THRESHOLD_24K` = `0`

---

## 🛠 Troubleshooting

| Problem | Solution |
|---|---|
| No WhatsApp received | Re-send activation message to CallMeBot, check API key |
| No email received | Check spam folder, verify Gmail App Password |
| Scraping fails | Jos Alukkas Online may have changed layout — open an issue |
| Workflow not running | Check Actions tab is enabled in your repo settings |

---

## 📊 Viewing Logs

After each run, GitHub saves a `last_check.json` file under **Actions → Artifacts** showing:
- Timestamp of check
- 22K and 24K rates found
- Whether an alert was triggered

---

## ⚠️ Disclaimer

Gold rates are scraped from Jos Alukkas Online for informational purposes only.
Always verify rates with your local jeweller before making purchase decisions.
