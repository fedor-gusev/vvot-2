import boto3
from botocore.client import ClientError
from os import path
import os
import random
import shutil
import string
import pathlib
from pathlib import Path
from jinja2 import Template

ROOT_DIRECTORY = path.dirname(pathlib.Path(__file__).parent)

SITE_CONFIGURATION = {
    "ErrorDocument": {"Key": "error.html"},
    "IndexDocument": {"Suffix": "index.html"},
}

IMG_SUFFIX = [".jpg", ".jpeg"]
ACL = 'public-read'


def create_client(access, secret, endpoint, region):
    return boto3.session.Session().client(
        service_name='s3',
        endpoint_url=endpoint,
        aws_access_key_id=access,
        aws_secret_access_key=secret,
        region_name=region)


def create_resource(access, secret, endpoint, region):
    return boto3.session.Session().resource(
        service_name='s3',
        endpoint_url=endpoint,
        aws_access_key_id=access,
        aws_secret_access_key=secret,
        region_name=region)


def make_bucket(bucket_name, access, secret, endpoint, region):
    s3 = create_client(access, secret, endpoint, region)
    try:
        s3.head_bucket(Bucket=bucket_name)
        print(f"Бакет '{bucket_name}' существует.")
    except ClientError:
        s3.create_bucket(Bucket=bucket_name, ACL=ACL)


def get_albums(bucket_name, access, secret, endpoint, region):
    s3 = create_client(access, secret, endpoint, region)
    try:
        s3.list_objects(Bucket=bucket_name)['Contents']
    except Exception:
        raise Exception("Bucket is empty")
    unique_albums = []
    for key in s3.list_objects(Bucket=bucket_name)['Contents']:
        if key['Key'].endswith("/") and key['Key'].split("/")[0] not in unique_albums:
            unique_albums.append(key['Key'].split("/")[0])
    for value in unique_albums:
        print(value)


def get_files(bucket_name, access, secret, album, endpoint, region):
    s3 = create_resource(access, secret, endpoint, region)
    my_bucket = s3.Bucket(bucket_name)
    count_objects = 0
    count_files = 0

    for my_bucket_object in my_bucket.objects.filter(Prefix=f'{album}/', Delimiter='/'):
        count_objects = count_objects + 1
        if my_bucket_object.key.endswith(".jpg") or my_bucket_object.key.endswith(".jpeg"):
            print(my_bucket_object.key.split(f'{album}/')[1])
            count_files = count_files + 1

    if count_objects == 0:
        raise Exception(f"Альбом {album} не существует!")
    if count_files == 0:
        raise Exception(f"Альбом {album} пуст!")


def delete_album(bucket_name, access, secret, album, endpoint, region):
    s3 = create_resource(access, secret, endpoint, region)
    my_bucket = s3.Bucket(bucket_name)
    try:
        assert s3.Object(bucket_name, f'{album}/').get()
        for my_bucket_object in my_bucket.objects.filter(Prefix=f'{album}/'):
            s3.Object(bucket_name, my_bucket_object.key).delete()
    except Exception:
        raise Exception(f"Альбом {album} не существует!")


def delete_photo_in_album(bucket_name, access, secret, album, photo, endpoint, region):
    s3 = create_resource(access, secret, endpoint, region)
    assert s3.Bucket(bucket_name)
    try:
        assert s3.Object(bucket_name, f'{album}/').get()
    except:
        raise Exception(f"Альбом {album} не существует!")
    try:
        photo_path = f'{album}/{photo}'
        assert s3.Object(bucket_name, photo_path).get()
        s3.Object(bucket_name, photo_path).delete()
    except Exception:
        raise Exception(f"Фото '{photo}' не существует!")


