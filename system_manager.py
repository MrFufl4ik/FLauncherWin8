import subprocess
import psutil
import os

os_name = os.name

WIN_FILE_MANAGER = "explorer.exe"
UNIX_FILE_MANAGER = "nemo"


def windows_patch_path(original_path):
    return original_path.replace('/', '\\')


def is_windows():
    if os_name == "nt":
        return True
    elif os_name == 'posix':
        return False


def start_file_explorer(path: str) -> int:
    if is_windows():
        file_explorer_run_cmd = f"{WIN_FILE_MANAGER} {windows_patch_path(path)}"
        subprocess.Popen(file_explorer_run_cmd)
    else:
        file_explorer_run_cmd = [UNIX_FILE_MANAGER, path]
        if os.path.exists(f"/bin/{UNIX_FILE_MANAGER}"):
            subprocess.Popen(file_explorer_run_cmd)
        else:
            return 3
    return 0


def kill_process_by_name(process_name) -> bool:
    for process in psutil.process_iter(['name']):
        try:
            if process.info['name'] == process_name:
                process.kill()
                print(f"Процесс {process_name} (PID: {process.pid}) был убит.")
                return True
        except:
            print(f"Ошибка при закрытие, {process_name}, {process.pid}")
    return False


def is_process_running(process_name):
    for process in psutil.process_iter(attrs=['pid', 'name']):
        if process.info['name'] == process_name:
            return True
    return False