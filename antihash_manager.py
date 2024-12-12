import hashlib
#tests
import os
import consts

def get_file_sha1(filename: str) -> str:
    openedFile = open(filename, "rb")
    hash = hashlib.sha1(openedFile.read())
    return hash.hexdigest()

def check_sum_sha1(filename: str, hash_sum: str) -> bool:
    file_hash = get_file_sha1(filename)
    if file_hash == hash_sum:
        return True
    return False

def check_sums_sha1(filename: str, hash_sums: list):
    for hash in hash_sums:
        if check_sum_sha1(filename, hash): return True
    return False

def create_hashes(folder_path: str) -> list:
    hashes = []
    files = os.listdir(folder_path)
    files_to_hash = [f for f in files if os.path.isfile(os.path.join(folder_path, f))]

    for file in files_to_hash:
        hashes.append(get_file_sha1(f"{folder_path}/{file}"))

    return hashes

