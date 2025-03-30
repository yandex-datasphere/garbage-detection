## Segmentation Backend

В рамках проекта распознавания мусора был создан инструмент для автоматизированной разметки датасетов на основе модели Segment Anything.

### Установка

Данный Backend может быть собран с помощью Docker: 
`docker build -t garbage-docker .`

Чтобы изменить модель, достаточно поменять файл `src/model.pt`

Для того, чтобы развернуть Docker-образ в Datasphere, можно воспользоваться [следующей инструкцией](https://yandex.cloud/ru/docs/datasphere/tutorials/node-from-docker).
Действия по настройке из инструкции выполняются один раз. [Текущий проект с нодами](https://datasphere.yandex.cloud/communities/bt1rnjt1276e3aqlfo3e/projects/bt1opovj0dk2pdvbquog)

### Сборка новой версии и развёртывание в Datasphere

Здесь описаны действия, которые нужно выполнять каждый раз для создания новой версии:

- собирать под linux/amd64:
`docker build -t garbage-docker --platform linux/amd64 .`

- аутентифицироваться в Container Registry
`yc iam create-token` -> в ответе IAM-токен

- `docker login --username iam --password <IAM-токен> cr.yandex`

- загрузить докер-образ в Container registry:
`docker tag garbage-docker cr.yandex/<rid>/garbage:v<x>`,
`docker push cr.yandex/<rid>/garbage:v<x>`, где вместо <x> подставить номер версии.
Здесь `<rid>` - ID нашего реестра (нужно подставить соответствующий id), `garbage:v<x>` - произвольной название + тег, может быть любым

- создать новую ноду из нового Docker-образа.
    - порт нужно указывать такой же, какой в `server.py` (8000)
    - лучше ставить большой таймаут, например, 600 секунд

- После создания ноды нужно переключить alias datasphere.user.segmentation-backend на использование новой ноды.

Протестировать работу сервера удобно с помощью тестового клиента
`test_client.py`. Там можно выбрать между localhost-ом и alias-ом в датасфере.