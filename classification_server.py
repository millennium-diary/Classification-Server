import io
import cv2
import socket
import numpy as np
from PIL import Image
from datetime import datetime
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


HOST = '0.0.0.0'  # 가용할 host 알아서 입력
PORT = 9000

serverSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    serverSock.bind((HOST, PORT))
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    print(ip_address, '서버 시작')

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

        # 전송
        conn.send(result.encode('utf_8'))
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        print(f'sent ({current_time})')
        print('=========================')

except socket.error as err:
    print('soc err: ', err)