# pdf_export.py — Rapports PDF admin
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from datetime import datetime, date as ddate
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from database import get_connection
from config import MONNAIE, BOUTIQUE_NOM

BLEU=colors.HexColor("#1a2940"); CYAN=colors.HexColor("#4a90d9")
VERT=colors.HexColor("#27ae60"); ROUGE=colors.HexColor("#e74c3c")
ORANGE=colors.HexColor("#f39c12"); BLANC=colors.white; GRIS=colors.HexColor("#f0f4f8")

def _style(hc=None):
    hc=hc or CYAN
    return TableStyle([
        ("BACKGROUND",(0,0),(-1,0),hc),("TEXTCOLOR",(0,0),(-1,0),BLANC),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,0),9),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[BLANC,colors.HexColor("#eef3f9")]),
        ("FONTSIZE",(0,1),(-1,-1),8),("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#ccddee")),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
    ])

def _doc(path): return SimpleDocTemplate(path,pagesize=A4,leftMargin=2*cm,rightMargin=2*cm,topMargin=2*cm,bottomMargin=2*cm)
def _ts(): return ParagraphStyle("t",fontSize=16,textColor=BLEU,fontName="Helvetica-Bold",spaceAfter=3)
def _ss(): return ParagraphStyle("s",fontSize=9,textColor=colors.HexColor("#667788"),spaceAfter=8)
def _hs(): return ParagraphStyle("h",fontSize=11,textColor=BLEU,fontName="Helvetica-Bold",spaceBefore=12,spaceAfter=6)

