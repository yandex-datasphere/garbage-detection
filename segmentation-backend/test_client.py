import json
import shutil
import time

import requests

# url = "https://node-api.datasphere.yandexcloud.net/hello"
# if __name__ == '__main__':
#     headers = {
#         "x-node-alias": "datasphere.user.segmentation-backend",
#         "Authorization": "Api-Key AQVN1vLuEmspghqfLIBxf2nmNDzctez-kjrrxKdx",
#         "x-folder-id": "b1gbm9skjpv4gt0r8dmi",
#     }
#
#     start = time.time()
#     response = requests.post(url, headers=headers)
#     end = time.time()
#     print(end - start)
#     print(response.text)

import ast

# url = "http://127.0.0.1:8000/process"
url = "https://node-api.datasphere.yandexcloud.net/process"
if __name__ == '__main__':
    headers = {
        "x-node-alias": "datasphere.user.segmentation-backend",
        "Authorization": "Api-Key AQVN1vLuEmspghqfLIBxf2nmNDzctez-kjrrxKdx",
        "x-folder-id": "b1gbm9skjpv4gt0r8dmi",
    }
    # headers={}

    start = time.time()
    response = requests.post(url, headers=headers, files={"image": open("003_image.jpg", 'rb')})
    end = time.time()
    print(end - start)
    # print(response.text)

    if response.status_code == 400:
        print(response.text)
    else:
        save_file = open("img.jpg", "wb")
        save_file.write(response.content)
        save_file.close()

        cl_coefs_str = response.cookies.get("cl_coefs").replace("\\054", ",")[1:-1]
        cl_coefs = ast.literal_eval(cl_coefs_str)
        print(cl_coefs)
        del response
