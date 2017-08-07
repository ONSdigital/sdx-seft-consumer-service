import argparse

from sdc.crypto.utils.generate_secrets import add_private_key_to_dict, add_public_key_to_dict, generate_secrets_file

KEY_PURPOSE_RAS_SUBMISSION = 'ras-submission'


def generate_secrets_for_sdx(keys_folder):

    keys = {}

    add_private_key_to_dict(keys, KEY_PURPOSE_RAS_SUBMISSION, 'sdc-seft-encrytpion-sdx-private-key.pem', keys_folder)
    add_public_key_to_dict(keys, KEY_PURPOSE_RAS_SUBMISSION, 'sdc-seft-signing-ras-public-key.pem', keys_folder)

    secrets = {}

    generate_secrets_file(keys, secrets)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate Survey Data Exchange secrets file.')
    parser.add_argument('folder', type=str, help='The folder that contains the secrets and keys')

    args = parser.parse_args()

    keys_folder = args.folder
    generate_secrets_for_sdx(keys_folder)
