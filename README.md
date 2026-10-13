# Membership Club Toolkit

Three small Python scripts for a business that runs a membership club (a coffee club, a gym, a book box, anything with tiers and a monthly fee).

Small businesses usually have the same customer in three places: the signup form, the cash register, and the email newsletter tool. None of them agree. This project takes those three exports and does three things with them:

1. **Builds one clean customer list** out of the messy exports.
2. **Works out what each membership tier is worth.**
3. **Drafts the member emails that are due** (welcome, anniversary, win-back) and puts them in a folder for a person to approve. Nothing is sent automatically.

All the data in this repo is fake. `make_sample_data.py` generates it, mess included.

## What it looks like

Step 1 turns this (three different files, three different formats):

```
signup form:  ANDRE.FLORES44@EXAMPLE.COM, 2105556737, Silver
register:     "FLORES, Andre", andre.flores44@example.com, (210) 555-6737, Sampler pack, 48.00
newsletter:   Andre.flores44@example.com , Andre Flores, no
```

into one row:

```
C1012, Andre, Flores, andre.flores44@example.com, 2105556737, Silver, active, 2025-02-13, , False, 12, 346.0, 2026-09-10
```

Step 2 prints a table like this and saves a chart:

```
tier                       Bronze    Silver      Gold
members                        71        35        14
churn_rate_pct               25.4      28.6      14.3
avg_months_stayed            12.0      10.7      13.1
value_per_member_month      23.59      39.7     75.22
value_per_member_so_far    283.08    424.79    985.38
share_of_revenue_pct         41.2      30.5      28.2
```

![Tier value chart](reports/tier_value.png)

In the sample data, a Gold member is worth about three times a Bronze member, but Bronze still brings in the most money overall because there are five times as many of them. That is the kind of thing an owner would want to know before changing prices.

Step 3 writes drafts like this to `outbox_for_review/`:

```
To: tara.garza14@example.com
Subject: 2 years as a member. Thank you, Tara!

Hi Tara,

Next week marks 2 years since you joined the club as a Bronze member.
...
```

## How to run it

You need Python 3.9 or newer.

```
pip install -r requirements.txt

python make_sample_data.py     # optional, the sample data is already in data/raw
python clean_customers.py      # step 1
python tier_value.py           # step 2
python email_journeys.py       # step 3

python -m unittest discover tests
```

## What is in here

| File | What it does |
|---|---|
| `make_sample_data.py` | Makes the fake, messy exports in `data/raw/` |
| `clean_customers.py` | Cleans and merges them into `data/clean/customers_clean.csv` and writes a cleaning report |
| `tier_value.py` | Calculates churn, months stayed, and value for each tier. Saves a table and a chart in `reports/` |
| `email_journeys.py` | Picks who is due for which email and writes drafts plus `review_queue.csv` |
| `templates/` | The email wording, as plain text files anyone can edit |
| `docs/data_dictionary.md` | What every column in the clean list means and how records are matched |
| `docs/handover.md` | How to run this with real data and what to change |
| `tests/` | 11 small tests for the cleaning rules and the email rules |

## How the cleaning works

- Emails are lowercased and trimmed, so `ANDRE.FLORES44@EXAMPLE.COM` and ` Andre.flores44@example.com ` count as the same person.
- Phone numbers are cut down to 10 digits, so `(210) 555-6737` and `210.555.6737` match.
- If someone filled out the signup form twice, the earliest signup is kept.
- A register sale with no email is matched to a person by phone number. In the sample data that rescues 90 of 92 sales.
- Sales that match nobody are kept as non-member customers.
- At the end the script checks that total dollars in the clean list equals total dollars in the raw sales file. If cleaning lost a sale, the two numbers would not match.

## How tier value is calculated

For each tier:

- **Churn rate** = members who cancelled / all members who ever joined that tier
- **Months stayed** = signup date to cancel date (or to today for active members)
- **Value per member per month** = monthly fee + extra purchases per member per month
- **Value per member so far** = value per month x average months stayed

This is on purpose a simple version of customer lifetime value. It only counts months that have already happened, so it runs low for tiers where most members are still active. `docs/handover.md` lists this and the other limits.

## How the email rules work

| Journey | Who gets it |
|---|---|
| Welcome | Active members who joined in the last 7 days |
| Anniversary | Active members whose join anniversary is within the next 7 days |
| Win-back | Members who cancelled 30 to 120 days ago |

Two safety rules: people who are not subscribed to the newsletter are skipped, and every draft starts as `approved = NO` in the review queue. A person has to read it and change that to YES.

## Skills this project uses

- **Data analysis** with Python and pandas: grouping, aggregating, calculating churn and customer value, and charting with matplotlib
- **Data cleaning**: standardizing emails, phones and names, removing duplicates, and merging three sources into one table
- **CRM basics**: one customer record per person, a documented data dictionary, and member status and tier tracking
- **Email automation**: date-based trigger rules, fill-in templates, opt-out handling, and a human approval step
- **Documentation and testing**: a handover guide, a data dictionary, and unit tests

## Ideas for later

- Load the clean list into SQLite so it can be queried with SQL
- Add a "has not ordered in 60 days" check-in email for active members
- Compare tiers by the month people joined, to see if newer members cancel faster
