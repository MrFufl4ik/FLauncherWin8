import sys
import consts
import os
import config_manager
import pathlib

from ftplib import FTP

current_directory = os.getcwd()


def create_ftp(ip: str, port: int, user: str, passwd: str) -> FTP:
    try:
        server = FTP()
        server.encoding = "utf-8"
        server.connect(ip, port)
        server.login(user, passwd)
        return server
    except Exception as E:
        print(E)
        print("Не удалось подключится к ФТП серверу!")
    return None


def get_files(server_path: str, ftp: FTP) -> list:
    try:
        files = ftp.nlst(server_path)
        return files
    except Exception as E:
        print(E)
        print("Папка не существует")
    return None


def get_modpack_version(modpack_id: str) -> int:
    config = config_manager.mc_config_get(f"{current_directory}/modpacks/{modpack_id}")
    if config is not None:
        modpack_version = config.get("update_version")
        if modpack_version is not None:
            try:
                return int(modpack_version)
            except Exception as E:
                print(E)
                sys.exit(1)
    return 0


def download_file(local_path: str, server_path: str, ftp: FTP) -> int:
    print(f"Пытаюсь получить файл: /{server_path}")
    if os.path.exists(local_path): os.remove(local_path)
    try:
        with open(local_path, "wb") as file:
            ftp.retrbinary(f"RETR {server_path}", file.write)
            print("Успешно!")
            return 0
    except Exception as E:
        print(E)
        print("Ошибка при загрузке")
    return 1


def post_update(modpack_id: str):
    modpack_path = f"{current_directory}/{consts.MODPACKS_FOLDER_NAME}/{modpack_id}"
    config = config_manager.upd_config_get(modpack_path)
    if config is not None:
        list_file_for_delete = config.get("files_delete", None)
        set_config_data = config.get("config_set", None)
        if list_file_for_delete is not None:
            for file in list_file_for_delete:
                file_path = f"{modpack_path}/{file}"
                if os.path.exists(file_path): os.remove(file_path)
            print("Удаленны бесполезные файлы...")
        if set_config_data is not None:
            config_manager.mc_config_set(modpack_path, set_config_data)
            print("Выставлены новые настройки...")
        os.remove(f"{modpack_path}/{consts.UPD_CONFIG_NAME}")


def install_update(modpack_id: str, update_pkg: str, ftp: FTP) -> int:
    ret = download_file(consts.UPDATE_ARCHIVE_FILE_NAME, f"{consts.MODPACKS_FOLDER_NAME}/{modpack_id}/{update_pkg}",
                        ftp)
    if ret == 0:
        os.system(f"\"C:\\Program Files\\7-Zip\\7zFM.exe\" {current_directory}\\{consts.UPDATE_ARCHIVE_FILE_NAME}")
        return 0
    return 1


def check_update(modpack_id: str, ftp: FTP) -> str:
    curr_version = get_modpack_version(modpack_id)
    files = get_files(f"{consts.MODPACKS_FOLDER_NAME}/{modpack_id}", ftp)
    if files is not None:
        for update_pkg in files:
            pkg_name = pathlib.Path(update_pkg).stem
            if pkg_name.isdigit():
                version = int(pkg_name)
                if version > curr_version:
                    return update_pkg
    return None
