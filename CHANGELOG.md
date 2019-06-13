### Unreleased
 - Remove python 3.4 and 3.5 from travis builds
 - Add python 3.7 to travis builds
 - Update packages such as sdc-rabbit, pika and tornado to allow upgrade to python 3.7

### 2.3.3 2019-04-02
 - Update pyyaml and fix reprocessing script

### 2.3.2 2019-03-14
 - Revert heartbeat changes introduced in 2.3.1 while keeping package upgrades

### 2.3.1 2019-02-28
 - Add heartbeat to improve connection reliability

### 2.3.0 2019-02-19
 - Remove receipting from service as RAS handles its own receipting when receiving the spreadsheet.

### 2.2.1 2019-01-22
 - Update version of sdc-cryptography to 0.3.0
 - Update version of requests to 2.21.0 to fix security issue

### 2.2.0 2018-12-20
 - Add case_id and survey_id to logger fields to aid in debugging
 - Update dependencies to fix security vulnerability

### 2.1.0 2018-07-31
 - Adding scripts for managing response on quarantine queue
 - Remove unchecked folder and fixed log statements for AV scan

### 2.0.0 2018-06-14
 - OPSWAT anti-virus integration
 - Fix health check
 - Import publishers from sdc.rabbit module, not sdc.rabbit.publisher

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
