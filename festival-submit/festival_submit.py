#!/usr/bin/env python3
"""Festival Submit - Automated Festival Submission System"""
import argparse, json, re, sqlite3, sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional
try:
    import tomllib
except ImportError:
    import tomli as tomllib

@dataclass
class ActConfig:
    id: str; name: str; tagline: str; genres: list; subgenres: list; active: bool
    members: int; member_names: list; instruments: list; year_formed: int; hometown: str
    set_lengths: list; min_stage_width: int; min_stage_depth: int
    power_requirements: str; backline_needs: list; sound_check_time: int
    fees: dict; travel: dict; assets: dict; festival_prefs: dict; bio_short: str; bio_long: str

@dataclass 
class FestivalConfig:
    id: str; name: str; location: str; distance_miles: int; dates_typical: str
    duration_days: int; genre_focus: list; estimated_attendance: int; stages: int
    website: str; submission_url: str; submission_deadline_typical: str
    submission_fee: float; accepts: list; pay_range: str; provides: list
    notes: str; suitable_acts: list; tier: str; priority: str = "normal"

class ConfigManager:
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.acts, self.festivals, self.templates = {}, {}, {}
        self.settings, self.festival_settings = {}, {}
        
    def load_all(self):
        self._load_acts(); self._load_festivals(); self._load_templates()
        
    def _load_acts(self):
        f = self.config_dir / "acts.toml"
        if not f.exists(): return
        with open(f, "rb") as fp: data = tomllib.load(fp)
        self.settings = data.get("settings", {})
        for aid, a in data.get("acts", {}).items():
            self.acts[aid] = ActConfig(
                id=aid, name=a.get("name",""), tagline=a.get("tagline",""),
                genres=a.get("genres",[]), subgenres=a.get("subgenres",[]),
                active=a.get("active",True), members=a.get("members",1),
                member_names=a.get("member_names",[]), instruments=a.get("instruments",[]),
                year_formed=a.get("year_formed",2020), hometown=a.get("hometown",""),
                set_lengths=a.get("set_lengths",[60]), min_stage_width=a.get("min_stage_width",10),
                min_stage_depth=a.get("min_stage_depth",8), power_requirements=a.get("power_requirements",""),
                backline_needs=a.get("backline_needs",[]), sound_check_time=a.get("sound_check_time",30),
                fees=a.get("fees",{}), travel=a.get("travel",{}), assets=a.get("assets",{}),
                festival_prefs=a.get("festival_prefs",{}), bio_short=a.get("bio_short","").strip(),
                bio_long=a.get("bio_long","").strip())
                
    def _load_festivals(self):
        f = self.config_dir / "festivals.toml"
        if not f.exists(): return
        with open(f, "rb") as fp: data = tomllib.load(fp)
        self.festival_settings = data.get("settings", {})
        for tier in ["local", "regional", "national", "international"]:
            for fid, fd in data.get("festivals", {}).get(tier, {}).items():
                self.festivals[f"{tier}.{fid}"] = FestivalConfig(
                    id=f"{tier}.{fid}", name=fd.get("name",""), location=fd.get("location",""),
                    distance_miles=fd.get("distance_miles",0), dates_typical=fd.get("dates_typical",""),
                    duration_days=fd.get("duration_days",1), genre_focus=fd.get("genre_focus",[]),
                    estimated_attendance=fd.get("estimated_attendance",0), stages=fd.get("stages",1),
                    website=fd.get("website",""), submission_url=fd.get("submission_url",""),
                    submission_deadline_typical=fd.get("submission_deadline_typical",""),
                    submission_fee=fd.get("submission_fee",0), accepts=fd.get("accepts",[]),
                    pay_range=fd.get("pay_range",""), provides=fd.get("provides",[]),
                    notes=fd.get("notes",""), suitable_acts=fd.get("suitable_acts",[]),
                    tier=tier, priority=fd.get("priority","normal"))
                    
    def _load_templates(self):
        f = self.config_dir / "templates.toml"
        if not f.exists(): return
        with open(f, "rb") as fp: data = tomllib.load(fp)
        self.templates = data.get("templates", {})
        
    def get_active_acts(self): return [a for a in self.acts.values() if a.active]
    
    def match_festivals_to_act(self, act):
        matches = []
        for fest in self.festivals.values():
            if act.id in fest.suitable_acts: matches.append(fest)
        return matches

