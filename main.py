import sys
import os

import consts
import launchmc
import system_manager
import config_manager
import update_manager

from PyQt5 import QtWidgets
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QListWidget, QLabel, QComboBox
from PyQt5.QtCore import QRegularExpression
from PyQt5.QtGui import QRegularExpressionValidator

from window import Ui_MainWindow
from window_create import Ui_Form as Ui_Create_Form
from window_settings import Ui_Form as Ui_Settings_Form
from window_log import Ui_Form as Ui_Log_Form
from window_download import Ui_Form as Ui_Download_Form
from consts import *
from ftplib import FTP

current_directory = os.getcwd()


def get_folders() -> list:
    if system_manager.is_windows():
        return [name for name in os.listdir(f"{current_directory}\\{MODPACKS_FOLDER_NAME}")]
    else:
        return [name for name in os.listdir(f"{current_directory}/{MODPACKS_FOLDER_NAME}")]


def create_modpack_folder():
    if not os.path.exists(MODPACKS_FOLDER_NAME): os.makedirs(MODPACKS_FOLDER_NAME)


def is_modpack(folder):
    if os.path.exists(f"{current_directory}/{MODPACKS_FOLDER_NAME}/{folder}/{LAUNCHER_FILE_NAME}"): return True
    return False


def get_modpacks() -> list:
    folders = get_folders()
    modpacks = []
    for folder in folders:
        if is_modpack(folder): modpacks.append(folder)
    return modpacks


def get_title_name(modpack_name: str) -> str:
    modpack_path = f"{current_directory}/{MODPACKS_FOLDER_NAME}/{modpack_name}"
    config = config_manager.mc_config_get(modpack_path)
    if config is not None:
        modpack_title_name = config.get("titlename")
        if modpack_title_name is not None:
            return modpack_title_name

    return modpack_name


def get_title_name_none(modpack_name: str) -> str:
    modpack_path = f"{current_directory}/{MODPACKS_FOLDER_NAME}/{modpack_name}"
    config = config_manager.mc_config_get(modpack_path)
    if config is not None:
        modpack_title_name = config.get("titlename")
        if modpack_title_name is not None:
            return modpack_title_name

    return None


def get_current_index_lw(lw: QListWidget) -> int:
    if lw.currentItem():
        return lw.currentRow()
    return None


def set_banner(label: QLabel, path: str):
    label.setPixmap(QPixmap(path))


def clear_banner(label: QLabel):
    label.setPixmap(QPixmap(DEFAULT_BANNER_FILE))


def is_string_filled(s: str):
    if s is not None: return bool(s.strip())
    return False


def none_string(s: str) -> str:
    if is_string_filled(s): return s
    return None


