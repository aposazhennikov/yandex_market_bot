# Yandex Market Bot

Этот проект представляет собой Telegram-бота, который автоматически загружает файл Excel, сравнивает его с предыдущей версией, обновляет XML файл и логирует все изменения. Проект упакован в Docker-контейнер для удобства развертывания и использования.

## Структура проекта

- **main.py**: Основной скрипт, который запускает Telegram-бота, скачивает файл Excel и запускает процесс сравнения и обновления.
- **excel_main.py**: Скрипт, который сравнивает новый и старый файлы Excel, генерирует сводку изменений и обновляет XML файл.
- **xml_converter.py**: Скрипт, который генерирует XML файл из данных Excel и выполняет поиск изображений для продуктов.
- **start.sh**: Скрипт для запуска проекта в screen сессии, чтобы он продолжал работать в фоне.
- **Dockerfile**: Dockerfile для создания контейнера, в котором будет выполняться проект.
- **nginx.conf**: Конфигурационный файл для Nginx, который используется для ограничения доступа к XML файлу через HTTP Basic аутентификацию.

## Установка и запуск

### Требования

- Docker
- Git
- Proxy Server в Германии или любой другой стране из которой доступен ChatGPT(Если скрипт будет запускаться на сервере расположенном в России)
### Установка Docker и Docker Compose

