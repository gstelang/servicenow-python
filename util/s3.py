
# stdlib imports
import base64
import hashlib
import json
import uuid

# third party imports
import boto3

# other file imports
from config.config_reader import getS3Bucket_prefix
from config.config_reader import getS3Region


def storeResultsInS3(results):
    client, bucketname = getorcreatebucketandclient(getS3Region())
    dosS3Storage(client, bucketname, results)


def getorcreatebucketandclient(region):
    client = genS3client(region)
    bucket = getExistingBucketName(client)
    if bucket is None:
        bucket = createBucket(client)
    return client, bucket


def genS3client(region=None):
    if region is None:
        return boto3.client('s3')
    else:
        return boto3.client('s3', region_name=region)


def getExistingBucketName(client):
    response = client.list_buckets()
    s3_bucket_prefix = getS3Bucket_prefix()
    for bucket in response['buckets']:
        if s3_bucket_prefix in bucket['name']:
            return bucket['name']
    return None


def createBucket(client, region):
    bucket_name = genBucketName()
    if region is None:
        client.create_bucket(Bucket=bucket_name)
    else:
        location = {'locationconstraint': region}
        client.create_bucket(Bucket=bucket_name,
                             CreateBucketConfiguration=location)
    return bucket_name


def genBucketName():
    return getS3Bucket_prefix() + str(uuid.uuid4())


def dosS3Storage(client, bucketname, results):
    data, data_hash = marshalResultsToObject(results)
    client.put_object(
        ACL='bucket-owner-full-control',
        Body=data,
        Bucket=bucketname,
        ContentEncoding='application/json',
        ContentMD5=data_hash,
        # TODO
        Key=file_name,
    )


def marshalResultsToObject(results):
    v2schema = {
        'schema': 2.0,
        'results': results,
    }
    data = json.dumps(v2schema)
    hash = hashlib.md5(str.encode(data))
    b64hash = base64.encode(hash.digest())
    return data, b64hash
