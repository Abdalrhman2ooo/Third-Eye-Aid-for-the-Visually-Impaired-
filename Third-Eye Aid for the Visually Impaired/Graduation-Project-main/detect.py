import argparse
import sys
import time
import cv2
import pika
import json
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from utils import visualize


def run(model: str, camera_id: int, width: int, height: int) -> None:
    # Setup RabbitMQ connection
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='detection_results')

    # Variables to calculate FPS and maintain detection consistency
    counter, fps = 0, 0
    start_time = time.time()
    last_detection = None
    detection_streak = 0

    # Start capturing video input from the camera
    cap = cv2.VideoCapture(camera_id)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def visualize_callback(result: vision.ObjectDetectorResult, output_image: mp.Image, timestamp_ms: int):
        nonlocal last_detection, detection_streak  # Use nonlocal to modify outer scope variables
        current_detection = [{'label': det.categories[0].category_name, 'score': det.categories[0].score}
                             for det in result.detections]
        most_confident_detection = max(current_detection, key=lambda x: x['score']) if current_detection else None

        if most_confident_detection and (last_detection == most_confident_detection['label']):
            detection_streak += 1
        else:
            detection_streak = 1

        last_detection = most_confident_detection['label'] if most_confident_detection else None

        if detection_streak == 5:
            # Publish only the label of the object detected 5 times consecutively
            channel.basic_publish(exchange='',
                                  routing_key='detection_results',
                                  body=json.dumps({'label': last_detection}))
            print(f"Published detection to RabbitMQ: {last_detection}")
            detection_streak = 0  # Reset after sending

    # Initialize the object detection model
    base_options = python.BaseOptions(model_asset_path=model)
    options = vision.ObjectDetectorOptions(base_options=base_options,
                                           running_mode=vision.RunningMode.LIVE_STREAM,
                                           score_threshold=0.5,
                                           result_callback=visualize_callback)
    detector = vision.ObjectDetector.create_from_options(options)

    # Continuously capture images from the camera and run inference
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            sys.exit(
                'ERROR: Unable to read from webcam. Please verify your webcam settings.'
            )

        counter += 1
        image = cv2.flip(image, 1)

        # Convert the image from BGR to RGB as required by the TFLite model.
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)

        # Run object detection using the model.
        detector.detect_async(mp_image, counter)

        # Calculate the FPS
        if counter % 10 == 0:
            end_time = time.time()
            fps = 10 / (end_time - start_time)
            start_time = time.time()

        # Show the FPS
        fps_text = 'FPS = {:.1f}'.format(fps)
        cv2.putText(image, fps_text, (24, 20), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 255), 1)
        cv2.imshow('object_detector', image)

        # Stop the program if the ESC key is pressed.
        if cv2.waitKey(1) == 27:
            break

    detector.close()
    cap.release()
    cv2.destroyAllWindows()
    connection.close()


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--model',
        help='Path to the efficientdet.tflite model file',
        default=r'efficientdet_lite2.tflite')  #input the path to your model here
    parser.add_argument(
        '--cameraId', help='Id of camera.', type=int, default=0)
    parser.add_argument(
        '--frameWidth',
        help='Width of frame to capture from camera.',
        type=int,
        default=1280)
    parser.add_argument(
        '--frameHeight',
        help='Height of frame to capture from camera.',
        type=int,
        default=720)
    args = parser.parse_args()

    run(args.model, int(args.cameraId), args.frameWidth, args.frameHeight)


if __name__ == '__main__':
    main()
