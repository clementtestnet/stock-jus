# pdf_export.py — Rapports PDF admin (LEFT JOIN partout)
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
from config import MONNAIE, BOUTIQUE_NOM

BLEU   = colors.HexColor("#1a2940")
CYAN   = colors.HexColor("#4a90d9")
VERT   = colors.HexColor("#1e8449")
ROUGE  = colors.HexColor("#c0392b")
ORANGE = colors.HexColor("#d68910")
BLANC  = colors.white
GRIS   = colors.HexColor("#f5f7fa")


def _doc(path):
    return SimpleDocTemplate(path, pagesize=A4,
                              leftMargin=2*cm, rightMargin=2*cm,
                              topMargin=2*cm, bottomMargin=2*cm)

def _p(text, size=10, bold=False, color=colors.black, align=0):
    fn = "Helvetica-Bold" if bold else "Helvetica"
    return Paragraph(text, ParagraphStyle("_", fontSize=size, fontName=fn,
                                           textColor=color, alignment=align))

def _tbl_style(header_color):
    return TableStyle([
        ("BACKGROUND",    (0,0),(-1,0),  header_color),
        ("TEXTCOLOR",     (0,0),(-1,0),  BLANC),
        ("FONTNAME",      (0,0),(-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),(-1,0),  9),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [BLANC, GRIS]),
        ("FONTSIZE",      (0,1),(-1,-1), 8),
        ("GRID",          (0,0),(-1,-1), 0.4, colors.HexColor("#ccddee")),
        ("ALIGN",         (0,0),(-1,-1), "CENTER"),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
    ])


# ── Rapport Stock ────────────────────────────────────────────────────────────

def rapport_stock(output_path):
    conn  = get_connection()
    rows  = conn.execute(
        "SELECT nom,unite,stock_actuel,stock_minimum,prix_vente FROM produits ORDER BY nom"
    ).fetchall()
    conn.close()

    total_val = sum(r[2]*r[4] for r in rows)
    total_bts = sum(r[2] for r in rows)
    alertes   = sum(1 for r in rows if r[2] <= r[3])
    now       = datetime.now().strftime("%d/%m/%Y %H:%M")

    doc   = _doc(output_path)
    story = [
        _p(f"{BOUTIQUE_NOM} — État du Stock", 16, bold=True, color=BLEU),
        _p(f"Généré le {now}", 9, color=colors.gray),
        HRFlowable(width="100%", thickness=1, color=CYAN, spaceAfter=10),
    ]

    # Résumé
    res = Table(
        [["Produits","Total en stock","Valeur totale","Alertes"],
         [str(len(rows)), str(total_bts), f"{total_val:,.0f} {MONNAIE}", str(alertes)]],
        colWidths=[4*cm, 4*cm, 5*cm, 4*cm])
    res.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0), BLEU),
        ("TEXTCOLOR",     (0,0),(-1,0), BLANC),
        ("FONTNAME",      (0,0),(-1,0), "Helvetica-Bold"),
        ("BACKGROUND",    (0,1),(-1,1), GRIS),
        ("FONTNAME",      (0,1),(-1,1), "Helvetica-Bold"),
        ("FONTSIZE",      (0,1),(-1,1), 13),
        ("TEXTCOLOR",     (3,1),(3,1),  ROUGE if alertes > 0 else VERT),
        ("ALIGN",         (0,0),(-1,-1),"CENTER"),
        ("TOPPADDING",    (0,0),(-1,-1), 7),
        ("BOTTOMPADDING", (0,0),(-1,-1), 7),
        ("GRID",          (0,0),(-1,-1), 0.4, colors.HexColor("#ccddee")),
    ]))
    story += [res, Spacer(1,10),
              _p("Détail par produit", 11, bold=True, color=BLEU)]

    data = [["Produit","Unité","Stock","Min","Prix","Valeur","Statut"]]
    for r in rows:
        data.append([r[0], r[1], str(r[2]), str(r[3]),
                     f"{r[4]:.0f}", f"{r[2]*r[4]:,.0f}",
                     "Bas" if r[2] <= r[3] else "OK"])
    t = Table(data, colWidths=[4.5*cm,2*cm,2.5*cm,2.5*cm,2.5*cm,3*cm,1.8*cm])
    s = _tbl_style(CYAN)
    for i, r in enumerate(rows, 1):
        if r[2] <= r[3]:
            s.add("TEXTCOLOR", (6,i),(6,i), ROUGE)
            s.add("FONTNAME",  (0,i),(-1,i),"Helvetica-Bold")
        else:
            s.add("TEXTCOLOR", (6,i),(6,i), VERT)
    t.setStyle(s)
    story.append(t)
    doc.build(story)
    return output_path


# ── Rapport Achats ───────────────────────────────────────────────────────────

