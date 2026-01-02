#!/usr/bin/env python3
"""Festival Submit - Automated Scheduler for cron/launchd"""
import json, sys
from datetime import datetime, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from festival_submit import ConfigManager, SubmissionDatabase, TemplateEngine, ReportGenerator

class AutomationRunner:
    def __init__(self):
        self.base = Path(__file__).parent
        self.config = ConfigManager(self.base / "config")
        self.db = SubmissionDatabase(self.base / "data" / "submissions.db")
        self.logs = self.base / "logs"
        self.reports = self.base / "reports"
        self.logs.mkdir(exist_ok=True)
        self.reports.mkdir(exist_ok=True)
        
    def setup(self):
        self.config.load_all()
        self.db.connect()
        
    def teardown(self):
        self.db.close()
        
    def log(self, msg, level="INFO"):
        ts = datetime.now().isoformat()
        line = f"[{ts}] [{level}] {msg}"
        print(line)
        with open(self.logs / f"automation_{datetime.now():%Y-%m}.log", "a") as f:
            f.write(line + "\n")
            
    def run_daily(self):
        self.log("Starting daily automation")
        
        # Check deadlines
        deadlines = self.db.get_upcoming_deadlines(7)
        self.log(f"Found {len(deadlines)} deadlines in next 7 days")
        for d in deadlines:
            self.log(f"  DEADLINE: {d['festival_name']} ({d['act_id']}) - {d['deadline_date']}", "WARN")
            
        # Check follow-ups
        followups = self.db.get_submissions_needing_followup()
        self.log(f"Found {len(followups)} submissions needing follow-up")
        
        # Generate daily report
        report = ReportGenerator(self.config, self.db).generate_status_report()
        report_file = self.reports / f"daily_{datetime.now():%Y-%m-%d}.md"
        report_file.write_text(report)
        self.log(f"Report saved: {report_file}")
        
        return {"deadlines": len(deadlines), "followups": len(followups)}
        
    def run_weekly(self):
        self.log("Starting weekly automation")
        
        # Generate calendar
        calendar = ReportGenerator(self.config, self.db).generate_calendar(12)
        cal_file = self.reports / f"calendar_{datetime.now():%Y-%m-%d}.md"
        cal_file.write_text(calendar)
        
        # Generate opportunity reports for each act
        for act in self.config.get_active_acts():
            opp = ReportGenerator(self.config, self.db).generate_opportunities(act.id)
            opp_file = self.reports / f"opportunities_{act.id}.md"
            opp_file.write_text(opp)
            self.log(f"Generated opportunities report for {act.name}")
            
        return {"calendar": str(cal_file)}
        
    def run_all(self):
        self.setup()
        try:
            daily = self.run_daily()
            weekly = self.run_weekly() if datetime.now().weekday() == 0 else {}
            return {**daily, **weekly}
        finally:
            self.teardown()

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--daily", action="store_true")
    p.add_argument("--weekly", action="store_true")
    p.add_argument("--all", action="store_true")
    args = p.parse_args()
    
    runner = AutomationRunner()
    runner.setup()
    try:
        if args.daily: results = runner.run_daily()
        elif args.weekly: results = runner.run_weekly()
        else: results = runner.run_all()
        print(json.dumps(results, indent=2))
    finally:
        runner.teardown()

if __name__ == "__main__": main()
