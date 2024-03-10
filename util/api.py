import json
import time

# third party imports
import requests


def getIPListFromAPI():
    ip_list = []

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
        ip_list.extends(data['iplist'])

    return ip_list


def getResultsFromAPI(ip_list):
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

    return results    