def rapport_stock(output_path):
    doc=_doc(output_path); story=[]
    now=datetime.now().strftime("%d/%m/%Y %H:%M")
    story+=[Paragraph(f"{BOUTIQUE_NOM} — Etat du Stock",_ts()),
            Paragraph(f"Genere le {now}",_ss()),
            HRFlowable(width="100%",thickness=1,color=CYAN,spaceAfter=10)]
    conn=get_connection()
    rows=conn.execute("SELECT nom,unite,stock_actuel,stock_minimum,prix_vente FROM produits ORDER BY nom").fetchall()
    conn.close()
    total_val=sum(r[2]*r[4] for r in rows); total_bts=sum(r[2] for r in rows); alertes=sum(1 for r in rows if r[2]<=r[3])
    res=Table([["Produits","Total en stock","Valeur totale","Alertes"],[str(len(rows)),str(total_bts),f"{total_val:,.0f} {MONNAIE}",str(alertes)]],colWidths=[4*cm,4*cm,5*cm,4*cm])
    res.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),BLEU),("TEXTCOLOR",(0,0),(-1,0),BLANC),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("BACKGROUND",(0,1),(-1,1),GRIS),("FONTNAME",(0,1),(-1,1),"Helvetica-Bold"),("FONTSIZE",(0,1),(-1,1),13),("TEXTCOLOR",(3,1),(3,1),ROUGE if alertes>0 else VERT),("ALIGN",(0,0),(-1,-1),"CENTER"),("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7),("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#ccddee"))]))
    story+=[res,Spacer(1,10),Paragraph("Detail par produit",_hs())]
    data=[["Produit","Unite","Stock","Min","Prix","Valeur","Statut"]]
    for r in rows:
        data.append([r[0],r[1],str(r[2]),str(r[3]),f"{r[4]:.0f}",f"{r[2]*r[4]:,.0f}","Bas" if r[2]<=r[3] else "OK"])
    t=Table(data,colWidths=[4.5*cm,2*cm,2.5*cm,2.5*cm,2.5*cm,3*cm,1.8*cm])
    s=_style(CYAN)
    for i,r in enumerate(rows,1):
        if r[2]<=r[3]: s.add("TEXTCOLOR",(6,i),(6,i),ROUGE); s.add("FONTNAME",(0,i),(-1,i),"Helvetica-Bold")
        else: s.add("TEXTCOLOR",(6,i),(6,i),VERT)
    t.setStyle(s); story.append(t); doc.build(story); return output_path

def rapport_achats(output_path, date_debut, date_fin):
    doc=_doc(output_path); story=[]
    now=datetime.now().strftime("%d/%m/%Y %H:%M")
    story+=[Paragraph(f"{BOUTIQUE_NOM} — Rapport Achats",_ts()),
            Paragraph(f"Periode: {date_debut} -> {date_fin}  |  Genere le {now}",_ss()),
            HRFlowable(width="100%",thickness=1,color=ORANGE,spaceAfter=10)]
    conn=get_connection()
    rows=conn.execute("""SELECT a.date_achat,p.nom,COALESCE(f.nom,'-'),a.quantite,a.prix_unitaire,a.prix_total,COALESCE(a.notes,'-')
        FROM achats a JOIN produits p ON a.produit_id=p.id LEFT JOIN fournisseurs f ON a.fournisseur_id=f.id
        WHERE a.date_achat BETWEEN ? AND ? ORDER BY a.date_achat DESC""",(date_debut,date_fin+" 23:59:59")).fetchall()
    conn.close()
    total=sum(r[5] for r in rows); bts=sum(r[3] for r in rows)
    res=Table([["Nb lignes","Paquets achetes","Total depense"],[str(len(rows)),str(bts),f"{total:,.0f} {MONNAIE}"]],colWidths=[5*cm,6*cm,6*cm])
    res.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),BLEU),("TEXTCOLOR",(0,0),(-1,0),BLANC),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("BACKGROUND",(0,1),(-1,1),GRIS),("FONTNAME",(0,1),(-1,1),"Helvetica-Bold"),("FONTSIZE",(0,1),(-1,1),13),("TEXTCOLOR",(2,1),(2,1),ROUGE),("ALIGN",(0,0),(-1,-1),"CENTER"),("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7),("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#ccddee"))]))
    story+=[res,Spacer(1,10),Paragraph("Liste des achats",_hs())]
    data=[["Date","Produit","Fournisseur","Qte","Prix","Total","Notes"]]
    for r in rows: data.append([str(r[0])[:10],r[1],r[2],str(r[3]),f"{r[4]:.0f}",f"{r[5]:,.0f}",r[6][:25]])
    t=Table(data,colWidths=[2.3*cm,4*cm,3.5*cm,1.5*cm,2.3*cm,2.8*cm,3.3*cm])
    t.setStyle(_style(ORANGE)); story.append(t); doc.build(story); return output_path

def rapport_ventes(output_path, date_debut, date_fin):
    doc=_doc(output_path); story=[]
    now=datetime.now().strftime("%d/%m/%Y %H:%M")
    story+=[Paragraph(f"{BOUTIQUE_NOM} — Rapport Ventes",_ts()),
            Paragraph(f"Periode: {date_debut} -> {date_fin}  |  Genere le {now}",_ss()),
            HRFlowable(width="100%",thickness=1,color=VERT,spaceAfter=10)]
    conn=get_connection()
    rows=conn.execute("""SELECT v.date_vente,p.nom,v.quantite,COALESCE(v.paquets_offerts,0),v.prix_unitaire,v.prix_total,COALESCE(v.client,'-'),COALESCE(v.notes,'-')
        FROM ventes v JOIN produits p ON v.produit_id=p.id
        WHERE v.date_vente BETWEEN ? AND ? ORDER BY v.date_vente DESC""",(date_debut,date_fin+" 23:59:59")).fetchall()
    conn.close()
    total=sum(r[5] for r in rows); bts=sum(r[2] for r in rows)
    res=Table([["Nb ventes","Paquets vendus","Total recettes"],[str(len(rows)),str(bts),f"{total:,.0f} {MONNAIE}"]],colWidths=[5*cm,6*cm,6*cm])
    res.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),BLEU),("TEXTCOLOR",(0,0),(-1,0),BLANC),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("BACKGROUND",(0,1),(-1,1),GRIS),("FONTNAME",(0,1),(-1,1),"Helvetica-Bold"),("FONTSIZE",(0,1),(-1,1),13),("TEXTCOLOR",(2,1),(2,1),VERT),("ALIGN",(0,0),(-1,-1),"CENTER"),("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7),("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#ccddee"))]))
    story+=[res,Spacer(1,10),Paragraph("Liste des ventes",_hs())]
    data=[["Date","Produit","Qte","Offerts","Prix","Total","Client","Notes"]]
    for r in rows: data.append([str(r[0])[:10],r[1],str(r[2]),f"+{r[3]}" if r[3]>0 else "-",f"{r[4]:.0f}",f"{r[5]:,.0f}",r[6],r[7][:15]])
    t=Table(data,colWidths=[2.3*cm,3.5*cm,1.5*cm,1.8*cm,2.3*cm,2.8*cm,2.5*cm,2.6*cm])
    t.setStyle(_style(VERT)); story.append(t); doc.build(story); return output_path
