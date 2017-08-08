import os

from app import settings

# ras keys
RAS_SEFT_CONSUMER_PRIVATE_KEY = settings.get_key(os.getenv('TEST_RAS_SEFT_PUBLIC_KEY', "./test_keys/sdc-seft-signing-ras-private-key.pem"))

# sdx keys
SDX_SEFT_CONSUMER_PUBLIC_KEY = settings.get_key(os.getenv('PRIVATE_KEY', "./test_keys/sdc-seft-encryption-sdx-public-key.pem"))
