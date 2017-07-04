# sdx-seft-consumer-service

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/e761d8b0e15b42a092388e490682ae08)](https://www.codacy.com/app/ons-sdc/sdx-seft-consumer-service?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=ONSdigital/sdx-seft-consumer-service&amp;utm_campaign=Badge_Grade)

Microservice for consuming SEFT files from RAS via a Rabbit MQ and sending onto the internal ONS network

# Generate the public/private key pair

openssl genrsa -aes256 -out sdc-seft-encryption-sdx-private-key.pem 4096
openssl rsa -pubout -in sdc-seft-encryption-sdx-private-key.pem -out sdc-seft-encryption-sdx-public-key.pem

openssl genrsa -aes256 -out sdc-seft-signing-ras-private-key.pem 4096
openssl rsa -pubout -in sdc-seft-signing-ras-private-key.pem -out sdc-seft-signing-ras-public-key.pem

### License

Copyright ©‎ 2016, Office for National Statistics (https://www.ons.gov.uk)

Released under MIT license, see [LICENSE](LICENSE) for details.
