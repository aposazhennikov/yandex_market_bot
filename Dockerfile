# Используем официальный образ Ubuntu
FROM ubuntu:22.04

# Обновляем систему и устанавливаем зависимости, включая curl и screen
RUN apt update && apt upgrade -y && \
    apt install -y tzdata && \
    ln -fs /usr/share/zoneinfo/Europe/Moscow /etc/localtime && \
    dpkg-reconfigure --frontend noninteractive tzdata && \
    apt install -y software-properties-common curl screen locales && \
    locale-gen en_US.UTF-8 && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt update && apt install -y python3.12 python3.12-venv python3.12-dev && \
    python3.12 --version && \
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12 && \
    /usr/local/bin/pip3 install --upgrade pip

ENV PATH="/opt/venv/bin:$PATH"
# Устанавливаем локали
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем все файлы проекта в рабочую директорию
COPY ./requirements.txt /app

# Создаем и активируем виртуальное окружение
RUN python3.12 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r requirements.txt

# Устанавливаем переменные окружения
ENV API_ID=your_api_id
ENV API_HASH=your_api_hash
ENV PHONE_NUMBER=your_phone_number
ENV BOT_USERNAME=pavilion89bot
ENV CHAT_GPT_API_KEY=your_chat_gpt_api_key
ENV ASSISTANT_ID=your_assistant_id
ENV DELAY_TIME=60
ENV IMAGE_COUNT=15
ENV OPENAI_PROXY_URL=proxy_url
COPY start.sh .

# Делаем скрипт исполняемым
RUN chmod +x start.sh

# Запускаем скрипт через start.sh
CMD ["./start.sh"]
