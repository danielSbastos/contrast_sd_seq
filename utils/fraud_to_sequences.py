"""
PKDD'99 Czech Financial Dataset - Rich Event Sequences (Dynamic Demographics, No ACCOUNT_OPENED)
Includes: transactions, loans, cards, standing orders,
and demographic markers (age, gender, income, crime, education).
Removes redundant ACCOUNT_OPENED event.
"""

import os
import pandas as pd
from tqdm import tqdm

DATA_DIR = "data/data_berka/"
OUTPUT_FILE = "data/pkdd_sequences_rich_full.dat"
MIN_SEQ_LEN = 1
RARE_THRESHOLD = 0.00

# ----------------------------------------------------
# Utilities
# ----------------------------------------------------
def load_table(name):
    for ext in [".asc", ".csv", ".txt"]:
        path = os.path.join(DATA_DIR, name + ext)
        if os.path.exists(path):
            return pd.read_csv(path, sep=";", encoding="latin-1")
    raise FileNotFoundError(f"File for table '{name}' not found in {DATA_DIR}")

def clean_str(x):
    if pd.isna(x) or str(x).strip() == "":
        return None
    return str(x).strip().replace(" ", "_").upper()

def translate_operation(op):
    op = clean_str(op)
    mapping = {
        "VKLAD": "DEPOSIT",
        "VYBER": "CARD_WITHDRAWAL",
        "VYBER_KARTOU": "CARD_WITHDRAWAL",
        "PREVOD_Z_UCTU": "TRANSFER_FROM",
        "PREVOD_NA_UCET": "TRANSFER_TO",
        "PRIJEM": "CREDIT",
        "VYDAJ": "DEBIT",
    }
    return mapping.get(op, op)

def discretize_amount(x):
    try:
        x = float(x)
    except:
        return "UNK"
    if x < 1000: return "A"
    elif x < 5000: return "B"
    elif x < 10000: return "C"
    elif x < 50000: return "D"
    else: return "E"

def bucket_gap(days):
    if days <= 1: return "GAP_SHORT"
    elif days <= 7: return "GAP_MED"
    elif days <= 30: return "GAP_LONG"
    else: return "GAP_VLONG"

def discretize_loan_amount(x):
    try:
        x = float(x)
    except:
        return "UNK"
    if x < 50000: return "SMALL"
    elif x < 150000: return "MEDIUM"
    else: return "LARGE"

# ----------------------------------------------------
# Load tables
# ----------------------------------------------------
print("Loading PKDD'99 tables ...")
account = load_table("account")
loan = load_table("loan")
trans = load_table("trans")
disp = load_table("disp")
client = load_table("client")
district = load_table("district")
card = load_table("card")
order = load_table("order")

print(f"{len(account)} accounts, {len(trans)} transactions, {len(loan)} loans")

# ----------------------------------------------------
# Compute dynamic thresholds for regional demographics
# ----------------------------------------------------
for col in ["A10", "A13", "A15"]:
    district[col] = pd.to_numeric(district[col], errors="coerce")

income_thresh = district["A10"].median(skipna=True)
edu_thresh = district["A13"].median(skipna=True)
crime_thresh = district["A15"].median(skipna=True)

print("\nDynamic thresholds:")
print(f"  Income (A10): median = {income_thresh:.2f}")
print(f"  Education (A13): median = {edu_thresh:.2f}")
print(f"  Crime rate (A15): median = {crime_thresh:.4f}")

# ----------------------------------------------------
# Risk labeling
# ----------------------------------------------------
# Default: risky if status is D (defaulted)
# Optionally include B (written off) to reduce imbalance
loan["risky"] = loan["status"].isin(["B", "D"])

loan_info = loan[["account_id", "risky"]]
account = account.merge(loan_info, on="account_id", how="left")
account["risky"] = account["risky"].fillna(False)

# ----------------------------------------------------
# Transaction encoding
# ----------------------------------------------------
trans = trans.merge(account[["account_id", "risky"]], on="account_id", how="left")
trans["date"] = pd.to_datetime(trans["date"].astype(str), format="%y%m%d", errors="coerce")
trans = trans.sort_values(["account_id", "date"])
trans["delta_days"] = trans.groupby("account_id")["date"].diff().dt.days.fillna(0)
trans["gap_bucket"] = trans["delta_days"].apply(bucket_gap)

