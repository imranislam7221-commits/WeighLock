# KG <-> Ton-KG display, DB te sobsomoy KG save hobe
def format_weight(kg, unit="KG"):
    try:
        kg = int(float(kg))
    except Exception:
        kg = 0
    if unit == "TON_KG":
        ton = kg // 1000
        rest = kg % 1000
        # ex: 1233 -> 1 Ton 233 Kg (1.233)
        return f"{ton} Ton {rest} Kg"
    return f"{kg} KG"


def format_weight_bn(kg, unit="KG"):
    # Bangla line er jonno
    en = format_weight(kg, unit)
    if unit == "TON_KG":
        try:
            kg = int(float(kg))
            return f"{kg//1000} টন {kg%1000} কেজি"
        except Exception:
            return en
    return f"{kg} কেজি"
