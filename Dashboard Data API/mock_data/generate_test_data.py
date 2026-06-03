# Standalone script to generate test data for the mock database

from sqlalchemy import create_engine, text
from datetime import datetime, timedelta

def insert_order_sqlalchemy(engine, card_code, card_name, doc_num, doc_entry, doc_date, doc_due_date, comments):
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO OPOR (CardCode, CardName, DocNum, DocDate, DocEntry, DocDueDate, Comments)
                VALUES (:card_code, :card_name, :doc_num, :doc_date, :doc_entry, :doc_due_date, :comments)
            """),
            {
                "card_code": card_code,
                "card_name": card_name,
                "doc_num": doc_num,
                "doc_date": doc_date,
                "doc_entry": doc_entry,
                "doc_due_date": doc_due_date,
                "comments": comments
            }
        )

def insert_orders_every_monday_sqlalchemy(engine, card_code, card_name, start_date, end_date):
    current = datetime.strptime(start_date, "%m/%d/%Y")
    end = datetime.strptime(end_date, "%m/%d/%Y")
    doc_num = 10000
    doc_entry = 1
    with engine.begin() as conn:
        while current <= end:
            if current.weekday() == 0:  # Monday
                doc_date = current.strftime("%Y-%m-%d")
                doc_due_date = (current + timedelta(days=7)).strftime("%Y-%m-%d")
                comments = f"Auto order for {doc_date}"
                conn.execute(
                    text("""
                        INSERT INTO OPOR (CardCode, CardName, DocNum, DocDate, DocEntry, DocDueDate, Comments)
                        VALUES (:card_code, :card_name, :doc_num, :doc_date, :doc_entry, :doc_due_date, :comments)
                    """),
                    {
                        "card_code": card_code,
                        "card_name": card_name,
                        "doc_num": doc_num,
                        "doc_date": doc_date,
                        "doc_entry": doc_entry,
                        "doc_due_date": doc_due_date,
                        "comments": comments
                    }
                )
                doc_num += 1
                doc_entry += 1
            current += timedelta(days=1)