#!/usr/bin/env python

# file imports
from util.common import validateIP
from util.s3 import storeResultsInS3
from util.nfs import *
from util.api import *


def getIPList(input_type):
    ip_list = None
    if input_type == 'nfs':
        ip_list = getIPListFromNfs()
    elif input_type == 'api':
        ip_list = getIPListFromAPI()

    if ip_list is None:
        raise Exception('unrecognized input_type "%s"' % input_type)
    else:
        for ip in ip_list:
            validateIP(ip)

    return ip_list


def getResults(scan_type, ip_list):
    results = None
    if scan_type == 'agent-pull':
        results = getResultsFromAPI(ip_list)
    elif scan_type == 'nfs-read':
        results = getResultsFromNfs(ip_list)
    else:
        raise Exception('unrecognized scan_type %s' % scan_type)

    return results


def storeResults(storage_type, results):
    if storage_type == 's3':
        storeResultsInS3(results)
    elif storage_type == 'nfs-write':
        storeResultsInNfs(results)
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
