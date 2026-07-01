"""
Gold Rate Alert System
Fetches exact Pune gold rates from PNG Gadgil & Sons' rate API
Sends WhatsApp (CallMeBot) + Email alerts when rate drops below threshold
Supports:
  - Multiple WhatsApp numbers for alerts
  - Separate number for daily health check
  - Gram-based total cost threshold
  - Daily health check message at 9 AM IST
"""

import os
import json
import smtplib
import requests
import logging
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ─── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

# ─── IST Timezone ────────────────────────────────────────────────────────────
IST = timezone(timedelta(hours=5, minutes=30))

def now_ist():
    return datetime.now(IST)

# ─── Config from GitHub Secrets ─────────────────────────────────────────────

# Per-gram thresholds (₹/gram)
THRESHOLD_22K = float(os.environ.get("THRESHOLD_22K") or "0")
THRESHOLD_24K = float(os.environ.get("THRESHOLD_24K") or "0")

# Gram quantity
GRAMS_22K = float(os.environ.get("GRAMS_22K") or "1")
GRAMS_24K = float(os.environ.get("GRAMS_24K") or "1")

# Total budget thresholds (overrides per-gram if set)
BUDGET_22K = float(os.environ.get("BUDGET_22K") or "0")
BUDGET_24K = float(os.environ.get("BUDGET_24K") or "0")

# ── WhatsApp Numbers ─────────────────────────────────────────────────────────
#
# ALERT numbers — who receives price drop alerts
# Comma-separated: "919876543210,919812345678"
# Each number needs its own CallMeBot API key (comma-separated in same order)
ALERT_NUMBERS  = [n.strip() for n in os.environ.get("ALERT_NUMBERS", "").split(",") if n.strip()]
ALERT_API_KEYS = [k.strip() for k in os.environ.get("ALERT_API_KEYS", "").split(",") if k.strip()]

# HEALTH CHECK number — who receives the daily 9 AM status message
# Can be same as alert number or different
# Leave blank to send health check to all alert numbers
HEALTH_NUMBER  = os.environ.get("HEALTH_NUMBER", "").strip()
HEALTH_API_KEY = os.environ.get("HEALTH_API_KEY", "").strip()

# ── Email ────────────────────────────────────────────────────────────────────
EMAIL_SENDER   = os.environ.get("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")

# Comma-separated list of emails to receive alerts
ALERT_EMAILS   = [e.strip() for e in os.environ.get("ALERT_EMAILS", "").split(",") if e.strip()]

# Separate email for health check (optional — falls back to ALERT_EMAILS if blank)
HEALTH_EMAIL   = os.environ.get("HEALTH_EMAIL", "").strip()

# Daily health check toggle
DAILY_HEALTH_CHECK = os.environ.get("DAILY_HEALTH_CHECK", "true").lower() == "true"


# ─── Send WhatsApp to a specific number ──────────────────────────────────────
def send_whatsapp_to(number: str, api_key: str, message: str):
    if not number or not api_key:
        log.warning(f"Skipping WhatsApp — missing number or api_key for {number}")
        return
    url    = "https://api.callmebot.com/whatsapp.php"
    params = {"phone": number, "text": message, "apikey": api_key}
    try:
        resp = requests.get(url, params=params, timeout=15)
        log.info(f"WhatsApp → {number} | Status: {resp.status_code} | {resp.text[:80]}")
    except Exception as e:
        log.error(f"WhatsApp failed for {number}: {e}")


# ─── Send WhatsApp to all alert numbers ──────────────────────────────────────
def send_alert_whatsapp(message: str):
    if not ALERT_NUMBERS:
        log.warning("No ALERT_NUMBERS configured.")
        return
    if len(ALERT_NUMBERS) != len(ALERT_API_KEYS):
        log.error("Mismatch: ALERT_NUMBERS and ALERT_API_KEYS must have same count.")
        return
    for number, api_key in zip(ALERT_NUMBERS, ALERT_API_KEYS):
        send_whatsapp_to(number, api_key, message)


# ─── Send WhatsApp health check ───────────────────────────────────────────────
def send_health_whatsapp(message: str):
    if HEALTH_NUMBER and HEALTH_API_KEY:
        # Send to dedicated health check number
        send_whatsapp_to(HEALTH_NUMBER, HEALTH_API_KEY, message)
    else:
        # Fall back to all alert numbers
        log.info("No separate HEALTH_NUMBER set — sending health check to all alert numbers.")
        send_alert_whatsapp(message)


