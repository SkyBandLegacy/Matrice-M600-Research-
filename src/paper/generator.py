"""
Academic Paper Template Generator.

Generates a fully-structured APA-formatted Word document pre-populated
from the research database. Sections auto-fill from relevant DB categories.

Output: A .docx file ready to edit in Word / LibreOffice.
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------
# Paper section definitions
# -----------------------------------------------------------------------

@dataclass
class PaperSection:
    heading: str
    db_category: Optional[str]       # which DB category to draw from
    db_product: Optional[str]        # which product to filter
    db_keyword: Optional[str]        # optional keyword filter
    placeholder: str                 # guidance text shown when DB is empty
    max_items: int = 5


PAPER_SECTIONS = [
    PaperSection(
        heading="Abstract",
        db_category=None,
        db_product=None,
        db_keyword=None,
        placeholder=(
            "[Write a 150–250 word abstract summarising: (1) the research objective, "
            "(2) the DJI M600 / GS Pro system architecture, (3) methodology, "
            "(4) key findings, and (5) conclusions.]"
        ),
        max_items=0,
    ),
    PaperSection(
        heading="1. Introduction",
        db_category="use_case",
        db_product=None,
        db_keyword="M600 unmanned aerial",
        placeholder=(
            "[Introduce the DJI Matrice 600 Pro as a research platform. "
            "Discuss the growing importance of heavy-lift UAVs in academic and "
            "industrial research. State the research gap and objectives.]"
        ),
        max_items=3,
    ),
    PaperSection(
        heading="2. Background and Literature Review",
        db_category=None,
        db_product=None,
        db_keyword="DJI UAV research",
        placeholder=(
            "[Review related work on: (1) UAV system architectures, "
            "(2) DJI platform research, (3) autonomous flight systems, "
            "(4) GCS software for mission planning.]"
        ),
        max_items=5,
    ),
    PaperSection(
        heading="3. System Architecture",
        db_category="hardware",
        db_product="M600",
        db_keyword=None,
        placeholder=(
            "[Describe the complete M600 system architecture: airframe, propulsion, "
            "power system, avionics, and payload interfaces.]"
        ),
        max_items=4,
    ),
    PaperSection(
        heading="3.1  Hardware Components",
        db_category="hardware",
        db_product="M600",
        db_keyword="component",
        placeholder=(
            "[Detail each hardware component: hexacopter frame, DJI A3 flight controller, "
            "TB47S / TB48S batteries, E2000 propulsion system, Lightbridge 2 video link.]"
        ),
        max_items=4,
    ),
    PaperSection(
        heading="3.2  Communication Protocols",
        db_category="protocol",
        db_product="M600",
        db_keyword=None,
        placeholder=(
            "[Describe all communication protocols: DJI Lightbridge 2 datalink, "
            "MAVLink protocol stack, Onboard SDK (OSDK) serial interface, "
            "CAN bus between flight controller and ESCs, RC link frequencies.]"
        ),
        max_items=4,
    ),
    PaperSection(
        heading="3.3  Software Architecture",
        db_category="software",
        db_product=None,
        db_keyword=None,
        placeholder=(
            "[Cover: DJI Pilot app, Mobile SDK, Onboard SDK, GS Pro app architecture, "
            "DJI Assistant 2 for firmware management, SDK communication layer.]"
        ),
        max_items=3,
    ),
    PaperSection(
        heading="4. DJI GS Pro — Mission Planning System",
        db_category="use_case",
        db_product="GS Pro",
        db_keyword="mission",
        placeholder=(
            "[Describe GS Pro: waypoint mission creation, flight path optimisation, "
            "area scanning modes, 3D mapping missions, live telemetry display, "
            "connection to M600 via Lightbridge 2.]"
        ),
        max_items=4,
    ),
    PaperSection(
        heading="5. Technical Specifications",
        db_category="spec",
        db_product="M600",
        db_keyword=None,
        placeholder=(
            "[Present key specs in a table: max takeoff weight, payload capacity, "
            "max flight time, max speed, operating frequency, GPS accuracy, "
            "hovering accuracy, supported payloads.]"
        ),
        max_items=4,
    ),
    PaperSection(
        heading="6. Use Cases and Applications",
        db_category="use_case",
        db_product=None,
        db_keyword="application",
        placeholder=(
            "[Survey real-world applications: aerial cinematography, precision agriculture, "
            "infrastructure inspection, disaster response, scientific data collection.]"
        ),
        max_items=4,
    ),
    PaperSection(
        heading="7. Discussion",
        db_category=None,
        db_product=None,
        db_keyword=None,
        placeholder=(
            "[Synthesise findings. Compare M600 capabilities against research requirements. "
            "Identify limitations and potential improvements. Discuss the role of GS Pro "
            "in enabling autonomous research missions.]"
        ),
        max_items=0,
    ),
    PaperSection(
        heading="8. Conclusion",
        db_category=None,
        db_product=None,
        db_keyword=None,
        placeholder=(
            "[Summarise contributions. Restate the significance of the M600 platform "
            "for research. Suggest future work.]"
        ),
        max_items=0,
    ),
]


# -----------------------------------------------------------------------
# Word document builder
# -----------------------------------------------------------------------

def _strip_markdown(text: str) -> str:
    """Remove simple markdown (* and **) from text."""
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    return text


class PaperGenerator:
    def __init__(self, db, citation_manager=None):
        """
        db: ResearchDatabase instance
        citation_manager: CitationManager instance (optional, for inline refs)
        """
        self.db = db
        self.cm = citation_manager

    def _fetch_section_content(self, sec: PaperSection) -> list[dict]:
        if sec.max_items == 0:
            return []
        return self.db.query_items(
            product=sec.db_product,
            category=sec.db_category,
            keyword=sec.db_keyword,
            limit=sec.max_items,
        )

    def generate_docx(self, output_path: Path, title: str = "DJI Matrice 600 Pro and GS Pro: System Architecture and Research Applications"):
        try:
            from docx import Document
            from docx.shared import Pt, Inches, RGBColor
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            from docx.enum.style import WD_STYLE_TYPE
            from docx.oxml.ns import qn
            from docx.oxml import OxmlElement
        except ImportError:
            logger.error("python-docx is required. Run: pip install python-docx")
            return

        output_path.parent.mkdir(parents=True, exist_ok=True)
        doc = Document()

        # ---- Page margins (APA: 1 inch all sides) ----
        for section in doc.sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)

        # ---- Styles ----
        normal = doc.styles["Normal"]
        normal.font.name = "Times New Roman"
        normal.font.size = Pt(12)

        # ---- Title page ----
        doc.add_paragraph()  # blank line
        title_para = doc.add_paragraph(title)
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title_para.runs[0]
        title_run.bold = True
        title_run.font.size = Pt(14)

        doc.add_paragraph()
        author_para = doc.add_paragraph("[Author Name(s)]")
        author_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        affil_para = doc.add_paragraph("[Department, University / Institution]")
        affil_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        course_para = doc.add_paragraph("[Course / Journal Name]")
        course_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        date_para = doc.add_paragraph("[Date]")
        date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        doc.add_page_break()

        # ---- Sections ----
        for sec in PAPER_SECTIONS:
            # Section heading
            level = 1 if sec.heading[0].isdigit() and "." not in sec.heading.split()[0] else 2
            if sec.heading == "Abstract":
                level = 1
            heading = doc.add_heading(sec.heading, level=level)
            heading.runs[0].font.name = "Times New Roman"

            items = self._fetch_section_content(sec)

            if items:
                for item in items:
                    # Source attribution note
                    source_note = doc.add_paragraph()
                    note_run = source_note.add_run(
                        f"[Source: {item['source_name']} — {item['title'][:80]}]"
                    )
                    note_run.italic = True
                    note_run.font.color.rgb = RGBColor(0x80, 0x80, 0x80)
                    note_run.font.size = Pt(10)

                    # Content paragraph
                    content = _strip_markdown(item["content_preview"])
                    para = doc.add_paragraph(content)
                    para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                    para.paragraph_format.first_line_indent = Inches(0.5)
                    para.paragraph_format.space_after = Pt(12)
            else:
                # Placeholder guidance
                para = doc.add_paragraph(sec.placeholder)
                para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                para.runs[0].italic = True
                para.runs[0].font.color.rgb = RGBColor(0x60, 0x60, 0xC0)
                para.paragraph_format.first_line_indent = Inches(0.5)
                para.paragraph_format.space_after = Pt(12)

            doc.add_paragraph()  # spacing

        # ---- References section ----
        doc.add_page_break()
        ref_heading = doc.add_heading("References", level=1)
        ref_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
        ref_heading.runs[0].font.name = "Times New Roman"

        if self.cm:
            refs = self.cm.get_apa_bibliography()
            for ref in refs:
                para = doc.add_paragraph()
                para.alignment = WD_ALIGN_PARAGRAPH.LEFT
                fmt = para.paragraph_format
                fmt.left_indent = Inches(0.5)
                fmt.first_line_indent = Inches(-0.5)
                fmt.space_after = Pt(12)

                parts = re.split(r"(\*[^*]+\*)", ref)
                for part in parts:
                    if part.startswith("*") and part.endswith("*"):
                        run = para.add_run(part[1:-1])
                        run.italic = True
                    else:
                        para.add_run(part)
        else:
            placeholder = doc.add_paragraph(
                "[References will be auto-populated once scraping is complete. "
                "Run: python -m src.citations.cli --format docx to generate.]"
            )
            placeholder.runs[0].italic = True
            placeholder.runs[0].font.color.rgb = RGBColor(0x60, 0x60, 0xC0)

        doc.save(str(output_path))
        logger.info("Paper template saved to %s", output_path)

    def generate_txt_outline(self, output_path: Path):
        """Generate a plain-text outline with DB content previews."""
        lines = []
        lines.append("DJI M600 / GS Pro — Research Paper Outline")
        lines.append("=" * 70)
        lines.append("")

        for sec in PAPER_SECTIONS:
            lines.append(f"\n{'=' * 60}")
            lines.append(sec.heading.upper())
            lines.append("=" * 60)

            items = self._fetch_section_content(sec)
            if items:
                for item in items:
                    lines.append(f"\n  [From: {item['source_name']}]")
                    lines.append(f"  {item['title']}")
                    lines.append(f"  {item['content_preview'][:250]}")
            else:
                lines.append(f"\n  {sec.placeholder}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines), encoding="utf-8")
        logger.info("Text outline saved to %s", output_path)
