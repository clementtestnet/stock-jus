# reduction.py
from config import MONNAIE

def calculer_reduction(quantite, palier, reduction_qte, prix_unitaire):
    if palier <= 0 or reduction_qte <= 0 or quantite <= 0:
        return {"nb_paliers": 0, "paquets_offerts": 0,
                "prix_total": quantite * prix_unitaire, "economie": 0, "detail": ""}
    nb_paliers      = quantite // palier
    paquets_offerts = nb_paliers * reduction_qte
    prix_total      = quantite * prix_unitaire
    economie        = paquets_offerts * prix_unitaire
    if nb_paliers > 0:
        detail = (f"{nb_paliers}x palier de {palier} "
                  f"→ +{paquets_offerts} offert(s) "
                  f"(économie: {economie:,.0f} {MONNAIE})")
    else:
        detail = f"Pas encore {palier} paquets — pas de réduction"
    return {"nb_paliers": nb_paliers, "paquets_offerts": paquets_offerts,
            "prix_total": prix_total, "economie": economie, "detail": detail}
