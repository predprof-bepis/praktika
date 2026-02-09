import argparse
import csv
import os
import sys


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dbtools import DB  # noqa: E402


def _write_csv(path: str, headers: list[str], rows: list[tuple]):
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    # utf-8-sig: корректно открывается в Excel (RU локаль)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        if headers:
            w.writerow(headers)
        w.writerows(rows)


def export_programs(db: DB) -> tuple[list[str], list[tuple]]:
    """Простой экспорт таблицы programs."""
    rows = db.run("SELECT id, name, budget_seats FROM programs ORDER BY id")
    return ["id", "name", "budget_seats"], rows


def export_applicants(db: DB) -> tuple[list[str], list[tuple]]:
    """Простой экспорт таблицы applicants."""
    rows = db.run(
        "SELECT id, physics_or_ict, russian, math, individual_achievements, total_score "
        "FROM applicants ORDER BY id"
    )
    return ["id", "physics_or_ict", "russian", "math", "individual_achievements", "total_score"], rows


def export_applications(db: DB) -> tuple[list[str], list[tuple]]:
    """Простой экспорт таблицы applications."""
    rows = db.run(
        "SELECT id, applicant_id, program_id, date, priority, consent "
        "FROM applications ORDER BY id"
    )
    return ["id", "applicant_id", "program_id", "date", "priority", "consent"], rows


def main():
    p = argparse.ArgumentParser(description="Простой экспорт таблиц в CSV из database.db")
    p.add_argument("--db", default="database.db", help="Путь к sqlite БД (по умолчанию: database.db)")
    p.add_argument(
        "--table",
        choices=["programs", "applicants", "applications"],
        help="Какую таблицу экспортировать",
    )
    # для обратной совместимости со старым интерфейсом
    p.add_argument(
        "--dataset",
        choices=["programs", "applicants", "applications", "contest_list"],
        help="УСТАРЕВШЕЕ: старый параметр, теперь используется только для простых таблиц",
    )
    p.add_argument("--out", default=None, help="Куда сохранить CSV (если не задано — сформируется автоматически)")
    args = p.parse_args()

    # определяем, что именно экспортировать
    table = args.table or args.dataset
    if table is None:
        raise SystemExit("Нужно указать --table (programs/applicants/applications)")
    if table == "contest_list":
        raise SystemExit("export_csv теперь работает только как простой экспорт таблиц (programs/applicants/applications)")

    db = DB(args.db)

    if table == "programs":
        headers, rows = export_programs(db)
        out = args.out or "programs.csv"
    elif table == "applicants":
        headers, rows = export_applicants(db)
        out = args.out or "applicants.csv"
    else:  # applications
        headers, rows = export_applications(db)
        out = args.out or "applications.csv"

    _write_csv(out, headers, rows)
    print(f"OK: wrote {len(rows)} rows -> {out}")


if __name__ == "__main__":
    main()

