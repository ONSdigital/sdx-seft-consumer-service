FROM onsdigital/flask-crypto-queue

RUN mkdir -p /app/logs

COPY app /app
COPY ftp /ftp
COPY startup.sh /startup.sh
COPY requirements.txt /requirements.txt
COPY Makefile /Makefile
COPY sdx_test_keys /sdx_test_keys
COPY ras_test_keys /ras_test_keys

RUN make build

ENTRYPOINT ./startup.sh
