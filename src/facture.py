# facture.py — Génération facture PDF (supporte vente unique ou panier multi-produits)

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from datetime import datetime
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from database import get_connection
from config import BOUTIQUE_NOM, BOUTIQUE_SLOGAN, BOUTIQUE_ADRESSE, BOUTIQUE_TELEPHONE, MONNAIE, UNITE_DEFAULT

BLEU = colors.HexColor("#1a2940")
CYAN = colors.HexColor("#4a90d9")
GRIS = colors.HexColor("#f5f7fa")
VERT = colors.HexColor("#1e8449")


def generer_facture(vente_ids, output_path):
    """
    Génère une facture PDF pour une ou plusieurs ventes.
    vente_ids : int  (vente unique)  OU  list[int]  (panier multi-produits)
    """
    if isinstance(vente_ids, int):
        vente_ids = [vente_ids]

    conn = get_connection()
    lignes = []
    client = None
    date_v = None
    notes  = None

    for vid in vente_ids:
        row = conn.execute("""
            SELECT v.id,
                   COALESCE(p.nom, v.produit_nom, 'Produit supprimé'),
                   v.quantite, v.prix_unitaire, v.prix_total,
                   COALESCE(v.paquets_offerts, 0),
                   v.date_vente, v.client, v.notes
            FROM ventes v
            LEFT JOIN produits p ON v.produit_id = p.id
            WHERE v.id = ?
        """, (vid,)).fetchone()
        if row:
            lignes.append(dict(row))
            if client is None:  client = row["client"]
            if date_v is None:  date_v = row["date_vente"]
            if notes  is None:  notes  = row["notes"]
    conn.close()

    if not lignes:
        raise ValueError(f"Aucune vente trouvée pour les ids: {vente_ids}")

    total_global = sum(l["prix_total"] for l in lignes)
    numero = f"{vente_ids[0]:04d}" if len(vente_ids) == 1 else f"{vente_ids[0]:04d}-{vente_ids[-1]:04d}"
    date_str = str(date_v)[:16] if date_v else datetime.now().strftime("%Y-%m-%d %H:%M")

    # ── Document ────────────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=1.5*cm, bottomMargin=1.5*cm,
        leftMargin=2*cm, rightMargin=2*cm)

    story = []

    # Styles
    s_titre   = ParagraphStyle("titre",   fontSize=22, textColor=BLEU,
                                fontName="Helvetica-Bold", spaceAfter=2)
    s_sub     = ParagraphStyle("sub",     fontSize=11, textColor=CYAN,
                                fontName="Helvetica", spaceAfter=4)
    s_info    = ParagraphStyle("info",    fontSize=10, textColor=colors.HexColor("#555555"))
    s_fact    = ParagraphStyle("fact",    fontSize=10, textColor=BLEU,
                                fontName="Helvetica-Bold")
    s_footer  = ParagraphStyle("footer",  fontSize=10, textColor=CYAN,
                                fontName="Helvetica-Bold", alignment=1)
    s_note    = ParagraphStyle("note",    fontSize=9,  textColor=colors.gray)

    # En-tête boutique
    header_data = [[
        Paragraph(f"<b>{BOUTIQUE_NOM}</b>", s_titre),
        Paragraph(f"<b>FACTURE N° {numero}</b>", s_fact),
    ],[
        Paragraph(BOUTIQUE_SLOGAN or "", s_sub),
        Paragraph(f"Date : {date_str}", s_info),
    ],[
        Paragraph(BOUTIQUE_ADRESSE or "", s_info),
        Paragraph(f"Client : {client or 'N/A'}", s_info),
    ],[
        Paragraph(f"Tél : {BOUTIQUE_TELEPHONE or 'N/A'}", s_info),
        Paragraph("", s_info),
    ]]
    header_tbl = Table(header_data, colWidths=[10*cm, 7*cm])
    header_tbl.setStyle(TableStyle([
        ("VALIGN",      (0,0), (-1,-1), "TOP"),
        ("ALIGN",       (1,0), (1,-1),  "RIGHT"),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
    ]))
    story.append(header_tbl)
    story.append(HRFlowable(width="100%", thickness=2, color=BLEU, spaceBefore=8, spaceAfter=10))

    # Tableau des lignes
    col_w = [7*cm, 2.2*cm, 2.8*cm, 2.2*cm, 2.8*cm]
    headers = [
        Paragraph("<b>Produit</b>",           ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=10, textColor=colors.white)),
        Paragraph("<b>Qté</b>",               ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=10, textColor=colors.white, alignment=1)),
        Paragraph(f"<b>Prix unit. ({MONNAIE})</b>", ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=10, textColor=colors.white, alignment=2)),
        Paragraph("<b>Offerts</b>",           ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=10, textColor=colors.white, alignment=1)),
        Paragraph(f"<b>Total ({MONNAIE})</b>",     ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=10, textColor=colors.white, alignment=2)),
    ]
    table_data = [headers]

    for i, l in enumerate(lignes):
        bg = GRIS if i % 2 == 0 else colors.white
        offerts_txt = f"+{l['paquets_offerts']}" if l["paquets_offerts"] > 0 else "-"
        row = [
            Paragraph(l["nom"], ParagraphStyle("r", fontSize=10)),
            Paragraph(str(l["quantite"]),           ParagraphStyle("rc", fontSize=10, alignment=1)),
            Paragraph(f"{l['prix_unitaire']:,.0f}", ParagraphStyle("rr", fontSize=10, alignment=2)),
            Paragraph(offerts_txt,                  ParagraphStyle("rc", fontSize=10, alignment=1)),
            Paragraph(f"{l['prix_total']:,.0f}",    ParagraphStyle("rr", fontSize=10, alignment=2,
                                                                    fontName="Helvetica-Bold")),
        ]
        table_data.append(row)

    prod_tbl = Table(table_data, colWidths=col_w, repeatRows=1)
    row_colors = [(colors.HexColor("#1a2940"), 0)] + \
                 [(GRIS if i % 2 == 1 else colors.white, i+1) for i in range(len(lignes))]
    tbl_style = [
        ("BACKGROUND", (0,0), (-1,0), BLEU),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [GRIS, colors.white]),
        ("GRID",       (0,0), (-1,-1), 0.4, colors.HexColor("#d0d8e4")),
        ("LINEBELOW",  (0,0), (-1,0), 1.5, colors.white),
        ("TOPPADDING", (0,0), (-1,-1), 7),
        ("BOTTOMPADDING",(0,0),(-1,-1), 7),
        ("LEFTPADDING", (0,0),(-1,-1), 6),
        ("RIGHTPADDING",(0,0),(-1,-1), 6),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
    ]
    prod_tbl.setStyle(TableStyle(tbl_style))
    story.append(prod_tbl)
    story.append(Spacer(1, 12))

    # Total global
    tot_data = [[
        Paragraph("", s_info),
        Paragraph(f"<b>TOTAL : {total_global:,.0f} {MONNAIE}</b>",
                  ParagraphStyle("tot", fontName="Helvetica-Bold", fontSize=14,
                                 textColor=colors.white, alignment=2)),
    ]]
    tot_tbl = Table(tot_data, colWidths=[10*cm, 7*cm])
    tot_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (1,0),(1,0), VERT),
        ("ROUNDEDCORNERS",(1,0),(1,0), [4,4,4,4]),
        ("TOPPADDING",    (0,0),(-1,-1), 10),
        ("BOTTOMPADDING", (0,0),(-1,-1), 10),
        ("RIGHTPADDING",  (1,0),(1,0), 16),
    ]))
    story.append(tot_tbl)
    story.append(Spacer(1, 16))

    # Notes
    if notes:
        story.append(Paragraph(f"<i>Notes : {notes}</i>", s_note))
        story.append(Spacer(1, 8))

    story.append(HRFlowable(width="100%", thickness=0.5,
                              color=colors.HexColor("#ccddee"), spaceAfter=8))
    story.append(Paragraph("Merci pour votre achat !", s_footer))

    doc.build(story)
    return output_path
