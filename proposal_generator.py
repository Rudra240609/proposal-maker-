"""
proposal_generator.py
Generates a professional solar proposal PDF matching the EnergyBae style.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.platypus.flowables import HRFlowable
from io import BytesIO
import math

# ── Brand colours ─────────────────────────────────────────────────────────────
GREEN      = colors.HexColor("#2E7D32")
LIGHT_GREEN = colors.HexColor("#66BB6A")
DARK_BLUE  = colors.HexColor("#0D47A1")
TABLE_BLUE = colors.HexColor("#1565C0")
TABLE_BLUE_LIGHT = colors.HexColor("#E3F2FD")
HEADER_BG  = colors.HexColor("#1B5E20")
WHITE      = colors.white
GREY       = colors.HexColor("#F5F5F5")
DARK_GREY  = colors.HexColor("#424242")
ORANGE     = colors.HexColor("#E65100")

PAGE_W, PAGE_H = A4
MARGIN = 20 * mm


def num_to_words(n):
    """Convert integer to Indian number words."""
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven",
            "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen",
            "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty",
            "Sixty", "Seventy", "Eighty", "Ninety"]

    def below_thousand(num):
        if num == 0:
            return ""
        elif num < 20:
            return ones[num]
        elif num < 100:
            return tens[num // 10] + (" " + ones[num % 10] if num % 10 else "")
        else:
            return ones[num // 100] + " Hundred" + (" " + below_thousand(num % 100) if num % 100 else "")

    if n == 0:
        return "Zero"
    parts = []
    crore = n // 10000000
    n %= 10000000
    lakh = n // 100000
    n %= 100000
    thousand = n // 1000
    n %= 1000
    remainder = n

    if crore:   parts.append(below_thousand(crore) + " Crore")
    if lakh:    parts.append(below_thousand(lakh) + " Lakh")
    if thousand: parts.append(below_thousand(thousand) + " Thousand")
    if remainder: parts.append(below_thousand(remainder))
    return " ".join(parts)


def make_styles():
    base = getSampleStyleSheet()

    styles = {
        "cover_title": ParagraphStyle("cover_title",
            fontSize=28, fontName="Helvetica-Bold",
            textColor=DARK_BLUE, alignment=TA_CENTER, spaceAfter=4),

        "cover_sub": ParagraphStyle("cover_sub",
            fontSize=18, fontName="Helvetica",
            textColor=DARK_GREY, alignment=TA_CENTER, spaceAfter=8),

        "section_header": ParagraphStyle("section_header",
            fontSize=12, fontName="Helvetica-Bold",
            textColor=GREEN, spaceBefore=10, spaceAfter=4),

        "body": ParagraphStyle("body",
            fontSize=9, fontName="Helvetica",
            textColor=DARK_GREY, spaceAfter=4, leading=14,
            alignment=TA_JUSTIFY),

        "table_header": ParagraphStyle("table_header",
            fontSize=9, fontName="Helvetica-Bold",
            textColor=WHITE, alignment=TA_LEFT),

        "table_cell": ParagraphStyle("table_cell",
            fontSize=9, fontName="Helvetica",
            textColor=DARK_GREY),

        "table_cell_bold": ParagraphStyle("table_cell_bold",
            fontSize=9, fontName="Helvetica-Bold",
            textColor=DARK_GREY),

        "highlight": ParagraphStyle("highlight",
            fontSize=10, fontName="Helvetica-Bold",
            textColor=ORANGE),

        "small": ParagraphStyle("small",
            fontSize=8, fontName="Helvetica",
            textColor=DARK_GREY, spaceAfter=2),

        "center": ParagraphStyle("center",
            fontSize=9, fontName="Helvetica",
            alignment=TA_CENTER, textColor=DARK_GREY),

        "green_bold": ParagraphStyle("green_bold",
            fontSize=9, fontName="Helvetica-Bold",
            textColor=GREEN),
    }
    return styles


def header_band(text, styles):
    """Green header band paragraph."""
    data = [[Paragraph(text, ParagraphStyle("hdr",
        fontSize=11, fontName="Helvetica-Bold", textColor=WHITE))]]
    t = Table(data, colWidths=[PAGE_W - 2 * MARGIN])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GREEN),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def info_table(rows, styles, col_widths=None):
    """Two-column key-value table."""
    w = PAGE_W - 2 * MARGIN
    if col_widths is None:
        col_widths = [w * 0.45, w * 0.55]
    data = [[Paragraph(k, styles["table_cell_bold"]),
             Paragraph(v, styles["table_cell"])] for k, v in rows]
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), WHITE),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, TABLE_BLUE_LIGHT]),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#BBDEFB")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#BBDEFB")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def generate_proposal_pdf(d: dict) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=MARGIN, bottomMargin=MARGIN)
    s = make_styles()
    story = []
    w = PAGE_W - 2 * MARGIN

    # ── PAGE 1 : Cover ────────────────────────────────────────────────────────
    # Top green bar
    top_bar_data = [[
        Paragraph(d["company_tagline"], ParagraphStyle("tb",
            fontSize=10, fontName="Helvetica-Bold", textColor=WHITE)),
        Paragraph(d["company_name"], ParagraphStyle("tb2",
            fontSize=10, fontName="Helvetica-Bold", textColor=WHITE,
            alignment=TA_RIGHT))
    ]]
    top_bar = Table(top_bar_data, colWidths=[w * 0.6, w * 0.4])
    top_bar.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GREEN),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(top_bar)
    story.append(Spacer(1, 12 * mm))

    story.append(Paragraph("Proposal", s["cover_title"]))
    story.append(Paragraph("Solar Rooftop System", s["cover_sub"]))
    story.append(Spacer(1, 10 * mm))

    # Cover info table
    cover_rows = [
        ("Prepared For:", d["customer_name"]),
        ("Proposal No.:", d["proposal_number"]),
        ("Proposed On:", d["proposal_date"]),
    ]
    cover_data = [[
        Paragraph(k, ParagraphStyle("ck", fontSize=10, fontName="Helvetica-Bold", textColor=WHITE)),
        Paragraph(v, ParagraphStyle("cv", fontSize=10, fontName="Helvetica-Bold", textColor=WHITE))
    ] for k, v in cover_rows]
    cover_t = Table(cover_data, colWidths=[w * 0.35, w * 0.65])
    cover_t.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [TABLE_BLUE, colors.HexColor("#1976D2")]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("BOX", (0, 0), (-1, -1), 1, WHITE),
    ]))
    story.append(cover_t)
    story.append(Spacer(1, 10 * mm))

    # Company footer on cover
    footer_rows = [
        ("Website:", d["company_website"]),
        ("Phone:", d["company_phone"]),
        ("Email:", d["company_email"]),
        ("Address:", d["company_address"]),
    ]
    story.append(info_table(footer_rows, s))
    story.append(PageBreak())

    # ── PAGE 2 : Cover Letter ─────────────────────────────────────────────────
    story.append(top_bar)
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph(f"To,<br/>{d['customer_name']},<br/>{d['customer_address'].replace(chr(10), '<br/>')}", s["body"]))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Dear Sir/Ma'am,", s["body"]))
    story.append(Paragraph(f"Greetings from {d['company_name']}!", s["body"]))
    story.append(Paragraph(
        "This is with reference to our discussion regarding your requirement of a solar power plant. "
        "Based on our preliminary analysis from the electricity bills submitted and discussions, "
        "we have found the following:",
        s["body"]))
    story.append(Spacer(1, 4 * mm))

    analysis_rows = [
        ("Projected Solar Capacity", f"{d['proposed_capacity']} kW"),
        ("Sanctioned Load", f"{d['sanctioned_load']} kW"),
        ("Sanctioned Load to be Increased", "0 kW"),
        ("Unit Cost", f"Rs. {d['unit_rate']} /kWh"),
    ]
    story.append(info_table(analysis_rows, s))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "Based on the above data, it is highly recommended that you should opt for a solar power plant at "
        "the earliest as the current cost of energy is very high and would continue to increase over the years.",
        s["body"]))
    story.append(Paragraph(
        "A solar power plant provides an excellent hedge against future energy cost escalations "
        "as well as saving the environment from harmful greenhouse gases.",
        s["body"]))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Thanks and Regards,", s["body"]))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(d["prepared_by"], s["section_header"]))
    story.append(Paragraph(d["prepared_by_title"], s["body"]))
    story.append(Paragraph(d["company_name"], s["body"]))
    story.append(Paragraph(f"Mobile: {d['company_phone']}", s["body"]))
    story.append(Paragraph(f"Email: {d['company_email']}", s["body"]))
    story.append(PageBreak())

    # ── PAGE 3 : Project Summary & Pricing ───────────────────────────────────
    story.append(top_bar)
    story.append(Spacer(1, 4 * mm))
    story.append(header_band("PROJECT SUMMARY", s))
    story.append(Spacer(1, 2 * mm))

    num_panels = math.ceil(d["proposed_capacity"] * 1000 / 600)
    summary_rows = [
        ("Name of the Customer", d["customer_name"]),
        ("Address / Location", d["customer_address"]),
        ("Proposed Capacity", f"{d['proposed_capacity']} kW"),
        ("Types of Modules", f"{d['panel_type']} ({d['panel_make']})"),
        ("Types of Inverters", f"{d['proposed_capacity']} kW ({d['inverter_make']})"),
        ("Annual Global Irradiation", f"{d['annual_irradiation']} kWh/m2"),
        ("Estimated Annual Generation", f"{d['estimated_annual_gen']:,} kWh (units)"),
        ("Type of Installation", d["installation_type"]),
        ("Payback Period", d["payback_period"]),
        ("Estimated Total Lifetime Savings (25 yrs)", f"Rs. {d['lifetime_savings']:,}/-"),
    ]
    story.append(info_table(summary_rows, s))
    story.append(Spacer(1, 4 * mm))

    story.append(header_band("PROJECT PRICING", s))
    story.append(Spacer(1, 2 * mm))

    amount_words = num_to_words(int(d["total_project_cost"])) + " Rupees Only"
    pricing_rows = [
        ("Design, Supply, Installation & Commissioning\n(Grid-tied Solar Power Plant with Liaisoning)",
         f"Rs. {d['rate_per_kw']:,}/kW x {d['proposed_capacity']} kW"),
        ("Project Cost (Sub-Total)", f"Rs. {d['project_cost_subtotal']:,}/-"),
        (f"GST ({d['gst_rate']}%)", f"Rs. {d['gst_amount']:,}/-"),
        ("TOTAL PROJECT COST (Payable Amount)", f"Rs. {d['total_project_cost']:,}/-"),
        ("Amount in Words", amount_words),
        ("PMSGY Subsidy", f"Rs. {d['total_subsidy']:,}/-"),
        ("TOTAL EFFECTIVE AMOUNT", f"Rs. {d['effective_amount']:,}/-"),
        ("Minimum Shadow Free Area Required", f"{d['proposed_capacity'] * 75} sq. ft."),
        ("Extra Charges", "MSEB Load Increase charges (Approx. Rs. 1000/kW)"),
        (f"AMC (Without Cleaning)", f"{d['amc_years']} Years FREE"),
        ("Solar Insurance", f"{d['amc_years']} Years FREE"),
    ]

    pricing_data = []
    for k, v in pricing_rows:
        is_bold = "TOTAL" in k.upper()
        style_k = s["table_cell_bold"] if is_bold else s["table_cell"]
        style_v = s["highlight"] if is_bold else s["table_cell"]
        pricing_data.append([
            Paragraph(k, style_k),
            Paragraph(v, style_v)
        ])

    pricing_t = Table(pricing_data, colWidths=[w * 0.5, w * 0.5])
    pricing_t.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, TABLE_BLUE_LIGHT]),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#BBDEFB")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#BBDEFB")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        # Highlight total rows
        ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#E8F5E9")),
        ("BACKGROUND", (0, 6), (-1, 6), colors.HexColor("#C8E6C9")),
    ]))
    story.append(pricing_t)
    story.append(PageBreak())

    # ── PAGE 4 : Bill of Material ─────────────────────────────────────────────
    story.append(top_bar)
    story.append(Spacer(1, 4 * mm))
    story.append(header_band(f"BILL OF MATERIAL — {d['proposed_capacity']} kW Grid Connected Solar Power Plant", s))
    story.append(Spacer(1, 2 * mm))

    bom_header = [
        Paragraph("Item", s["table_header"]),
        Paragraph("Description", s["table_header"]),
        Paragraph("Make", s["table_header"]),
        Paragraph("Qty", s["table_header"]),
    ]
    bom_rows = [
        ["Solar Panel", f"{d['panel_type']}, 144 cells, Eff >22%, IEC 61215", d["panel_make"], f"{num_panels} Nos."],
        ["Structure", "Mounting structures — Pre-GI Fabricated", "Pre-GI / SS ISI marked", "As reqd."],
        ["Inverter", f"Grid Interactive Inverter — {d['proposed_capacity']} kW String Inverter", d["inverter_make"] + " (5-10 yr Warranty)", "1 No."],
        ["AC/DC Cable", "Cu PVC flexible, LSZH XLPE, ISI marked", "Polycab / Finolex / ISI", "As reqd."],
        ["Junction Box", "DCDB, SPD & Fuse JB", "Eton / Finder / Equivalent", "Included"],
        ["AC Junction Box", "MCB, Fuse, SPD & LT Panel", "Reputed Make", "As reqd."],
        ["Earthing Kit", "AC, DC, Lightning Arrestor", "As per IEC specs", "As reqd."],
        ["Cables & Conduit", "Cable tray / Conduits, ISI marked", "ISI / Reputed", "As reqd."],
    ]

    bom_data = [bom_header] + [
        [Paragraph(r[0], s["table_cell_bold"]),
         Paragraph(r[1], s["table_cell"]),
         Paragraph(r[2], s["table_cell"]),
         Paragraph(r[3], s["table_cell"])]
        for r in bom_rows
    ]
    bom_t = Table(bom_data, colWidths=[w * 0.12, w * 0.42, w * 0.32, w * 0.14])
    bom_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_BLUE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, TABLE_BLUE_LIGHT]),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#BBDEFB")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#BBDEFB")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(bom_t)
    story.append(PageBreak())

    # ── PAGE 5 : Project Highlights & Terms ──────────────────────────────────
    story.append(top_bar)
    story.append(Spacer(1, 4 * mm))
    story.append(header_band("PROJECT HIGHLIGHTS", s))
    story.append(Spacer(1, 2 * mm))

    highlights = [
        "Reputed Panel and Inverter brands",
        f"5–10 Years Inverter Warranty",
        "MSEDCL Net Metering and Liaisoning Charges Included",
        f"{d['amc_years']}-Year AMC (Without Cleaning) and Solar Insurance Included",
        "Service Visit within 72 hours | Max. Inverter Repair/Replacement time 7 days",
        "Temporary Inverter to be installed in case of Extended Repair period",
        "12 Years Product Warranty + 30 Years Performance Warranty on Solar Modules",
        "Weekly Remote Monitoring through the Internet (Wi-Fi in client scope)",
    ]
    for h in highlights:
        story.append(Paragraph(f"• {h}", s["body"]))

    story.append(Spacer(1, 4 * mm))
    story.append(header_band("TERMS & CONDITIONS", s))
    story.append(Spacer(1, 2 * mm))

    terms_rows = [
        ("Validity of Quote", "10 Days from date of submission"),
        ("Project Execution", "60 Days from DISCOM approval"),
        ("Payment Terms", "20% Advance | 50% After MSEDCL Approval | 10% After Delivery | 15% After Installation | 5% After Meter"),
        ("Warranty — Inverter", "5 Years from Commissioning"),
        ("Warranty — Modules", "12 Years Product + 30 Years Performance"),
        ("Remote Monitoring", "Wi-Fi connection in client's scope"),
        ("GST", f"{d['gst_rate']}% on project (5% on panels/inverter, 18% on services/parts)"),
        ("Insurance", "Provided once plant is commissioned"),
        ("Force Majeure", "Projects subject to Force Majeure conditions"),
    ]
    story.append(info_table(terms_rows, s))
    story.append(Spacer(1, 4 * mm))

    story.append(header_band("ROLES & RESPONSIBILITIES", s))
    story.append(Spacer(1, 2 * mm))

    rr_header = [
        Paragraph("Activity", s["table_header"]),
        Paragraph("Responsibility", s["table_header"]),
    ]
    rr_rows = [
        ("Project Approval from Local DISCOM", d["company_name"]),
        ("Material Safety & Access to Roof", "Customer"),
        ("Civil & Electrical Work", d["company_name"]),
        ("Installation & Commissioning", d["company_name"]),
        ("Power Supply During Installation", "Customer"),
        ("Net Meter Liaisoning & Testing", d["company_name"]),
        ("DISCOM Interconnect Charges", "Customer"),
        ("Earthing & Lightning Protection Kit", d["company_name"]),
        ("Panel Cleaning", "Customer"),
    ]
    rr_data = [rr_header] + [
        [Paragraph(a, s["table_cell"]), Paragraph(r, s["table_cell"])]
        for a, r in rr_rows
    ]
    rr_t = Table(rr_data, colWidths=[w * 0.6, w * 0.4])
    rr_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_BLUE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, TABLE_BLUE_LIGHT]),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#BBDEFB")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#BBDEFB")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(rr_t)
    story.append(Spacer(1, 6 * mm))

    # Footer
    story.append(HRFlowable(width=w, color=GREEN, thickness=1))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(
        f"{d['company_name']} | {d['company_website']} | {d['company_phone']} | {d['company_email']}",
        ParagraphStyle("footer", fontSize=8, fontName="Helvetica", textColor=GREEN, alignment=TA_CENTER)
    ))
    story.append(Paragraph(d["company_address"],
        ParagraphStyle("footer2", fontSize=7, fontName="Helvetica", textColor=DARK_GREY, alignment=TA_CENTER)
    ))

    doc.build(story)
    return buf.getvalue()
