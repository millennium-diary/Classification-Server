import io
import cv2
import base64
import socket
import requests
import numpy as np
from PIL import Image
from datetime import datetime
from bs4 import BeautifulSoup
from keras.models import load_model

model = load_model('drawing_resnet.h5')
classes = [
    'airplane',
    'bus',
    'cake',
    'car',
    'cat',
    'dog',
    'grass',
    'house',
    'rainbow',
    'snowman'
]


# 클라이언트 측에서 보낸 바이트 배열을 이미지로 저장하여 클래스 예측하기
def string2image(byte_array, client_ip):
    client_ip = client_ip.replace('.', ',')
    filename = f'img_{client_ip}.jpg'

    byte = io.BytesIO(byte_array)
    png = Image.open(byte).convert('RGBA')
    new_image = Image.new('RGBA', png.size, 'WHITE')
    new_image.paste(png, mask=png)
    new_image.convert('RGB').save(filename)

    img = cv2.imread(filename)
    img = cv2.resize(img, dsize=(224, 224))

    X_test = np.array([img])
    pred = model.predict(X_test)
    pred = np.argmax(pred, axis=1)[0]

    result_class = classes[pred]
    print(f'result class: {result_class}')
    return result_class


# 사이트에서 첫 페이지에 있는 모든 이미지 링크 가져오기
def image_urls(result_class):
    url = f'https://www.flaticon.com/search?word={result_class}'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')

    images = []
    holders = soup.findAll('div', {'class': 'icon--holder'})
    for holder in holders[:20]:
        img = holder.find('img')
        link = img['data-src']

        link += 'URL'
        # crawled = base64.b64encode(requests.get(url).content)
        # print(crawled)
        images.append(link)

    # images[-1] += 'END'
    urls = ''.join(images)
    return urls


HOST = '0.0.0.0'  # 가용할 host 알아서 입력
PORT = 9000

serverSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    serverSock.bind((HOST, PORT))
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    print(ip_address, '서버 시작')
    print('--------------------------------------------')

    serverSock.listen(5)  # 클라이언트 동시 접속 수: 1 ~ 5
    while True:
        received = b''
        conn, addr = serverSock.accept()
        print('client info: ', addr[0], addr[1])

        while True:
            buffer = conn.recv(1024)
            received += buffer

            if received.endswith(b'END'):
                print('EOF\n')
                break

        image = received.replace(b'END', b'')
        result = string2image(image, addr[0])
        urls = image_urls(result)

        # 전송
        conn.send(urls.encode('utf_8'))
        # for url in urls:
        #     print(url.encode('utf_8'))
        #     conn.send(url.encode('utf_8'))
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        print(f'sent ({current_time})')
        print('=========================')

except socket.error as err:
    print('soc err: ', err)