class SubmissionDatabase:
    def __init__(self, db_path: Path):
        self.db_path, self.conn = db_path, None
        
    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        
    def close(self):
        if self.conn: self.conn.close()
        
    def _create_tables(self):
        c = self.conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY, act_id TEXT, festival_id TEXT, festival_name TEXT,
            submission_date TEXT, deadline_date TEXT, status TEXT DEFAULT 'draft',
            template_used TEXT, submission_fee REAL DEFAULT 0, response_date TEXT,
            response_status TEXT, notes TEXT, follow_up_date TEXT, follow_up_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        c.execute("""CREATE TABLE IF NOT EXISTS scheduled_tasks (
            id INTEGER PRIMARY KEY, task_type TEXT, act_id TEXT, festival_id TEXT,
            scheduled_date TEXT, status TEXT DEFAULT 'pending', parameters TEXT,
            result TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, executed_at TEXT)""")
        self.conn.commit()
        
    def add_submission(self, act_id, festival_id, festival_name, deadline_date=None, fee=0, notes=None):
        c = self.conn.cursor()
        c.execute("INSERT INTO submissions (act_id,festival_id,festival_name,deadline_date,submission_fee,notes) VALUES (?,?,?,?,?,?)",
            (act_id, festival_id, festival_name, deadline_date, fee, notes))
        self.conn.commit()
        return c.lastrowid
        
    def get_pending_submissions(self, act_id=None):
        c = self.conn.cursor()
        if act_id: c.execute("SELECT * FROM submissions WHERE status IN ('draft','submitted') AND act_id=? ORDER BY deadline_date", (act_id,))
        else: c.execute("SELECT * FROM submissions WHERE status IN ('draft','submitted') ORDER BY deadline_date")
        return [dict(r) for r in c.fetchall()]
        
    def get_upcoming_deadlines(self, days=30):
        c = self.conn.cursor()
        future = (datetime.now() + timedelta(days=days)).isoformat()[:10]
        c.execute("SELECT * FROM submissions WHERE deadline_date<=? AND status='draft' ORDER BY deadline_date", (future,))
        return [dict(r) for r in c.fetchall()]
        
    def get_submissions_needing_followup(self):
        c = self.conn.cursor()
        c.execute("SELECT * FROM submissions WHERE status='submitted' AND response_status IS NULL ORDER BY submission_date")
        return [dict(r) for r in c.fetchall()]
        
    def get_submission_stats(self, act_id=None):
        c = self.conn.cursor()
        q = "SELECT COUNT(*) FROM submissions" + (f" WHERE act_id='{act_id}'" if act_id else "")
        c.execute(q); total = c.fetchone()[0]
        c.execute(q.replace("COUNT(*)","COUNT(*)") + (" AND" if act_id else " WHERE") + " status='submitted'"); submitted = c.fetchone()[0]
        c.execute(q.replace("COUNT(*)","COUNT(*)") + (" AND" if act_id else " WHERE") + " response_status='accepted'"); accepted = c.fetchone()[0]
        c.execute(q.replace("COUNT(*)","COUNT(*)") + (" AND" if act_id else " WHERE") + " response_status='rejected'"); rejected = c.fetchone()[0]
        return {"total":total,"submitted":submitted,"accepted":accepted,"rejected":rejected,"pending":submitted-accepted-rejected}

