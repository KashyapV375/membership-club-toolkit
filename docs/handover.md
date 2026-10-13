# Handover notes

For whoever runs this next.

## Running it

```
pip install -r requirements.txt
python clean_customers.py
python link_surveys.py
python tier_value.py
python email_journeys.py
```

Run them in that order. The later steps read the file that step 1 writes.

## Using your own data

Replace the files in `data/raw/` with real exports. The column names have to match the sample files:

- `website_signups.csv`: signup_date, first_name, last_name, email, phone, tier, status, cancel_date
- `pos_sales_export.csv`: order_id, order_date, customer_name, email, phone, item, amount
- `newsletter_list.csv`: Email Address, Full Name, Subscribed
- `survey_responses.csv`: Timestamp, Email, Phone, then one column per question. The script finds the questions by looking for the words "satisfied", "recommend" and "contact" in the column name, so the exact wording can change.

If an export uses different names, rename the columns in the CSV or change the names at the top of the matching `load_` function in `clean_customers.py`.

## Things you might need to change

| What | Where |
|---|---|
| Monthly fee for each tier | `MONTHLY_FEE` at the top of `tier_value.py` |
| How many days count as a "new" member | `WELCOME_DAYS` in `email_journeys.py` |
| When win-back emails go out | `WIN_BACK_MIN_DAYS` and `WIN_BACK_MAX_DAYS` in `email_journeys.py` |
| The wording of the emails | the `.txt` files in `templates/` (first line is the subject) |

## Approving emails

`email_journeys.py` never sends anything. It writes drafts to `outbox_for_review/` and a list called `review_queue.csv`. Read each draft, then change `approved` from NO to YES for the ones that are fine. Sending is a separate step that is not part of this project.

## Known limits

- People are matched by email first and phone second. Someone who uses two emails and two phone numbers will show up as two people.
- "Value per member so far" only counts the months that have already happened. Active members will keep paying, so the real lifetime number is higher.
- The tier table needs a fair number of members per tier to mean much. With 14 Gold members in the sample, one cancellation moves the churn rate by 7 points.
- A member only gets one journey per run. If someone is new and also near an anniversary (not possible in practice), welcome wins.
