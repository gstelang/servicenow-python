import yaml

with open('./config/config.yaml', 'r') as file:
    config = yaml.safe_load(file)


def getNfsReadDir():
    return config['nfs']['read_dir']


def getNfsWriteDir():
    return config['nfs']['write_dir']


def getS3Region():
    return config['s3']['region']


def getS3Bucket_prefix():
    return config['s3']['bucket_prefix']
