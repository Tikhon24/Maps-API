import requests
from io import BytesIO
import sys

from PIL import Image

from PyQt6 import uic
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QTableWidgetItem, QHeaderView, QWidget, QPushButton


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
        # задаем фиксированный размер
        size = [600, 450]
        self.setFixedSize(*size)
        # получаем топоним
        self.toponym_to_find = ''
        if len(sys.argv) > 1:
            self.toponym_to_find = " ".join(sys.argv[1:])
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
        self.map_size = [str(num) for num in size]

        # если передан топоним, делаем запрос и рисуем карту
        if self.toponym_to_find:
            image = Image.open(BytesIO(self.get_map_picture()))
            image.save('map.png')
            pixmap = QPixmap('map.png')
            self.map_label.setPixmap(pixmap)

    def get_response(self, server, params):
        return requests.get(server, params=params)

    def get_map_picture(self):
        # Преобразуем ответ в json-объект
        json_response = self.get_response(self.geocoder_server, self.geocoder_params).json()
        # Получаем первый топоним из ответа геокодера.
        toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
        # Координаты центра топонима:
        toponym_coodrinates = toponym["Point"]["pos"]
        # Долгота и широта:
        toponym_longitude, toponym_lattitude = toponym_coodrinates.split(" ")
        # Собираем параметры для запроса к StaticMapsAPI:
        self.map_params = {
            "ll": ",".join([toponym_longitude, toponym_lattitude]),
            "spn": ",".join(get_delta(toponym)),
            "apikey": self.map_apikey,
            "size": ','.join(self.map_size)
        }

        return self.get_response(self.map_server, self.map_params).content


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec())
