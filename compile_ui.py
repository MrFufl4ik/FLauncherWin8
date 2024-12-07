import os
import system_manager

current_directory = os.getcwd()

compile_cmds_nt = [
    f"pyside6-uic.exe create_modpack_window.ui -o {current_directory}\\window_create.py",
    #f"pyside6-uic.exe main_window.ui -o {current_directory}\\window.py",
    f"pyside6-uic.exe settings_window.ui -o {current_directory}\\window_settings.py",
]

compile_cmds_linux = [
    f"pyuic5 -x create_modpack_window.ui -o {current_directory}/window_create.py",
    f"pyuic5 -x main_window.ui -o {current_directory}/window.py",
    f"pyuic5 -x settings_window.ui -o {current_directory}/window_settings.py",
    f"pyuic5 -x log_window.ui -o {current_directory}/window_log.py",
    f"pyuic5 -x download_window.ui -o {current_directory}/window_download.py",
]

def main():
    os.chdir("ui")
    if system_manager.is_windows():
        for cmd in compile_cmds_nt:
            print("Use:",cmd)
            os.system(cmd)
    else:
        for cmd in compile_cmds_linux:
            print("Use:",cmd)
            os.system(cmd)


if __name__ == "__main__":
    main()