import os
import requests
import urllib.request
import datetime

OUTPUT_PATH = os.path.join(os.getcwd(), 'output.json')
DOWNLOAD_PATH = os.path.join(os.getcwd(), 'downloads')

LOG_PATH = os.path.join(os.getcwd(), 'all.log')
Y_DISK_PATH = 'test'
PHOTOS_TO_UPLOAD = 5
VK_ID = 10406825
ALBUM_ID = 'profile'

with open('vk_secret.txt', 'r') as file_object:
    vk_token = file_object.read().strip()

with open('yd_secret.txt', 'r') as file_object:
    yd_token = file_object.read().strip()


def logger(message):
    log_item = message
    with open(LOG_PATH, "a") as log:
        log.writelines(str(log_item))


class VkDownloader:
    def __init__(self, vk_id, vk_token):
        self.id = vk_id
        self.vk_token = vk_token
        self.res = []
        self.res_album = []
        self.new_likes_list = []
        self.link_list = []
        self.upload_list = []
        self.upload_data = []
        self.likes_list = []
        self.json_list = []
        self.json_data = {}
        self.like_data = []

    def data_parser(self, vk_id, token, album_id):
        url = 'https://api.vk.com/method/photos.get'
        params = {
            'user_id': vk_id,
            'access_token': token,
            'v': '5.77',
            'album_id': album_id,
            'extended': 1,
            'photo_sizes': 1
        }
        response = requests.get(url, params=params)
        self.res = response.json()['response']['items']
        return self.res

    def rename_duplicates(self):
        for ind, elm in enumerate(self.res):
            likes = str(elm['likes']['count'])
            date = int(elm['date'])
            date_to_photo = datetime.datetime.fromtimestamp(date).strftime('%Y-%m-%d')
            date_to_photo = str(date_to_photo)
            if self.new_likes_list.count(likes) == 1:
                self.new_likes_list.append(likes + '_' + date_to_photo)
            else:
                self.new_likes_list.append(likes)
        return self.new_likes_list

    def make_link_list(self):
        for ind, elm in enumerate(self.res):
            link = elm['sizes'][-1]['url']
            size_type = elm['sizes'][-1]['type']
            width = elm['sizes'][-1]['width']
            height = elm['sizes'][-1]['height']
            self.like_data = [size_type, width, height, link]
            self.likes_list.append(self.like_data)
        zipped_data = zip(self.new_likes_list, self.likes_list)
        zipped_data = list(zipped_data)
        for ind, elm in enumerate(zipped_data):
            like_data = [elm[0], elm[1][0], elm[1][1], elm[1][2], elm[1][-1]]
            self.link_list.append(like_data)

        self.link_list = sorted(self.link_list, key=lambda x: x[2], reverse=True)
        return self.link_list

    def data_download(self):
        for item in self.link_list:
            file_name = item[0]+'.jpg'
            link = item[4]
            size_type = item[1]
            local_path = os.path.join(DOWNLOAD_PATH, file_name)

            upload_data_item = [file_name, local_path]
            self.upload_data.append(upload_data_item)

            urllib.request.urlretrieve(link, local_path)
            log_time = datetime.datetime.now()
            print(f'{log_time}: Фото "{file_name}" загружено на локальный диск в папку {DOWNLOAD_PATH}')
            logger(f'{log_time}: Фото "{file_name}" загружено на локальный диск в папку {DOWNLOAD_PATH} \n')
            json_data = {'file_name': file_name, 'size': size_type}
            self.json_list.append(json_data)

        with open(OUTPUT_PATH, "w") as output:
            output.write(str(self.json_list))
        return self.upload_data

    def upload_best_list(self, number):
        photo_quantity = int(number)
        for ind, elm in enumerate(self.upload_data):
            if ind <= photo_quantity-1:
                self.upload_list.append(elm)
        return self.upload_list


class YaUploader:
    def __init__(self, yd_token):
        self.yd_token = yd_token

    def get_ya_headers(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': 'OAuth {}'.format(yd_token)
        }

    def create_dir(self, Y_DISK_PATH):
        url = "https://cloud-api.yandex.net/v1/disk/resources"
        headers = self.get_ya_headers()
        params = {"path": Y_DISK_PATH, "overwrite": "true"}
        response = requests.put(url, headers=headers, params=params)
        if response.status_code == 201:
            print(f'Папка "{Y_DISK_PATH}" создана')
        else:
            print(f'Папка "{Y_DISK_PATH}" уже существует по указанному адресу')

    def get_upload_link(self, Y_DISK_PATH):
        upload_url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        headers = self.get_ya_headers()
        params = {"path": Y_DISK_PATH, "overwrite": "true"}
        response = requests.get(upload_url, headers=headers, params=params)
        href = response.json()
        return href

    def upload_file(self, upload_list):
        for elm in upload_list:
            href = self.get_upload_link(f"{Y_DISK_PATH}/" + elm[0]).get("href", "")
            response = requests.put(href, data=open(elm[1], 'rb'))
            response.raise_for_status()
            if response.status_code == 201:
                log_time = datetime.datetime.now()
                print(f'{log_time}: Фото "{elm[0]}" загружено на Yandex.Disk в папку {Y_DISK_PATH}')
                logger(f'{log_time}: Фото "{elm[0]}" загружено на Yandex.Disk в папку {Y_DISK_PATH} \n')


class PhotoBackup:
    def __init__(self):

        vk = VkDownloader(VK_ID, vk_token)
        yd = YaUploader(yd_token)
        vk.data_parser(VK_ID, vk_token, ALBUM_ID)
        vk.rename_duplicates()
        vk.make_link_list()
        vk.data_download()
        yd.create_dir(Y_DISK_PATH)
        yd.upload_file(vk.upload_best_list(PHOTOS_TO_UPLOAD))


if __name__ == '__main__':
    photo_bak = PhotoBackup()
