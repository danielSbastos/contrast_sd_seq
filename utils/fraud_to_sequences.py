"""
PKDD'99 Czech Financial Dataset - Rich Event Sequences
Dataset: https://relational.fel.cvut.cz/dataset/Financial
"""

import os
import pandas as pd
from tqdm import tqdm

DATA_DIR = "data/data_berka/"
OUTPUT_FILE = "data/pkdd_sequences_rich_expanded.dat"
MIN_SEQ_LEN = 1
RARE_THRESHOLD = 0.00

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

print("Loading PKDD'99 tables ...")
account = load_table("account")
loan = load_table("loan")
trans = load_table("trans")
print(f"{len(account)} accounts, {len(trans)} transactions, {len(loan)} loans")

# Identify risky loans
loan["risky"] = loan["status"].isin(["D"])
loan_info = loan[["account_id", "risky"]]
account = account.merge(loan_info, on="account_id", how="left")
account["risky"] = account["risky"].fillna(False)

# Merge risk info into transactions
trans = trans.merge(account[["account_id", "risky"]], on="account_id", how="left")
trans["date"] = pd.to_datetime(trans["date"].astype(str), format="%y%m%d", errors="coerce")
trans = trans.sort_values(["account_id", "date"])

# Compute gap between transactions
trans["delta_days"] = trans.groupby("account_id")["date"].diff().dt.days.fillna(0)
trans["gap_bucket"] = trans["delta_days"].apply(bucket_gap)

# Identify OTHER / rare operations
main_ops = {"DEPOSIT", "CARD_WITHDRAWAL", "TRANSFER_TO", "TRANSFER_FROM", "CREDIT", "DEBIT"}
trans["op_clean"] = trans["operation"].apply(translate_operation)

op_counts = trans.loc[~trans["op_clean"].isin(main_ops), "op_clean"].value_counts()
freq_threshold = RARE_THRESHOLD * len(trans)
common_ops = op_counts[op_counts >= freq_threshold].index.tolist()

def encode_transaction_expanded(row):
    ttype = clean_str(row.get("type", ""))
    op = translate_operation(row.get("operation", None))
    if op is None:
        return None  # drop NONE events

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
        base = clean_str(row.get("operation", ttype), default=None)
        if base is None:
            return None  # drop rare/none
        if base not in common_ops:
            base = f"MISC_{base}"

    return f"{base}_{amt}" + (f"_{gap}" if gap else "")

print("Encoding transaction events ...")
tqdm.pandas()
trans["event"] = trans.progress_apply(encode_transaction_expanded, axis=1)
trans = trans.dropna(subset=["event"])  # remove NONE events

# Encode loan events
loan["date"] = pd.to_datetime(loan["date"].astype(str), format="%y%m%d", errors="coerce")
loan["loan_event"] = loan.apply(
    lambda r: f"LOAN_TAKEN_{discretize_loan_amount(r['amount'])}", axis=1
)

# Merge transactions and loans into sequences
print("Merging transactions and loans into sequences ...")
merged_sequences = []

for acc_id, acc_trans in trans.groupby("account_id"):
    acc_loans = loan[loan["account_id"] == acc_id]

    df_t = acc_trans[["date", "event"]].rename(columns={"event": "item"})
    df_l = acc_loans[["date", "loan_event"]].rename(columns={"loan_event": "item"})

    df_all = pd.concat([df_t, df_l], ignore_index=True)
    df_all = df_all.dropna(subset=["date"]).sort_values("date")

    grouped = df_all.groupby("date")["item"].apply(list).reset_index()
    itemsets = grouped["item"].tolist()

    # Append LOAN_DEFAULTED if account is risky
    if account.loc[account["account_id"] == acc_id, "risky"].any():
        itemsets.append(["LOAN_DEFAULTED"])

    # Avoid starting sequence with rare MISC / OTHER
    while itemsets and all("MISC" in it or "OTHER" in it for it in itemsets[0]):
        first_itemset = itemsets.pop(0)
        if len(itemsets) == 0:
            itemsets = [first_itemset]
            break

    merged_sequences.append((acc_id, itemsets))

print(f"Merged {len(merged_sequences)} account sequences.")

# Write sequences to output
print(f"Writing labeled sequences → {OUTPUT_FILE}")
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for acc_id, itemsets in merged_sequences:
        label = 1 if account.loc[account["account_id"] == acc_id, "risky"].any() else 0
        if len(itemsets) >= MIN_SEQ_LEN:
            seq_parts = []
            for items in itemsets:
                seq_parts.append(" ".join(items) + " -1")
            seq_line = f"{label} " + " ".join(seq_parts) + " -2"
            f.write(seq_line + "\n")

print("✅ Done.")
print(f"Saved {len(merged_sequences)} labeled sequences to '{OUTPUT_FILE}'")

# Print full event alphabet
all_events = set(trans["event"].unique().tolist())
all_loan_events = set(loan["loan_event"].unique().tolist())
all_events.update(all_loan_events)
all_events.add("LOAN_DEFAULTED")

print("\nFull event alphabet:")
for ev in sorted(all_events):
    print(ev)
