# facture.py — Facture PDF (vente unique ou panier multi-produits)
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                 Paragraph, Spacer, HRFlowable)
from datetime import datetime
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from database import get_connection
from config import (BOUTIQUE_NOM, BOUTIQUE_SLOGAN, BOUTIQUE_ADRESSE,
                    BOUTIQUE_TELEPHONE, MONNAIE, UNITE_DEFAULT)

BLEU = colors.HexColor("#1a2940")
CYAN = colors.HexColor("#4a90d9")
GRIS = colors.HexColor("#f5f7fa")
VERT = colors.HexColor("#1e8449")


def _p(text, size=10, bold=False, color=colors.black, align=0):
    fn = "Helvetica-Bold" if bold else "Helvetica"
    return Paragraph(text, ParagraphStyle("_", fontSize=size, fontName=fn,
                                           textColor=color, alignment=align))


def generer_facture(vente_ids, output_path):
    """
    vente_ids : int  (vente unique) OU list[int] (panier multi-produits)
    """
    if isinstance(vente_ids, int):
        vente_ids = [vente_ids]

    conn = get_connection()
    lignes, client, date_v, notes = [], None, None, None
    for vid in vente_ids:
        row = conn.execute("""
            SELECT v.id,
                   COALESCE(p.nom, v.produit_nom, 'Produit supprimé'),
                   v.quantite, v.prix_unitaire, v.prix_total,
                   COALESCE(v.paquets_offerts,0),
                   v.date_vente, v.client, v.notes
            FROM ventes v
            LEFT JOIN produits p ON v.produit_id = p.id
            WHERE v.id = ?
        """, (vid,)).fetchone()
        if row:
            lignes.append(dict(row))
            client = client or row["client"]
            date_v = date_v or row["date_vente"]
            notes  = notes  or row["notes"]
    conn.close()
    if not lignes:
        raise ValueError(f"Aucune vente trouvée : {vente_ids}")

    total_global = sum(l["prix_total"] for l in lignes)
    numero   = f"{vente_ids[0]:04d}" if len(vente_ids) == 1 \
               else f"{vente_ids[0]:04d}-{vente_ids[-1]:04d}"
    date_str = str(date_v)[:16] if date_v else datetime.now().strftime("%Y-%m-%d %H:%M")

    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            topMargin=1.5*cm, bottomMargin=1.5*cm,
                            leftMargin=2*cm, rightMargin=2*cm)
    story = []

    # ── En-tête ──────────────────────────────────────────────────────────
    hdr = Table([[
        _p(f"<b>{BOUTIQUE_NOM}</b>", 20, bold=True, color=BLEU),
        _p(f"<b>FACTURE N° {numero}</b>", 12, bold=True, color=BLEU, align=2),
    ],[
        _p(BOUTIQUE_SLOGAN or "", 11, color=CYAN),
        _p(f"Date : {date_str}", 10, align=2),
    ],[
        _p(BOUTIQUE_ADRESSE or "", 10),
        _p(f"Client : {client or 'N/A'}", 10, align=2),
    ],[
        _p(f"Tél : {BOUTIQUE_TELEPHONE or 'N/A'}", 10),
        _p("", 10),
    ]], colWidths=[10*cm, 7*cm])
    hdr.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
    ]))
    story += [hdr, HRFlowable(width="100%", thickness=2, color=BLEU,
                               spaceBefore=8, spaceAfter=10)]

    # ── Lignes produits ───────────────────────────────────────────────────
    W = [7*cm, 2*cm, 2.8*cm, 2*cm, 3.2*cm]
    head = [
        _p("<b>Produit</b>",             10, bold=True, color=colors.white),
        _p("<b>Qté</b>",                 10, bold=True, color=colors.white, align=1),
        _p(f"<b>Prix ({MONNAIE})</b>",   10, bold=True, color=colors.white, align=2),
        _p("<b>Offerts</b>",             10, bold=True, color=colors.white, align=1),
        _p(f"<b>Total ({MONNAIE})</b>",  10, bold=True, color=colors.white, align=2),
    ]
    tdata = [head]
    for l in lignes:
        off = f"+{l['paquets_offerts']}" if l["paquets_offerts"] > 0 else "—"
        tdata.append([
            _p(l["nom"],                         10),
            _p(str(l["quantite"]),               10, align=1),
            _p(f"{l['prix_unitaire']:,.0f}",     10, align=2),
            _p(off,                              10, align=1),
            _p(f"{l['prix_total']:,.0f}", 10, bold=True, align=2),
        ])
    tbl = Table(tdata, colWidths=W, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,0),  BLEU),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[GRIS, colors.white]),
        ("GRID",         (0,0),(-1,-1), 0.4, colors.HexColor("#d0d8e4")),
        ("LINEBELOW",    (0,0),(-1,0),  1.5, colors.white),
        ("TOPPADDING",   (0,0),(-1,-1), 7),
        ("BOTTOMPADDING",(0,0),(-1,-1), 7),
        ("LEFTPADDING",  (0,0),(-1,-1), 6),
        ("RIGHTPADDING", (0,0),(-1,-1), 6),
        ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
    ]))
    story += [tbl, Spacer(1, 12)]

    # ── Total ─────────────────────────────────────────────────────────────
    tot = Table([[
        _p("", 10),
        _p(f"<b>TOTAL : {total_global:,.0f} {MONNAIE}</b>",
           14, bold=True, color=colors.white, align=2),
    ]], colWidths=[10*cm, 7*cm])
    tot.setStyle(TableStyle([
        ("BACKGROUND",   (1,0),(1,0), VERT),
        ("TOPPADDING",   (0,0),(-1,-1), 10),
        ("BOTTOMPADDING",(0,0),(-1,-1), 10),
        ("RIGHTPADDING", (1,0),(1,0),  16),
    ]))
    story += [tot, Spacer(1, 16)]

    if notes:
        story += [_p(f"<i>Notes : {notes}</i>", 9, color=colors.gray), Spacer(1,8)]

    story += [
        HRFlowable(width="100%", thickness=0.5,
                    color=colors.HexColor("#ccddee"), spaceAfter=8),
        _p("Merci pour votre achat !", 11, bold=True, color=CYAN, align=1),
    ]
    doc.build(story)
    return output_path
