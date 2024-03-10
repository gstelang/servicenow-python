import json
import os
import time

from config.config_reader import getNfsWriteDir
from config.config_reader import getNfsReadDir


def getIPListFromNfs():
    ip_list = []
    with open('path-to-ip-lists.txt') as fd:
        path_to_ip_lists = fd.read()

    for dir_name, subdir_list, file_list in os.walk(path_to_ip_lists):
        for file in file_list:
            with open(file) as fd:
                data = json.load(fd)
            ip_list.extend(data['iplist'])

    return ip_list


def getResultsFromNfs(ip_list):
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

    return results


def storeResultsInNfs(results):
    file_name = time.strftime('%y-%m-%d-%h:%m:%s', time.localtime())
    file_full_path = '/'.join([getNfsWriteDir(), file_name]) + '.json'
    v2schema = {
        'schema': 2.0,
        'results': results,
    }
    data = json.dumps(v2schema)
    with open(file_full_path, 'w') as fd:
        fd.write(data)
