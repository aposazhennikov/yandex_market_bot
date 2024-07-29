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

# ВАЖНО!
Замените domain в файле nginx/nginx.conf на свой домен! Также нужжен будет аккаунт OpenAI и созданные в нем API ключи! 
Также нужен будет аккаунт Telegram из под которого будут отправляться сообщения боту для загрузки Excel-файла с инфомрацией о товарах!
И нужно будет получить API_ID API_HASH для телеграмм аккаунта!

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
0. Создайте Docker network типа bridge 
    ```bash
    docker network create --driver bridge yandex_market_bot
    ```
1. Запустите контейнер:
    ```bash
    docker run -d \
      --name yandex_market_bot \
      --restart=always \
      --network yandex_market_bot \
      -v /app/yandex_market/app:/app \
      -e API_ID="your_api_id" \
      -e API_HASH="your_api_hash" \
      -e PHONE_NUMBER="+71234567890" \
      -e BOT_USERNAME="pavilion89bot" \
      -e OPENAI_API_KEY="sk-None-" \
      -e OPENAI_PROXY_URL="http://login:password@your.vpn-or-proxy.com:3128" \
      -e ASSISTANT_ID="123" \
      -e DELAY_TIME=60 \
      -e IMAGE_COUNT=15 \
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

    location /static {
        auth_basic "Restricted Access";
        auth_basic_user_file /etc/nginx/.htpasswd;
        proxy_pass http://yandex_market_bot:5000/static;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        auth_basic "Restricted Access";
        auth_basic_user_file /etc/nginx/.htpasswd;
        proxy_pass http://yandex_market_bot:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
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
### Работа с GPT:

Запросы к GPT нужны для создания description - описания, определения категории товара, а также производителя. 

Поэтому важно создать ассистента, это можно сделать онлайн через platform.openai.com

В репозитории также есть PROMPT для асистента GPT который я использовал на этом проекте.

Также здесь есть отдельный файл message.py он нужен для тестов работы ChatGPT. В него важно подставить API_KEY и ASSISTANT_ID актуальные вашим данным. 
В случае если вы протестили новую функцию с GPT и решили ее оставить, для изменения ее в основном скрипте нужно будет отредактировать файл xml_converter.py
Найти в нем класс XMLGenerator и изменить статический метод get_product_details_from_gpt.

При создании Асистента рекомендую использовать chatgpt-3.5-turbo ее мощности достаточно для наших задач, но он дешевле.

### Дополнительная информация:

- В коде используется функция os.getenv('name_of_variable') - она забирает чувствительные данные из переменных окружения, это сделанно для больше безопасности, 
чтобы тестировать код на локальном окружении нужно сначала установить все переменные(их можно посмотреть при запуске docker контейнера yandex_market_bot)
- У поиска картинки есть методы валидации, которые проверяют изображение на то проходит ли оно правило Яндекс Маркета.
- У поиска картинки и запроса к GPT есть N число попыток. Если все они прошли с ошибкой скрипт переходит к заполнению следующей карточки товара.
- Добавил в репозиторий products.xml В качестве референса, как он должен выглядеть.
- Каждые DELAY_TIME секунд скрипт повторяет свою логику:
         1) Отправить сообщение в телеграмм "Получить Excel-файл" боту pavilion89bot,
         2) Скачать products.xlsx
         3) Если такой файл уже был -> Переимменовать его в products._old.xlsx
         4) Сравнить изменения в новом и старом .xlsx файле и если они есть(Изменилась цена или описание, удалилася или добавилась строка в файле)
         5) Записать эти изменения в products.xml
         6) Если же products.xml нет создать его с нуля

В зависимости от кол-ва ядер сервера на котором запускается код будет та или иная скорость выполнения скрипта, при использовании 3х ядерного сервера скрипт отработал с нуля(то есть полность создал файл products.xml) за 200секунд для 700 товаров.

# Обновлено:

Добавлен WEB UI он написан на Framework'e Flask и запускается вместе с остальным скриптом в main.py он прослушивает на 0.0.0.0 и порту 5000, поэтому для того чтобы подключиться к нему мы и создаем docker network которую привязываем и к контейнеру с NGINX и к контейнеру с Python. Чтобы проверить доступность WEB UI можно сделать curl изнутри контейнера с nginx:

```bash
docker exec -it nginx_yandex_market bash
curl yandex_market_bot:5000 
```
Так как контейнеры объеденены одной сетью, имя контейнера является DNS и резолвится в IP.
nginx обрабатывает / и перенаправляет в flask запросы.


#  TODO:
- Подумать как решить проблему с цветами товаров, иногда когда в наименовании товара есть цвет изображение к нему через BING ищется разных цветов...
- Подумать о реализации заполнения всех параметров с помощью GPT.

 
