import os
import re
import smtplib
import ssl
from pathlib import Path
from subprocess import run
from datetime import datetime

LOCAL_DIR = "/store/backup"
REMOTE_DIR = "/root/store/backup/other"
REMOTE_USER = "root"
REMOTE_HOST = "192.168.1.20"
SSH_KEY_PATH = "/root/.ssh/id_rsa"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = "Ali.hamaza7979@gmail.com"
EMAIL_PASSWORD = "zwfv nqwa yfey yuuk"
EMAIL_RECIPIENT = "hamza.digitaldoer@gmail.com"

STATE_FILE = "/var/log/backup_last_sent.txt"

files = sorted(Path(LOCAL_DIR).glob("*.tgz"), key=lambda f: f.stat().st_mtime, reverse=True)
pattern = re.compile(r"backup\.nightly\.SIEM_(\d{2}\.\d{2}_\d{2}_\d{4})\.(config|data)\.\d+\.tgz")
latest_date = None
pair_files = {}

for f in files:
    m = pattern.match(f.name)
    if not m:
        continue
    date_key, ftype = m.groups()
    pair_files.setdefault(date_key, {})[ftype] = f
    if {"config", "data"} <= pair_files[date_key].keys():
        latest_date = date_key
        break

if not latest_date:
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] ❌ No complete backup pair found.")
    exit(1)

config_file = pair_files[latest_date]["config"]
data_file = pair_files[latest_date]["data"]

if os.path.exists(STATE_FILE):
    with open(STATE_FILE) as sf:
        if sf.read().strip() == latest_date:
            print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] ✅ Backup {latest_date} already sent. Skipping.")
            exit(0)

for file in (config_file, data_file):
    res = run(["scp", "-i", SSH_KEY_PATH, str(file), f"{REMOTE_USER}@{REMOTE_HOST}:{REMOTE_DIR}"])
    if res.returncode != 0:
        print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] ❌ SCP failed for {file.name}")
        exit(2)

subject = f"Backup Sent: {latest_date}"
body = (f"Backup files transferred:\n\nDate: {latest_date}\nFiles:\n"
        f"- {config_file.name}\n- {data_file.name}\n\n"
        f"Time: {datetime.now():%Y-%m-%d %H:%M:%S}\n")

message = (f"From: {EMAIL_SENDER}\n"
           f"To: {EMAIL_RECIPIENT}\n"
           f"Subject: {subject}\n\n{body}")

try:
    ctx = ssl.create_default_context()
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as srv:
        srv.starttls(context=ctx)
        srv.login(EMAIL_SENDER, EMAIL_PASSWORD)
        srv.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, message)
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] ✅ Email sent.")
except Exception as e:
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] ❌ Email failed: {e}")
    exit(3)

try:
    with open(STATE_FILE, "w") as sf:
        sf.write(latest_date)
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] 📝 Updated state file with {latest_date}")
except IOError as e:
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] ⚠️ Could not update state file: {e}")