class TemplateEngine:
    def __init__(self, config): self.config = config
    
    def render(self, template_id, act_id, festival_id):
        tmpl = self.config.templates.get(template_id, {})
        act = self.config.acts.get(act_id)
        fest = self.config.festivals.get(festival_id)
        if not act or not fest: raise ValueError("Act or festival not found")
        v = {
            "act_name": act.name, "genres": ", ".join(act.genres), "members": str(act.members),
            "instruments": ", ".join(act.instruments), "set_lengths": ", ".join(f"{s}min" for s in act.set_lengths),
            "bio_short": act.bio_short, "website": act.assets.get("website",""),
            "epk_url": act.assets.get("epk_url",""), "instagram": act.assets.get("instagram",""),
            "bandcamp": act.assets.get("bandcamp",""), "festival_name": fest.name,
            "contact_name": self.config.settings.get("default_contact_name",""),
            "contact_email": self.config.settings.get("default_contact_email",""),
        }
        subj = tmpl.get("subject",""); body = tmpl.get("body","")
        for k,val in v.items(): subj = subj.replace(f"{{{k}}}", str(val)); body = body.replace(f"{{{k}}}", str(val))
        return subj, body

class ReportGenerator:
    def __init__(self, config, db): self.config, self.db = config, db
    
    def generate_status_report(self, act_id=None):
        stats = self.db.get_submission_stats(act_id)
        lines = [f"# Festival Submission Status Report", f"Generated: {datetime.now():%Y-%m-%d %H:%M}", "",
            "## Summary", f"- Total: {stats['total']}", f"- Submitted: {stats['submitted']}",
            f"- Accepted: {stats['accepted']}", f"- Rejected: {stats['rejected']}", ""]
        deadlines = self.db.get_upcoming_deadlines(30)
        if deadlines:
            lines.append("## Upcoming Deadlines")
            for d in deadlines: lines.append(f"- {d['deadline_date']}: {d['festival_name']} ({d['act_id']})")
        return "\n".join(lines)
        
    def generate_calendar(self, months=6):
        lines = [f"# Festival Submission Calendar", f"Generated: {datetime.now():%Y-%m-%d}", ""]
        for i in range(months):
            m = datetime.now() + timedelta(days=30*i)
            lines.append(f"## {m:%B %Y}")
            fests = [f for f in self.config.festivals.values() if m.strftime("%B").lower() in f.submission_deadline_typical.lower()]
            if fests:
                for f in fests: lines.append(f"- **{f.name}**: {f.submission_deadline_typical} ({', '.join(f.suitable_acts)})")
            else: lines.append("*No known deadlines*")
            lines.append("")
        return "\n".join(lines)
        
    def generate_opportunities(self, act_id):
        act = self.config.acts.get(act_id)
        if not act: return f"Act not found: {act_id}"
        matches = self.config.match_festivals_to_act(act)
        lines = [f"# Opportunities: {act.name}", f"Genres: {', '.join(act.genres)}", ""]
        for tier in ["local","regional","national","international"]:
            tm = [f for f in matches if f.tier == tier]
            if tm:
                lines.append(f"## {tier.title()} ({len(tm)})")
                for f in tm: lines.append(f"- **{f.name}** ({f.location}) - Deadline: {f.submission_deadline_typical}")
                lines.append("")
        return "\n".join(lines)

