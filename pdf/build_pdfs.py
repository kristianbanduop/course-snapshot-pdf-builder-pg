from pathlib import Path
import json

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Table,
    TableStyle,
)

# --------------------------------------------------
# Paths
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "extracted.json"
OUTPUT_DIR = BASE_DIR / "output" / "pdfs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# Faculty mapping
# --------------------------------------------------
FACULTY_MAP = {
    "BAL": "Faculty of Business and Law",
    "CCI": "Faculty of Creative and Cultural Industries",
    "HSS": "Faculty of Humanities and Social Sciences",
    "SAH": "Faculty of Science and Health",
    "TEC": "Faculty of Technology",
}

PURPLE = colors.HexColor("#621360")


def build_pdf_for_school(school_name, courses):
    faculty_code = courses[0].get("faculty", "").strip()
    faculty_name = FACULTY_MAP.get(faculty_code, faculty_code)

    output_file = OUTPUT_DIR / f"{school_name.replace(' ', '_')}_Course_Snapshot.pdf"

    styles = getSampleStyleSheet()
    styles["Normal"].alignment = TA_LEFT

    styles.add(ParagraphStyle(
        name="FacultyTitle",
        fontSize=22,
        leading=26,
        textColor=PURPLE,
        fontName="Helvetica-Bold",
        spaceAfter=18,
    ))

    styles.add(ParagraphStyle(
        name="SchoolTitle",
        fontSize=16,
        leading=20,
        textColor=PURPLE,
        fontName="Helvetica-Bold",
        spaceAfter=18,
    ))

    styles.add(ParagraphStyle(
        name="CourseTitle",
        fontSize=14,
        leading=18,
        textColor=PURPLE,
        fontName="Helvetica-Bold",
        spaceBefore=18,
        spaceAfter=8,
    ))

    styles.add(ParagraphStyle(
        name="SectionHeading",
        fontSize=11,
        leading=14,
        textColor=PURPLE,
        fontName="Helvetica-Bold",
        spaceBefore=12,
        spaceAfter=6,
    ))

    doc = SimpleDocTemplate(
        str(output_file),
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    story = []

    # --------------------------------------------------
    # Title page
    # --------------------------------------------------
    story.append(Paragraph(faculty_name, styles["FacultyTitle"]))
    story.append(Paragraph(school_name, styles["SchoolTitle"]))

    intro = [
        "Course and module updates – Course snapshot for September 2026 entry",
        "We’re pleased to share these updates to your chosen course(s).",
        "Some modules have been refined into 15-credit increments (15, 30, 45, 60, or 120 credits) "
        "to provide a more flexible and enriching learning experience.",
        "This document provides a clear snapshot of course information at the time of publication for your reference.",
        "Publication date: February 2026",
    ]

    for line in intro:
        story.append(Paragraph(line, styles["Normal"]))
        story.append(Spacer(1, 8))

    story.append(PageBreak())

    # --------------------------------------------------
    # TABLE OF CONTENTS (MANUAL, WORKING)
    # --------------------------------------------------
    story.append(Paragraph("Contents", styles["SectionHeading"]))
    story.append(Spacer(1, 12))

    for idx, course in enumerate(courses):
        anchor = f"course_{idx}"
        toc_link = f'<link href="#{anchor}">{course["title"]}</link>'
        story.append(Paragraph(toc_link, styles["Normal"]))
        story.append(Spacer(1, 6))

    story.append(PageBreak())

    # --------------------------------------------------
    # Courses
    # --------------------------------------------------
    for idx, course in enumerate(courses):
        anchor = f"course_{idx}"

        story.append(Paragraph(
            f'<a name="{anchor}"/>{course["title"]}',
            styles["CourseTitle"]
        ))

        story.append(Paragraph("Overview", styles["SectionHeading"]))
        story.append(Paragraph(course.get("overview", ""), styles["Normal"]))

        story.append(Paragraph("Course highlights", styles["SectionHeading"]))
        for h in course.get("highlights", []):
            story.append(Paragraph(f"• {h}", styles["Normal"]))

        story.append(Paragraph("Modules", styles["SectionHeading"]))

        for year, modules in course.get("modules", {}).items():
            story.append(Paragraph(year, styles["SectionHeading"]))

            table_data = [["Module name", "Credits", "Core / Optional", "Description"]]

            for m in modules:
                table_data.append([
                    Paragraph(m["module_name"], styles["Normal"]),
                    Paragraph(str(m["credits"]), styles["Normal"]),
                    Paragraph(m["core_optional"], styles["Normal"]),
                    Paragraph(m["description"], styles["Normal"]),
                ])

            table = Table(
                table_data,
                colWidths=[100, 50, 90, None],
                repeatRows=1,
            )

            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))

            story.append(table)
            story.append(Spacer(1, 12))

        story.append(PageBreak())

    doc.build(story)


def main():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    schools = {}
    for course in data:
        schools.setdefault(course["school"], []).append(course)

    for school, courses in schools.items():
        build_pdf_for_school(school, courses)


if __name__ == "__main__":
    main()
