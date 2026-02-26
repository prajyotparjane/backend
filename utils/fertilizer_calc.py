def fertilizer_recommendation(deficiency):
    result = []

    N = deficiency.get("N", 0)
    P = deficiency.get("P", 0)
    K = deficiency.get("K", 0)

    # ---------- Nitrogen ----------
    if N > 0:
        if N < 20:
            result.append("Compost: 80–100 kg/acre")
            result.append("Neem Cake: 10–15 kg/acre")
            result.append("Vermicompost: 30–40 kg/acre")
        elif N <= 40:
            result.append("Compost: 150–200 kg/acre")
            result.append("Neem Cake: 25–40 kg/acre")
            result.append("Vermicompost: 60–80 kg/acre")
        else:
            result.append("Compost: 250–300 kg/acre")
            result.append("Neem Cake: 50–70 kg/acre")
            result.append("Vermicompost: 100–120 kg/acre")

    # ---------- Phosphorus ----------
    if P > 0:
        if P < 10:
            result.append("Rock Phosphate: 10–15 kg/acre")
        elif P <= 25:
            result.append("Rock Phosphate: 20–30 kg/acre")
        else:
            result.append("Rock Phosphate: 40–50 kg/acre")

    # ---------- Potassium ----------
    if K > 0:
        if K < 20:
            result.append("Wood Ash: 15–20 kg/acre")
        elif K <= 40:
            result.append("Wood Ash: 25–35 kg/acre")
        else:
            result.append("Wood Ash: 40–50 kg/acre")

    return result
