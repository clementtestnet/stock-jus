# facture.py — Génération facture PDF

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

BLEU  = colors.HexColor("#1a2940")
CYAN  = colors.HexColor("#4a90d9")
VERT  = colors.HexColor("#27ae60")
BLANC = colors.white
GRIS  = colors.HexColor("#f0f4f8")

def generer_facture(vente_id, output_path):
    conn  = get_connection()
    vente = conn.execute("""
        SELECT v.id, v.date_vente, v.quantite, v.prix_unitaire, v.prix_total,
               v.client, v.notes, p.nom, p.unite, COALESCE(v.paquets_offerts,0)
        FROM ventes v JOIN produits p ON v.produit_id=p.id WHERE v.id=?
    """, (vente_id,)).fetchone()
    conn.close()
    if not vente:
        raise ValueError(f"Vente #{vente_id} introuvable.")

    doc = SimpleDocTemplate(output_path, pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2*cm)
    story = []

    # En-tête
    t_s  = ParagraphStyle("t", fontSize=18, textColor=BLEU, fontName="Helvetica-Bold", spaceAfter=2)
    r_s  = ParagraphStyle("r", fontSize=10, textColor=BLEU, fontName="Helvetica-Bold")
    sub  = f"{BOUTIQUE_SLOGAN}"
    if BOUTIQUE_ADRESSE:   sub += f"<br/>{BOUTIQUE_ADRESSE}"
    if BOUTIQUE_TELEPHONE: sub += f"<br/>Tel: {BOUTIQUE_TELEPHONE}"

    hdr = Table([[
        Paragraph(f"<b>{BOUTIQUE_NOM}</b><br/>{sub}", t_s),
        Paragraph(f"<b>FACTURE N {vente[0]:04d}</b><br/>Date: {str(vente[1])[:10]}<br/>Heure: {datetime.now().strftime('%H:%M')}", r_s)
    ]], colWidths=[10*cm, 7*cm])
    hdr.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), GRIS),
        ("TOPPADDING", (0,0),(-1,-1), 12), ("BOTTOMPADDING",(0,0),(-1,-1),12),
        ("LEFTPADDING",(0,0),(-1,-1), 10), ("ALIGN",(1,0),(1,0),"RIGHT"),
        ("VALIGN",     (0,0),(-1,-1), "MIDDLE"),
    ]))
    story += [hdr, Spacer(1,12)]

    # Client
    n_s = ParagraphStyle("n", fontSize=10, textColor=BLEU)
    story.append(Paragraph(f"<b>Client:</b> {vente[5] or 'Client'}", n_s))
    story.append(Spacer(1,8))
    story.append(HRFlowable(width="100%", thickness=1, color=CYAN, spaceAfter=10))

    # Détail
    h_s = ParagraphStyle("h", fontSize=11, textColor=BLEU, fontName="Helvetica-Bold", spaceAfter=8)
    story.append(Paragraph("<b>Detail de la vente</b>", h_s))

    paquets_offerts = vente[9]
    data = [
        ["Produit", "Unite", "Quantite", f"Prix ({MONNAIE})", "Offerts", "Total"],
        [vente[7], vente[8], str(vente[2]),
         f"{vente[3]:,.0f}", f"+{paquets_offerts}" if paquets_offerts > 0 else "-",
         f"{vente[4]:,.0f} {MONNAIE}"],
    ]
    t = Table(data, colWidths=[4.5*cm, 2*cm, 2.2*cm, 2.8*cm, 2*cm, 3.2*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0), CYAN), ("TEXTCOLOR",(0,0),(-1,0), BLANC),
        ("FONTNAME",      (0,0),(-1,0), "Helvetica-Bold"), ("FONTSIZE",(0,0),(-1,0), 9),
        ("FONTSIZE",      (0,1),(-1,1), 10),
        ("TEXTCOLOR",     (4,1),(4,1), VERT), ("FONTNAME",(4,1),(4,1),"Helvetica-Bold"),
        ("ALIGN",         (2,0),(-1,-1), "CENTER"),
        ("GRID",          (0,0),(-1,-1), 0.5, colors.HexColor("#ccddee")),
        ("TOPPADDING",    (0,0),(-1,-1), 7), ("BOTTOMPADDING",(0,0),(-1,-1),7),
    ]))
    story += [t, Spacer(1,8)]

    if paquets_offerts > 0:
        g_s = ParagraphStyle("g", fontSize=10, textColor=VERT, fontName="Helvetica-Bold")
        story.append(Paragraph(f"Cadeau inclus: +{paquets_offerts} {UNITE_DEFAULT}(s) offert(s) !", g_s))
        story.append(Spacer(1,6))

    # Total
    tot = Table([["", f"TOTAL A PAYER:", f"{vente[4]:,.0f} {MONNAIE}"]],
                colWidths=[9*cm, 4*cm, 4.7*cm])
    tot.setStyle(TableStyle([
        ("BACKGROUND", (1,0),(-1,0), BLEU), ("TEXTCOLOR",(1,0),(-1,0), BLANC),
        ("FONTNAME",   (1,0),(-1,0), "Helvetica-Bold"), ("FONTSIZE",(1,0),(-1,0),12),
        ("ALIGN",      (1,0),(-1,0), "CENTER"),
        ("TOPPADDING", (0,0),(-1,-1),10), ("BOTTOMPADDING",(0,0),(-1,-1),10),
    ]))
    story += [tot, Spacer(1,20)]

    story.append(HRFlowable(width="100%", thickness=0.5,
                              color=colors.HexColor("#ccddee"), spaceAfter=8))
    f_s = ParagraphStyle("f", fontSize=10, textColor=CYAN, fontName="Helvetica-Bold", alignment=1)
    story.append(Paragraph("Merci pour votre achat !", f_s))

    doc.build(story)
    return output_path
