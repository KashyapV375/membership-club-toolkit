"""Step 2: clean the survey responses, link each one to a customer, and split by customer type.

Survey exports are messy in their own way: the column names are whole questions, people type
"4/5" or "four" where a number should be, some answer twice, and some leave the email blank.
This script fixes that, matches every response to a row in the clean customer list
(by email, then by phone), and reports the key numbers for each membership tier.

Input:  data/raw/survey_responses.csv, data/clean/customers_clean.csv
Output: data/clean/survey_linked.csv     - one row per person who answered, with their customer_id
        reports/survey_by_tier.csv       - satisfaction, recommend score and contact count by tier

Run:  python link_surveys.py      (after clean_customers.py)
"""
import pandas as pd

from clean_customers import clean_email, clean_phone

NUMBER_WORDS = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
SHORT_NAMES = {"Timestamp": "answered_on", "Email": "email", "Phone": "phone"}


def parse_score(value, lowest, highest):
    """Pull the number out of answers like '4', ' 4/5 ', 'four' or '9 - definitely'.

    Returns None if there is no usable number or it is outside lowest..highest.
    """
    if pd.isna(value):
        return None
    text = str(value).strip().lower()
    if text in NUMBER_WORDS:
        number = NUMBER_WORDS[text]
    else:
        digits = ""
        for ch in text:                 # read digits from the start, stop at the first non-digit
            if ch.isdigit():
                digits += ch
            elif digits:
                break
        if not digits:
            return None
        number = int(digits)
    return number if lowest <= number <= highest else None


def rename_columns(df):
    """Replace the long question text with short column names."""
    names = dict(SHORT_NAMES)
    for column in df.columns:
        question = column.lower()
        if "satisfied" in question:
            names[column] = "satisfaction"
        elif "recommend" in question:
            names[column] = "recommend"
        elif "contact" in question:
            names[column] = "contacts_per_year"
    return df.rename(columns=names)


def net_promoter_score(scores):
    """NPS = % who answer 9 or 10, minus % who answer 0 to 6."""
    scores = scores.dropna()
    if len(scores) == 0:
        return None
    return round(((scores >= 9).mean() - (scores <= 6).mean()) * 100)


def main():
    customers = pd.read_csv("data/clean/customers_clean.csv", dtype={"phone": str})
    survey = rename_columns(pd.read_csv("data/raw/survey_responses.csv", dtype=str))
    rows_read = len(survey)

    survey["email"] = survey["email"].apply(clean_email)
    survey["phone"] = survey["phone"].apply(clean_phone)
    survey["satisfaction"] = survey["satisfaction"].apply(parse_score, args=(1, 5))
    survey["recommend"] = survey["recommend"].apply(parse_score, args=(0, 10))
    survey["contacts_per_year"] = pd.to_numeric(survey["contacts_per_year"], errors="coerce")
    unreadable = int(survey["satisfaction"].isna().sum())

    # link each response to a customer: email first, phone second
    by_email = dict(zip(customers["email"].dropna(), customers["customer_id"]))
    by_phone = dict(zip(customers["phone"].dropna(), customers["customer_id"]))
    survey["customer_id"] = survey["email"].map(by_email)
    by_phone_only = survey["customer_id"].isna() & survey["phone"].notna()
    survey.loc[by_phone_only, "customer_id"] = survey.loc[by_phone_only, "phone"].map(by_phone)
    linked_by_phone = int((by_phone_only & survey["customer_id"].notna()).sum())
    not_linked = int(survey["customer_id"].isna().sum())

    # one answer per person: keep the most recent
    linked = survey.dropna(subset=["customer_id"]).sort_values("answered_on")
    repeats = int(linked.duplicated("customer_id").sum())
    linked = linked.drop_duplicates("customer_id", keep="last")

    linked = linked.merge(customers[["customer_id", "tier", "status", "total_spent"]], on="customer_id")
    columns = ["customer_id", "tier", "status", "answered_on", "satisfaction", "recommend",
               "contacts_per_year", "total_spent"]
    linked[columns].sort_values("customer_id").to_csv("data/clean/survey_linked.csv", index=False)

    rows = []
    for tier in ["Bronze", "Silver", "Gold"]:
        group = linked[linked["tier"] == tier]
        members_in_tier = int((customers["tier"] == tier).sum())
        rows.append({"tier": tier,
                     "responses": len(group),
                     "response_rate_pct": round(len(group) / members_in_tier * 100, 1),
                     "avg_satisfaction": round(group["satisfaction"].mean(), 2),
                     "net_promoter_score": net_promoter_score(group["recommend"]),
                     "avg_contacts_per_year": round(group["contacts_per_year"].mean(), 2)})
    by_tier = pd.DataFrame(rows)
    by_tier.to_csv("reports/survey_by_tier.csv", index=False)

    by_status = linked.groupby("status").agg(responses=("satisfaction", "count"),
                                             avg_satisfaction=("satisfaction", "mean")).round(2)

    print("Survey linking report")
    print("---------------------")
    print(f"Responses read:                  {rows_read}")
    print(f"Linked to a customer by email:   {rows_read - not_linked - linked_by_phone}")
    print(f"Linked by phone (no email given): {linked_by_phone}")
    print(f"Could not be linked:             {not_linked}")
    print(f"Repeat answers removed:          {repeats}")
    print(f"Satisfaction answers unreadable: {unreadable}")
    print(f"People in the final file:        {len(linked)}\n")
    print(by_tier.to_string(index=False))
    print()
    print(by_status.to_string())
    print("\nSaved data/clean/survey_linked.csv and reports/survey_by_tier.csv")


if __name__ == "__main__":
    main()
