import uuid
from io import BytesIO
import time as t
from threading import Thread

import cv2
import serial
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils import timezone
from easyocr import easyocr
from cars.models import Car
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import datetime
import win32print
import win32api

video_processing1 = None
video_processing2 = None


def start_video_processing_threads():
    global video_processing1, video_processing2

    if not video_processing1:
        video_processing1 = Thread(target=run_video_processing1)
        video_processing1.start()

    if not video_processing2:
        video_processing2 = Thread(target=run_video_processing2)
        video_processing2.start()


def run_video_processing1():
    cap1 = None
    try:

        cap1 = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        languages = ['en']
        reader = easyocr.Reader(languages)

        frame_skip = 5
        frame_count = 0

        while True:
            ret, frame = cap1.read()

            if not ret:
                break

            if frame_count % frame_skip == 0:
                processed_frame = preprocess_image(frame)
                contours = find_contours(processed_frame)
                filtered_contours = filter_contours(contours)

                get_car_numbers(frame, filtered_contours, reader, 1)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            frame_count += 1
    except Exception as e:
        print(f"Error in video processing: {e}")

    finally:
        cap1.release()
        cv2.destroyAllWindows()


def run_video_processing2():
    cap2 = None
    try:
        cap2 = cv2.VideoCapture(2, cv2.CAP_DSHOW)
        languages = ['en']
        reader = easyocr.Reader(languages)

        frame_skip = 5
        frame_count = 0

        while True:
            ret, frame = cap2.read()

            if not ret:
                break

            if frame_count % frame_skip == 0:
                processed_frame = preprocess_image(frame)
                contours = find_contours(processed_frame)
                filtered_contours = filter_contours(contours)

                result_frame = draw_contours(frame, filtered_contours)
                cv2.imshow("ANPR Result", result_frame)

                get_car_numbers(frame, filtered_contours, reader, 2)
            frame_count += 1
    except Exception as e:
        print(f"Error in video processing: {e}")

    finally:
        cap2.release()
        cv2.destroyAllWindows()


def save_rotated_plate(image, x, y, w, h, angle, car_number, camera_index):
    print(camera_index, car_number, Car.objects.filter(number=car_number, finish_time__isnull=True).exists())
    try:
        matching_cars = Car.objects.filter(number=car_number, finish_time__isnull=True)
        if matching_cars.count() and camera_index == 2:
            car = matching_cars.first()
            car.finish_time = timezone.now()
            car.save()
        elif camera_index == 1 and not Car.objects.filter(number=car_number, finish_time__isnull=True).exists():
            rotated_car_number_region = rotate_image(image[y:y + h, x:x + w], angle)
            pil_rotated_image = Image.fromarray(rotated_car_number_region)
            image_io = BytesIO()
            pil_rotated_image.save(image_io, format='JPEG')
            car = Car(id=uuid.uuid4(), number=car_number)
            car.plate_image.save(f'detected_plate_{car_number}_rotated.jpg',
                                 InMemoryUploadedFile(image_io, None, 'image.jpg', 'image/jpeg', image_io.tell(),
                                                      None))
            car.save()
    except Exception as e:
        print(f"Error in save_rotated_plate: {e}")


def preprocess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    return edges


def find_contours(image):
    contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours


def filter_contours(contours, min_area=1000):
    return [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]


def draw_contours(image, contours):
    result = image.copy()
    cv2.drawContours(result, contours, -1, (0, 255, 0), 2)
    return result


def validate_car_number(car_number):
    return (
            (len(car_number) == 8 and car_number[:2].isdigit() and car_number[2].isalpha() and car_number[
                2].isupper() and
             car_number[3:6].isdigit() and car_number[6:8].isalpha() and car_number[6:8].isupper()) or
            (len(car_number) == 8 and car_number[:5].isdigit() and car_number[5:].isalpha() and car_number[
                                                                                                5:].isupper())
    )


def rotate_image(image, angle):
    rows, cols = image.shape[:2]
    rotation_matrix = cv2.getRotationMatrix2D((cols / 2, rows / 2), angle, 1)
    return cv2.warpAffine(image, rotation_matrix, (cols, rows), flags=cv2.INTER_LINEAR)


def get_car_numbers(image, contours, reader, cam):
    car_numbers = set()
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        car_number_region = image[y:y + h, x:x + w]

        for angle in range(-10, 11, 2):
            rotated_car_number_region = rotate_image(car_number_region, angle)

            results = reader.readtext(rotated_car_number_region)
            if results:
                car_number = results[0][1].replace(" ", "")
                if validate_car_number(car_number):
                    car_numbers.add(car_number)
                    save_rotated_plate(image, x, y, w, h, angle, car_number, cam)

    return list(car_numbers)


def ser_command(command):
    ser = serial.Serial(
        port='\\\\.\\COM4',
        baudrate=115200,
        parity=serial.PARITY_ODD,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS
    )
    if ser.isOpen():
        ser.close()
    ser.open()
    ser.isOpen()
    ser.write(command.encode('utf-8'))
    ser.close()


def print_check(car: Car):

    now = datetime.datetime.now()
    date_time = now.strftime("%Y-%m-%d %H:%M:%S")

    pdf_filename = "receipt.pdf"
    pdf = canvas.Canvas(pdf_filename, pagesize=letter)

    pdf.setFont("Helvetica-Bold", 10)

    pdf.drawString(0.1 * inch, 10.9 * inch, '===================================================')
    pdf.drawString(0.1 * inch, 10.7 * inch, 'JIZZAX MARKAZIY DEHQON')
    pdf.drawString(0.1 * inch, 10.5 * inch, 'BOZORI AJ')
    pdf.drawString(0.1 * inch, 10.3 * inch, 'STIR: 201075201')
    pdf.drawString(0.1 * inch, 10 * inch, '===================================================')
    pdf.drawString(0.1 * inch, 9.7 * inch, 'Kassir: Normatov Dilshod')
    pdf.drawString(0.1 * inch, 9.4 * inch, 'Avto turargoh')
    pdf.drawString(0.1 * inch, 9.1 * inch, "----------------------------------------------------")
    pdf.drawString(0.1 * inch, 8.8 * inch, "Mashina raqami: {}".format(car.number))
    pdf.drawString(0.1 * inch, 8.5 * inch, "Turgan vaqti: {}".format(car.been))
    pdf.drawString(0.1 * inch, 8.2 * inch, "Kirish vaqti: {}".format(car.create_time))
    pdf.drawString(0.1 * inch, 7.9 * inch, "Chiqish vaqti: {}".format(date_time))
    pdf.drawString(0.1 * inch, 7.6 * inch, "Narxi: {}".format(car.price))
    pdf.drawString(0.1 * inch, 7.3 * inch, "----------------------------------------------------")


    pdf.save()

    # Set the printer name
    printer_name = "XP-58"


    # Print the PDF on the specified printer
    win32api.ShellExecute(0, "print", pdf_filename, f'"{printer_name}"', ".", 0)