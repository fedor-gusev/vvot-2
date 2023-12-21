#!/usr/bin/python3
#!pip install boto3
#!pip install jinja2

import argparse
import sys
from impl.app_functions import init, list_func, delete, download, upload, make_site

parser = argparse.ArgumentParser(prog='cloudphoto')
parser_cmd = parser.add_subparsers(title='command', dest='command')
init_cmd = parser_cmd.add_parser('init', help='Ининциализация программы')
list_cmd = parser_cmd.add_parser('list', help='Просмотр альбома/альбомов')
list_cmd.add_argument('--album', metavar='ALBUM', type=str, help='Название альбома')
download_cmd = parser_cmd.add_parser('download', help="Скачивание фотографий")
download_cmd.add_argument('--album', metavar='ALBUM', type=str, help='Название альбома', required=True)
download_cmd.add_argument('--path', metavar='PHOTOS_DIR', type=str, default='.', help='Путь к фотографиям',
                          required=False)
upload_cmd = parser_cmd.add_parser('upload', help='Выгрузка фотографий')
upload_cmd.add_argument('--album', metavar='ALBUM', type=str, help='Название альбома', required=True)
upload_cmd.add_argument('--path', metavar='PHOTOS_DIR', type=str, default='.', help='Путь к фотографиям',
                        required=False)
delete_cmd = parser_cmd.add_parser('delete', help='Удаление альбома')
delete_cmd.add_argument('--album', metavar='ALBUM', type=str, help='Название альбома')
delete_cmd.add_argument('--photo', metavar='PHOTO', type=str, help='Название фотографии')
mksite_cmd = parser_cmd.add_parser('mksite', help='Публикация веб-страницы')
args = parser.parse_args()


def __main__():
    try:
        if args.command == 'init':
            aws_access_key_id = input('aws_access_key_id is ')
            aws_secret_access_key = input('aws_secret_access_key is ')
            bucket_name = input('bucket_name is ')
            init(bucket_name, aws_access_key_id, aws_secret_access_key)
        elif args.command == 'list':
            list_func(args.album)
        elif args.command == 'upload':
            upload(args.album, args.path)
        elif args.command == 'delete':
            delete(args.album, args.photo)
        elif args.command == 'download':
            download(args.album, args.path)
        elif args.command == 'mksite':
            make_site()
        else:
            print(f"Команда {args.command} не распознана. Используйте --help")
            sys.exit(1)

        print("Команда успешно выполнена")
        sys.exit(0)

    except Exception as err:
        print(f"Ошибка: {err}")
        sys.exit(1)


__main__()
