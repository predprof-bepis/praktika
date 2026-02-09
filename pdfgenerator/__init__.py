import pandas as pd
import matplotlib.pyplot as plt

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from datetime import datetime, date as date_type
from pathlib import Path

# Регистрация шрифта с кириллицей (чтобы не было чёрных квадратов)
def _register_cyrillic_font():
    font_name = "CyrillicFont"
    for path in [
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/liberation-sans/LiberationSans-Regular.ttf"),
    ]:
        if path.exists():
            try:
                pdfmetrics.registerFont(TTFont(font_name, str(path)))
                return font_name
            except Exception:
                continue
    return "Helvetica"


class PDFGenerator:
    def __init__(self, db_obj, dbman):
        self.db = db_obj
        self.dbman = dbman
        self.styles = getSampleStyleSheet()
        self._font_name = _register_cyrillic_font()
        self.styles["Normal"].fontName = self._font_name
        self.styles["Heading2"].fontName = self._font_name

        self.static_dir = Path("static")
        self.static_dir.mkdir(exist_ok=True)

    def generate_pdf(self, pdf_filename, date=None):
        if date is None:
            date = datetime.now()
        if isinstance(date, datetime):
            pass
        elif isinstance(date, date_type):
            date = datetime.combine(date, datetime.min.time())
        elif isinstance(date, str):
            date = date.strip()
            for fmt in (
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%Y-%m-%d",
                "%d.%m.%Y",
                "%d/%m/%Y",
            ):
                try:
                    date = datetime.strptime(date, fmt)
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(
                    f"date must be YYYY-MM-DD, DD.MM.YYYY or DD/MM/YYYY, got: {date!r}"
                )
        else:
            raise TypeError(
                f"date must be datetime, date or string (YYYY-MM-DD), got {type(date).__name__}: {date!r}"
            )
        programs_df = pd.DataFrame(
            self.db.get_program(),
            columns=["id", "name", "budget_seats"]
        )
        applicants_df = pd.DataFrame(
            self.db.get_applicant(),
            columns=[
                "id",
                "physics_or_ict",
                "russian",
                "math",
                "individual_achievements",
                "total_score"
            ]
        )
        applications_df = pd.DataFrame(
            self.db.get_application(),
            columns=["id", "applicant_id", "program_id", "date", "priority", "consent"]
        )
        date_str = date.strftime("%Y-%m-%d")
        applications_on_date = applications_df[applications_df["date"].astype(str) == date_str]

        apps_full = (
            applications_on_date
            .merge(applicants_df, left_on="applicant_id", right_on="id")
            .merge(programs_df, left_on="program_id", right_on="id", suffixes=("", "_program"))
        )
        apps_full_all_dates = (
            applications_df
            .merge(applicants_df, left_on="applicant_id", right_on="id")
            .merge(programs_df, left_on="program_id", right_on="id", suffixes=("", "_program"))
        )

        programs_full = pd.DataFrame(
            self.db.get_program(),
            columns=["id", "name", "budget_seats"]
        )
        enrollment = self._compute_global_enrollment(apps_full, programs_full)

        doc = SimpleDocTemplate(pdf_filename, pagesize=A4)
        story = []

        story.append(Paragraph(
            f"<b>Дата и время формирования отчёта:</b> {date:%d.%m.%Y %H:%M}",
            self.styles["Normal"]
        ))
        story.append(Spacer(1, 20))

        for _, prog in programs_df.iterrows():
            prog_name = prog["name"]
            prog_id = prog["id"]
            budget_seats = prog["budget_seats"]
            story.append(Paragraph(
                f"<b>Образовательная программа:</b> {prog_name}",
                self.styles["Heading2"]
            ))
            story.append(Spacer(1, 10))
            pass_score = self.dbman.count_pass_score(
                [prog_name],
                date=date.strftime("%Y-%m-%d")
            )
            pass_score_val = pass_score.get(prog_name)
            pass_score_display = "НЕДОБОР" if (pass_score_val is None or pass_score_val == 0) else pass_score_val
            story.append(Paragraph(
                f"Проходной балл: <b>{pass_score_display}</b>",
                self.styles["Normal"]
            ))
            story.append(Spacer(1, 10))

            graph_path = self.plot_dynamics(apps_full_all_dates, prog_id, prog_name)

            story.append(Image(str(graph_path), width=400, height=250))
            story.append(Spacer(1, 15))

            table_rows = self.enrolled_list_with_status(
                apps_full, prog_id, budget_seats, enrollment
            )
            enrolled_only = enrollment.get("by_program", {}).get(prog_id, [])

            story.append(Paragraph("<b>Список зачисленных</b>", self.styles["Heading2"]))
            story.append(Spacer(1, 6))
            if enrolled_only:
                enc_data = [[
                    Paragraph("ID абитуриента", self.styles["Normal"]),
                    Paragraph("Сумма баллов", self.styles["Normal"]),
                    Paragraph("Приоритет", self.styles["Normal"]),
                ]]
                for row in enrolled_only:
                    enc_data.append([
                        Paragraph(str(row["applicant_id"]), self.styles["Normal"]),
                        Paragraph(str(row["total_score"]), self.styles["Normal"]),
                        Paragraph(str(int(row["priority"])), self.styles["Normal"]),
                    ])
                enc_table = Table(enc_data, colWidths=[100, 100, 80])
                enc_table.setStyle(TableStyle([
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ]))
                story.append(enc_table)
            else:
                story.append(Paragraph("Нет зачисленных.", self.styles["Normal"]))
            story.append(Spacer(1, 15))

            story.append(Paragraph("<b>Статистика по приоритетам</b>", self.styles["Heading2"]))
            story.append(Spacer(1, 6))
            prio_stats = self.priority_stats(apps_full, prog_id, enrollment)
            prio_data = [[
                Paragraph("Приоритет", self.styles["Normal"]),
                Paragraph("Подано заявлений", self.styles["Normal"]),
                Paragraph("Зачислено", self.styles["Normal"]),
            ]]
            for p in [1, 2, 3, 4]:
                prio_data.append([
                    Paragraph(str(p), self.styles["Normal"]),
                    Paragraph(str(int(prio_stats["applied"].get(p, 0))), self.styles["Normal"]),
                    Paragraph(str(int(prio_stats["enrolled"].get(p, 0))), self.styles["Normal"]),
                ])
            prio_table = Table(prio_data, colWidths=[80, 120, 90])
            prio_table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]))
            story.append(prio_table)
            story.append(Spacer(1, 15))

            # Ранее здесь выводился пофамильный список абитуриентов с согласием
            # (принят / не принят). По требованиям заказчика этот список
            # из отчёта убран, чтобы в PDF не было персональных данных
            # абитуриентов с согласием. Агрегированная статистика остаётся ниже.
            story.append(Spacer(1, 25))

        story.append(Paragraph("<b>Общая статистика по ОП (п.2.14.e)</b>", self.styles["Heading2"]))
        story.append(Spacer(1, 10))
        prog_names = ["pm", "ivt", "itss", "ib"]
        header = [Paragraph("", self.styles["Normal"])] + [
            Paragraph(p.upper() if p != "itss" else "ИТСС", self.styles["Normal"]) for p in prog_names
        ]
        header[1], header[2] = Paragraph("ПМ", self.styles["Normal"]), Paragraph("ИВТ", self.styles["Normal"])
        header[3], header[4] = Paragraph("ИТСС", self.styles["Normal"]), Paragraph("ИБ", self.styles["Normal"])
        rows_stats = [header]
        programs_list = list(programs_df.itertuples(index=False))
        for row_name, get_vals in [
            ("Общее кол-во заявлений", lambda pid: len(apps_full[apps_full["program_id"] == pid])),
            ("Количество мест на ОП", lambda pid: next((p.budget_seats for p in programs_list if p.id == pid), 0)),
            ("Кол-во заявлений 1-го приоритета", lambda pid: len(apps_full[(apps_full["program_id"] == pid) & (apps_full["priority"] == 1)])),
            ("Кол-во заявлений 2-го приоритета", lambda pid: len(apps_full[(apps_full["program_id"] == pid) & (apps_full["priority"] == 2)])),
            ("Кол-во заявлений 3-го приоритета", lambda pid: len(apps_full[(apps_full["program_id"] == pid) & (apps_full["priority"] == 3)])),
            ("Кол-во заявлений 4-го приоритета", lambda pid: len(apps_full[(apps_full["program_id"] == pid) & (apps_full["priority"] == 4)])),
        ]:
            row = [Paragraph(row_name, self.styles["Normal"])]
            for p in programs_list:
                row.append(Paragraph(str(get_vals(p.id)), self.styles["Normal"]))
            rows_stats.append(row)
        by_program = enrollment.get("by_program", {})
        for prio in [1, 2, 3, 4]:
            row = [Paragraph(f"Кол-во зачисленных {prio}-го приоритета", self.styles["Normal"])]
            for p in programs_list:
                lst = by_program.get(p.id, [])
                row.append(Paragraph(str(sum(1 for x in lst if x.get("priority") == prio)), self.styles["Normal"]))
            rows_stats.append(row)
        table_stats = Table(rows_stats, colWidths=[180, 50, 50, 50, 50])
        table_stats.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ]))
        story.append(table_stats)
        story.append(Spacer(1, 20))

        doc.build(story)

    def plot_dynamics(self, apps_full, program_id, program_name):
        days = sorted(apps_full["date"].unique())
        values = []

        for day in days:
            day_str = day if isinstance(day, str) else (day.strftime("%Y-%m-%d") if hasattr(day, "strftime") else str(day))
            score_dict = self.dbman.count_pass_score([program_name], date=day_str)
            score = score_dict.get(program_name, "НЕДОБОР")
            values.append(score if isinstance(score, (int, float)) else 0)

        plt.figure()
        plt.plot(days, values, marker="o")
        plt.title(f"Динамика проходного балла ({program_name})")
        plt.xlabel("День")
        plt.ylabel("Баллы")
        plt.grid()
        plt.tight_layout()

        filename = self.static_dir / f"{program_id}.png"
        plt.savefig(filename)
        plt.close()

        return filename

    @staticmethod
    def enrolled_list(apps_full, program_id, budget):
        accepted = (
            apps_full[
                (apps_full["program_id"] == program_id) &
                (apps_full["consent"] == 1)
            ]
            .sort_values("total_score", ascending=False)
        )

        return accepted.head(budget)[
            ["applicant_id", "total_score"]
        ].to_dict("records")

    @staticmethod
    def _compute_global_enrollment(apps_full, programs_df):

        budget = programs_df.set_index("id")["budget_seats"].to_dict()
        with_consent = apps_full[apps_full["consent"] == 1].copy()
        enrolled_applicant = {}
        by_program = {pid: [] for pid in programs_df["id"]}
        places_left = budget.copy()

        for priority in [1, 2, 3, 4]:
            cand = with_consent[
                (with_consent["priority"] == priority) &
                (~with_consent["applicant_id"].isin(enrolled_applicant))
            ]
            cand = cand.sort_values("total_score", ascending=False)
            for _, row in cand.iterrows():
                aid, pid = row["applicant_id"], row["program_id"]
                if aid in enrolled_applicant:
                    continue
                if places_left.get(pid, 0) <= 0:
                    continue
                enrolled_applicant[aid] = pid
                by_program[pid].append({
                    "applicant_id": aid,
                    "total_score": row["total_score"],
                    "priority": row["priority"],
                })
                places_left[pid] -= 1

        return {"by_program": by_program, "applicant_to_program": enrolled_applicant}

    @staticmethod
    def enrolled_list_with_status(apps_full, program_id, budget, enrollment):
        applicant_to_program = enrollment.get("applicant_to_program", {})
        with_consent = (
            apps_full[
                (apps_full["program_id"] == program_id) &
                (apps_full["consent"] == 1)
            ]
            .sort_values("total_score", ascending=False)
            .reset_index(drop=True)
        )
        rows = []
        for _, row in with_consent.iterrows():
            aid = row["applicant_id"]
            has_consent = row["consent"] == 1
            accepted_here = applicant_to_program.get(aid) == program_id
            rows.append({
                "applicant_id": aid,
                "total_score": row["total_score"],
                "priority": row["priority"],
                "accepted": has_consent and accepted_here,
            })
        return rows

    @staticmethod
    def priority_stats(apps_full, program_id, enrollment):
        prog = apps_full[apps_full["program_id"] == program_id]
        applied = prog.groupby("priority").size().reindex([1, 2, 3, 4], fill_value=0)
        by_program = enrollment.get("by_program", {}).get(program_id, [])
        if by_program:
            enrolled_df = pd.DataFrame(by_program)
            enrolled_by_prio = enrolled_df.groupby("priority").size().reindex([1, 2, 3, 4], fill_value=0)
        else:
            enrolled_by_prio = pd.Series({p: 0 for p in [1, 2, 3, 4]})
        return {"applied": applied, "enrolled": enrolled_by_prio}
