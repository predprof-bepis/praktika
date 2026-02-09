import sys
import os
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from dbtools import DB

DATES = ["2026-08-01", "2026-08-02", "2026-08-03", "2026-08-04"]
PROGRAMS = ["pm", "ivt", "itss", "ib"]
PROGRAM_IDS = {p: i + 1 for i, p in enumerate(PROGRAMS)}
PLACES = {"pm": 40, "ivt": 50, "itss": 30, "ib": 20}

COUNTS = {
    "2026-08-01": {"pm": 60, "ivt": 100, "itss": 50, "ib": 70},
    "2026-08-02": {"pm": 380, "ivt": 370, "itss": 350, "ib": 260},
    "2026-08-03": {"pm": 1000, "ivt": 1150, "itss": 1050, "ib": 800},
    "2026-08-04": {"pm": 1240, "ivt": 1390, "itss": 1240, "ib": 1190},
}

PAIR_INTERSECTIONS = {
    "2026-08-01": [("pm", "ivt", 22), ("pm", "itss", 17), ("pm", "ib", 20), ("ivt", "itss", 19), ("ivt", "ib", 22), ("itss", "ib", 17)],
    "2026-08-02": [("pm", "ivt", 190), ("pm", "itss", 190), ("pm", "ib", 150), ("ivt", "itss", 190), ("ivt", "ib", 140), ("itss", "ib", 120)],
    "2026-08-03": [("pm", "ivt", 760), ("pm", "itss", 600), ("pm", "ib", 410), ("ivt", "itss", 750), ("ivt", "ib", 460), ("itss", "ib", 500)],
    "2026-08-04": [("pm", "ivt", 1090), ("pm", "itss", 1110), ("pm", "ib", 1070), ("ivt", "itss", 1050), ("ivt", "ib", 1040), ("itss", "ib", 1090)],
}
TRIPLE_QUAD = {
    "2026-08-01": {"pm,ivt,itss": 5, "pm,ivt,ib": 5, "ivt,itss,ib": 5, "pm,itss,ib": 5, "pm,ivt,itss,ib": 3},
    "2026-08-02": {"pm,ivt,itss": 70, "pm,ivt,ib": 70, "ivt,itss,ib": 70, "pm,itss,ib": 70, "pm,ivt,itss,ib": 50},
    "2026-08-03": {"pm,ivt,itss": 500, "pm,ivt,ib": 260, "ivt,itss,ib": 300, "pm,itss,ib": 250, "pm,ivt,itss,ib": 200},
    "2026-08-04": {"pm,ivt,itss": 1020, "pm,ivt,ib": 1020, "ivt,itss,ib": 1000, "pm,itss,ib": 1040, "pm,ivt,itss,ib": 1000},
}


