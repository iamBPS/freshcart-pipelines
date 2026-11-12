
import json
import os
import sys
import pika

if len(sys.argv) != 3:
    print("Usage: python stream/driver.py NAME PATTERN")
    sys.exit(1)

name = sys.argv[1]
pattern = sys.argv[2]
url = os.environ["RABBITMQ_URL"]

connection = pika.BlockingConnection(
    pika.URLParameters(url)
)
channel = connection.channel()

channel.exchange_declare(
    exchange="rapido-dispatch",
    exchange_type="topic",
    durable=True
)

result = channel.queue_declare(queue="", exclusive=True)
queue_name = result.method.queue

channel.queue_bind(
    exchange="rapido-dispatch",
    queue=queue_name,
    routing_key=pattern
)

print(f"{name} listening for: {pattern}", flush=True)


def callback(ch, method, properties, body):
    message = json.loads(body)

    if not message.get("zone"):
        print(
            f"REJECTED: Missing zone | {message}",
            flush=True
        )
        ch.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=False
        )
        return

    print(
        f"PROCESSED [{method.routing_key}]: {message}",
        flush=True
    )

    ch.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_consume(
    queue=queue_name,
    on_message_callback=callback,
    auto_ack=False
)

try:
    channel.start_consuming()
except KeyboardInterrupt:
    print(f"{name} stopped.")
    channel.stop_consuming()
finally:
    connection.close()
