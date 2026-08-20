"""
reduction.py — Calcul automatique des reductions par palier
Exemple : palier=10, reduction_qte=2
  - 10 paquets achetes  → 2 paquets offerts  (total recu: 12)
  - 15 paquets achetes  → 2 paquets offerts  (10 en reduction + 5 au prix normal)
  - 20 paquets achetes  → 4 paquets offerts  (2x palier)
  - 25 paquets achetes  → 4 paquets offerts  (2x palier + 5 au prix normal)
"""


def calculer_reduction(quantite: int, palier: int, reduction_qte: int, prix_unitaire: float):
    """
    Retourne un dict avec :
      - nb_paliers       : nombre de fois le palier est atteint
      - paquets_offerts  : nombre de paquets gratuits
      - qte_payante      : quantite reellement payee
      - prix_total       : prix total apres reduction
      - economie         : montant economise
      - detail           : texte explicatif
    """
    if palier <= 0 or reduction_qte <= 0:
        return {
            "nb_paliers": 0,
            "paquets_offerts": 0,
            "qte_payante": quantite,
            "prix_total": quantite * prix_unitaire,
            "economie": 0,
            "detail": ""
        }

    nb_paliers      = quantite // palier
    paquets_offerts = nb_paliers * reduction_qte
    qte_payante     = quantite  # on paie la quantite commandee, on recoit en plus
    prix_total      = qte_payante * prix_unitaire
    economie        = paquets_offerts * prix_unitaire

    if nb_paliers > 0:
        detail = (
            f"{nb_paliers}x palier de {palier} → "
            f"+{paquets_offerts} paquet(s) offert(s) "
            f"(economie : {economie:,.0f})"
        )
    else:
        detail = f"Pas encore {palier} paquets — pas de reduction"

    return {
        "nb_paliers": nb_paliers,
        "paquets_offerts": paquets_offerts,
        "qte_payante": qte_payante,
        "prix_total": prix_total,
        "economie": economie,
        "detail": detail
    }
