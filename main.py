import requests
from io import BytesIO
import sys

from PIL import Image

from PyQt6 import uic
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QWidget, QPushButton
from PyQt6.QtCore import Qt

LIGHT = 'light'
DARK = 'dark'

# Минимальный и максимальный масштаб
MIN_SPN = 0.01
MAX_SPN = 90

def get_delta(toponym) -> list[str, str]:
    lower_corner = toponym["boundedBy"]["Envelope"]["lowerCorner"].split()
    upper_corner = toponym["boundedBy"]["Envelope"]["upperCorner"].split()
    dx = float(upper_corner[0]) - float(lower_corner[0])
    dy = float(upper_corner[-1]) - float(lower_corner[-1])
    return [str(dx), str(dy)]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('maps_api.ui', self)  # Загружаем дизайн
        # задаем тему карты
        self.theme = LIGHT
        self.theme_button.clicked.connect(self.change_theme)
        # задаем фиксированный размер
        size = [800, 450]
        self.setFixedSize(*size)
        # получаем топоним
        self.toponym_to_find = ''
        if len(sys.argv) > 1:
            self.toponym_to_find = " ".join(sys.argv[1:])

        self.init_api_settings()
        self.show_map()

    def init_api_settings(self):
        # параметры апи геокодера
        self.geocoder_server = "http://geocode-maps.yandex.ru/1.x/"
        self.geocoder_apikey = "8013b162-6b42-4997-9691-77b7074026e0"
        self.geocoder_params = {
            "apikey": self.geocoder_apikey,
            "format": "json",
            "geocode": self.toponym_to_find
        }
        # параметры апи карт
        self.map_server = "https://static-maps.yandex.ru/v1"
        self.map_apikey = "f3a0fe3a-b07e-4840-a1da-06f18b2ddf13"
        self.map_params = {
            "ll": '',
            "spn": '',
            "apikey": ''
        }
        self.map_size = [str(num) for num in [600, 450]]
        # Начальный масштаб
        self.spn = get_delta(self.get_toponym())
        self.spn = [float(x) for x in self.spn]

    def get_response(self, server, params):
        return requests.get(server, params=params)

    def get_toponym(self):
        json_response = self.get_response(self.geocoder_server, self.geocoder_params).json()
        return json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]

    def get_map_picture(self):
        toponym = self.get_toponym()
        toponym_coodrinates = toponym["Point"]["pos"]
        toponym_longitude, toponym_lattitude = toponym_coodrinates.split(" ")
        self.map_params = {
            "ll": ",".join([toponym_longitude, toponym_lattitude]),
            "spn": ",".join(map(str, self.spn)),
            "apikey": self.map_apikey,
            "size": ','.join(self.map_size),
            "theme": self.theme
        }
        return self.get_response(self.map_server, self.map_params)

    def show_map(self):
        if self.toponym_to_find:
            image = Image.open(BytesIO(self.get_map_picture().content))
            image.save('map.png')
            pixmap = QPixmap('map.png')
            self.map_label.setPixmap(pixmap)

    def change_theme(self):
        if self.theme == LIGHT:
            self.theme = DARK
        elif self.theme == DARK:
            self.theme = LIGHT
        self.show_map()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_PageUp:
            self.zoom_in()
        elif event.key() == Qt.Key.Key_PageDown:
            self.zoom_out()
        super().keyPressEvent(event)

    def zoom_in(self):
        # Увеличение масштаба
        self.spn = [min(x / 1.55, MAX_SPN) for x in self.spn]
        self.show_map()

    def zoom_out(self):
        # Уменьшение масштаба
        self.spn = [max(x * 1.55, MIN_SPN) for x in self.spn]
        self.show_map()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec())