def _build_program_sets_for_date(date_str, max_applicant_id: int):
    counts = COUNTS[date_str]
    pairs = PAIR_INTERSECTIONS[date_str]
    triples = TRIPLE_QUAD[date_str]
    total_slots = sum(counts.values())
    pair_sum = sum(p[2] for p in pairs)
    quad = triples.get("pm,ivt,itss,ib", 0)
    triple_only = sum(v for k, v in triples.items() if k.count(",") == 2)
    n_unique = total_slots - pair_sum + triple_only - quad
    n_unique = max(n_unique, total_slots // 2)
    # не создаём applicant_id больше реально существующих абитуриентов
    n_unique = min(n_unique, max_applicant_id)
    pool = list(range(1, max_applicant_id + 1))
    random.shuffle(pool)

    in_all4 = min(triples.get("pm,ivt,itss,ib", 0), n_unique // 4)
    in_3 = min(triple_only, (n_unique - in_all4) // 3)
    in_2 = min(max(0, pair_sum - 3 * in_3 - 6 * in_all4), n_unique - in_all4 - in_3)
    in_1 = max(0, n_unique - in_all4 - in_3 - in_2)
    idx = [0]

    def next_aid():
        aid = pool[idx[0] % len(pool)]
        idx[0] += 1
        return aid

    sets = {p: set() for p in PROGRAMS}
    for _ in range(in_all4):
        aid = next_aid()
        for p in PROGRAMS:
            sets[p].add(aid)
    for _ in range(in_3):
        aid = next_aid()
        progs = random.sample(PROGRAMS, 3)
        for p in progs:
            sets[p].add(aid)
    for _ in range(in_2):
        aid = next_aid()
        progs = random.sample(PROGRAMS, 2)
        for p in progs:
            sets[p].add(aid)
    for _ in range(in_1):
        aid = next_aid()
        p = random.choice(PROGRAMS)
        sets[p].add(aid)
    for p in PROGRAMS:
        target = counts[p]
        lst = list(sets[p])
        while len(lst) < target:
            aid = next_aid()
            if aid not in sets[p]:
                lst.append(aid)
                sets[p].add(aid)
        while len(lst) > target:
            lst.pop(random.randrange(len(lst)))
        sets[p] = set(lst)
    return sets


def program_data(db):
    for name, seats in [("pm", 40), ("ivt", 50), ("itss", 30), ("ib", 20)]:
        db.run(
            "INSERT INTO programs(name, budget_seats) VALUES (?, ?)",
            name, seats
        )


def generate_applicants_and_applications(db, seed=42):
    random.seed(seed)
    max_applicants = 3500
    db.run("DELETE FROM applications")
    db.run("DELETE FROM sqlite_sequence WHERE name = 'applications'")
    db.run("DELETE FROM applicants")
    db.run("DELETE FROM sqlite_sequence WHERE name = 'applicants'")
    db.run("DELETE FROM programs")
    db.run("DELETE FROM sqlite_sequence WHERE name = 'programs'")
    program_data(db)

    applicants_batch = []
    for i in range(1, max_applicants + 1):
        p = random.randint(50, 100)
        r = random.randint(50, 100)
        m = random.randint(50, 100)
        ia = random.randint(0, 10)
        total = p + r + m + ia
        applicants_batch.append((p, r, m, ia, total))
    db.run_many(
        "INSERT INTO applicants (physics_or_ict, russian, math, individual_achievements, total_score) VALUES (?, ?, ?, ?, ?)",
        *applicants_batch
    )

    all_apps = []
    for date_str in DATES:
        # множества абитуриентов по программам формируются ТОЛЬКО из существующих id (1..max_applicants)
        sets = _build_program_sets_for_date(date_str, max_applicants)
        min_consent = {p: PLACES[p] + 1 for p in PROGRAMS} if date_str == "2026-08-04" else {}
        by_applicant = {}
        for prog in PROGRAMS:
            for aid in sets[prog]:
                by_applicant.setdefault(aid, []).append(prog)
        for aid, progs in by_applicant.items():
            random.shuffle(progs)
            consent = 1 if date_str == "2026-08-04" and random.random() < 0.6 else random.choice([0, 1])
            for prio, prog in enumerate(progs, 1):
                pid = PROGRAM_IDS[prog]
                all_apps.append((aid, pid, date_str, prio, consent))
        if date_str == "2026-08-04":
            for prog in PROGRAMS:
                pid = PROGRAM_IDS[prog]
                need = PLACES[prog] + 1
                rows_prog = [(r[0], r[4]) for r in all_apps if r[1] == pid and r[2] == date_str]
                with_consent = sum(1 for _, c in rows_prog if c == 1)
                if with_consent < need:
                    without = [i for i, r in enumerate(all_apps) if r[1] == pid and r[2] == date_str and r[4] == 0]
                    for j in range(need - with_consent):
                        if j < len(without):
                            idx = without[j]
                            all_apps[idx] = (all_apps[idx][0], all_apps[idx][1], all_apps[idx][2], all_apps[idx][3], 1)

    db.run_many(
        "INSERT INTO applications (applicant_id, program_id, date, priority, consent) VALUES (?, ?, ?, ?, ?)",
        *all_apps
    )


if __name__ == "__main__":
    db = DB()
    db.create_tables()
    generate_applicants_and_applications(db)
    print("OK")