# ─── Send Email ───────────────────────────────────────────────────────────────
def send_email_to(recipients: list, subject: str, body: str):
    if not EMAIL_SENDER or not EMAIL_PASSWORD or not recipients:
        log.warning("Email credentials or recipients not set, skipping.")
        return
    try:
        html_body = f"""
        <html><body style="font-family:Arial,sans-serif;background:#fffbf0;padding:20px;">
          <div style="max-width:500px;margin:auto;background:#fff;border-radius:12px;
                      border:2px solid #f0c040;padding:24px;">
            <h2 style="color:#b8860b;">🪙 Gold Alert System — Pune</h2>
            <p style="font-size:16px;">{body.replace(chr(10), '<br>')}</p>
            <hr style="border-color:#f0c040;">
            <p style="font-size:12px;color:#999;">
              Sent by your Gold Alert System • {now_ist().strftime('%d %b %Y, %I:%M %p')} IST
            </p>
          </div>
        </body></html>
        """
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            for recipient in recipients:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"]    = EMAIL_SENDER
                msg["To"]      = recipient
                msg.attach(MIMEText(body, "plain"))
                msg.attach(MIMEText(html_body, "html"))
                server.sendmail(EMAIL_SENDER, recipient, msg.as_string())
                log.info(f"Email sent to {recipient}")
    except Exception as e:
        log.error(f"Email send failed: {e}")


def send_alert_email(subject: str, body: str):
    send_email_to(ALERT_EMAILS, subject, body)


def send_health_email(subject: str, body: str):
    if HEALTH_EMAIL:
        send_email_to([HEALTH_EMAIL], subject, body)
    else:
        send_email_to(ALERT_EMAILS, subject, body)


# ─── Fetch Pune Gold Rate ────────────────────────────────────────────────────
def fetch_pune_gold_rates():
    """
    Fetches today's Pune gold rate (22K and 24K, 999 purity) from the JSON API
    that backs PNG Gadgil & Sons' gold rate page. Scraping their HTML directly
    is unreliable — the rate table there is filled in client-side via this
    same API call, so we hit it directly instead.
    """
    url = "https://goldpriceeditor.droidinfinity.com/api/external/metal-prices/1085"

    log.info(f"Fetching Pune gold rates from {url}")
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    rates = {}
    metal_rates = data.get("rates", {})
    if "goldPrice22K" in metal_rates:
        rates["22K"] = int(metal_rates["goldPrice22K"])
        log.info(f"22K: Rs.{rates['22K']}/gram")
    if "goldPrice24K" in metal_rates:
        rates["24K"] = int(metal_rates["goldPrice24K"])
        log.info(f"24K: Rs.{rates['24K']}/gram")

    log.info(f"Final rates: {rates}")
    return rates


# ─── Helpers ─────────────────────────────────────────────────────────────────
def fmt(amount: float) -> str:
    return f"{int(amount):,}"

def is_health_check_time() -> bool:
    now = now_ist()
    return now.hour == 9 and now.minute < 10

def build_rate_summary(rates: dict) -> list:
    lines = ["📊 Current Pune Gold Rates:"]
    if "22K" in rates:
        rate  = rates["22K"]
        total = rate * GRAMS_22K
        lines.append(f"  22K → ₹{fmt(rate)}/gram")
        if GRAMS_22K != 1:
            lines.append(f"       {int(GRAMS_22K)}g total = ₹{fmt(total)}")
    if "24K" in rates:
        rate  = rates["24K"]
        total = rate * GRAMS_24K
        lines.append(f"  24K → ₹{fmt(rate)}/gram")
        if GRAMS_24K != 1:
            lines.append(f"       {int(GRAMS_24K)}g total = ₹{fmt(total)}")
    return lines


