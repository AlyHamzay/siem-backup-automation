# SIEM Backup Automation

This project automates the process of transferring daily SIEM backup files (`.tgz`) to a remote server via SCP and notifies via email.

## Features
- Automatically detects latest `config` + `data` backup pair
- Skips already-sent backups using a state file
- Sends email notification on successful transfer
- Bash and Python versions included
- Cron-job ready with logging

## Files
- `backup_send.sh`: Bash version using `mailx`
- `send_backup.py`: Python version using Gmail SMTP
- Logs to `/var/log/send_backup_Python.log` (or custom path)

## Cron Example
```bash
0 1 * * * /usr/bin/python3 /root/send_backup.py >> /var/log/send_backup_Python.log 2>&1