class FestivalSubmitCLI:
    def __init__(self):
        self.base = Path(__file__).parent
        self.config = ConfigManager(self.base / "config")
        self.db = SubmissionDatabase(self.base / "data" / "submissions.db")
        
    def run(self, args):
        (self.base / "data").mkdir(exist_ok=True)
        self.config.load_all(); self.db.connect()
        try:
            return {"init": self._init, "acts": self._acts, "festivals": self._festivals,
                "match": lambda: self._match(args), "submit": lambda: self._submit(args),
                "status": lambda: self._status(args), "report": lambda: self._report(args),
                "calendar": lambda: self._calendar(args), "render": lambda: self._render(args),
                "templates": self._templates}.get(args.command, lambda: 1)()
        finally: self.db.close()
            
    def _init(self): print("Database initialized."); return 0
    
    def _acts(self):
        print("\n=== Acts ===\n")
        for a in sorted(self.config.acts.values(), key=lambda x: x.name):
            print(f"{'✓' if a.active else '✗'} {a.id}: {a.name} ({', '.join(a.genres[:2])})")
        return 0
        
    def _festivals(self):
        print("\n=== Festivals ===\n")
        for tier in ["local","regional","national","international"]:
            fests = [f for f in self.config.festivals.values() if f.tier == tier]
            if fests:
                print(f"## {tier.upper()}")
                for f in sorted(fests, key=lambda x: x.name):
                    print(f"  • {f.name} ({f.location}) - {f.submission_deadline_typical}")
                print()
        return 0
        
    def _match(self, args):
        act = self.config.acts.get(args.act)
        if not act: print(f"Act not found: {args.act}"); return 1
        matches = self.config.match_festivals_to_act(act)
        print(f"\n=== Matches for {act.name} ({len(matches)}) ===\n")
        for f in matches: print(f"  • {f.name} ({f.tier}) - {f.location}")
        return 0
        
    def _submit(self, args):
        act = self.config.acts.get(args.act)
        fest = self.config.festivals.get(args.festival)
        if not act or not fest: print("Act or festival not found"); return 1
        sid = self.db.add_submission(args.act, args.festival, fest.name, getattr(args,'deadline',None), fest.submission_fee)
        print(f"Submission #{sid} created: {act.name} → {fest.name}")
        return 0
        
    def _status(self, args):
        stats = self.db.get_submission_stats(getattr(args,'act',None))
        print(f"\nTotal: {stats['total']} | Submitted: {stats['submitted']} | Accepted: {stats['accepted']}")
        pending = self.db.get_pending_submissions(getattr(args,'act',None))
        if pending:
            print("\nPending:")
            for p in pending: print(f"  [{p['status']}] {p['festival_name']} ({p['act_id']})")
        return 0
        
    def _report(self, args):
        gen = ReportGenerator(self.config, self.db)
        t = getattr(args,'type','status')
        if t == 'status': print(gen.generate_status_report(getattr(args,'act',None)))
        elif t == 'opportunities': print(gen.generate_opportunities(args.act) if hasattr(args,'act') and args.act else "Need --act")
        elif t == 'calendar': print(gen.generate_calendar())
        return 0
        
    def _calendar(self, args):
        print(ReportGenerator(self.config, self.db).generate_calendar(getattr(args,'months',6)))
        return 0
        
    def _render(self, args):
        try:
            subj, body = TemplateEngine(self.config).render(args.template, args.act, args.festival)
            print(f"Subject: {subj}\n\n{body}")
        except Exception as e: print(f"Error: {e}"); return 1
        return 0
        
    def _templates(self):
        print("\n=== Templates ===")
        for tid, t in self.config.templates.items(): print(f"  • {tid}: {t.get('name','')}")
        return 0

def main():
    p = argparse.ArgumentParser(description="Festival Submit CLI")
    sp = p.add_subparsers(dest="command")
    sp.add_parser("init"); sp.add_parser("acts"); sp.add_parser("festivals"); sp.add_parser("templates")
    m = sp.add_parser("match"); m.add_argument("--act", required=True)
    s = sp.add_parser("submit"); s.add_argument("--act", required=True); s.add_argument("--festival", required=True); s.add_argument("--deadline")
    st = sp.add_parser("status"); st.add_argument("--act")
    r = sp.add_parser("report"); r.add_argument("--type", choices=["status","calendar","opportunities"], default="status"); r.add_argument("--act")
    c = sp.add_parser("calendar"); c.add_argument("--months", type=int, default=6)
    rn = sp.add_parser("render"); rn.add_argument("--template", required=True); rn.add_argument("--act", required=True); rn.add_argument("--festival", required=True)
    args = p.parse_args()
    if not args.command: p.print_help(); return 1
    return FestivalSubmitCLI().run(args)

if __name__ == "__main__": sys.exit(main())