class FLauncherWindow(QMainWindow):
    def __init__(self):
        super(FLauncherWindow, self).__init__()
        self.modpacks = None
        self.ftp = None
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.init_main_window()

    def init_main_window(self):
        create_modpack_folder()
        self.modpacks = []
        self.ui.pushButton_reload.clicked.connect(self.modpacks_update)
        self.ui.pushButton_run.clicked.connect(self.run)
        self.ui.pushButton_exit.clicked.connect(self.stop)
        self.ui.pushButton_folder.clicked.connect(self.run_explorer)
        self.ui.pushButton_create.clicked.connect(self.init_create_window)
        self.ui.pushButton_config.clicked.connect(self.init_settings_window)
        self.ui.pushButton_log.clicked.connect(self.init_log_window)
        self.ui.pushButton_download.clicked.connect(self.update_or_install_modpack)
        self.ui.list_view.currentItemChanged.connect(self.update_lw)
        self.modpacks_update()

    def init_log_window(self):
        self.log_window = QtWidgets.QDialog()
        self.log_ui_window = Ui_Log_Form()
        self.log_ui_window.setupUi(self.log_window)

        self.log_window.setWindowTitle(f"{WINDOW_NAME} | Логи")

        self.log_window.show()
        self.read_log()

    def init_create_window(self):
        self.create_window = QtWidgets.QDialog()
        self.create_ui_window = Ui_Create_Form()
        self.create_ui_window.setupUi(self.create_window)

        self.create_window.show()
        self.create_window.setWindowTitle(f"{WINDOW_NAME} | Создание модпака")

        input_validator = QRegularExpressionValidator(QRegularExpression("[A-za-z0-9]+"),
                                                      self.create_ui_window.lineEdit_id)
        self.create_ui_window.lineEdit_id.setValidator(input_validator)

        self.create_ui_window.pushButton_create.clicked.connect(self.create_modpack)

    def init_settings_window(self):
        if get_current_index_lw(self.ui.list_view) is not None:
            self.settings_window = QtWidgets.QDialog()
            self.settings_ui_window = Ui_Settings_Form()
            self.settings_ui_window.setupUi(self.settings_window)

            self.settings_window.show()
            modpack_title_name = get_title_name(self.modpacks[get_current_index_lw(self.ui.list_view)])
            self.settings_window.setWindowTitle(f"{WINDOW_NAME} | {modpack_title_name}")

            self.settings_ui_window.comboBoxLoader.currentTextChanged.connect(self.update_version_loader)

            self.default_settings()
            self.import_settings()

            self.settings_ui_window.pushButtonDone.clicked.connect(self.export_settings)
        else:
            QMessageBox.critical(
                self,
                f"{WINDOW_NAME} | Ошибка!",
                "Выберите модпак, для настройки!",
                buttons=QMessageBox.Ok,
                defaultButton=QMessageBox.Ok,
            )

    def init_download_window(self, ftp: FTP):
        self.download_window = QtWidgets.QDialog()
        self.download_ui_window = Ui_Download_Form()
        self.download_ui_window.setupUi(self.download_window)

        self.download_window.show()
        self.download_window.setWindowTitle(f"{WINDOW_NAME} | Установка модпаков")

        input_validator = QRegularExpressionValidator(QRegularExpression("[A-za-z0-9]+"),
                                                      self.download_ui_window.installLineEdit)
        self.download_ui_window.installLineEdit.setValidator(input_validator)

        self.ftp = ftp
        self.download_ui_window.installPushButton.clicked.connect(self.install_modpack)

    def update_or_install_modpack(self):
        modpack_at_id = get_current_index_lw(self.ui.list_view)

        print("Попытка залогинится в ФТП...")

        config = config_manager.lnc_config_get(current_directory)
        if config is not None:
            update_ip = config.get("update_ip", None)
            update_port = config.get("update_port", None)
            update_user = config.get("update_user", None)
            update_pass = config.get("update_passwd", None)

            if update_ip is not None and update_port is not None and update_user is not None and update_pass is not None:
                ftp = update_manager.create_ftp(str(update_ip), int(update_port), str(update_user), str(update_pass))
                if ftp is not None:
                    print("Соеденение с ФТП сервером установленно")
                    if modpack_at_id is not None:
                        modpack_name = self.modpacks[modpack_at_id]
                        modpack_path = f"{current_directory}/{MODPACKS_FOLDER_NAME}/{modpack_name}"

                        update_pkg = update_manager.check_update(modpack_name, ftp)
                        if update_pkg is not None:
                            update_status = update_manager.install_update(modpack_name, update_pkg, ftp)
                            if update_status == 0:
                                update_manager.post_update(modpack_name)
                                print("Обновление установленно")
                                QMessageBox.information(
                                    self,
                                    f"{WINDOW_NAME} | Оповещение!",
                                    f"Новое обновление установленно: {update_pkg}!",
                                    buttons=QMessageBox.Ok,
                                    defaultButton=QMessageBox.Ok,
                                )
                        else:
                            print("Обновлений не найдено")
                            QMessageBox.information(
                                self,
                                f"{WINDOW_NAME} | Оповещение!",
                                f"Обновлений нет.\nделать больше нечего...",
                                buttons=QMessageBox.Ok,
                                defaultButton=QMessageBox.Ok,
                            )
                    else:
                        self.init_download_window(ftp)
                else:
                    QMessageBox.critical(
                        self,
                        f"{WINDOW_NAME} | Ошибка!",
                        f"Сервер оффлайн! [{update_ip}:{update_port}]",
                        buttons=QMessageBox.Ok,
                        defaultButton=QMessageBox.Ok,
                    )
            else:
                print("Конфиг не заполнен!")
        else:
            print("Конфиг не создан...")

    def install_modpack(self):
        modpack_name = self.download_ui_window.installLineEdit.text()

        if is_string_filled(modpack_name):
            update_pkg = update_manager.check_update(modpack_name, self.ftp)
            if update_pkg is not None:
                update_status = update_manager.install_update(modpack_name, update_pkg, self.ftp)
                if update_status == 0:
                    update_manager.post_update(modpack_name)
                    print("Модпак установлен")
                    QMessageBox.information(
                        self,
                        f"{WINDOW_NAME} | Оповещение!",
                        f"Модпак установлен: {modpack_name}!",
                        buttons=QMessageBox.Ok,
                        defaultButton=QMessageBox.Ok,
                    )
            else:
                print("Такой модпак не найден на сервере!")
                QMessageBox.information(
                    self,
                    f"{WINDOW_NAME} | Оповещение!",
                    f"Такой модпак не найден на сервере!\nделать больше нечего...",
                    buttons=QMessageBox.Ok,
                    defaultButton=QMessageBox.Ok,
                )
        else:
            QMessageBox.critical(
                self,
                f"{WINDOW_NAME} | Ошибка!",
                f"Заполните поле с названием",
                buttons=QMessageBox.Ok,
                defaultButton=QMessageBox.Ok,
            )

    def read_log(self):
        with open(consts.LOG_FILE_NAME) as f:
            lines = f.readlines()
            for line in lines:
                self.log_ui_window.logTextEdit.append(line.strip())

    def update_version_loader(self):
        if self.settings_ui_window.comboBoxLoader.currentText() is not None:
            loader = self.settings_ui_window.comboBoxLoader.currentText().lower()
            self.load_version_loader(loader)

    def load_version_loader(self, loader):
        mcinfo_loader_path = f"{current_directory}/{MINECRAFT_INFO_FOLDER}/versions_{loader}.mcc"
        self.settings_ui_window.comboBoxVersion.clear()
        if os.path.exists(mcinfo_loader_path):
            with open(mcinfo_loader_path, 'r') as file:
                lines = file.readlines()
                for version in lines:
                    self.settings_ui_window.comboBoxVersion.addItem(version.strip())
        else:
            print(f"Файл не существует: {mcinfo_loader_path}")

    def default_settings(self):
        for loader in LOADERS:
            self.settings_ui_window.comboBoxLoader.addItem(loader.title())
        self.load_version_loader(LOADERS[0])

    def import_settings(self):
        modpack_at_id = get_current_index_lw(self.ui.list_view)
        modpack_name = self.modpacks[modpack_at_id]
        modpack_path = f"{current_directory}/{MODPACKS_FOLDER_NAME}/{modpack_name}"
        modpack_banner_path = f"{modpack_path}/{BANNER_FILE_NAME}"

        config = config_manager.mc_config_get(modpack_path)
        if config is not None:
            modpack_player_name = config.get("username", consts.DEFAULT_CONFIG.get("username"))
            modpack_loader = config.get("loader", consts.DEFAULT_CONFIG.get("loader"))
            modpack_version = config.get("version", consts.DEFAULT_CONFIG.get("version"))
            modpack_java_args = config.get("java_args", consts.DEFAULT_CONFIG.get("java_args"))

            for loader in LOADERS:
                if loader == modpack_loader:
                    self.settings_ui_window.comboBoxLoader.setCurrentText(loader.title())

            self.load_version_loader(modpack_loader)
            for i in range(self.settings_ui_window.comboBoxVersion.count()):
                if self.settings_ui_window.comboBoxVersion.itemText(i) == modpack_version:
                    self.settings_ui_window.comboBoxVersion.setCurrentText(modpack_version)

            if is_string_filled(modpack_player_name):
                self.settings_ui_window.lineEditPlayerName.setText(modpack_player_name)
            else:
                self.settings_ui_window.lineEditPlayerName.setText(DEFAULT_CONFIG.get("username"))

            if is_string_filled(modpack_java_args):
                self.settings_ui_window.lineEditJavaArgs.setText(modpack_java_args)
            else:
                self.settings_ui_window.lineEditJavaArgs.setText(DEFAULT_CONFIG.get("java_args"))

        modpack_title_name = get_title_name_none(modpack_name)
        if modpack_title_name is not None: self.settings_ui_window.lineEditVisualName.setText(modpack_title_name)

    def export_settings(self):
        modpack_at_id = get_current_index_lw(self.ui.list_view)
        if modpack_at_id is not None:
            modpack_name = self.modpacks[modpack_at_id]
            modpack_path = f"{current_directory}/{MODPACKS_FOLDER_NAME}/{modpack_name}"
            modpack_title_name = self.settings_ui_window.lineEditVisualName.text()
            modpack_java_args = self.settings_ui_window.lineEditJavaArgs.text()
            modpack_user_name = self.settings_ui_window.lineEditPlayerName.text()
            modpack_loader = self.settings_ui_window.comboBoxLoader.currentText().lower()
            modpack_version = self.settings_ui_window.comboBoxVersion.currentText()

            config = {
                "username": none_string(modpack_user_name),
                "loader": none_string(modpack_loader),
                "version": none_string(modpack_version),
                "titlename": none_string(modpack_title_name),
                "java_args": none_string(modpack_java_args),
            }
            new_config = {}
            for field in config:
                if config.get(field) is not None:
                    new_config.setdefault(field, config.get(field))

            result = config_manager.mc_config_set(modpack_path, new_config)

            if result != 0:
                QMessageBox.critical(
                    self.settings_window,
                    f"{WINDOW_NAME} | Ошибка!",
                    "Сохранить конфиг не удалось!",
                    buttons=QMessageBox.Ok,
                    defaultButton=QMessageBox.Ok,
                )
            else:
                QMessageBox.information(
                    self.settings_window,
                    f"{WINDOW_NAME} | Оповещение!",
                    "Конфиг успешно сохранен!",
                    buttons=QMessageBox.Ok,
                    defaultButton=QMessageBox.Ok,
                )
                print(f"Применены настройки: {config}")
        else:
            self.settings_window.close()

    def create_modpack(self):
        if self.create_ui_window.lineEdit_id.text():
            modpack_id = self.create_ui_window.lineEdit_id.text()
            modpack_title = self.create_ui_window.lineEdit_title_name.text()
            modpack_path = f"{current_directory}/{MODPACKS_FOLDER_NAME}/{modpack_id}"
            if not os.path.exists(modpack_path):
                os.makedirs(modpack_path)
                if is_string_filled(modpack_title):
                    config_manager.mc_config_set(modpack_path, {"titlename": modpack_title})
                with open(f"{modpack_path}/{LAUNCHER_FILE_NAME}", 'w') as launcher_file:
                    launcher_file.write("")
            else:
                QMessageBox.critical(
                    self.create_window,
                    f"{WINDOW_NAME} | Ошибка!",
                    "Папка модпака с таким ID уже существует!",
                    buttons=QMessageBox.Ok,
                    defaultButton=QMessageBox.Ok,
                )

        else:
            QMessageBox.critical(
                self.create_window,
                f"{WINDOW_NAME} | Ошибка!",
                "Поле ID не заполнено!",
                buttons=QMessageBox.Ok,
                defaultButton=QMessageBox.Ok,
            )

    def modpacks_update(self):
        self.ui.list_view.clear()
        self.modpacks = get_modpacks()
        for modpack in self.modpacks: self.ui.list_view.addItem(get_title_name(modpack))
        clear_banner(self.ui.top_image)

    def update_lw(self):
        index = get_current_index_lw(self.ui.list_view)
        if index is not None:
            banner_file = f"{current_directory}/{MODPACKS_FOLDER_NAME}/{self.modpacks[index]}/banner.png"
            if os.path.exists(banner_file):
                set_banner(self.ui.top_image, banner_file)
            else:
                clear_banner(self.ui.top_image)
        else:
            clear_banner(self.ui.top_image)

    def run_explorer(self):
        index = get_current_index_lw(self.ui.list_view)
        if index is not None:
            modpack_folder = f"{current_directory}/{MODPACKS_FOLDER_NAME}/{self.modpacks[index]}"
            if os.path.exists(modpack_folder):
                result = system_manager.start_file_explorer(modpack_folder)
                if result == 3:
                    QMessageBox.critical(
                        self,
                        f"{WINDOW_NAME} | Ошибка!",
                        f"Установите: {system_manager.UNIX_FILE_MANAGER.title()}!",
                        buttons=QMessageBox.Ok,
                        defaultButton=QMessageBox.Ok,
                    )
            else:
                self.modpacks_update()
        else:
            result = system_manager.start_file_explorer(current_directory)
            if result == 3:
                QMessageBox.critical(
                    self,
                    f"{WINDOW_NAME} | Ошибка!",
                    f"Установите {system_manager.UNIX_FILE_MANAGER.title()}!",
                    buttons=QMessageBox.Ok,
                    defaultButton=QMessageBox.Ok,
                )

    def stop(self):
        if system_manager.is_windows():
            if launchmc.stop_mc():
                print("Клиент успешно закрыт!")
                QMessageBox.information(
                    self,
                    f"{WINDOW_NAME} | Оповещение!",
                    "Модпак закрыт!",
                    buttons=QMessageBox.Ok,
                    defaultButton=QMessageBox.Ok,
                )
            else:
                print("Клиент не запущен!")
                QMessageBox.critical(
                    self,
                    f"{WINDOW_NAME} | Ошибка!",
                    "Модпак не запущен!\nЕсли вы запустили модпак по ошибке и хотите его закрыть, подождите пару секунд и повторите попытку.",
                    buttons=QMessageBox.Ok,
                    defaultButton=QMessageBox.Ok,
                )
        else:
            QMessageBox.critical(
                self,
                f"{WINDOW_NAME} | Ошибка!",
                "Бро, это линукс :)\nТута мои полномочия всё",
                buttons=QMessageBox.Ok,
                defaultButton=QMessageBox.Ok,
            )

    def run(self):
        if self.ui.list_view.currentItem():
            pos_at = get_current_index_lw(self.ui.list_view)
            if pos_at is not None:
                modpack = self.modpacks[pos_at]
                config = config_manager.mc_config_get(f"{current_directory}/{MODPACKS_FOLDER_NAME}/{modpack}")
                if config is not None:
                    print(f"Запускаю майнкрафт с конфигом: {config}")
                    if launchmc.run_mc(config, f"{current_directory}/{MODPACKS_FOLDER_NAME}/{modpack}/client"):
                        print("Запуск проходит успешно...")
                    else:
                        print("Лаунчер не поддерживает несколько майнкрафтов!")
                        QMessageBox.critical(
                            self,
                            f"{WINDOW_NAME} | Ошибка!",
                            "Запуск двух майнкрафт клиентов невозможен!",
                            buttons=QMessageBox.Ok,
                            defaultButton=QMessageBox.Ok,
                        )
                else:
                    self.modpacks_update()
            else:
                QMessageBox.critical(
                    self,
                    f"{WINDOW_NAME} | Ошибка!",
                    "Странная ошибка, в списке. Эммм.",
                    buttons=QMessageBox.Ok,
                    defaultButton=QMessageBox.Ok,
                )

        else:
            QMessageBox.critical(
                self,
                f"{WINDOW_NAME} | Ошибка!",
                "Выберите модпак, для запуска!",
                buttons=QMessageBox.Ok,
                defaultButton=QMessageBox.Ok,
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FLauncherWindow()
    window.show()

    sys.exit(app.exec())
