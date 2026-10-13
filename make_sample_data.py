"""Make fake, messy sample data for a small membership club.

Everything in here is made up. The mess is on purpose (mixed-up casing,
different phone formats, people who signed up twice) so the cleaning
script has something real to fix.

Run:  python make_sample_data.py
"""
import csv
import random
from datetime import date, timedelta

random.seed(7)  # same fake data every time

FIRST = ["Maya", "Jordan", "Luis", "Priya", "Sam", "Elena", "Marcus", "Hannah", "Omar",
         "Grace", "Diego", "Nina", "Caleb", "Aisha", "Tom", "Rosa", "Kevin", "Lena",
         "Andre", "Sofia", "Ben", "Tara", "Victor", "Julia", "Noah", "Imani", "Erik",
         "Carmen", "Peter", "Yuki"]
LAST = ["Reyes", "Carter", "Nguyen", "Patel", "Brooks", "Garza", "Kim", "Lopez", "Shah",
        "Turner", "Flores", "Morgan", "Bell", "Rivera", "Hughes", "Castro", "Wood",
        "Singh", "Ortiz", "Foster"]
TIERS = {"Bronze": 15, "Silver": 30, "Gold": 55}   # monthly fee in dollars
ITEMS = [("Bag of coffee", 16), ("Gift box", 42), ("Mug", 14), ("Brewing class", 35),
         ("Sampler pack", 24), ("Pastry box", 18)]
TODAY = date(2026, 9, 30)   # the "as of" date for the sample data


def messy_email(email):
    """Return the email the way a rushed person might type it."""
    choice = random.random()
    if choice < 0.15:
        return email.upper()
    if choice < 0.30:
        return " " + email.capitalize() + " "
    return email


def messy_phone(digits):
    """Same phone number, different ways people write it."""
    a, b, c = digits[:3], digits[3:6], digits[6:]
    return random.choice([f"({a}) {b}-{c}", f"{a}-{b}-{c}", f"{a}.{b}.{c}", digits, f"+1 {a} {b} {c}"])


def messy_tier(tier):
    return random.choice([tier, tier, tier.lower(), tier.upper(), tier + " "])


