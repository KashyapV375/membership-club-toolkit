# Data dictionary: customers_clean.csv

One row per person. Built by `clean_customers.py` from the three files in `data/raw/`.

| Column | Type | Example | Where it comes from | Notes |
|---|---|---|---|---|
| customer_id | text | C1002 | made by the script | Changes if the list is rebuilt with new people. Email is the real key. |
| first_name | text | Kevin | signup form, or register for non-members | Title case |
| last_name | text | Brooks | signup form, or register for non-members | Title case |
| email | text | kevin.brooks85@example.com | signup form, register | Lowercase, no spaces. Blank if the person never gave one. |
| phone | text | 2105557381 | signup form, register | 10 digits only |
| tier | text | Silver | signup form | Bronze, Silver, Gold, or None for non-members |
| status | text | active | signup form | active, cancelled, or non-member |
| signup_date | date | 2024-09-22 | signup form | Earliest signup if the person signed up twice |
| cancel_date | date | 2026-03-01 | signup form | Blank for active members |
| newsletter | True/False | True | newsletter list | False if unsubscribed or not on the list |
| total_orders | number | 5 | register sales | Count of orders |
| total_spent | number | 169.0 | register sales | Dollars spent on orders. Does not include the monthly fee. |
| last_order_date | date | 2026-07-31 | register sales | Blank if no orders |

## Matching rules

1. Two signup rows with the same email (after cleaning) are the same person. The earliest signup is kept.
2. A sale is matched to a person by email.
3. If a sale has no email, it is matched by phone number.
4. A sale that matches nobody is kept as a non-member customer, so no money goes missing.

The script prints a check at the end: total spent in the clean list has to equal the total in the raw sales file.

# Data dictionary: survey_linked.csv

One row per person who answered the survey. Built by `link_surveys.py`.

| Column | Type | Example | Notes |
|---|---|---|---|
| customer_id | text | C1002 | Links back to customers_clean.csv |
| tier | text | Silver | Copied from the customer list |
| status | text | active | Copied from the customer list |
| answered_on | date | 2026-09-15 | If a person answered twice, the most recent answer is kept |
| satisfaction | number | 4 | 1 to 5. Answers like "4/5" and "four" are read as 4. |
| recommend | number | 8 | 0 to 10. Used for Net Promoter Score. |
| contacts_per_year | number | 2 | How many times the person says the club contacted them |
| total_spent | number | 169.0 | Copied from the customer list |

## Survey matching rules

1. A response is matched to a customer by email.
2. If the response has no email, it is matched by phone number.
3. A response that matches nobody is counted in the report as "could not be linked" and left out of the tier numbers.

Net Promoter Score = percent who answer 9 or 10, minus percent who answer 0 to 6.