# ─── Main ────────────────────────────────────────────────────────────────────
def main():
    log.info("=" * 50)
    log.info("Gold Alert System — Starting check")
    log.info(f"Alert numbers  : {ALERT_NUMBERS}")
    log.info(f"Health number  : {HEALTH_NUMBER or 'same as alert numbers'}")
    log.info(f"Alert emails   : {ALERT_EMAILS}")
    log.info(f"Health email   : {HEALTH_EMAIL or 'same as alert emails'}")

    rates = fetch_pune_gold_rates()
    now   = now_ist().strftime("%d %b %Y, %I:%M %p")

    if not rates:
        log.error("Could not fetch gold rates.")
        error_msg = (
            f"⚠️ Gold Alert System — Scraping Failed\n"
            f"Could not fetch Pune gold rates at {now} IST\n"
            f"Please check pngadgilandsons.com manually."
        )
        send_alert_whatsapp(error_msg)
        send_alert_email("⚠️ Gold Alert — Scraping Failed", error_msg)
        return

    alerts_triggered = []

    # ── Check 22K ────────────────────────────────────────────────────────
    if "22K" in rates:
        rate_22k  = rates["22K"]
        total_22k = rate_22k * GRAMS_22K
        if BUDGET_22K > 0:
            threshold_met   = total_22k <= BUDGET_22K
            threshold_label = f"total budget ₹{fmt(BUDGET_22K)} for {int(GRAMS_22K)}g"
        elif THRESHOLD_22K > 0:
            threshold_met   = rate_22k <= THRESHOLD_22K
            threshold_label = f"per-gram target ₹{fmt(THRESHOLD_22K)}"
        else:
            threshold_met   = False
            threshold_label = ""
        if threshold_met:
            alerts_triggered.append(
                f"22K Gold has hit your target!\n"
                f"  Rate     : ₹{fmt(rate_22k)}/gram\n"
                f"  Quantity : {int(GRAMS_22K)} gram(s)\n"
                f"  Total    : ₹{fmt(total_22k)}\n"
                f"  Target   : {threshold_label}"
            )
            log.info("🔔 22K ALERT triggered")

    # ── Check 24K ────────────────────────────────────────────────────────
    if "24K" in rates:
        rate_24k  = rates["24K"]
        total_24k = rate_24k * GRAMS_24K
        if BUDGET_24K > 0:
            threshold_met   = total_24k <= BUDGET_24K
            threshold_label = f"total budget ₹{fmt(BUDGET_24K)} for {int(GRAMS_24K)}g"
        elif THRESHOLD_24K > 0:
            threshold_met   = rate_24k <= THRESHOLD_24K
            threshold_label = f"per-gram target ₹{fmt(THRESHOLD_24K)}"
        else:
            threshold_met   = False
            threshold_label = ""
        if threshold_met:
            alerts_triggered.append(
                f"24K Gold has hit your target!\n"
                f"  Rate     : ₹{fmt(rate_24k)}/gram\n"
                f"  Quantity : {int(GRAMS_24K)} gram(s)\n"
                f"  Total    : ₹{fmt(total_24k)}\n"
                f"  Target   : {threshold_label}"
            )
            log.info("🔔 24K ALERT triggered")

    # ── Send price alert ──────────────────────────────────────────────────
    if alerts_triggered:
        lines = [f"🪙 Gold Rate Alert — Pune ({now} IST)", ""]
        for a in alerts_triggered:
            lines.append(f"✅ {a}")
            lines.append("")
        lines += build_rate_summary(rates)
        lines += ["", "⚡ Act fast — rates change quickly!"]
        full_message = "\n".join(lines)
        send_alert_whatsapp(full_message)
        send_alert_email("🪙 Gold Rate Alert — Pune", full_message)
    else:
        log.info("No alerts triggered.")

    # ── Daily health check at 9:00–9:10 AM IST ───────────────────────────
    if DAILY_HEALTH_CHECK and is_health_check_time():
        log.info("Sending daily health check message...")
        lines = [
            f"✅ Gold Alert System — Working Fine",
            f"📅 {now} IST",
            "",
        ]
        lines += build_rate_summary(rates)
        lines += ["", "📌 Your Targets:"]
        if BUDGET_22K > 0:
            lines.append(f"  22K → Alert when {int(GRAMS_22K)}g ≤ ₹{fmt(BUDGET_22K)}")
        elif THRESHOLD_22K > 0:
            lines.append(f"  22K → Alert when rate ≤ ₹{fmt(THRESHOLD_22K)}/g")
        if BUDGET_24K > 0:
            lines.append(f"  24K → Alert when {int(GRAMS_24K)}g ≤ ₹{fmt(BUDGET_24K)}")
        elif THRESHOLD_24K > 0:
            lines.append(f"  24K → Alert when rate ≤ ₹{fmt(THRESHOLD_24K)}/g")
        lines += ["", "System is running every 10 minutes. 👍"]
        health_msg = "\n".join(lines)
        send_health_whatsapp(health_msg)
        send_health_email("✅ Gold Alert — Daily Status (System Working)", health_msg)

    # ── Save log ──────────────────────────────────────────────────────────
    with open("last_check.json", "w") as f:
        json.dump({
            "timestamp_ist"   : now,
            "rates"           : rates,
            "alerts_triggered": len(alerts_triggered),
            "grams_22k"       : GRAMS_22K,
            "grams_24k"       : GRAMS_24K,
            "total_cost_22k"  : rates.get("22K", 0) * GRAMS_22K,
            "total_cost_24k"  : rates.get("24K", 0) * GRAMS_24K,
        }, f, indent=2)

    log.info("Check complete.")
    log.info("=" * 50)


if __name__ == "__main__":
    main()