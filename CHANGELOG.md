### Unreleased
 - Downgrade structlogger to fix issue with tornado

### 1.0.1
  - Remove JSON logging
  - Remove unnecessary code
  - Set a listen port from the env var "SEFT_SDX_CONSUMER_SERVICE_PORT", or default to 8080
  - Add basic auth to RM SDX gateway calls

### 1.0.0
  - Initial release
  - Namespace config
  - FTP port must be an int
  - Updated to use SDC crypto library
  - Ensure integrity and version of library dependencies
  - Namespace config
  - Add healthcheck endpoint

