"""
pdf_export.py — Génération de rapports PDF avec ReportLab
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from database import get_connection


# ── Couleurs maison ────────────────────────────────────────────────
BLEU   = colors.HexColor("#1a2940")
CYAN   = colors.HexColor("#4a90d9")
VERT   = colors.HexColor("#27ae60")
ROUGE  = colors.HexColor("#e74c3c")
ORANGE = colors.HexColor("#f39c12")
GRIS   = colors.HexColor("#f0f4f8")
BLANC  = colors.white


def _header_table_style(header_color=CYAN):
    return TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), header_color),
        ("TEXTCOLOR",     (0, 0), (-1, 0), BLANC),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 9),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [BLANC, colors.HexColor("#eef3f9")]),
        ("FONTSIZE",      (0, 1), (-1, -1), 8),
        ("GRID",          (0, 0), (-1, -1), 0.4, colors.HexColor("#ccddee")),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ])


def _get_styles():
    s = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=s["Normal"],
                                  fontSize=18, textColor=BLEU,
                                  fontName="Helvetica-Bold", spaceAfter=4)
    sub_style   = ParagraphStyle("sub",   parent=s["Normal"],
                                  fontSize=9, textColor=colors.HexColor("#667788"),
                                  spaceAfter=10)
    section_style = ParagraphStyle("section", parent=s["Normal"],
                                    fontSize=12, textColor=BLEU,
                                    fontName="Helvetica-Bold",
                                    spaceBefore=14, spaceAfter=6)
    return title_style, sub_style, section_style


# ══════════════════════════════════════════════════════════════════
# 1. RAPPORT ÉTAT DU STOCK
# ══════════════════════════════════════════════════════════════════
def rapport_stock(output_path: str):
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2*cm)
    title_s, sub_s, sec_s = _get_styles()
    now = datetime.now().strftime("%d/%m/%Y à %H:%M")
    story = []

    story.append(Paragraph("🧃 Rapport — État du Stock", title_s))
    story.append(Paragraph(f"Généré le {now}", sub_s))
    story.append(HRFlowable(width="100%", thickness=1, color=CYAN, spaceAfter=10))

    conn = get_connection()
    rows = conn.execute("""
        SELECT nom, unite, stock_actuel, stock_minimum, prix_vente,
               stock_actuel * prix_vente AS valeur
        FROM produits ORDER BY nom
    """).fetchall()

    total_val = sum(r[5] for r in rows)
    total_bts = sum(r[2] for r in rows)
    nb_alertes = sum(1 for r in rows if r[2] <= r[3])

    # Cartes résumé
    resume_data = [
        ["Produits", "Total bouteilles", "Valeur totale", "Alertes stock bas"],
        [str(len(rows)), str(total_bts), f"{total_val:,.0f} CDF", str(nb_alertes)],
    ]
    t = Table(resume_data, colWidths=[4*cm, 4*cm, 5*cm, 4*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), BLEU),
        ("TEXTCOLOR",     (0, 0), (-1, 0), BLANC),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND",    (0, 1), (-1, 1), GRIS),
        ("FONTNAME",      (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 1), (-1, 1), 13),
        ("TEXTCOLOR",     (3, 1), (3, 1), ROUGE if nb_alertes > 0 else VERT),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("GRID",          (0, 0), (-1, -1), 0.4, colors.HexColor("#ccddee")),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    # Tableau détail
    story.append(Paragraph("Détail par produit", sec_s))
    data = [["Produit", "Unité", "Stock actuel", "Stock min", "Prix vente", "Valeur", "Statut"]]
    for r in rows:
        statut = "⚠ Bas" if r[2] <= r[3] else "✓ OK"
        data.append([r[0], r[1], str(r[2]), str(r[3]),
                     f"{r[4]:.0f} CDF", f"{r[5]:,.0f} CDF", statut])

    t2 = Table(data, colWidths=[4.5*cm, 2*cm, 2.5*cm, 2.5*cm, 2.5*cm, 3*cm, 1.8*cm])
    style2 = _header_table_style(CYAN)
    for i, r in enumerate(rows, 1):
        if r[2] <= r[3]:
            style2.add("TEXTCOLOR", (6, i), (6, i), ROUGE)
            style2.add("FONTNAME",  (0, i), (-1, i), "Helvetica-Bold")
        else:
            style2.add("TEXTCOLOR", (6, i), (6, i), VERT)
    t2.setStyle(style2)
    story.append(t2)

    conn.close()
    doc.build(story)
    return output_path


# ══════════════════════════════════════════════════════════════════
# 2. RAPPORT ACHATS PAR PÉRIODE
# ══════════════════════════════════════════════════════════════════
def rapport_achats(output_path: str, date_debut: str, date_fin: str):
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2*cm)
    title_s, sub_s, sec_s = _get_styles()
    now = datetime.now().strftime("%d/%m/%Y à %H:%M")
    story = []

    story.append(Paragraph("🛒 Rapport — Achats & Approvisionnements", title_s))
    story.append(Paragraph(f"Période : {date_debut} → {date_fin}  |  Généré le {now}", sub_s))
    story.append(HRFlowable(width="100%", thickness=1, color=ORANGE, spaceAfter=10))

    conn = get_connection()
    rows = conn.execute("""
        SELECT a.date_achat, p.nom, COALESCE(f.nom,'—'), a.quantite,
               a.prix_unitaire, a.prix_total, COALESCE(a.notes,'—')
        FROM achats a
        JOIN produits p ON a.produit_id = p.id
        LEFT JOIN fournisseurs f ON a.fournisseur_id = f.id
        WHERE a.date_achat BETWEEN ? AND ?
        ORDER BY a.date_achat DESC
    """, (date_debut, date_fin + " 23:59:59")).fetchall()

    total_depense = sum(r[5] for r in rows)
    total_bts     = sum(r[3] for r in rows)

    # Résumé
    res = [["Nb lignes", "Bouteilles achetées", "Total dépensé"],
           [str(len(rows)), str(total_bts), f"{total_depense:,.0f} CDF"]]
    t = Table(res, colWidths=[5*cm, 6*cm, 6*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLEU),
        ("TEXTCOLOR",  (0, 0), (-1, 0), BLANC),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 1), (-1, 1), GRIS),
        ("FONTNAME",   (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 1), (-1, 1), 13),
        ("TEXTCOLOR",  (2, 1), (2, 1), ROUGE),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("GRID",       (0, 0), (-1, -1), 0.4, colors.HexColor("#ccddee")),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Liste des achats", sec_s))
    data = [["Date", "Produit", "Fournisseur", "Qté", "Prix unit.", "Total", "Notes"]]
    for r in rows:
        data.append([str(r[0])[:10], r[1], r[2], str(r[3]),
                     f"{r[4]:.0f}", f"{r[5]:,.0f}", r[6][:25]])

    t2 = Table(data, colWidths=[2.3*cm, 4*cm, 3.5*cm, 1.5*cm, 2.3*cm, 2.8*cm, 3.3*cm])
    t2.setStyle(_header_table_style(ORANGE))
    story.append(t2)

    conn.close()
    doc.build(story)
    return output_path


# ══════════════════════════════════════════════════════════════════
# 3. RAPPORT VENTES PAR PÉRIODE
# ══════════════════════════════════════════════════════════════════
def rapport_ventes(output_path: str, date_debut: str, date_fin: str):
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2*cm)
    title_s, sub_s, sec_s = _get_styles()
    now = datetime.now().strftime("%d/%m/%Y à %H:%M")
    story = []

    story.append(Paragraph("💰 Rapport — Ventes", title_s))
    story.append(Paragraph(f"Période : {date_debut} → {date_fin}  |  Généré le {now}", sub_s))
    story.append(HRFlowable(width="100%", thickness=1, color=VERT, spaceAfter=10))

    conn = get_connection()
    rows = conn.execute("""
        SELECT v.date_vente, p.nom, v.quantite, v.prix_unitaire,
               v.prix_total, COALESCE(v.client,'—'), COALESCE(v.notes,'—')
        FROM ventes v
        JOIN produits p ON v.produit_id = p.id
        WHERE v.date_vente BETWEEN ? AND ?
        ORDER BY v.date_vente DESC
    """, (date_debut, date_fin + " 23:59:59")).fetchall()

    total_recettes = sum(r[4] for r in rows)
    total_bts      = sum(r[2] for r in rows)

    res = [["Nb ventes", "Bouteilles vendues", "Total recettes"],
           [str(len(rows)), str(total_bts), f"{total_recettes:,.0f} CDF"]]
    t = Table(res, colWidths=[5*cm, 6*cm, 6*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLEU),
        ("TEXTCOLOR",  (0, 0), (-1, 0), BLANC),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 1), (-1, 1), GRIS),
        ("FONTNAME",   (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 1), (-1, 1), 13),
        ("TEXTCOLOR",  (2, 1), (2, 1), VERT),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("GRID",       (0, 0), (-1, -1), 0.4, colors.HexColor("#ccddee")),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Liste des ventes", sec_s))
    data = [["Date", "Produit", "Qté", "Prix unit.", "Total", "Client", "Notes"]]
    for r in rows:
        data.append([str(r[0])[:10], r[1], str(r[2]),
                     f"{r[3]:.0f}", f"{r[4]:,.0f}", r[5], r[6][:20]])

    t2 = Table(data, colWidths=[2.3*cm, 4.5*cm, 1.5*cm, 2.3*cm, 2.8*cm, 3*cm, 3.3*cm])
    t2.setStyle(_header_table_style(VERT))
    story.append(t2)

    conn.close()
    doc.build(story)
    return output_path
