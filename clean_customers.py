"""Step 1: build one clean customer list out of three messy exports.

Input  (data/raw):   website_signups.csv, pos_sales_export.csv, newsletter_list.csv
Output (data/clean): customers_clean.csv  - one row per person
                     cleaning_report.txt  - what got fixed, so the numbers can be checked

Run:  python clean_customers.py
"""
import pandas as pd

RAW = "data/raw/"
CLEAN = "data/clean/"


def clean_email(value):
    """Lowercase, no spaces. Blank or broken emails become None."""
    if pd.isna(value):
        return None
    email = str(value).strip().lower()
    if "@" not in email or " " in email:
        return None
    return email


def clean_phone(value):
    """Keep only the 10 digits, so (210) 555-1234 and 210.555.1234 match."""
    if pd.isna(value):
        return None
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]          # drop the +1 country code
    return digits if len(digits) == 10 else None


def clean_name(value):
    """'  MAYA ' -> 'Maya'."""
    if pd.isna(value):
        return ""
    return str(value).strip().title()


def split_pos_name(value):
    """The register writes names as 'REYES, Maya'. Return ('Maya', 'Reyes')."""
    text = str(value)
    if "," in text:
        last, first = text.split(",", 1)
    else:
        parts = text.split()
        first, last = parts[0], " ".join(parts[1:])
    return clean_name(first), clean_name(last)


def yes_no(value):
    """'Y', 'yes', 'Yes' -> True.  'no', 'N', blank -> False."""
    return str(value).strip().lower() in ("y", "yes", "true", "1")


def load_members():
    """Website signups -> one row per member (people who signed up twice get merged)."""
    df = pd.read_csv(RAW + "website_signups.csv")
    rows_before = len(df)
    df["email"] = df["email"].apply(clean_email)
    df["phone"] = df["phone"].apply(clean_phone)
    df["first_name"] = df["first_name"].apply(clean_name)
    df["last_name"] = df["last_name"].apply(clean_name)
    df["tier"] = df["tier"].str.strip().str.title()
    df["status"] = df["status"].str.strip().str.lower()
    df["signup_date"] = pd.to_datetime(df["signup_date"])
    df["cancel_date"] = pd.to_datetime(df["cancel_date"])
    # same email = same person. Keep the earliest signup.
    df = df.sort_values("signup_date").drop_duplicates(subset="email", keep="first")
    return df, rows_before - len(df)


def load_sales(members):
    """Register sales -> totals per person. Rows with no email get matched by phone."""
    sales = pd.read_csv(RAW + "pos_sales_export.csv")
    sales["email"] = sales["email"].apply(clean_email)
    sales["phone"] = sales["phone"].apply(clean_phone)
    sales["order_date"] = pd.to_datetime(sales["order_date"])
    names = sales["customer_name"].apply(split_pos_name)
    sales["first_name"] = [n[0] for n in names]
    sales["last_name"] = [n[1] for n in names]

    # fill in a missing email when the phone number matches someone we already know
    phone_to_email = dict(zip(members["phone"], members["email"]))
    known = sales[sales["email"].notna()].drop_duplicates("phone")
    phone_to_email.update(dict(zip(known["phone"], known["email"])))
    missing = sales["email"].isna()
    sales.loc[missing, "email"] = sales.loc[missing, "phone"].map(phone_to_email)
    filled = int(missing.sum() - sales["email"].isna().sum())

    # anyone still without an email gets a key made from their phone so they are not lost
    sales["match_key"] = sales["email"].fillna("phone:" + sales["phone"].fillna("unknown"))
    return sales, int(missing.sum()), filled


def main():
    members, duplicate_signups = load_members()
    sales, blank_emails, filled_emails = load_sales(members)

    news = pd.read_csv(RAW + "newsletter_list.csv")
    news["email"] = news["Email Address"].apply(clean_email)
    news["newsletter"] = news["Subscribed"].apply(yes_no)
    news_dupes = int(news.duplicated("email").sum())
    news = news.drop_duplicates("email")[["email", "newsletter"]]

    # order totals per person
    totals = sales.groupby("match_key").agg(
        total_orders=("order_id", "count"),
        total_spent=("amount", "sum"),
        last_order_date=("order_date", "max"),
    ).reset_index()

    # start with members, then add customers who bought something but never joined
    customers = members.merge(totals, how="left", left_on="email", right_on="match_key")
    member_keys = set(members["email"])
    non_members = sales[~sales["match_key"].isin(member_keys)].drop_duplicates("match_key")
    non_members = non_members[["match_key", "first_name", "last_name", "email", "phone"]]
    non_members = non_members.merge(totals, on="match_key")
    non_members["tier"] = "None"
    non_members["status"] = "non-member"
    customers = pd.concat([customers, non_members], ignore_index=True)

    customers = customers.merge(news, how="left", on="email")
    customers["newsletter"] = customers["newsletter"].eq(True)   # not on the list = not subscribed
    customers["total_orders"] = customers["total_orders"].fillna(0).astype(int)
    customers["total_spent"] = customers["total_spent"].fillna(0).round(2)

    customers = customers.sort_values(["status", "last_name", "first_name"]).reset_index(drop=True)
    customers.insert(0, "customer_id", ["C" + str(1000 + i) for i in range(len(customers))])
    columns = ["customer_id", "first_name", "last_name", "email", "phone", "tier", "status",
               "signup_date", "cancel_date", "newsletter", "total_orders", "total_spent", "last_order_date"]
    customers = customers[columns]
    customers.to_csv(CLEAN + "customers_clean.csv", index=False, date_format="%Y-%m-%d")

    report = [
        "Cleaning report",
        "---------------",
        f"Signup rows read:                 {len(members) + duplicate_signups}",
        f"Duplicate signups merged:         {duplicate_signups}",
        f"Sales rows read:                  {len(sales)}",
        f"Sales rows with no email:         {blank_emails}",
        f"  ...matched to a person by phone: {filled_emails}",
        f"Duplicate newsletter rows removed: {news_dupes}",
        "",
        f"Final list: {len(customers)} people",
        f"  members (active):    {(customers['status'] == 'active').sum()}",
        f"  members (cancelled): {(customers['status'] == 'cancelled').sum()}",
        f"  non-members:         {(customers['status'] == 'non-member').sum()}",
        f"  missing an email:    {customers['email'].isna().sum()}",
        "",
        "Check: total spent in clean list = $" + f"{customers['total_spent'].sum():,.2f}",
        "       total in raw sales file   = $" + f"{sales['amount'].sum():,.2f}",
    ]
    with open(CLEAN + "cleaning_report.txt", "w") as f:
        f.write("\n".join(report) + "\n")
    print("\n".join(report))


if __name__ == "__main__":
    main()
