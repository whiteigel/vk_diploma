import os
import requests
import urllib.request
# import collections
import datetime
import time
import sys

output_path = os.path.join(os.getcwd(), 'output.json')
download_path = os.path.join(os.getcwd(), 'downloads')
log_path = os.path.join(os.getcwd(), 'all.log')
ydisk_file_path = 'vk_img/'

with open('vk_secret.txt', 'r') as file_object:
    vk_token = file_object.read().strip()

with open('yd_secret.txt', 'r') as file_object:
    yd_token = file_object.read().strip()

class VkDownloader:
    def __init__(self, vk_id, vk_token, yd_token):
        self.id = vk_id
        self.vk_token = vk_token
        self.yd_token = yd_token

    def get_images_from_vk(self, id, token):
        json_list = []
        json_data = {}
        upload_data = {}
        URL = 'https://api.vk.com/method/photos.get'
        params = {
            'user_id': id,
            'access_token': token,
            'v':'5.77',
            'album_id': 'profile',
            'extended': 1,
            'photo_sizes': 1
        }
        response = requests.get(URL, params=params)
        res = response.json()['response']['items']
        for ind, elm in enumerate(res):
            likes = str(elm['likes']['count'])
            link = elm['sizes'][-1]['url']
            size_type = elm['sizes'][-1]['type']
            photo_name = likes + '.jpg'
            json_data = {'file_name':photo_name, 'size':size_type}
            json_list.append(json_data)
            local_path = os.path.join(download_path, photo_name)
            upload_data[photo_name] = local_path
            urllib.request.urlretrieve(link, local_path)
            datetime_object = datetime.datetime.now()
            print(f'{datetime_object}: Фото {photo_name} загружено на локальный диск в папку {download_path}')
            self.logger(f'{datetime_object}: Фото {photo_name} загружено на локальный диск в папку {download_path} \n')

        with open(output_path, "w") as output:
            output.write(str(json_list))
        return [upload_data]

    def logger(self, message):
        log_item = message
        with open(log_path, "a") as log:
            log.writelines(str(log_item))

    def get_ya_headers(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': 'OAuth {}'.format(yd_token)
        }

    def get_upload_link(self, ydisk_file_path):
        upload_url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        headers = self.get_ya_headers()
        params = {"path": ydisk_file_path, "overwrite": "true"}
        response = requests.get(upload_url, headers=headers, params=params)
        href = response.json()['href']
        return href

    def upload_file(self, upload_data):
        for ind, elm in enumerate(upload_data):
            for key, value in elm.items():
                href = self.get_upload_link(ydisk_file_path + key)
                response = requests.put(href, data=open(value, 'rb'))
                response.raise_for_status()
                if response.status_code == 201:
                    datetime_object = datetime.datetime.now()
                    print(f'{datetime_object}: Фото "{key}" загружено на Yandex.Disk в папку {ydisk_file_path}')
                    self.logger(f'{datetime_object}: Фото "{key}" загружено на Yandex.Disk в папку {ydisk_file_path} \n')

if __name__ == '__main__':
    vk = VkDownloader(10406825, vk_token, yd_token)
    vk.upload_file(vk.get_images_from_vk(10406825, vk_token))
