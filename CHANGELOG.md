### Unreleased

### 1.4.0 2018-02-05
 - Added support for different survey_ids

### 1.3.0 2018-01-04
 - Improve test output and implemented Pytest
 - Add case_id to log

### 1.2.0 2017-11-21
 - Remove sdx-common logging
 - Add Cloudfoundry deployment files

### 1.1.0 2017-11-01
 - Update logging to be more explicit and informative
 - Removed unchanging configurable variables.

### 1.0.2
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

