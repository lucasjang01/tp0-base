import logging
import os
import sys
import yaml

from common.client import Client


def init_config():
    with open('/config.yaml', 'r') as f:
        yaml_config = yaml.safe_load(f)

    return {
        'id': os.environ['CLI_ID'],
        'server_address': os.environ.get('CLI_SERVER_ADDRESS', 'server:12345'),
        'log_level': os.environ.get('CLI_LOG_LEVEL', 'INFO'),
        'batch_max_amount': yaml_config['batch']['maxAmount'],
    }


def init_logger(log_level):
    logging.basicConfig(
        format='%(asctime)s %(levelname)-5s     %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=getattr(logging, log_level.upper(), logging.INFO),
        stream=sys.stdout,
    )


def main():
    config = init_config()
    init_logger(config['log_level'])
    logging.info(f"action: config | result: success | client_id: {config['id']} | server_address: {config['server_address']} | log_level: {config['log_level']}")

    client = Client(config)
    client.start_client_loop()


if __name__ == '__main__':
    main()
