# sdx-seft-consumer-service

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/e761d8b0e15b42a092388e490682ae08)](https://www.codacy.com/app/ons-sdc/sdx-seft-consumer-service?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=ONSdigital/sdx-seft-consumer-service&amp;utm_campaign=Badge_Grade)

Microservice for consuming SEFT files from RAS via a Rabbit MQ and sending onto the internal ONS network. These files will
be scanned by the anti-virus server.

# Generate the public/private key pair
```shell
$ openssl genrsa -aes256 -out sdc-seft-encryption-sdx-private-key.pem 4096
$ openssl rsa -pubout -in sdc-seft-encryption-sdx-private-key.pem -out sdc-seft-encryption-sdx-public-key.pem

$ openssl genrsa -aes256 -out sdc-seft-signing-ras-private-key.pem 4096
$ openssl rsa -pubout -in sdc-seft-signing-ras-private-key.pem -out sdc-seft-signing-ras-public-key.pem
```

Once these keys have been generated you'll need to use the sdc-cryptography library to convert them to the required yml
format (https://github.com/ONSdigital/sdc-cryptography)

## Installation
This application presently installs required packages from requirements files:
- `requirements.txt`: packages for the application, with hashes for all packages: see https://pypi.org/project/hashin/
- `test-requirements.txt`: packages for testing and linting

It's also best to use `pyenv` and `pyenv-virtualenv`, to build in a virtual environment with the currently recommended version of Python.  To install these, see:
- https://github.com/pyenv/pyenv
- https://github.com/pyenv/pyenv-virtualenv
- (Note that the homebrew version of `pyenv` is easiest to install, but can lag behind the latest release of Python.)

### Getting started
Once your virtual environment is set, install the requirements:
```shell
$ make build
```

To test, first run `make build` as above, then run:
```shell
$ make test
```

It's also possible to install within a container using docker. From the sdx-seft-consumer directory:
```shell
$ docker build -t sdx-seft-consumer .
```

## Usage

Start sdx-seft-consumer service using the following command:
```shell
$ make start
````

To run the End to End test you must have a running Rabbit MQ server. You must also have a valid OPSWAT API
key configured as an environment variable (see below). Once  these are in place the end to end test will run automatically.

## Configuration

The main configuration options are listed below:

| Environment Variable                  | Default                           | Description
|---------------------------------------|-----------------------------------|--------------
| SEFT_RABBITMQ_HOST                    | `localhost`                       | Host for rabbit mq 1
| SEFT_RABBITMQ_HOST2                   | `localhost`                       | Host for rabbit mq 2
| SEFT_RABBITMQ_PORT                    | '5672'                            | Port for rabbit mq 1
| SEFT_RABBITMQ_PORT2                   | '5672'                            | Port for rabbit mq 2
| SEFT_FTP_HOST                         | `localhost`                       | FTP host
| SEFT_FTP_PORT                         | `2021`                            | FTP port
| SEFT_FTP_USER                         | `ons`                             | FTP username
| SEFT_FTP_PASS                         | `ons`                             | FTP password
| SEFT_CONSUMER_FTP_FOLDER              | `.`                               | FTP Folder
| SDX_SEFT_CONSUMER_KEYS_FILE           | ``                                | RAS/SDX encryption and signing keys
| LOGGING_LEVEL                         | `DEBUG`                           | Logging sensitivity
| ANTI_VIRUS_ENABLED                    | `True`                            | Enable or disable A/V scan
| ANTI_VIRUS_BASE_URL                   | `https://scan.metadefender.com/v2`| The address of the A/V servers
| ANTI_VIRUS_API_KEY                    | ``                                | The API key for A/V servers
| ANTI_VIRUS_CA_CERT                    | ``                                | The path to ONS CA file used to verify internal https certificates

### License

Copyright ©‎ 2016, Office for National Statistics (https://www.ons.gov.uk)

Released under MIT license, see [LICENSE](LICENSE) for details.
