"""Collect RabbitMQ FreshCart orders for one minute and load them into DuckDB."""

import json
import os
import time
from datetime import datetime, timezone

import pika

from config import DATA_DIR
from src.extract import write_landing
from src.load import create_bronze_tables, load_file
from src.transform import run_transformations
from src.db import get_connection

EXCHANGE = "freshcart-orders"
QUEUE = "freshcart-orders-lakehouse"
ROUTING_KEY = "orders.created"
DEFAULT_DURATION_SECONDS = 60
METRICS_PATH = DATA_DIR / "bonus_run_metrics.json"
REQUIRED_FIELDS = {
    "order_id", "cust_email", "cust_name", "order_date",
    "amount", "currency", "pincode", "updated_at",
}


def is_freshcart_order(message):
    if not isinstance(message, dict) or not REQUIRED_FIELDS.issubset(message):
        return False
    return all(message.get(field) not in (None, "") for field in REQUIRED_FIELDS)


def read_gold_metrics():
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS order_count,
                COUNT(DISTINCT order_id) AS distinct_order_count,
                ROUND(COALESCE(SUM(amount_inr), 0), 2) AS revenue_inr,
                COALESCE(SUM(loyalty_points), 0) AS loyalty_points
            FROM gold.fct_orders
            """
        ).fetchone()

    return {
        "order_count": int(row[0]),
        "distinct_order_count": int(row[1]),
        "revenue_inr": str(row[2]),
        "loyalty_points": int(row[3]),
    }


def record_and_compare_metrics(metrics, run_id):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    previous = None
    if METRICS_PATH.exists():
        try:
            previous = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            previous = None

    snapshot = {"run_id": run_id, **metrics}
    history = []
    if previous:
        history = previous.get("history", [])
        if not history:
            history.append(previous.get("latest", previous))
    history.append(snapshot)

    METRICS_PATH.write_text(
        json.dumps({"latest": snapshot, "history": history}, indent=2),
        encoding="utf-8",
    )

    print("Gold metrics:")
    print(json.dumps(metrics, indent=2))

    if previous:
        prior = previous.get("latest", previous)
        compared_fields = (
            "order_count", "distinct_order_count", "revenue_inr", "loyalty_points"
        )
        unchanged = all(prior.get(field) == metrics.get(field) for field in compared_fields)
        if unchanged:
            print("IDEMPOTENCY PASS: Gold order count, revenue and loyalty points did not increase.")
        else:
            print("Gold metrics changed since the previous run. Compare the two snapshots above.")
    else:
        print("First batch snapshot saved. Repeat the same publisher + consumer run to prove idempotency.")


def main():
    url = os.environ.get("RABBITMQ_URL")
    if not url:
        raise RuntimeError("Set the RABBITMQ_URL environment variable first.")

    connection = pika.BlockingConnection(pika.URLParameters(url))
    captured_orders = []
    delivery_tags = []

    try:
        channel = connection.channel()
        channel.exchange_declare(
            exchange=EXCHANGE,
            exchange_type="topic",
            durable=True,
        )
        channel.queue_declare(queue=QUEUE, durable=True)
        channel.queue_bind(
            exchange=EXCHANGE,
            queue=QUEUE,
            routing_key=ROUTING_KEY,
        )
        channel.basic_qos(prefetch_count=500)

        def callback(ch, method, properties, body):
            try:
                message = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                print("REJECTED: message is not valid JSON")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return

            if not is_freshcart_order(message):
                print(f"REJECTED: not a complete FreshCart web-order record: {message}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return

            captured_orders.append(message)
            # Keep messages unacknowledged until the raw landing file and Gold load succeed.
            delivery_tags.append(method.delivery_tag)
            print(f"RECEIVED {message['order_id']} ({len(captured_orders)} collected)")

        channel.basic_consume(
            queue=QUEUE,
            on_message_callback=callback,
            auto_ack=False,
        )

        duration = DEFAULT_DURATION_SECONDS
        print(f"Listening on {QUEUE} for {duration} seconds...")
        deadline = time.monotonic() + duration
        while time.monotonic() < deadline:
            connection.process_data_events(time_limit=1)

        if not captured_orders:
            print("No FreshCart orders received in the one-minute window; nothing loaded.")
            return

        run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        landing_path = write_landing("web", captured_orders, run_id)
        create_bronze_tables()
        loaded = load_file(landing_path)
        run_transformations()

        # Acknowledge only after the batch has been persisted and transformed successfully.
        for delivery_tag in delivery_tags:
            channel.basic_ack(delivery_tag=delivery_tag)

        print(f"Landing file: {landing_path}")
        print(f"Rows loaded into Bronze: {loaded}")
        metrics = read_gold_metrics()
        record_and_compare_metrics(metrics, run_id)

    finally:
        if connection.is_open:
            connection.close()


if __name__ == "__main__":
    main()