main_ops = {"DEPOSIT", "CARD_WITHDRAWAL", "TRANSFER_TO", "TRANSFER_FROM", "CREDIT", "DEBIT"}
trans["op_clean"] = trans["operation"].apply(translate_operation)
op_counts = trans.loc[~trans["op_clean"].isin(main_ops), "op_clean"].value_counts()
freq_threshold = RARE_THRESHOLD * len(trans)
common_ops = op_counts[op_counts >= freq_threshold].index.tolist()

def encode_transaction_expanded(row):
    ttype = clean_str(row.get("type", ""))
    op = translate_operation(row.get("operation", None))
    if op is None:
        return None
    amt = discretize_amount(row.get("amount", 0))
    gap = row.get("gap_bucket", "")
    if "DEPOSIT" in op or "CREDIT" in ttype:
        base = "DEPOSIT"
    elif "WITHDRAW" in op or "CARD_WITHDRAWAL" in op or "DEBIT" in ttype:
        base = "CARD_WITHDRAWAL" if "CARD_WITHDRAWAL" in op else "WITHDRAW"
    elif "TRANSFER_TO" in op:
        base = "TRANSFER"
    elif "TRANSFER_FROM" in op:
        base = "TRANSFER_IN"
    else:
        base = clean_str(row.get("operation", ttype))
        if base is None:
            return None
        if base not in common_ops:
            base = f"MISC_{base}"
    return f"{base}_{amt}" + (f"_{gap}" if gap else "")

print("Encoding transaction events ...")
tqdm.pandas()
trans["event"] = trans.progress_apply(encode_transaction_expanded, axis=1)
trans = trans.dropna(subset=["event"])

# ----------------------------------------------------
# Loan events
# ----------------------------------------------------
loan["date"] = pd.to_datetime(loan["date"].astype(str), format="%y%m%d", errors="coerce")
loan["loan_event"] = loan.apply(
    lambda r: f"LOAN_TAKEN_{discretize_loan_amount(r['amount'])}", axis=1
)
loan["loan_status_event"] = loan["status"].map({
    "A": "LOAN_REPAID",
    "B": "LOAN_WRITTEN_OFF",
    "C": "LOAN_RUNNING",
    "D": "LOAN_DEFAULTED"
})

# ----------------------------------------------------
# Card issuance events
# ----------------------------------------------------
card["issued"] = pd.to_datetime(card["issued"].astype(str), format="%y%m%d", errors="coerce")
card["card_event"] = "CARD_ISSUED_" + card["type"].astype(str)

# ----------------------------------------------------
# Standing order events
# ----------------------------------------------------
order["order_event"] = "STANDING_ORDER_CREATED"

# ----------------------------------------------------
# Demographic profile encoding (age, gender, income, crime, education)
# ----------------------------------------------------
def encode_client_demographics(client_row, district_row):
    birth = str(client_row.get("birth_number", ""))
    if len(birth) < 6:
        age_group, gender = "UNK", "UNK"
    else:
        year = int(birth[:2])
        year = 1900 + year if year > 24 else 2000 + year
        age = 2025 - year
        age_group = "YOUNG" if age < 30 else "MID" if age < 50 else "OLD"
        gender = "MALE" if int(birth[2:4]) < 50 else "FEMALE"

    events = [f"PROFILE_{age_group}_{gender}"]

    if district_row is not None:
        try:
            income = float(district_row["A10"])
            events.append("PROFILE_REGION_HIGH_INCOME" if income >= income_thresh else "PROFILE_REGION_LOW_INCOME")
        except:
            pass

        try:
            crime = float(district_row["A15"])
            events.append("PROFILE_REGION_HIGH_CRIME" if crime >= crime_thresh else "PROFILE_REGION_LOW_CRIME")
        except:
            pass

        try:
            edu = float(district_row["A13"])
            events.append("PROFILE_REGION_HIGH_EDU" if edu >= edu_thresh else "PROFILE_REGION_LOW_EDU")
        except:
            pass

    return events

# ----------------------------------------------------
# Merge all into sequences
# ----------------------------------------------------
print("Merging transactions, loans, and extra events into sequences ...")
merged_sequences = []