Для установки Docker и Docker Compose следуйте официальной [инструкции Docker](https://docs.docker.com/get-docker/) и [инструкции Docker Compose](https://docs.docker.com/compose/install/).

### Сборка контейнера

1. Клонируйте репозиторий:
    ```bash
    git clone https://github.com/aposazhennikov/yandex_market_bot.git
    ```
2. Создайте папку для этого проекта:
    ```bash
    mkdir /app
    ```
3. Переместите папку проекта в созданную папку app:
    ```bash
    mv yandex_market_bot /app
    ```
4. Зайдите в целевую папку с Dockerfile:
    ```bash
    cd /app/yandex_market_bot
    ```
5. Постройте Docker-образ:
    ```bash
    docker build -t yandex_market_bot .
    ```

### Запуск контейнера

1. Запустите контейнер:
    ```bash
    docker run -d \
      --name yandex_market_bot \
      --restart=always \
      -v /app/yandex_market/app:/app \
      -e API_ID="your_api_id" \
      -e API_HASH="your_api_hash" \
      -e PHONE_NUMBER="+71234567890" \
      -e BOT_USERNAME="pavilion89bot" \
      -e OPENAI_API_KEY="sk-None-" \
      -e OPENAI_PROXY_URL="http://login:password@your.vpn-or-proxy.com:3128" \
      -e ASSISTANT_ID="123" \
      -e DELAY_TIME=60 \
      -e IMAGE_COUNT=3 \
      yandex_market_bot 
    ```

2. Чтобы убедиться, что контейнер запущен:
    ```bash
    docker ps -a
    ```

### Переменные окружения

Для работы проекта необходимо настроить следующие переменные окружения:

- `API_ID`: ID вашего Telegram API.
- `API_HASH`: Hash вашего Telegram API.
- `PHONE_NUMBER`: Номер телефона вашего Telegram аккаунта. С которого будут идти запросы к боту pavilion89bot для скачивания EXCEL Файла
- `BOT_USERNAME`: Имя пользователя вашего бота.
- `OPENAI_API_KEY`: API ключ OpenAI.
- `ASSISTANT_ID`: ID вашего ассистента OpenAI.
- `DELAY_TIME`: Время задержки между запросами в секундах к боту pavilion89bot(по умолчанию 60 секунд).
- `IMAGE_COUNT`: Количество изображений для поиска (по умолчанию 15). То сколько фоток в карточку товара мы добавим.
- `OPENAI_PROXY_URL`: URL прокси для OpenAI (если требуется).

### Просмотр логов

1. Для просмотра логов внутри контейнера:
    ```bash
    docker logs yandex_market_bot
    ```

2. Для просмотра логов в реальном времени:
    ```bash
    docker logs -f yandex_market_bot
    ```

### Остановка и удаление контейнера

1. Чтобы остановить контейнер:
    ```bash
    docker stop yandex_market_bot
    ```

2. Чтобы удалить контейнер:
    ```bash
    docker rm -f yandex_market_bot
    ```

### Nginx конфигурация

Для ограничения доступа к XML файлу через HTTP Basic аутентификацию используется Nginx. Конфигурация описана в файле `nginx.conf`:

```nginx
server {
    listen 80;
    server_name CHANGE_TO_YOUR_DOMAIN;

    location /products.xml {
        auth_basic "Restricted Access";
        auth_basic_user_file /etc/nginx/.htpasswd;
        root /usr/share/nginx/html;
    }

    location / {
        return 403;
    }
}
```

### Запуск Nginx контейнера

1. Создайте файл `.htpasswd` для аутентификации:
    ```bash
    sudo apt-get install apache2-utils
    htpasswd -c /app/yandex_market/nginx/.htpasswd YOUR_USERNAME_TO_HTTP_ACCES_TO_THE_FILE_PRODUCTS_FROM_WEB
    ```

2. Запустите контейнер Nginx:
    ```bash
    docker run -d -p 80:80 \
      -v /app/yandex_market/nging/nginx.conf:/etc/nginx/conf.d/default.conf \
      -v /app/yandex_market/nginx/.htpasswd:/etc/nginx/.htpasswd \
      -v /app/yandex_market/app/:/usr/share/nginx/html/ \
      --restart always \
      --name nginx_yandex_market nginx:latest
    ```

### Прокси для OpenAI

Так как OpenAI не работает в России, вам нужно использовать прокси для доступа к API. Установите переменную `OPENAI_PROXY_URL` при запуске docker контейнера 'yandex_market_bot' с URL вашего прокси.

### Получение API_ID и API_HASH в Telegram

1. Перейдите на сайт [my.telegram.org](https://my.telegram.org).
2. Войдите в свою учетную запись Telegram.
3. Перейдите в раздел "API development tools".
4. Создайте новое приложение и получите `API_ID` и `API_HASH`.
5. После запуска контейнера вам скорее всего придется ввести при первом запуске свой номер телефона и проверочный код.
6. А далее в проекте создается файл session, в котором записаны данные о текущей сессии, из-за этого файла при будущих запусках подтверждение не потребуется.

### Описание переменных окружения

- `DELAY_TIME`: Время задержки между запросами к боту в секундах. Используется для контроля частоты запросов.
- `IMAGE_COUNT`: Количество изображений для поиска в Bing для каждого продукта. Количество картинок которые мы добавим в карточку товара.

### Проверка работоспособности

После запуска контейнера убедитесь, что он работает правильно. Проверьте логи на наличие ошибок и убедитесь, что бот выполняет свои задачи.

### Отладка и мониторинг

Для выполнения команд внутри контейнера используйте `docker exec`:
```bash
docker exec -it yandex_market_bot /bin/bash
```

### Обновление контейнера

Если вы внесли изменения в код или зависимости, выполните следующие шаги для обновления контейнера:

1. Пересоберите образ:
    ```bash
    docker build -t yandex_market_bot .
    ```

2. Остановите и удалите старый контейнер:
    ```bash
    docker rm -f yandex_market_bot_container
    ```

3. Запустите новый контейнер:
    ```bash
    docker run -d \
      --name yandex_market_bot \
      --restart=always \
      -v /app/yandex_market/app:/app \
      -e API_ID="your_api_id" \
      -e API_HASH="your_api_hash" \
      -e PHONE_NUMBER="+71234567890" \
      -e BOT_USERNAME="pavilion89bot" \
      -e OPENAI_API_KEY="sk-None-" \
      -e OPENAI_PROXY_URL="http://login:password@vpn.aposazhennikov.ru:3128" \
      -e ASSISTANT_ID="123" \
      -e DELAY_TIME=60 \
      -e IMAGE_COUNT=3 \
      yandex_market_bot 
    ```
