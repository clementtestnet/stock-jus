# reduction.py — Calcul réduction par palier
# Exemple palier=10, offerts=2 :
#   10 paquets → +2 offerts (reçoit 12)
#   15 paquets → +2 offerts (reçoit 17)
#   20 paquets → +4 offerts (reçoit 24)

def calculer_reduction(quantite, palier, reduction_qte, prix_unitaire):
    if palier <= 0 or reduction_qte <= 0:
        return {"nb_paliers":0,"paquets_offerts":0,"qte_payante":quantite,
                "prix_total":quantite*prix_unitaire,"economie":0,"detail":""}
    nb_paliers      = quantite // palier
    paquets_offerts = nb_paliers * reduction_qte
    prix_total      = quantite * prix_unitaire
    economie        = paquets_offerts * prix_unitaire
    detail = (f"{nb_paliers}x palier de {palier} -> +{paquets_offerts} offert(s) "
              f"(economie: {economie:,.0f} {' '})" if nb_paliers > 0
              else f"Pas encore {palier} paquets - pas de reduction")
    return {"nb_paliers":nb_paliers,"paquets_offerts":paquets_offerts,
            "qte_payante":quantite,"prix_total":prix_total,
            "economie":economie,"detail":detail}
