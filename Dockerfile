FROM ubuntu AS sdnops-base

COPY docker-compose /usr/bin/
RUN apt update && \
    apt install -y python3 python3-pip cmake vim iproute2 && \
    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install pynng fastapi[all] python-jose[cryptography] passlib[bcrypt] requests &&\
    apt autoremove -y && apt clean && \
    echo "set expandtab\nset softtabstop=2\nset encoding=utf-8\n" > /root/.vimrc

FROM sdnops-base AS sdnops
WORKDIR /root
COPY . ./

ENTRYPOINT ["/root/entrypoint.sh"]
CMD ["respondent"]
