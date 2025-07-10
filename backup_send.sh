#!/bin/bash
set -euo pipefail

# ── CONFIG ─────────────────────────────────────────────────────
LOCAL_DIR="/store/backup"
REMOTE_DIR="/root/store/backup/other"
REMOTE_USER="root"
REMOTE_HOST="192.168.1.20"
SSH_KEY_PATH="/root/.ssh/id_rsa"

EMAIL_SENDER="Ali.hamaza7979@gmail.com"
EMAIL_PASSWORD="zwfv nqwa yfey yuuk"
EMAIL_RECIPIENT="hamza.digitaldoer@gmail.com"

STATE_FILE="/var/log/backup_last_sent.txt"
# ──────────────────────────────────────────────────────────────

cd "$LOCAL_DIR" || exit 1
config_file=""
data_file=""
latest_date=""

for f in $(ls -t backup.nightly.SIEM_*.tgz); do
    if [[ "$f" =~ backup\.nightly\.SIEM_([0-9]{2}\.[0-9]{2}_[0-9]{2}_[0-9]{4})\.(config|data)\.[0-9]+\.tgz ]]; then
        date_key="${BASH_REMATCH[1]}"
        type="${BASH_REMATCH[2]}"
        file_path=$(ls -1 backup.nightly.SIEM_${date_key}.${type}.*.tgz 2>/dev/null | head -n 1)
        if [[ -n "$file_path" ]]; then
            [[ "$type" == "config" ]] && config_file="$file_path"
            [[ "$type" == "data" ]] && data_file="$file_path"
        fi
        if [[ -n "$config_file" && -n "$data_file" ]]; then
            latest_date="$date_key"
            break
        fi
    fi
done

if [[ -z "$latest_date" ]]; then
    echo "❌ No complete backup pair found."
    exit 1
fi

if [[ -f "$STATE_FILE" ]]; then
    last_sent=$(cat "$STATE_FILE")
    if [[ "$last_sent" == "$latest_date" ]]; then
        echo "[`date '+%Y-%m-%d %H:%M:%S'`] ✅ Last backup ($latest_date) already sent. Skipping."
        exit 0
    else
        echo "[`date '+%Y-%m-%d %H:%M:%S'`] ℹ️ Last sent was $last_sent, new backup is $latest_date — proceeding."
    fi
fi

for file in "$config_file" "$data_file"; do
    echo "[`date '+%Y-%m-%d %H:%M:%S'`] 📤 Transferring $file..."
    scp -i "$SSH_KEY_PATH" "$file" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR"
    if [[ $? -ne 0 ]]; then
        echo "[`date '+%Y-%m-%d %H:%M:%S'`] ❌ SCP failed for $file"
        exit 2
    fi
done

BODY=$(cat <<EOF
Backup files transferred:

Date: $latest_date
Files:
- $config_file
- $data_file

Time: $(date '+%Y-%m-%d %H:%M:%S')
EOF
)

echo "$BODY" | mailx -s "Backup Sent: $latest_date" -r "$EMAIL_SENDER" "$EMAIL_RECIPIENT"

if [[ $? -eq 0 ]]; then
    echo "[`date '+%Y-%m-%d %H:%M:%S'`] ✅ Email sent to $EMAIL_RECIPIENT"
else
    echo "[`date '+%Y-%m-%d %H:%M:%S'`] ❌ Email failed."
    exit 3
fi

echo "$latest_date" > "$STATE_FILE"
echo "[`date '+%Y-%m-%d %H:%M:%S'`] 📝 Updated state file with $latest_date"
