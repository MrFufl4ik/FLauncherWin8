import os
import system_manager

current_directory = os.getcwd()

compile_cmds_nt = [
    f"pyside6-uic.exe create_modpack_window.ui -o {current_directory}\\window_create.py",
    #f"pyside6-uic.exe main_window.ui -o {current_directory}\\window.py",
    f"pyside6-uic.exe settings_window.ui -o {current_directory}\\window_settings.py",
]

compile_cmds_linux = [
    #f"pyside6-uic create_modpack_window.ui -o {current_directory}/window_create.py",
    #f"pyside6-uic main_window.ui -o {current_directory}/window.py",
    #f"pyside6-uic settings_window.ui -o {current_directory}/window_settings.py",
    #f"pyside6-uic log_window.ui -o {current_directory}/window_log.py",
    f"pyside6-uic download_window.ui -o {current_directory}/window_download.py",
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