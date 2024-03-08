#!/usr/bin/env python

# stdlib imports
import json
import os
import time

# third party imports
import requests

# file imports
from util.common import storeResultsInS3
from util.common import validateIP

# TODO: this is cli parameters
input_type = 'nfs' # or api
scan_type = 'agent-pull' # or nfs-read
storage_type = 's3' # or nfs-write'

# TODO: move this to yaml
max_agent_pull_retries = 10

# nfs config
nfs_read_dir = '/nfs/agent-output'
nfs_write_dir = '/nfs/ip-scanner-results'

# s3 config
s3_region = 'eu-west-1'
s3_bucket_prefix = 'ip-scanner-results'

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
        response = requests.get('https://api/iplist?page=%d' % page_counter)
        if response.status_code != 200:
            raise Exception('non-200 status code: %d' % response.status_code)
        data = json.loads(response.text)
        ip_list.extend(data['iplist'])
    for ip in ip_list:
        validateIP(ip)
if ip_list is None:
    raise Exception('unrecognized input_type "%s"' % input_type)

results = None
if scan_type == 'agent-pull':
    results = dict()
    for ip in ip_list:
        response = requests.get('https://%s/portdiscovery' % ip)
        if response.status_code != 200:
            raise Exception('non-200 status code: %d' % response.status_code)
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
            raise Exception('non-200 status code: %d' % response.status_code)
        results[ip] = data['status']
elif scan_type == 'nfs-read':
    results = dict()
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

if storage_type == 's3':
    storeResultsInS3(results, s3_region)
elif storage_type == 'nfs-write':
    file_name = time.strftime('%y-%m-%d-%h:%m:%s', time.localtime())
    file_full_path = '/'.join([nfs_write_dir, file_name]) + '.json'
    v2schema = {
        'schema': 2.0,
        'results': results,
    }
    data = json.dumps(v2schema)
    with open(file_full_path, 'w') as fd:
        fd.write(data)
else:
    raise Exception('unrecognized storage_type %s' % storage_type)

