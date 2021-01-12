FROM emptypage/open_jtalk:20.4_1.11
ENV DEBIAN_FRONTEND=noninteractive
RUN set -x && \
    apt-get -y update && \
    apt-get -y install libopus-dev python3 python3-pip tzdata portaudio19-dev && \
    apt-get -y clean && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /root
RUN set -x && \
    pip3 install -r /root/requirements.txt && \
    pip3 install ptvsd
COPY discordjtalkbot /root/discordjtalkbot
RUN set -x && \
    mv /root/discordjtalkbot/cogs/modules/files/discordjtalkbot-config.sample.json \
    /root/discordjtalkbot/cogs/modules/files/discordjtalkbot-config.json && \
    sed -i -e "s/\/opt/\/lib/g" \
    /root/discordjtalkbot/cogs/modules/files/discordjtalkbot-config.json && \
    sed -i -e "s/open-jtalk/open_jtalk/g" \
    /root/discordjtalkbot/cogs/modules/files/discordjtalkbot-config.json && \
    cat  /root/discordjtalkbot/cogs/modules/files/discordjtalkbot-config.json && \
    ls -l /root/discordjtalkbot
ENV IS_DOCKER=true\
    TOKEN="__test___"\
    VOICE_HELLO=""\
    TEXT_START=""\
    TEXT_END=""\
    OPEN_JTALK_FLAGS=""
WORKDIR /root/discordjtalkbot
# ENTRYPOINT ["python3", "discordjtalkbot.py"]
CMD ["python3", "discordjtalkbot.py"]