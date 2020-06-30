import os
import time
import logging

import requests
import yaml

from ifcb.data.transfer.remote import RemoteIfcb
from ifcb.data.transfer.deposit import fileset_destination_dir

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def load_config(config_file):
    logging.info(f'loading configuration from {config_file}...')

    with open(config_file) as fin:
        config = yaml.load(fin)

    return config

def sync_ifcb(name, dashboard_url, ifcb_config):
    address = ifcb_config['address']
    netbios_name = ifcb_config.get('netbios_name',None)
    username = ifcb_config.get('username','ifcb')
    password = ifcb_config.get('password','ifcb')
    share = ifcb_config.get('share','Data')
    directory = ifcb_config.get('directory','')
    destination_directory = ifcb_config.get('destination')
    dataset = ifcb_config['dataset']
    day_dirs = ifcb_config.get('day_dirs',False)

    def destination(lid):
        if day_dirs:
            dest = os.path.join(destination_directory, fileset_destination_dir(lid))
        else:
            dest = destination_directory

        logging.info(f'copying files for {lid} into {dest}...')

        return dest

    def hit_sync_endpoint(lid):
        url = f'{dashboard_url}/api/sync_bin?dataset={dataset}&bin={lid}'
        try:
            logging.info(f'hitting {url} ...')
            requests.get(url)
        except:
            logging.error(f'unable to reach {url}, {lid} not synced!')

    ifcb = RemoteIfcb(address, username, password, netbios_name=netbios_name, share=share, directory=directory)

    logging.info(f'connecting to {name} ...')

    with ifcb:
        ifcb.sync(destination, fileset_callback=hit_sync_endpoint)

def sync_ifcbs(config):
    dashboard_url = config['dashboard']['url']
    logging.info(f'dashboard URL = {dashboard_url}')

    for name, ifcb_config in config['ifcbs'].items():
        print(f'transferring from {name}...')
        sync_ifcb(name, dashboard_url, ifcb_config)

def main(config_file='transfer_config.yml'):
    config = load_config(config_file)

    while True:
        sync_ifcbs(config)
        time.sleep(5000)

if __name__ == '__main__':
    main() 