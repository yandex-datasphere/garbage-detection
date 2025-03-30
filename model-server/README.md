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

Полученный контейнер нужно будет [разместить в Container Registry в Yandex Cloud](https://yandex.cloud/ru/docs/container-registry/operations/docker-image/docker-image-push), и затем использовать для [создания ноды Datasphere](https://yandex.cloud/ru/docs/tutorials/ml-ai/node-from-docker).