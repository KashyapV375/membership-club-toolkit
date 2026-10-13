"""Step 2: what is each membership tier worth?

Reads the clean customer list and works out, for every tier:
  - how many members it has and how many cancelled (churn)
  - how long members stay
  - how much a member brings in per month (monthly fee + extra purchases)
  - an estimated value over the whole time a member stays

Output: reports/tier_value.csv and reports/tier_value.png

Run:  python tier_value.py
      python tier_value.py 2026-12-31     (use a different "as of" date)
"""
import sys

import matplotlib
matplotlib.use("Agg")   # draw to a file, no window needed
import matplotlib.pyplot as plt
import pandas as pd

MONTHLY_FEE = {"Bronze": 15, "Silver": 30, "Gold": 55}
TIER_ORDER = ["Bronze", "Silver", "Gold"]
DAYS_PER_MONTH = 30.4


def months_as_member(row, as_of):
    """Months between signup and cancel date (or the as-of date if still active)."""
    end = row["cancel_date"] if pd.notna(row["cancel_date"]) else as_of
    months = (end - row["signup_date"]).days / DAYS_PER_MONTH
    return max(months, 1)   # count at least the first month they paid for


def tier_table(customers, as_of):
    members = customers[customers["tier"].isin(TIER_ORDER)].copy()
    members["months"] = members.apply(months_as_member, axis=1, as_of=as_of)
    members["fee_revenue"] = members["months"] * members["tier"].map(MONTHLY_FEE)
    members["total_revenue"] = members["fee_revenue"] + members["total_spent"]
    members["cancelled"] = members["status"] == "cancelled"

    rows = []
    for tier in TIER_ORDER:
        group = members[members["tier"] == tier]
        member_months = group["months"].sum()
        rows.append({
            "tier": tier,
            "members": len(group),
            "active": int((~group["cancelled"]).sum()),
            "churn_rate_pct": round(group["cancelled"].mean() * 100, 1),
            "avg_months_stayed": round(group["months"].mean(), 1),
            "monthly_fee": MONTHLY_FEE[tier],
            # extra spend is divided by member-months so long-time members don't skew it
            "extra_spend_per_month": round(group["total_spent"].sum() / member_months, 2),
            "avg_order_value": round(group["total_spent"].sum() / max(group["total_orders"].sum(), 1), 2),
            "total_revenue": round(group["total_revenue"].sum(), 2),
        })
    table = pd.DataFrame(rows)
    table["value_per_member_month"] = (table["monthly_fee"] + table["extra_spend_per_month"]).round(2)
    table["value_per_member_so_far"] = (table["value_per_member_month"] * table["avg_months_stayed"]).round(2)
    table["share_of_revenue_pct"] = (table["total_revenue"] / table["total_revenue"].sum() * 100).round(1)
    return table


def make_chart(table, path):
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    colors = ["#b08d57", "#9aa0a6", "#d4af37"]
    charts = [("value_per_member_month", "Value per member per month ($)"),
              ("churn_rate_pct", "Members who cancelled (%)"),
              ("share_of_revenue_pct", "Share of total revenue (%)")]
    for ax, (column, title) in zip(axes, charts):
        bars = ax.bar(table["tier"], table[column], color=colors)
        ax.set_title(title)
        for bar, value in zip(bars, table[column]):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{value:g}", ha="center", va="bottom")
        ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=150)


def main():
    customers = pd.read_csv("data/clean/customers_clean.csv", parse_dates=["signup_date", "cancel_date"])
    if len(sys.argv) > 1:
        as_of = pd.Timestamp(sys.argv[1])
    else:
        # default: the latest date that appears anywhere in the data
        as_of = max(customers["signup_date"].max(), customers["cancel_date"].max())
    table = tier_table(customers, as_of)
    table.to_csv("reports/tier_value.csv", index=False)
    make_chart(table, "reports/tier_value.png")

    print(f"Tier value as of {as_of.date()}\n")
    print(table.T.to_string(header=False))
    best = table.sort_values("value_per_member_so_far", ascending=False).iloc[0]
    biggest = table.sort_values("share_of_revenue_pct", ascending=False).iloc[0]
    print(f"\nMost valuable per member: {best['tier']} (${best['value_per_member_so_far']:,.0f} per member so far)")
    print(f"Biggest share of revenue: {biggest['tier']} ({biggest['share_of_revenue_pct']}%)")
    print("\nSaved reports/tier_value.csv and reports/tier_value.png")


if __name__ == "__main__":
    main()
