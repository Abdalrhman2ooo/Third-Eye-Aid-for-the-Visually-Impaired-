import subprocess


def start_scripts():
    # Start the producer script
    producer = subprocess.Popen(['python', 'detect.py'])

    # Start the consumer script
    consumer = subprocess.Popen(['python', 'MAIN.py'])

    # Wait for the scripts to finish (optional)
    producer.wait()
    consumer.wait()


if __name__ == '__main__':
    start_scripts()
