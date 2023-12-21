import fileinput
import os
from impl.boto_functions import make_bucket, get_albums, get_files, delete_album, delete_photo_in_album
from impl.boto_functions import download_album, upload_album, make_site_album
from pathlib import Path

file_dir = f"~{os.sep}.config{os.sep}cloudphoto{os.sep}"
file_path = file_dir + f"cloudphotorc.ini"


def init(bucket_name, aws_access_key, secret):
    check_file_exists()
    with fileinput.FileInput(os.path.expanduser(file_path), inplace=True) as file:
        for line in file:
            line = line.replace("INPUT_BUCKET_NAME", bucket_name)
            line = line.replace("INPUT_AWS_ACCESS_KEY_ID", aws_access_key)
            line = line.replace("INPUT_AWS_SECRET_ACCESS_KEY", secret)
            print(line, end='')
    bucket, access, secret, endpoint, region = get_params()
    make_bucket(bucket, access, secret, endpoint, region)


def check_file_exists():
    if not os.path.exists(file_path):
        Path(os.path.expanduser(file_dir)).mkdir(parents=True, exist_ok=True)
        with open(os.path.expanduser(file_path), 'w') as file:
            file.write("[DEFAULT]\n")
            file.write("bucket = INPUT_BUCKET_NAME\n")
            file.write("aws_access_key_id = INPUT_AWS_ACCESS_KEY_ID\n")
            file.write("aws_secret_access_key = INPUT_AWS_SECRET_ACCESS_KEY\n")
            file.write("region = ru-central1\n")
            file.write("endpoint_url = https://storage.yandexcloud.net")


# Выделяется по названию, т.к. функция list уже существует
def list_func(album):
    bucket, access, secret, endpoint, region = get_params()

    if album is None: 
        get_albums(bucket, access, secret, endpoint, region)
    else:
        get_files(bucket, access, secret, album, endpoint, region)


def delete(album, photo):
    bucket, access, secret, endpoint, region = get_params()
    if photo is None: 
        delete_album(bucket, access, secret, album, endpoint, region)
    else:
        delete_photo_in_album(bucket, access, secret, album, photo, endpoint, region)


def download(album, path):
    bucket, access, secret, endpoint, region = get_params()
    download_album(bucket, access, secret, album, path, endpoint, region)


def upload(album, path):
    bucket, access, secret, endpoint, region = get_params()
    upload_album(bucket, access, secret, album, path, endpoint, region)         


def make_site():
    bucket, access, secret, endpoint, region = get_params()
    make_site_album(bucket, access, secret, endpoint, region)


def get_params():
    config = {}
    i = 0
    with open(os.path.expanduser(file_path), 'r') as file:
        for line in file:
            i = i + 1
            if i == 1:
                continue
            name, value = line.strip().split(' = ', 1)
            config[name] = value

    bucket = config['bucket']
    access = config['aws_access_key_id']
    secret = config['aws_secret_access_key']
    endpoint = config['endpoint_url']
    region = config['region']
    if (bucket == "INPUT_BUCKET_NAME" or access == "INPUT_AWS_ACCESS_KEY_ID"
            or secret == "INPUT_AWS_SECRET_ACCESS_KEY"):
        raise Exception("Неиницилизированный файл конфигурации!")
    return bucket, access, secret, endpoint, region
