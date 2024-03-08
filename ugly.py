#!/usr/bin/env python

# stdlib imports
import json
import os
import time
import sys

# third party imports
import requests

# file imports
from util.common import storeResultsInS3
from util.common import validateIP
from config.config_reader import *


def getIPList(input_type):
    ip_list = None
    if input_type == 'nfs':
        with open('path-to-ip-lists.txt') as fd:
            path_to_ip_lists = fd.read()
        ip_list = []
        for dir_name, subdir_list, file_list in os.walk(path_to_ip_lists):
            for file in file_list:
                with open(file) as fd:
                    data = json.load(fd)
                ip_list.extend(data['iplist'])
                for ip in ip_list:
                    validateIP(ip)
    elif input_type == 'api':
        response = requests.get('https://api/iplist')
        if response.status_code != 200:
            raise Exception('non-200 status code: %d' % response.status_code)
        data = json.loads(response.text)
        ip_list = data['iplist']
        page_counter = 0
        while data['more'] is True:
            page_counter += 1
            response = requests.get(
                'https://api/iplist?page=%d' % page_counter)
            if response.status_code != 200:
                raise Exception('non-200 status code: %d' %
                                response.status_code)
            data = json.loads(response.text)
            ip_list.extend(data['iplist'])
        for ip in ip_list:
            validateIP(ip)
    if ip_list is None:
        raise Exception('unrecognized input_type "%s"' % input_type)

    return ip_list


def getResults(scan_type, ip_list):
    results = None
    if scan_type == 'agent-pull':
        results = dict()
        max_agent_pull_retries = 10

        for ip in ip_list:
            response = requests.get('https://%s/portdiscovery' % ip)
            if response.status_code != 200:
                raise Exception('non-200 status code: %d' %
                                response.status_code)
            data = json.loads(response.text)
            agent_url = '%s/api/2.0/status' % data['agenturl']
            response = requests.get(agent_url)
            retries = 0
            while response.status_code == 503:
                if retries > max_agent_pull_retries:
                    raise Exception('max retries exceeded for ip %s' % ip)
                retries += 1
                time_to_wait = float(response.headers['retry-after'])
                time.sleep(time_to_wait)
                response = requests.get(agent_url)
            if response.status_code != 200:
                raise Exception('non-200 status code: %d' %
                                response.status_code)
            results[ip] = data['status']
    elif scan_type == 'nfs-read':
        results = dict()
        nfs_read_dir = getNfsReadDir()
        for ip in ip_list:
            agent_nfs_path = '%s/%s' % (nfs_read_dir, ip)
            for dir_name, subdir_list, file_list in os.walk(agent_nfs_path):
                for file in file_list:
                    with open(file) as fd:
                        data = json.load(fd)
                    if 'schema' not in data or float(data['schema']) < 2.0:
                        result = data
                    else:
                        result = data['status']
                    results[ip] = result
    else:
        raise Exception('unrecognized scan_type %s' % scan_type)

    return results


def storeResults(storage_type, results):
    if storage_type == 's3':
        storeResultsInS3(results, getS3Region())
    elif storage_type == 'nfs-write':
        file_name = time.strftime('%y-%m-%d-%h:%m:%s', time.localtime())
        file_full_path = '/'.join([getNfsWriteDir(), file_name]) + '.json'
        v2schema = {
            'schema': 2.0,
            'results': results,
        }
        data = json.dumps(v2schema)
        with open(file_full_path, 'w') as fd:
            fd.write(data)
    else:
        raise Exception('unrecognized storage_type %s' % storage_type)


def main(input_type, scan_type, storage_type):
    print("Getting ip list from " + input_type + " with scan_type as " +
          scan_type + " and storing on " + storage_type)
    ip_list = getIPList(input_type)
    results = getResults(scan_type, ip_list)
    storeResults(storage_type, results)


if __name__ == "__main__":
    from argparse import ArgumentParser

    # TODO: check match, add exception and exit if it does not
    parser = ArgumentParser(
        description="Command line utility to do magic with ips")

    parser.add_argument("--input", required=True,
                        help="nfs or api", dest="input_type")
    parser.add_argument("--scan", required=True,
                        help="agent-pull or nfs-read", dest="scan_type")
    parser.add_argument("--storage", required=True,
                        help="s3 or nfs-write", dest="storage_type")

    args = parser.parse_args()
    main(args.input_type, args.scan_type, args.storage_type)
