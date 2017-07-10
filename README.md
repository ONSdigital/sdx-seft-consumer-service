# sdx-seft-consumer-service

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/e761d8b0e15b42a092388e490682ae08)](https://www.codacy.com/app/ons-sdc/sdx-seft-consumer-service?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=ONSdigital/sdx-seft-consumer-service&amp;utm_campaign=Badge_Grade)

Microservice for consuming SEFT files from RAS via a Rabbit MQ and sending onto the internal ONS network

# Generate the public/private key pair

openssl genrsa -aes256 -out sdc-seft-encryption-sdx-private-key.pem 4096
openssl rsa -pubout -in sdc-seft-encryption-sdx-private-key.pem -out sdc-seft-encryption-sdx-public-key.pem

openssl genrsa -aes256 -out sdc-seft-signing-ras-private-key.pem 4096
openssl rsa -pubout -in sdc-seft-signing-ras-private-key.pem -out sdc-seft-signing-ras-public-key.pem


## Installation

To install, use:

```bash
make build
```

To install using local sdx-common repo (requires SDX_HOME environment variable), use:

```bash
make dev
```

To run the test suite, use:

```bash
make test
```

## Configuration

The main configuration options are listed below:

| Environment Variable            | Default                        | Description
|---------------------------------|--------------------------------|--------------
| RABBITMQ_HOST                   | `localhost`                    | Host for rabbit mq 1
| RABBITMQ_HOST2                  | `localhost`                    | Host for rabbit mq 2
| RABBITMQ_PORT                   | '5672'                         | Port for rabbit mq 1
| RABBITMQ_PORT2                  | '5672'                         | Port for rabbit mq 2
| RABBIT_QUEUE                    | `Seft.Responses`               | Incoming queue to read from
| RABBIT_EXCHANGE                 | `message`                      | RabbitMQ exchange to use
| RABBIT_QUARANTINE_QUEUE         | `"Seft.Responses.Quarantine"`  | Rabbit quarantine queue
| FTP_HOST                        | `localhost`                    | FTP host
| FTP_PORT                        | `2021`                         | FTP port
| FTP_USER                        | `ons`                          | FTP username
| FTP_PASS                        | `ons`                          | FTP password
| FTP_FOLDER                      | `.`                            | FTP Folder
| RAS_SEFT_PUBLIC_KEY             | ``                             | RAS Public key for checking signing
| SDX_SEFT_PRIVATE_KEY            | ``                             | SDX Private key for decrypting
| SDX_SEFT_PRIVATE_KEY_PASSWORD   | ``                             | Password to the SDX private key
| LOGGING_LEVEL                   | `DEBUG`                        | Logging sensitivity


### License

Copyright ©‎ 2016, Office for National Statistics (https://www.ons.gov.uk)

Released under MIT license, see [LICENSE](LICENSE) for details.
