import csv
import os
from typing import List

from services.report_service import (
    get_daily_summary, get_sales_by_date, get_profit_per_product,
    get_low_stock_items, get_purchase_history_summary,
)
from services.inventory_service import get_inventory_summary


def export_daily_summary(dest_path: str, date_from: str, date_to: str) -> str:
    """Export day-by-day revenue breakdown to CSV."""
    summary = get_daily_summary(date_from, date_to)
    rows = get_sales_by_date(date_from, date_to)
    with open(dest_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Daily Summary Report", f"{date_from} to {date_to}"])
        w.writerow([f"Total Revenue: {summary['revenue']:,.0f}",
                     f"Total Purchases: {summary['cost']:,.0f}",
                     f"Gross Profit: {summary['profit']:,.0f}"])
        w.writerow([])
        w.writerow(["Date", "Revenue", "Sale Batches"])
        for r in rows:
            w.writerow([r["date"], f"{r['revenue']:,.0f}", r["batches"]])
    return os.path.abspath(dest_path)


def export_profit_per_product(dest_path: str, date_from: str, date_to: str) -> str:
    """Export profit-per-product report to CSV."""
    rows = get_profit_per_product(date_from, date_to)
    with open(dest_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Profit Per Product", f"{date_from} to {date_to}"])
        w.writerow([])
        w.writerow(["Product", "Revenue", "Est. Cost", "Est. Profit"])
        for r in rows:
            w.writerow([
                r["product_name"],
                f"{r['revenue']:,.0f}",
                f"{r['estimated_cost']:,.0f}",
                f"{r['profit']:,.0f}",
            ])
    return os.path.abspath(dest_path)


def export_low_stock(dest_path: str) -> str:
    """Export low-stock items to CSV."""
    items = get_low_stock_items()
    with open(dest_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Low Stock Report"])
        w.writerow([])
        w.writerow(["Product", "Category", "In Stock", "Unit", "Threshold"])
        for item in items:
            w.writerow([
                item["name"],
                item["category"] or "",
                f"{item['display_qty']:,.0f}",
                item["display_unit"],
                item["low_stock_threshold"],
            ])
    return os.path.abspath(dest_path)


def export_purchase_history(dest_path: str) -> str:
    """Export purchase history to CSV."""
    rows = get_purchase_history_summary()
    with open(dest_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Purchase History"])
        w.writerow([])
        w.writerow(["Date", "Items", "Total Spent", "Notes"])
        for r in rows:
            w.writerow([
                r["date"],
                r["item_count"],
                f"{r['total']:,.0f}",
                r["notes"] or "",
            ])
    return os.path.abspath(dest_path)


def export_inventory(dest_path: str) -> str:
    """Export full inventory to CSV."""
    items = get_inventory_summary()
    with open(dest_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Inventory Report"])
        w.writerow([])
        w.writerow(["Product", "Category", "In Stock", "Unit", "Status"])
        for d in items:
            status = "Low Stock" if d["is_low"] else "OK"
            w.writerow([
                d["name"],
                d["category"] or "",
                f"{d['display_qty']:,.0f}",
                d["display_unit"],
                status,
            ])
    return os.path.abspath(dest_path)
