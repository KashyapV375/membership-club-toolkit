"""Step 3: decide which members should get which email, and write the drafts.

Nothing is sent. Every draft goes into outbox_for_review/ and is listed in
review_queue.csv with approved = NO, so a person has to read and approve it first.

Journeys:
  welcome      joined in the last 7 days
  anniversary  membership anniversary is in the next 7 days
  win_back     cancelled 30 to 120 days ago

People who are not on the newsletter list are skipped (they did not opt in).

Run:  python email_journeys.py
      python email_journeys.py 2026-12-31     (pretend today is a different date)
"""
import os
import sys

import pandas as pd

WELCOME_DAYS = 7
ANNIVERSARY_DAYS_AHEAD = 7
WIN_BACK_MIN_DAYS = 30
WIN_BACK_MAX_DAYS = 120
OUTBOX = "outbox_for_review/"


def days_until_anniversary(signup_date, today):
    """Days until the next anniversary of signup_date, and which year number it is."""
    years = today.year - signup_date.year
    try:
        next_one = signup_date.replace(year=today.year)
    except ValueError:                      # signed up on Feb 29
        next_one = signup_date.replace(year=today.year, day=28)
    if next_one < today:
        years += 1
        next_one = next_one.replace(year=today.year + 1)
    return (next_one - today).days, years


def pick_journey(row, today):
    """Return (journey_name, extra_info) for one customer, or (None, None)."""
    if row["status"] == "active":
        days_in = (today - row["signup_date"]).days
        if 0 <= days_in <= WELCOME_DAYS:
            return "welcome", {}
        days_left, years = days_until_anniversary(row["signup_date"], today)
        if years >= 1 and days_left <= ANNIVERSARY_DAYS_AHEAD:
            return "anniversary", {"years": years, "year_word": "year" if years == 1 else "years"}
    if row["status"] == "cancelled" and pd.notna(row["cancel_date"]):
        days_gone = (today - row["cancel_date"]).days
        if WIN_BACK_MIN_DAYS <= days_gone <= WIN_BACK_MAX_DAYS:
            return "win_back", {}
    return None, None


def load_template(name):
    """Templates are plain text. The first line is the subject."""
    with open(f"templates/{name}.txt") as f:
        text = f.read()
    subject, body = text.split("\n", 1)
    return subject.replace("Subject:", "").strip(), body.strip()


def main():
    customers = pd.read_csv("data/clean/customers_clean.csv", parse_dates=["signup_date", "cancel_date"])
    if len(sys.argv) > 1:
        today = pd.Timestamp(sys.argv[1])
    else:
        today = max(customers["signup_date"].max(), customers["cancel_date"].max())

    os.makedirs(OUTBOX, exist_ok=True)
    for old in os.listdir(OUTBOX):          # start with an empty outbox each run
        os.remove(OUTBOX + old)

    queue = []
    skipped = 0
    for _, row in customers.iterrows():
        journey, extra = pick_journey(row, today)
        if journey is None:
            continue
        if not row["newsletter"] or pd.isna(row["email"]):
            skipped += 1
            continue
        subject, body = load_template(journey)
        fields = {"first_name": row["first_name"], "tier": row["tier"], **extra}
        subject, body = subject.format(**fields), body.format(**fields)
        filename = f"{journey}_{row['customer_id']}.txt"
        with open(OUTBOX + filename, "w") as f:
            f.write(f"To: {row['email']}\nSubject: {subject}\n\n{body}\n")
        queue.append({"customer_id": row["customer_id"], "email": row["email"], "journey": journey,
                      "subject": subject, "draft_file": filename, "approved": "NO"})

    queue = pd.DataFrame(queue, columns=["customer_id", "email", "journey", "subject", "draft_file", "approved"])
    queue.to_csv(OUTBOX + "review_queue.csv", index=False)

    print(f"Email journeys for {today.date()}")
    print(queue["journey"].value_counts().to_string() if len(queue) else "No emails due.")
    print(f"\n{len(queue)} drafts written to {OUTBOX} (none sent)")
    print(f"{skipped} people skipped because they are not subscribed or have no email")


if __name__ == "__main__":
    main()
