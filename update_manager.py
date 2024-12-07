import sys
import consts
import os
import config_manager
import pathlib
import py7zr

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


def unzip_update(modpack_id: str) -> int:
    update_archive_file_name = consts.UPDATE_ARCHIVE_FILE_NAME
    extract_path = f"{current_directory}/{consts.MODPACKS_FOLDER_NAME}/{modpack_id}/"
    if os.path.exists(update_archive_file_name):
        if not os.path.exists(extract_path): os.makedirs(extract_path)
        print("Пытаюсь распокавать архив: " + update_archive_file_name)
        try:
            with py7zr.SevenZipFile(update_archive_file_name, 'r') as f:
                f.extractall(extract_path)
            print("Успешно!")
            return 0
        except Exception as E:
            print(E)
            print("Ошибка при распоковке")
    return 1


def install_update(modpack_id: str, update_pkg: str, ftp: FTP) -> int:
    ret = download_file(consts.UPDATE_ARCHIVE_FILE_NAME, f"{consts.MODPACKS_FOLDER_NAME}/{modpack_id}/{update_pkg}",
                        ftp)
    if ret == 0:
        unzip_update(modpack_id)
        os.remove(consts.UPDATE_ARCHIVE_FILE_NAME)
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


def main():
    ftp = create_ftp(consts.UPDATE_DOMAIN, consts.UPDATE_PORT, consts.UPDATE_USER, consts.UPDATE_PASSWORD)
    if ftp is not None:
        update_pkg = check_update("prikol", ftp)
        if update_pkg is not None:
            ret = install_update("prikol", update_pkg, ftp)
            if ret == 0:
                post_update("prikol")


if __name__ == "__main__": main()
