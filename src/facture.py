"""
facture.py — Generation de facture PDF pour une vente
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from datetime import datetime
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from database import get_connection

BLEU   = colors.HexColor("#1a2940")
CYAN   = colors.HexColor("#4a90d9")
VERT   = colors.HexColor("#27ae60")
BLANC  = colors.white
GRIS   = colors.HexColor("#f0f4f8")


def generer_facture(vente_id: int, output_path: str):
    """Génère une facture PDF pour une vente donnée."""
    conn = get_connection()
    vente = conn.execute("""
        SELECT v.id, v.date_vente, v.quantite, v.prix_unitaire, v.prix_total,
               v.client, v.notes, p.nom, p.unite
        FROM ventes v JOIN produits p ON v.produit_id = p.id
        WHERE v.id = ?
    """, (vente_id,)).fetchone()
    conn.close()

    if not vente:
        raise ValueError(f"Vente #{vente_id} introuvable.")

    doc = SimpleDocTemplate(output_path, pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    title_s = ParagraphStyle("t", fontSize=20, textColor=BLEU,
                               fontName="Helvetica-Bold", spaceAfter=2)
    sub_s   = ParagraphStyle("s", fontSize=9, textColor=colors.HexColor("#667788"),
                               spaceAfter=4)
    normal_s = ParagraphStyle("n", fontSize=10, textColor=BLEU)

    story = []

    # ── En-tête ──────────────────────────────────────────────────
    header_data = [[
        Paragraph("<b>🧃 Stock Jus</b><br/>Vente de Jus en Bouteille", title_s),
        Paragraph(
            f"<b>FACTURE N° {vente[0]:04d}</b><br/>"
            f"Date : {str(vente[1])[:10]}<br/>"
            f"Heure : {datetime.now().strftime('%H:%M')}",
            ParagraphStyle("r", fontSize=10, textColor=BLEU, fontName="Helvetica-Bold")
        )
    ]]
    t_header = Table(header_data, colWidths=[10*cm, 7*cm])
    t_header.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), GRIS),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("ALIGN",         (1, 0), (1, 0), "RIGHT"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(t_header)
    story.append(Spacer(1, 15))

    # ── Client ───────────────────────────────────────────────────
    client_nom = vente[5] or "Client"
    story.append(Paragraph(f"<b>Client :</b> {client_nom}", normal_s))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=CYAN, spaceAfter=10))

    # ── Tableau produit ──────────────────────────────────────────
    story.append(Paragraph("<b>Détail de la vente</b>",
                            ParagraphStyle("h", fontSize=11, textColor=BLEU,
                                           fontName="Helvetica-Bold", spaceAfter=8)))

    data = [
        ["Produit", "Unité", "Quantité", "Prix unitaire", "Total"],
        [vente[7], vente[8], str(vente[2]),
         f"{vente[3]:,.0f} CDF", f"{vente[4]:,.0f} CDF"],
    ]
    t = Table(data, colWidths=[5.5*cm, 2.5*cm, 2.5*cm, 3.5*cm, 3.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), CYAN),
        ("TEXTCOLOR",     (0, 0), (-1, 0), BLANC),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 10),
        ("BACKGROUND",    (0, 1), (-1, 1), BLANC),
        ("FONTSIZE",      (0, 1), (-1, 1), 10),
        ("ALIGN",         (2, 0), (-1, -1), "CENTER"),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#ccddee")),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    # ── Total ────────────────────────────────────────────────────
    total_data = [
        ["", "TOTAL À PAYER :", f"{vente[4]:,.0f} CDF"]
    ]
    t_total = Table(total_data, colWidths=[9.5*cm, 4*cm, 4*cm])
    t_total.setStyle(TableStyle([
        ("BACKGROUND",    (1, 0), (-1, 0), BLEU),
        ("TEXTCOLOR",     (1, 0), (-1, 0), BLANC),
        ("FONTNAME",      (1, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (1, 0), (-1, 0), 12),
        ("ALIGN",         (1, 0), (-1, 0), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(t_total)
    story.append(Spacer(1, 20))

    # ── Notes ────────────────────────────────────────────────────
    if vente[6]:
        story.append(Paragraph(f"<b>Notes :</b> {vente[6]}", normal_s))
        story.append(Spacer(1, 10))

    # ── Pied de page ─────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5,
                              color=colors.HexColor("#ccddee"), spaceAfter=8))
    story.append(Paragraph(
        "Merci pour votre achat ! 🧃",
        ParagraphStyle("footer", fontSize=10, textColor=CYAN,
                        fontName="Helvetica-Bold", alignment=1)
    ))

    doc.build(story)
    return output_path
