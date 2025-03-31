## Сервер для сегментации

Для работы плагина QGIS необходим работающий в облаке сервер сегментации изображений на основе обученной модели. Такой сервер удобнее всего разместить в виде ноды Datasphere в Yandex Cloud.

Для подготовки сервера необходимо создать Docker-контейнер:

* Загружаем файл с моделью в папку `code`:
```
wget https://storage.yandexcloud.net/socialtech/garbage-detect/seg-model/model.pt -O code/model.pt
```
* Создаем Docker Image:
```
docker build -t segmentation-server --platform linux/amd64 .
```

Полученный контейнер нужно будет [разместить в Container Registry в Yandex Cloud](https://yandex.cloud/ru/docs/container-registry/operations/docker-image/docker-image-push), и затем использовать для [создания ноды Datasphere](https://yandex.cloud/ru/docs/tutorials/ml-ai/node-from-docker):

* аутентифицироваться в Container Registry
`yc iam create-token` -> в ответе IAM-токен

* `docker login --username iam --password <IAM-токен> cr.yandex`

* загрузить докер-образ в Container registry:
`docker tag garbage-docker cr.yandex/<rid>/garbage:v<x>`,
`docker push cr.yandex/<rid>/garbage:v<x>`, где вместо <x> подставить номер версии.
Здесь `<rid>` - ID нашего реестра (нужно подставить соответствующий id), `garbage:v<x>` - произвольной название + тег, может быть любым

* создать новую ноду из нового Docker-образа.
    - порт нужно указывать такой же, какой в `server.py` (8000)
    - лучше ставить большой таймаут, например, 600 секунд

* После создания ноды нужно переключить alias datasphere.user.segmentation-backend на использование новой ноды.

Протестировать работу сервера удобно с помощью тестового клиента
`test_client.py`. Там можно выбрать между localhost-ом и alias-ом в датасфере.