def main():
    members = []
    used = set()
    while len(members) < 120:
        first, last = random.choice(FIRST), random.choice(LAST)
        if (first, last) in used:
            continue
        used.add((first, last))
        email = f"{first}.{last}{random.randint(1, 99)}@example.com".lower()
        phone = "210555" + str(random.randint(1000, 9999))
        tier = random.choices(list(TIERS), weights=[50, 35, 15])[0]
        signup = TODAY - timedelta(days=random.randint(1, 900))
        # higher tiers cancel a little less often in this fake data
        cancel_chance = {"Bronze": 0.40, "Silver": 0.28, "Gold": 0.18}[tier]
        cancel = None
        months_in = (TODAY - signup).days / 30
        if months_in > 2 and random.random() < cancel_chance:
            cancel = signup + timedelta(days=random.randint(45, max(46, (TODAY - signup).days - 5)))
        members.append({"first": first, "last": last, "email": email, "phone": phone,
                        "tier": tier, "signup": signup, "cancel": cancel})

    # make sure the sample has a few brand new members and a few anniversaries coming up,
    # so every email journey has someone in it
    for i, days_ago in enumerate([1, 3, 6]):
        members[i]["signup"], members[i]["cancel"] = TODAY - timedelta(days=days_ago), None
    for i, days_ago in enumerate([363, 361, 728], start=3):
        members[i]["signup"], members[i]["cancel"] = TODAY - timedelta(days=days_ago), None

    # 1) website signup form export
    signup_rows = []
    for m in members:
        signup_rows.append([m["signup"].isoformat(), m["first"], m["last"], messy_email(m["email"]),
                            messy_phone(m["phone"]), messy_tier(m["tier"]),
                            "cancelled" if m["cancel"] else "active",
                            m["cancel"].isoformat() if m["cancel"] else ""])
    # some people filled out the form twice
    for m in random.sample(members, 9):
        signup_rows.append([m["signup"].isoformat(), m["first"].upper(), m["last"], m["email"].upper(),
                            m["phone"], m["tier"], "cancelled" if m["cancel"] else "active",
                            m["cancel"].isoformat() if m["cancel"] else ""])
    random.shuffle(signup_rows)
    with open("data/raw/website_signups.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["signup_date", "first_name", "last_name", "email", "phone", "tier", "status", "cancel_date"])
        w.writerows(signup_rows)

    # 2) cash register (point of sale) export. Names are "LAST, First" and email is sometimes blank.
    walk_ins = [("Dana", "Price", "dana.price@example.com", "2105550101"),
                ("Chris", "Young", "", "2105550102"),
                ("Pat", "Ellis", "pat.ellis@example.com", "2105550103"),
                ("Robin", "Hale", "", "2105550104"),
                ("Alex", "Stone", "alex.stone@example.com", "2105550105")]
    sales = []
    order_id = 1001
    spend_boost = {"Bronze": 1.0, "Silver": 1.5, "Gold": 2.3}
    for m in members:
        end = m["cancel"] or TODAY
        months = max(1, (end - m["signup"]).days // 30)
        n_orders = int(random.random() * months * 0.5 * spend_boost[m["tier"]])
        for _ in range(n_orders):
            day = m["signup"] + timedelta(days=random.randint(0, (end - m["signup"]).days))
            item, price = random.choice(ITEMS)
            email = "" if random.random() < 0.2 else messy_email(m["email"])
            sales.append([order_id, day.isoformat(), f"{m['last'].upper()}, {m['first']}", email,
                          messy_phone(m["phone"]), item, f"{price * random.choice([1, 1, 2]):.2f}"])
            order_id += 1
    for first, last, email, phone in walk_ins:
        for _ in range(random.randint(1, 3)):
            day = TODAY - timedelta(days=random.randint(1, 400))
            item, price = random.choice(ITEMS)
            sales.append([order_id, day.isoformat(), f"{last.upper()}, {first}", email, messy_phone(phone), item, f"{price:.2f}"])
            order_id += 1
    sales.sort(key=lambda r: r[1])
    with open("data/raw/pos_sales_export.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["order_id", "order_date", "customer_name", "email", "phone", "item", "amount"])
        w.writerows(sales)

    # 3) newsletter list from the email tool. Different column names, yes/no written 4 ways.
    news = []
    for m in members:
        if random.random() < 0.85:
            subscribed = random.random() < 0.88
            word = random.choice(["yes", "Y", "Yes"]) if subscribed else random.choice(["no", "N"])
            news.append([messy_email(m["email"]), f"{m['first']} {m['last']}", word])
    for first, last, email, _ in walk_ins:
        if email:
            news.append([email, f"{first} {last}", "yes"])
    news += random.sample(news, 6)   # duplicates
    random.shuffle(news)
    with open("data/raw/newsletter_list.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Email Address", "Full Name", "Subscribed"])
        w.writerows(news)

    # 4) survey responses, the way a form tool exports them: long question text as column names,
    #    and people answering the same question in different ways ("4", "4/5", "four").
    words = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five"}
    survey = []
    for m in random.sample(members, 52):
        base = {"Bronze": 3.4, "Silver": 3.9, "Gold": 4.4}[m["tier"]] - (0.9 if m["cancel"] else 0)
        satisfaction = min(5, max(1, round(random.gauss(base, 0.8))))
        recommend = min(10, max(0, round(satisfaction * 2 + random.gauss(-0.5, 1.2))))
        contacts = max(0, round(random.gauss({"Bronze": 1.3, "Silver": 2.1, "Gold": 3.2}[m["tier"]], 0.9)))
        style = random.random()
        sat_text = str(satisfaction) if style < 0.6 else (f"{satisfaction}/5" if style < 0.8 else words[satisfaction])
        rec_text = str(recommend) if random.random() < 0.85 else f"{recommend} - " + ("definitely" if recommend >= 9 else "maybe")
        email = "" if random.random() < 0.15 else messy_email(m["email"])
        day = TODAY - timedelta(days=random.randint(2, 40))
        survey.append([day.isoformat(), email, messy_phone(m["phone"]), sat_text, rec_text, contacts])
    survey += random.sample(survey, 5)                       # a few people answered twice
    for i in range(3):                                       # and a few are not customers at all
        survey.append([(TODAY - timedelta(days=5 + i)).isoformat(), f"visitor{i}@example.com", "",
                       random.choice(["3", "4"]), random.choice(["6", "7"]), 0])
    random.shuffle(survey)
    with open("data/raw/survey_responses.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Timestamp", "Email", "Phone", "How satisfied are you with the club? (1-5)",
                    "How likely are you to recommend us? (0-10)", "About how many times did we contact you this year?"])
        w.writerows(survey)

    print(f"Wrote {len(signup_rows)} signup rows, {len(sales)} sales rows, {len(news)} newsletter rows "
          f"and {len(survey)} survey rows to data/raw/")


if __name__ == "__main__":
    main()
