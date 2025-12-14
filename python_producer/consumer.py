
from confluent_kafka import Consumer

conf = {
    'bootstrap.servers': 'kafka-broker-0.kafka-broker-service:19092',
    'group.id': 'my-consumer-group2',
    'auto.offset.reset': 'earliest'
}

consumer = Consumer(conf)
consumer.subscribe(['demo'])

print("Waiting for messages... (Ctrl+C to quit)")
try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue
        print(f"Received message from partition {msg.partition()}: {msg.value().decode('utf-8')}")
except KeyboardInterrupt:
    pass
finally:
    consumer.close()