def rapport_achats(output_path, date_debut, date_fin):
    conn = get_connection()
    rows = conn.execute("""
        SELECT a.date_achat,
               COALESCE(p.nom, a.produit_nom, '[produit supprimé]'),
               a.quantite, a.prix_unitaire, a.prix_total,
               COALESCE(a.notes,'-')
        FROM achats a
        LEFT JOIN produits p ON a.produit_id = p.id
        WHERE a.date_achat BETWEEN ? AND ?
        ORDER BY a.date_achat DESC
    """, (date_debut, date_fin + " 23:59:59")).fetchall()
    conn.close()

    total = sum(r[4] for r in rows)
    bts   = sum(r[2] for r in rows)
    now   = datetime.now().strftime("%d/%m/%Y %H:%M")

    doc   = _doc(output_path)
    story = [
        _p(f"{BOUTIQUE_NOM} — Rapport Achats", 16, bold=True, color=BLEU),
        _p(f"Période : {date_debut} → {date_fin}  |  Généré le {now}", 9, color=colors.gray),
        HRFlowable(width="100%", thickness=1, color=ORANGE, spaceAfter=10),
    ]

    res = Table(
        [["Nb lignes","Paquets achetés","Total dépensé"],
         [str(len(rows)), str(bts), f"{total:,.0f} {MONNAIE}"]],
        colWidths=[5*cm, 6*cm, 6*cm])
    res.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0), BLEU), ("TEXTCOLOR",(0,0),(-1,0),BLANC),
        ("FONTNAME",      (0,0),(-1,0), "Helvetica-Bold"),
        ("BACKGROUND",    (0,1),(-1,1), GRIS),
        ("FONTNAME",      (0,1),(-1,1), "Helvetica-Bold"), ("FONTSIZE",(0,1),(-1,1),13),
        ("TEXTCOLOR",     (2,1),(2,1),  ROUGE),
        ("ALIGN",         (0,0),(-1,-1),"CENTER"),
        ("TOPPADDING",    (0,0),(-1,-1), 7), ("BOTTOMPADDING",(0,0),(-1,-1),7),
        ("GRID",          (0,0),(-1,-1), 0.4, colors.HexColor("#ccddee")),
    ]))
    story += [res, Spacer(1,10), _p("Liste des achats", 11, bold=True, color=BLEU)]

    data = [["Date","Produit","Qté","Prix unit.","Total","Notes"]]
    for r in rows:
        data.append([str(r[0])[:10], r[1], str(r[2]),
                     f"{r[3]:.0f}", f"{r[4]:,.0f}", str(r[5])[:25]])
    t = Table(data, colWidths=[2.5*cm, 5*cm, 1.5*cm, 2.5*cm, 3*cm, 3.5*cm])
    t.setStyle(_tbl_style(ORANGE))
    story.append(t)
    doc.build(story)
    return output_path


# ── Rapport Ventes ───────────────────────────────────────────────────────────

def rapport_ventes(output_path, date_debut, date_fin):
    conn = get_connection()
    rows = conn.execute("""
        SELECT v.date_vente,
               COALESCE(p.nom, v.produit_nom, '[produit supprimé]'),
               v.quantite, COALESCE(v.paquets_offerts,0),
               v.prix_unitaire, v.prix_total,
               COALESCE(v.client,'-'), COALESCE(v.notes,'-')
        FROM ventes v
        LEFT JOIN produits p ON v.produit_id = p.id
        WHERE v.date_vente BETWEEN ? AND ?
        ORDER BY v.date_vente DESC
    """, (date_debut, date_fin + " 23:59:59")).fetchall()
    conn.close()

    total = sum(r[5] for r in rows)
    bts   = sum(r[2] for r in rows)
    now   = datetime.now().strftime("%d/%m/%Y %H:%M")

    doc   = _doc(output_path)
    story = [
        _p(f"{BOUTIQUE_NOM} — Rapport Ventes", 16, bold=True, color=BLEU),
        _p(f"Période : {date_debut} → {date_fin}  |  Généré le {now}", 9, color=colors.gray),
        HRFlowable(width="100%", thickness=1, color=VERT, spaceAfter=10),
    ]

    res = Table(
        [["Nb ventes","Paquets vendus","Total recettes"],
         [str(len(rows)), str(bts), f"{total:,.0f} {MONNAIE}"]],
        colWidths=[5*cm, 6*cm, 6*cm])
    res.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0), BLEU), ("TEXTCOLOR",(0,0),(-1,0),BLANC),
        ("FONTNAME",      (0,0),(-1,0), "Helvetica-Bold"),
        ("BACKGROUND",    (0,1),(-1,1), GRIS),
        ("FONTNAME",      (0,1),(-1,1), "Helvetica-Bold"), ("FONTSIZE",(0,1),(-1,1),13),
        ("TEXTCOLOR",     (2,1),(2,1),  VERT),
        ("ALIGN",         (0,0),(-1,-1),"CENTER"),
        ("TOPPADDING",    (0,0),(-1,-1), 7), ("BOTTOMPADDING",(0,0),(-1,-1),7),
        ("GRID",          (0,0),(-1,-1), 0.4, colors.HexColor("#ccddee")),
    ]))
    story += [res, Spacer(1,10), _p("Liste des ventes", 11, bold=True, color=BLEU)]

    data = [["Date","Produit","Qté","Offerts","Prix","Total","Client"]]
    for r in rows:
        data.append([str(r[0])[:10], r[1], str(r[2]),
                     f"+{r[3]}" if r[3] > 0 else "—",
                     f"{r[4]:.0f}", f"{r[5]:,.0f}", r[6]])
    t = Table(data, colWidths=[2.5*cm, 4.5*cm, 1.5*cm, 1.8*cm, 2.3*cm, 3*cm, 2.4*cm])
    t.setStyle(_tbl_style(VERT))
    story.append(t)
    doc.build(story)
    return output_path
