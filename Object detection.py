import math
from statistics import mean

import cv2
import webcolors
from win32api import GetSystemMetrics


class detected_object:
    def __init__(self, color, size, shape):
        self.size = size
        self.color = get_color_name(color)
        self.shape = shape

    def __repr__(self):
        return "{}, {} {}".format(self.size, self.color, self.shape)


def center_window(window_size):
    frame_height, frame_width, channels = window_size
    screen_width = int(GetSystemMetrics(0) / 2)
    screen_height = int(GetSystemMetrics(1) / 2)
    hsize = int(frame_height / 2)
    wsize = int(frame_width / 2)

    wcenter = screen_width - wsize
    hcenter = screen_height - hsize
    cv2.moveWindow('main', wcenter, hcenter)


def get_color_name(bgr_triplet):
    rgb_triplet = [bgr_triplet[2], bgr_triplet[1], bgr_triplet[0]]
    min_colours = {}
    for key, name in webcolors.HTML4_HEX_TO_NAMES.items():
        r_c, g_c, b_c = webcolors.hex_to_rgb(key)
        rd = (r_c - rgb_triplet[0]) ** 2
        gd = (g_c - rgb_triplet[1]) ** 2
        bd = (b_c - rgb_triplet[2]) ** 2
        min_colours[(rd + gd + bd)] = name

    return min_colours[min(min_colours.keys())]


def get_average_color(pixels_color):
    B_channel = []
    G_channel = []
    R_channel = []
    for a in pixels_color:
        B_channel.append(a[0])
        G_channel.append(a[1])
        R_channel.append(a[2])
    object_color = [int(mean(B_channel)), int(mean(G_channel)), int(mean(R_channel))]
    return object_color


def get_object_size(shape, height, width, resize_factor):
    small_size_sample = 100
    medium_size_sample = 250
    large_size_sample = 600
    tolerance_sample = 50

    if shape == "Triangle":
        area = 0.5 * width * height
    elif shape == "Square":
        area = width * height
    else:
        area = (math.pi * (width / 2) ** 2) / 4.2

    if math.isclose(area, small_size_sample * resize_factor, abs_tol=tolerance_sample * resize_factor):
        return "Small"
    elif math.isclose(area, medium_size_sample * resize_factor, abs_tol=tolerance_sample * resize_factor):
        return "Medium"
    elif math.isclose(area, large_size_sample * resize_factor, abs_tol=tolerance_sample * resize_factor):
        return "Large"
    else:
        return area


def categorize(objects, categorize_by):
    categorized = {}

    for i in objects:
        if categorize_by == "Size":
            key = i.size
        elif categorize_by == "Shape":
            key = i.shape
            if key == "Triangle":
                key = "Triangular"
            elif key == "Circle":
                key = "Circular"
        elif categorize_by == "Color":
            key = i.color
        else:
            print(f'Given criterion "{categorize_by}" is invalid')
            break
        name = "%s_objects" % key
        if not name in categorized.keys():
            categorized[name] = [i]
        else:
            categorized[name].append(i)

    return categorized


def detect_objects(video, resize_factor):
    background_color = 100  # kolor tła pomijany przy wyodrębnianiu kolorów
    object_height = 0
    prev_object_width = 0
    max_object_width = 0
    gathered_objects = list()
    object_color = []
    average_color = []
    Figure = []

    while (True):
        ret, frame = video.read()

        if not ret:  # koniec wyswietlania po końcu filmu
            for i in gathered_objects:
                yield i
            break

        frame = cv2.resize(frame,
                           (frame.shape[1] * resize_factor, frame.shape[0] * resize_factor))  # zmiania rozmiaru okienka

        font = cv2.FONT_HERSHEY_SIMPLEX
        if average_color and resize_factor > 2:  # wyswietlanie napisu w filmie
            cv2.putText(frame, f"Found: {Figure}", (0, frame.shape[0] - 50), font, 0.8,
                        (average_color[0], average_color[1], average_color[2]), 3, cv2.LINE_AA)
        cv2.imshow('main', frame)

        center_window(frame.shape)

        current_object_width = 0

        for index, pixel in enumerate(frame[0]):  # analiza pierwszej linii pixeli
            if any(number > background_color for number in pixel):
                current_object_width = current_object_width + 1  # zliczanie szerokosci obiektu
                object_color.append(pixel)  # detekcja wyróżniającego się koloru

            if index == frame.shape[1] - 1:

                if prev_object_width > 0:

                    if prev_object_width > max_object_width:
                        max_object_width = prev_object_width

                    elif current_object_width > max_object_width:
                        max_object_width = current_object_width
                    object_height = object_height + 1

                    if current_object_width == 0:

                        if prev_object_width / max_object_width < 0.2:
                            object_shape = "Triangle"
                        elif prev_object_width / max_object_width > 0.9:
                            object_shape = "Square"
                        else:
                            object_shape = "Circle"

                        average_color = get_average_color(object_color)
                        object_size = get_object_size(object_shape, object_height, max_object_width, resize_factor)
                        Figure = detected_object(average_color, object_size, object_shape)
                        gathered_objects.append(Figure)
                        object_height = 0
                        max_object_width = 0
                        object_color = []

                prev_object_width = current_object_width

        k = cv2.waitKey(15) & 0xFF
        if k == 27:  # koniec wyswietlania - po wcisnieciu ESC
            for i in gathered_objects:
                yield i
            break
        if k == ord(' '):
            cv2.waitKey(-1)

    cv2.destroyAllWindows()
    video.release()


def main():
    file_name = "PA_5.avi" #PA_1.mp4   PA_2.mp4    PA_3.mp4
    # categorize_by = "Size"
    categorize_by = "Shape"
    # categorize_by = "Color"

    video = cv2.VideoCapture(file_name)
    resize_factor = 4  # mnożnik wielkosci okna
    gathered_objects = list(detect_objects(video, resize_factor))
    for index, x in enumerate(gathered_objects):
        print(f"{index + 1}.{x}")
    print("\n")

    organized = categorize(gathered_objects, categorize_by)
    if organized.items():
        print("There are:")
        for key, values in organized.items():
            print(len(organized[key]))
            print(key)
            print("\n")


if __name__ == "__main__":
    main()
