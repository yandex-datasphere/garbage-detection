Данный Backend может быть собран с помощью Docker: 
`docker build -t garbage-docker .`

Чтобы изменить модель, достаточно поменять файл `src/model.pt`

Для того, чтобы развернуть Docker-образ в Datasphere, можно воспользоваться следующей инструкцией
https://yandex.cloud/ru/docs/datasphere/tutorials/node-from-docker
Действия по настройке из инструкции выполняются один раз

Здесь описаны действия, которые нужно выполнять каждый раз для создания новой версии

- собирать под linux/amd64:
`docker build -t garbage-docker --platform linux/amd64 .`

- аутентифицироваться в Container Registry
`yc iam create-token` -> в ответе IAM-токен

- `docker login --username iam --password <IAM-токен> cr.yandex`

- загрузить докер-образ в Container registry:
`docker tag garbage-docker cr.yandex/crpdvrl3lmu654l64uq9/garbage:v<x>`,
`docker push cr.yandex/crpdvrl3lmu654l64uq9/garbage:v<x>`, где вместо <x> подставить номер версии.
Здесь `crpdvrl3lmu654l64uq9` - ID нашего реестра, `garbage:v<x>` - произвольной название + тег, может быть любым