for acc_id, acc_trans in trans.groupby("account_id"):
    acc_loans = loan[loan["account_id"] == acc_id]
    acc_orders = order[order["account_id"] == acc_id]
    acc_disp = disp[disp["account_id"] == acc_id]
    acc_cards = card[card["disp_id"].isin(acc_disp["disp_id"])]

    df_t = acc_trans[["date", "event"]].rename(columns={"event": "item"})
    df_l = pd.concat([
        acc_loans[["date", "loan_event"]].rename(columns={"loan_event": "item"}),
        acc_loans[["date", "loan_status_event"]].rename(columns={"loan_status_event": "item"})
    ], ignore_index=True)
    df_c = acc_cards[["issued", "card_event"]].rename(columns={"issued": "date", "card_event": "item"})
    df_o = acc_orders.assign(date=pd.NaT)[["date", "order_event"]].rename(columns={"order_event": "item"})

    frames = [df_t, df_l, df_c, df_o]
    df_all = pd.concat(frames, ignore_index=True)
    df_all = df_all.dropna(subset=["item"])
    df_all["date"] = pd.to_datetime(df_all["date"], errors="coerce")
    df_all = df_all.sort_values("date")

    grouped = df_all.groupby("date", dropna=True)["item"].apply(list).reset_index()
    itemsets = grouped["item"].tolist()

    # Demographic profile (once at start)
    if len(acc_disp):
        client_id = acc_disp.iloc[0]["client_id"]
        c_row = client[client["client_id"] == client_id].iloc[0]
        idx = int(c_row["district_id"]) - 1  # 1-based index
        d_row = district.iloc[idx] if 0 <= idx < len(district) else None
        profile_items = encode_client_demographics(c_row, d_row)
        itemsets.insert(0, profile_items)

    # Append LOAN_DEFAULTED if risky
    if account.loc[account["account_id"] == acc_id, "risky"].any():
        itemsets.append(["LOAN_DEFAULTED"])

    if len(itemsets) >= MIN_SEQ_LEN:
        merged_sequences.append((acc_id, itemsets))

print(f"Merged {len(merged_sequences)} account sequences.")

# ----------------------------------------------------
# Write sequences to output
# ----------------------------------------------------
print(f"Writing labeled sequences → {OUTPUT_FILE}")
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for acc_id, itemsets in merged_sequences:
        label = 1 if account.loc[account["account_id"] == acc_id, "risky"].any() else 0
        seq_parts = []
        for items in itemsets:
            seq_parts.append(" ".join(items) + " -1")
        seq_line = f"{label} " + " ".join(seq_parts) + " -2"
        f.write(seq_line + "\n")

print("✅ Done.")
print(f"Saved {len(merged_sequences)} labeled sequences to '{OUTPUT_FILE}'")

# ----------------------------------------------------
# Print class balance
# ----------------------------------------------------
n_pos = sum(account["risky"])
n_total = len(account)
print(f"\nClass Distribution (Total {n_total} accounts):")
print(f"  Class '1' (risky): {n_pos} ({n_pos/n_total:.4%})")
print(f"  Class '0' (safe):  {n_total - n_pos} ({1 - n_pos/n_total:.4%})")

# ----------------------------------------------------
# Print event alphabet
# ----------------------------------------------------
all_events = set(trans["event"].unique().tolist())
all_loan_events = set(loan["loan_event"].unique().tolist())
all_loan_status = set(loan["loan_status_event"].unique().tolist())
all_card_events = set(card["card_event"].unique().tolist())
all_profile = {
    "PROFILE_YOUNG_MALE", "PROFILE_YOUNG_FEMALE",
    "PROFILE_MID_MALE", "PROFILE_MID_FEMALE",
    "PROFILE_OLD_MALE", "PROFILE_OLD_FEMALE",
    "PROFILE_REGION_HIGH_INCOME", "PROFILE_REGION_LOW_INCOME",
    "PROFILE_REGION_HIGH_CRIME", "PROFILE_REGION_LOW_CRIME",
    "PROFILE_REGION_HIGH_EDU", "PROFILE_REGION_LOW_EDU"
}
all_events.update(all_loan_events)
all_events.update(all_loan_status)
all_events.update(all_card_events)
all_events.update(all_profile)
all_events.add("LOAN_DEFAULTED")

print("\nFull event alphabet:")
for ev in sorted(all_events):
    print(ev)
