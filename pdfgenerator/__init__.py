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

from datetime import datetime
from pathlib import Path

# Регистрация шрифта с кириллицей (чтобы не было чёрных квадратов)
def _register_cyrillic_font():
    font_name = "CyrillicFont"
    for path in [
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
    ]:
        if path.exists():
            try:
                pdfmetrics.registerFont(TTFont(font_name, str(path)))
                return font_name
            except Exception:
                continue
    return "Helvetica"  # fallback без кириллицы


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

    def generate_pdf(self, program, pdf_filename, date=None):
        if date is None:
            date = datetime.now()
        if not isinstance(date, datetime):
            try:
                date = datetime.strptime(date, "%Y-%m-%d")
            except:
                raise TypeError("date must be datetime")
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

        apps_full = (
            applications_df
            .merge(applicants_df, left_on="applicant_id", right_on="id")
            .merge(programs_df, left_on="program_id", right_on="id", suffixes=("", "_program"))
        )

        if program is not None:
            if isinstance(program, str):
                program = [program]
            programs_df = programs_df[programs_df["name"].isin(program)]

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
                self.dbman.db_filter([prog_name], date=date.strftime("%Y-%m-%d"))
            )
            pass_score_val = pass_score.get(prog_name)
            pass_score_display = "НЕДОБОР" if (pass_score_val is None or pass_score_val == 0) else pass_score_val
            story.append(Paragraph(
                f"Проходной балл: <b>{pass_score_display}</b>",
                self.styles["Normal"]
            ))
            story.append(Spacer(1, 10))

            graph_path = self.plot_dynamics(apps_full, prog_id, prog_name)

            story.append(Image(str(graph_path), width=400, height=250))
            story.append(Spacer(1, 15))

            table_rows = self.enrolled_list_with_status(apps_full, prog_id, budget_seats)
            enrolled_only = [r for r in table_rows if r["accepted"]]

            # Список зачисленных по ОП
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

            # Статистика по приоритетам
            story.append(Paragraph("<b>Статистика по приоритетам</b>", self.styles["Heading2"]))
            story.append(Spacer(1, 6))
            prio_stats = self.priority_stats(apps_full, prog_id, budget_seats)
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

            # Таблица: все с согласием + принят/нет
            story.append(Paragraph("<b>Абитуриенты с согласием (принят / не принят)</b>", self.styles["Heading2"]))
            story.append(Spacer(1, 6))
            table_data = [[
                Paragraph("ID абитуриента", self.styles["Normal"]),
                Paragraph("Сумма баллов", self.styles["Normal"]),
                Paragraph("Приоритет", self.styles["Normal"]),
                Paragraph("Принят", self.styles["Normal"]),
            ]]
            for row in table_rows:
                table_data.append([
                    Paragraph(str(row["applicant_id"]), self.styles["Normal"]),
                    Paragraph(str(row["total_score"]), self.styles["Normal"]),
                    Paragraph(str(int(row["priority"])), self.styles["Normal"]),
                    Paragraph("Да" if row["accepted"] else "Нет", self.styles["Normal"]),
                ])
            table = Table(table_data, colWidths=[100, 100, 80, 80])
            table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]))
            story.append(table)
            story.append(Spacer(1, 25))

        doc.build(story)

    def plot_dynamics(self, apps_full, program_id, program_name):
        days = sorted(apps_full["date"].unique())
        values = []

        for day in days:
            score_dict = self.dbman.count_pass_score(
                [program_name],
                self.dbman.db_filter([program_name], date=day)
            )
            score = score_dict.get(program_name, 0)
            values.append(score)

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
    def enrolled_list_with_status(apps_full, program_id, budget):
        with_consent = (
            apps_full[
                (apps_full["program_id"] == program_id) &
                (apps_full["consent"] == 1)
            ]
            .sort_values("total_score", ascending=False)
            .reset_index(drop=True)
        )
        rows = []
        for k, (_, row) in enumerate(with_consent.iterrows()):
            has_consent = row["consent"] == 1
            in_budget = k < budget
            rows.append({
                "applicant_id": row["applicant_id"],
                "total_score": row["total_score"],
                "priority": row["priority"],
                "accepted": has_consent and in_budget,
            })
        return rows

    @staticmethod
    def priority_stats(apps_full, program_id, budget):
        prog = apps_full[apps_full["program_id"] == program_id]
        applied = prog.groupby("priority").size().reindex([1, 2, 3, 4], fill_value=0)
        with_consent = prog[prog["consent"] == 1].sort_values("total_score", ascending=False)
        enrolled = with_consent.head(budget)
        enrolled_by_prio = enrolled.groupby("priority").size().reindex([1, 2, 3, 4], fill_value=0)
        return {"applied": applied, "enrolled": enrolled_by_prio}