def download_album(bucket, access, secret, album, album_path, endpoint, region):
    s3 = create_client(access, secret, endpoint, region)
    album_path = Path(album_path)
    if not is_album_exist(s3, bucket, album):
        raise Exception(f"Альбом {album} не существует!")

    if not album_path.is_dir():
        raise Exception(f"{str(album_path)} - не директория!")

    list_object = s3.list_objects(Bucket=bucket, Prefix=album + '/', Delimiter='/')
    for key in list_object["Contents"]:
        if not key["Key"].endswith("/"):
            obj = s3.get_object(Bucket=bucket, Key=key["Key"])
            filename = Path(key['Key']).name

            filepath = album_path / filename
            with filepath.open("wb") as file:
                file.write(obj["Body"].read())


def upload_album(bucket, access, secret, album, album_path, endpoint, region):
    s3 = create_client(access, secret, endpoint, region)
    album_path = Path(album_path)
    check_album(album)
    count = 0

    if not album_path.is_dir():
        raise Exception(f"Альбом {str(album_path)} не существует")

    if not is_album_exist(s3, bucket, album):
        s3.put_object(Bucket=bucket, Key=(album + '/'))
        print(f"Создание альбома {album}...")

    for file in album_path.iterdir():
        if is_image(file):
            print(f"Загрузка файла {file.name}...")
            key = f"{album}/{file.name}"
            s3.upload_file(str(file), bucket, key)
            count += 1


def make_site_album(bucket, access, secret, endpoint, region):
    s3 = create_client(access, secret, endpoint, region)
    url = f"https://{bucket}.website.yandexcloud.net"
    albums = get_albums_data(s3, bucket)

    template = get_template("album.html")

    albums_rendered = []
    i = 1
    for album, photos in albums.items():
        print(photos)
        template_name = f"album{i}.html"
        rendered_album = Template(template).render(album=album, images=photos, url=url)
        photos_path = save_temporary_template(rendered_album)

        s3.upload_file(photos_path, bucket, template_name)
        albums_rendered.append({"name": template_name, "album": album})
        i += 1

    template = get_template("index.html")
    rendered_index = Template(template).render(template_objects=albums_rendered)
    photos_path = save_temporary_template(rendered_index)
    s3.upload_file(photos_path, bucket, "index.html")

    template = get_template("error.html")
    photos_path = save_temporary_template(template)
    s3.upload_file(photos_path, bucket, "error.html")

    s3.put_bucket_website(Bucket=bucket, WebsiteConfiguration=SITE_CONFIGURATION)
    remove_temporary_dir()
    print(url)


def is_image(file):
    return file.is_file() and file.suffix in IMG_SUFFIX


def get_albums_data(session, bucket: str):
    albums = {}
    list_objects = session.list_objects(Bucket=bucket)
    for key in list_objects["Contents"]:
        album_img = key["Key"].split("/")
        if len(album_img) != 2:
            continue
        album, img = album_img
        if img == '':
            continue
        if album in albums:
            albums[album].append(img)
        else:
            albums[album] = [img]
    return albums


def is_album_exist(session, bucket, album):
    list_objects = session.list_objects(
        Bucket=bucket,
        Prefix=album + '/',
        Delimiter='/',
    )
    if "Contents" in list_objects:
        for _ in list_objects["Contents"]:
            return True
    return False


def check_album(album: str):
    if album.count("/"):
        raise Exception("Название альбома не может содержать '/'")


def get_template(name):
    template_path = Path(ROOT_DIRECTORY) / "templates" / name
    with open(template_path, "r") as file:
        return file.read()


def save_temporary_template(template):
    filename = ''.join(random.choices(string.ascii_letters + string.digits, k=8)) + ".html"
    temp_path = Path(ROOT_DIRECTORY) / "temp" / filename
    if not temp_path.parent.exists():
        os.mkdir(temp_path.parent)

    with open(temp_path, "w") as file:
        file.write(template)

    return str(temp_path)


def remove_temporary_dir():
    temp_path = Path(ROOT_DIRECTORY) / "temp"
    shutil.rmtree(temp_path)
