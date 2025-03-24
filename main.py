import requests
from io import BytesIO
import sys

from PIL import Image

from PyQt6 import uic
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt6.QtCore import Qt

LIGHT = 'light'
DARK = 'dark'
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
        uic.loadUi('maps_api.ui', self)

        # Инициализация настроек
        self.theme = LIGHT
        self.theme_button.clicked.connect(self.change_theme)
        self.search_button.clicked.connect(self.search_object)
        self.search_input.returnPressed.connect(self.search_object)

        self.setFixedSize(807, 450)
        self.toponym_to_find = 'Красноярск' #Установили Красноярск :)
        if len(sys.argv) > 1:
            self.toponym_to_find = " ".join(sys.argv[1:])

        self.markers = [] # Добавляем список маркеров

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

        self.map_server = "https://static-maps.yandex.ru/v1"
        self.map_apikey = "f3a0fe3a-b07e-4840-a1da-06f18b2ddf13"
        self.map_size = [str(num) for num in [600, 450]]

        try:
            self.spn = [float(x) for x in get_delta(self.get_toponym())]
        except:
            self.spn = [0.5, 0.5]

    def get_response(self, server, params):
        return requests.get(server, params=params)

    def get_toponym(self):
        response = self.get_response(self.geocoder_server, self.geocoder_params)
        json_response = response.json()
        return json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]

    def get_map_picture(self):
        try:
            toponym = self.get_toponym()
            coordinates = toponym["Point"]["pos"].split()
            params = {
                "ll": ",".join(coordinates),
                "spn": ",".join(map(str, self.spn)),
                "apikey": self.map_apikey,
                "size": ",".join(self.map_size),
                "theme": self.theme
            }

            # Добавляем метки
            if self.markers:
                params["pt"] = "~".join(self.markers)
            return requests.get(self.map_server, params=params)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            return None

    def show_map(self):
        response = self.get_map_picture()
        if response and response.status_code == 200:
            Image.open(BytesIO(response.content)).save('map.png')
            self.map_label.setPixmap(QPixmap('map.png'))

    def change_theme(self):
        self.theme = DARK if self.theme == LIGHT else LIGHT
        self.show_map()

    # Поиск Объекта на карте
    def search_object(self):
        self.toponym_to_find = self.search_input.text()
        if self.toponym_to_find:
            try:
                self.init_api_settings()
                toponym = self.get_toponym()
                coords = toponym["Point"]["pos"].split()
                coords_str = ",".join(coords)
                self.markers.append(f"{coords_str},pm2dgl")  # Добавляем новую метку
                self.show_map()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка поиска", f"Не удалось найти: {self.toponym_to_find}")

    # Изменение масштаба
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_PageUp:
            self.spn = [min(x / 1.55, MAX_SPN) for x in self.spn]
            self.show_map()
        elif event.key() == Qt.Key.Key_PageDown:
            self.spn = [max(x * 1.55, MIN_SPN) for x in self.spn]
            self.show_map()
        super().keyPressEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec())