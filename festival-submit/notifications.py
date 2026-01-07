#!/usr/bin/env python3
"""Festival Submit - Notifications (email and desktop)"""
import os, smtplib, subprocess, sys
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from festival_submit import ConfigManager, SubmissionDatabase

class NotificationManager:
    def __init__(self):
        self.base = Path(__file__).parent
        self.config = ConfigManager(self.base / "config")
        self.db = SubmissionDatabase(self.base / "data" / "submissions.db")
        # Email config from environment
        self.smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        self.smtp_user = os.environ.get("SMTP_USER", "")
        self.smtp_pass = os.environ.get("SMTP_PASS", "")
        self.email_to = os.environ.get("EMAIL_TO", "")
        
    def setup(self):
        self.config.load_all()
        self.db.connect()
        
    def teardown(self):
        self.db.close()
        
    def send_desktop(self, title, message):
        """Send macOS desktop notification"""
        try:
            # Escape quotes and backslashes to prevent command injection
            title_escaped = title.replace('\\', '\\\\').replace('"', '\\"')
            message_escaped = message.replace('\\', '\\\\').replace('"', '\\"')
            subprocess.run(["osascript", "-e",
                f'display notification "{message_escaped}" with title "{title_escaped}" sound name "Glass"'], check=True)
            return True
        except: return False
        
    def send_email(self, subject, body):
        """Send email notification"""
        if not self.smtp_user or not self.email_to:
            print("Email not configured"); return False
        try:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = self.smtp_user
            msg["To"] = self.email_to
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as s:
                s.starttls()
                s.login(self.smtp_user, self.smtp_pass)
                s.send_message(msg)
            return True
        except Exception as e:
            print(f"Email failed: {e}"); return False
            
    def check_deadlines(self):
        """Check and notify upcoming deadlines"""
        notifications = []
        for days in [30, 14, 7, 3, 1]:
            target = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
            for d in self.db.get_upcoming_deadlines(days):
                if d.get("deadline_date") == target:
                    title = f"Festival Deadline in {days} Days!"
                    msg = f"{d['festival_name']} ({d['act_id']})"
                    self.send_desktop(title, msg)
                    notifications.append({"days": days, "festival": d["festival_name"]})
        return notifications
        
    def check_followups(self):
        """Check and notify needed follow-ups"""
        notifications = []
        for f in self.db.get_submissions_needing_followup():
            if f.get("submission_date"):
                days = (datetime.now() - datetime.fromisoformat(f["submission_date"])).days
                if days in [14, 28]:
                    self.send_desktop(f"Follow-up Needed ({days}d)", f["festival_name"])
                    notifications.append({"days": days, "festival": f["festival_name"]})
        return notifications
        
    def send_digest(self):
        """Send daily email digest"""
        stats = self.db.get_submission_stats()
        deadlines = self.db.get_upcoming_deadlines(7)
        body = f"""Festival Submit Daily Digest - {datetime.now():%Y-%m-%d}

STATISTICS
Total: {stats['total']} | Submitted: {stats['submitted']} | Accepted: {stats['accepted']}

UPCOMING DEADLINES (7 days)
"""
        for d in deadlines:
            body += f"- {d['deadline_date']}: {d['festival_name']} ({d['act_id']})\n"
        return self.send_email(f"Festival Submit Digest - {datetime.now():%Y-%m-%d}", body)
        
    def run_all(self):
        self.setup()
        try:
            dl = self.check_deadlines()
            fu = self.check_followups()
            print(f"Deadline notifications: {len(dl)}")
            print(f"Follow-up notifications: {len(fu)}")
            return {"deadlines": dl, "followups": fu}
        finally:
            self.teardown()

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--check", action="store_true", help="Run all checks")
    p.add_argument("--digest", action="store_true", help="Send email digest")
    p.add_argument("--test", action="store_true", help="Test notification")
    args = p.parse_args()
    
    nm = NotificationManager()
    if args.test:
        nm.send_desktop("Festival Submit Test", "Test notification")
    elif args.digest:
        nm.setup(); nm.send_digest(); nm.teardown()
    else:
        print(nm.run_all())

if __name__ == "__main__": main()
