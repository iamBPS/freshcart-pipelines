"""Publish deterministic FreshCart web-order events for the lakehouse bonus."""

import json
import os

import pika

EXCHANGE = "freshcart-orders"
QUEUE = "freshcart-orders-lakehouse"
ROUTING_KEY = "orders.created"

# Keep these records identical on every run to demonstrate idempotency.
SAMPLE_ORDERS = [
    {
        "order_id": "BONUS-ORD-9001",
        "cust_email": "bonus.customer1@example.com",
        "cust_name": "Bonus Customer One",
        "order_date": "2026-09-05",
        "amount": "1500.00",
        "currency": "INR",
        "pincode": "600041",
        "updated_at": "2026-09-05 10:00:00",
    },
    {
        "order_id": "BONUS-ORD-9002",
        "cust_email": "bonus.customer2@example.com",
        "cust_name": "Bonus Customer Two",
        "order_date": "2026-09-05",
        "amount": "2500.00",
        "currency": "INR",
        "pincode": "600041",
        "updated_at": "2026-09-05 10:05:00",
    },
    {
        "order_id": "BONUS-ORD-9003",
        "cust_email": "bonus.customer3@example.com",
        "cust_name": "Bonus Customer Three",
        "order_date": "2026-09-05",
        "amount": "999.00",
        "currency": "INR",
        "pincode": "600041",
        "updated_at": "2026-09-05 10:10:00",
    },
]


def main():
    url = os.environ.get("RABBITMQ_URL")
    if not url:
        raise RuntimeError("Set the RABBITMQ_URL environment variable first.")

    connection = pika.BlockingConnection(pika.URLParameters(url))
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

        for order in SAMPLE_ORDERS:
            channel.basic_publish(
                exchange=EXCHANGE,
                routing_key=ROUTING_KEY,
                body=json.dumps(order, separators=(",", ":")),
                properties=pika.BasicProperties(
                    content_type="application/json",
                    delivery_mode=2,
                    message_id=order["order_id"],
                ),
                mandatory=True,
            )
            print(f"PUBLISHED {order['order_id']}: INR {order['amount']}")

        print(f"Published {len(SAMPLE_ORDERS)} deterministic FreshCart orders.")
        print("Run this same publisher again for the idempotency demonstration.")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
