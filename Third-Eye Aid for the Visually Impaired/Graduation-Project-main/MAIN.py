import pika
import json
import random
from gtts import gTTS
import os
from playsound import playsound

# Generate random distance between the sensors' dead zone and max range in meters for simulation purposes
def generate_random_measurement():
    return random.uniform(2, 400) / 100.0

# format results into desired text and print it (pass it to text to speech engine)
def process_message(detection_result, distance):
    formatted_message = f"{detection_result} is {distance:.2f} meters away, take action."
    print(formatted_message)
    tts=gTTS(text=formatted_message, lang='en', slow=False)
    tts.save("temp.mp3")
    playsound("temp.mp3")

def callback(ch, method, properties, body):
    try:
        detection_results = json.loads(body)
        distance = generate_random_measurement()
        process_message(detection_results['label'], distance)  # Ensure that 'label' is the expected key.
        ch.basic_ack(delivery_tag=method.delivery_tag)  # Manually acknowledge the message.
    except json.JSONDecodeError:
        print("Received malformed JSON.")
    except Exception as e:
        print(f"An error occurred: {e}")

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='detection_results')
channel.basic_consume(queue='detection_results', on_message_callback=callback, auto_ack=False)

try:
    print("Starting to consume messages...")
    channel.start_consuming()
except KeyboardInterrupt:
    print("Stopped by user.")
except pika.exceptions.ConnectionClosedByBroker:
    print("Connection closed by broker.")
except Exception as e:
    print(f"Unhandled exception: {e}")
finally:
    if connection:
        connection.close()
