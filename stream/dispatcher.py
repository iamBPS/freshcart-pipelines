
import json
import os
import random
import time
import uuid
from datetime import datetime, timezone

import pika

RABBITMQ_URL = os.environ["RABBITMQ_URL"]
EXCHANGE = "rapido-dispatch"

connection = pika.BlockingConnection(
    pika.URLParameters(RABBITMQ_URL)
)
channel = connection.channel()

channel.exchange_declare(
    exchange=EXCHANGE,
    exchange_type="topic",
    durable=True
)

cities = {
    "bangalore": ["koramangala", "indiranagar", "whitefield"],
    "chennai": ["tnagar", "whitefield", "adyar"]
}

counter = 0

try:
    while True:
        counter += 1

        city = random.choice(list(cities.keys()))
        zone = random.choice(cities[city])
        request_type = random.choice(["ride", "food"])

        routing_key = f"{city}.{zone}.{request_type}"

        message = {
            "id": str(uuid.uuid4())[:8],
            "city": city,
            "type": request_type,
            "ts": datetime.now(timezone.utc).isoformat()
        }

        # Send a malformed message every 10th message.
        if counter % 10 != 0:
            message["zone"] = zone
            status = "VALID"
        else:
            status = "MALFORMED"

        channel.basic_publish(
            exchange=EXCHANGE,
            routing_key=routing_key,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2
            )
        )

        print(
            f"{status} [{routing_key}]: {json.dumps(message)}",
            flush=True
        )

        time.sleep(2)

except KeyboardInterrupt:
    print("Dispatcher stopped.")

finally:
    connection.close()
