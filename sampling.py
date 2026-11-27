"""ISO 2859-1 single sampling plans: normal inspection, general inspection level II.

Only AQL 0.65, 1.0, 1.5, 2.5, 4.0 and 6.5 are supported. Any other value raises
ValueError rather than guessing a plan.

How Table II-A is encoded: every AQL column follows the same diagonal, shifted down
one code letter for each step to a tighter AQL. With k as the row of the column's
first 0/1 entry (A for 6.5, B for 4.0, C for 2.5, D for 1.5, E for 1.0, F for 0.65):

    rows above k   down arrow -> row k
    row k          Ac 0, Re 1
    row k+1        up arrow   -> row k
    row k+2        down arrow -> row k+3
    rows k+3..k+10 Ac 1, 2, 3, 5, 7, 10, 14, 21 (Re = Ac + 1)
    below k+10     up arrow   -> row k+10

Following an arrow changes the sample size as well as Ac and Re.
"""

# Table I, general inspection level II: (largest lot size, code letter). Larger lots use Q.
LEVEL_II = (
    (8, "A"), (15, "B"), (25, "C"), (50, "D"), (90, "E"), (150, "F"), (280, "G"),
    (500, "H"), (1200, "J"), (3200, "K"), (10000, "L"), (35000, "M"), (150000, "N"),
    (500000, "P"),
)
LETTERS = "ABCDEFGHJKLMNPQR"
SAMPLE_SIZES = (2, 3, 5, 8, 13, 20, 32, 50, 80, 125, 200, 315, 500, 800, 1250, 2000)
FIRST_ZERO_ROW = {6.5: 0, 4.0: 1, 2.5: 2, 1.5: 3, 1.0: 4, 0.65: 5}
DIAGONAL_AC = (1, 2, 3, 5, 7, 10, 14, 21)


def code_letter(lot_size):
    if type(lot_size) is not int or lot_size < 2:
        raise ValueError("lot size must be a whole number of at least 2")
    for largest, letter in LEVEL_II:
        if lot_size <= largest:
            return letter
    return "Q"


def plan(lot_size, aql):
    """Return the plan as a dict: code letter, plan letter, sample size, Ac, Re."""
    if type(aql) not in (int, float) or aql not in FIRST_ZERO_ROW:
        allowed = ", ".join(str(value) for value in sorted(FIRST_ZERO_ROW))
        raise ValueError(f"AQL must be one of {allowed}")
    letter = code_letter(lot_size)
    row, k = LETTERS.index(letter), FIRST_ZERO_ROW[aql]
    if row <= k + 1:
        row, accept = k, 0
    else:
        row = min(max(row, k + 3), k + 3 + len(DIAGONAL_AC) - 1, len(LETTERS) - 1)
        accept = DIAGONAL_AC[row - (k + 3)]
    size = SAMPLE_SIZES[row]
    return {
        "standard": "ISO 2859-1 single sampling, normal inspection, level II",
        "code_letter": letter,
        "plan_letter": LETTERS[row],
        "sample_size": min(size, lot_size),
        "full_inspection": size >= lot_size,
        "accept": accept,
        "reject": accept + 1,
    }


def check(sampling, result):
    """Validate a requirement's sampling record and return (applied plan, blockers)."""
    if not isinstance(sampling, dict) or sampling.keys() != {
        "lot_size", "aql", "inspected", "nonconforming"
    }:
        raise ValueError("sampling must contain exactly: lot_size aql inspected nonconforming")
    inspected, found = sampling["inspected"], sampling["nonconforming"]
    for name, value in (("inspected", inspected), ("nonconforming", found)):
        if type(value) is not int or value < 0:
            raise ValueError(f"sampling {name} must be a non-negative whole number")
    if found > inspected:
        raise ValueError("sampling nonconforming exceeds units inspected")
    if type(sampling["lot_size"]) is int and inspected > sampling["lot_size"]:
        raise ValueError("sampling inspected exceeds lot size")
    applied = plan(sampling["lot_size"], sampling["aql"])

    blockers = []
    if inspected < applied["sample_size"] and found < applied["reject"]:
        blockers.append(
            f'sample incomplete: plan needs {applied["sample_size"]} units, '
            f"{inspected} inspected"
        )
    if result == "pass" and found > applied["accept"]:
        blockers.append(
            f'recorded pass contradicts the plan: {found} nonconforming, Ac {applied["accept"]}'
        )
    return applied, blockers
