# reduction.py
from config import MONNAIE


def _fmt_qte(q):
    """Affiche 2.0 comme '2' et 1.5 comme '1.5'."""
    q = float(q)
    return str(int(q)) if q == int(q) else str(q)


def calculer_reduction(quantite, palier, reduction_qte, prix_unitaire):
    """quantite peut être un float (ex: 0.5, 1.5 pour demi-paquet)."""
    quantite = float(quantite)
    if palier <= 0 or reduction_qte <= 0 or quantite <= 0:
        return {"nb_paliers": 0, "paquets_offerts": 0.0,
                "prix_total": quantite * prix_unitaire, "economie": 0, "detail": ""}
    nb_paliers      = int(quantite // palier)   # réduction sur paquets entiers seulement
    paquets_offerts = float(nb_paliers * reduction_qte)
    prix_total      = quantite * prix_unitaire
    economie        = paquets_offerts * prix_unitaire
    if nb_paliers > 0:
        detail = (f"{nb_paliers}x palier de {_fmt_qte(palier)} "
                  f"→ +{_fmt_qte(paquets_offerts)} offert(s) "
                  f"(économie: {economie:,.0f} {MONNAIE})")
    else:
        detail = f"Pas encore {_fmt_qte(palier)} paquets — pas de réduction"
    return {"nb_paliers": nb_paliers, "paquets_offerts": paquets_offerts,
            "prix_total": prix_total, "economie": economie, "detail": detail}
