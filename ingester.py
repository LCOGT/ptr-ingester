import os
import settings
from utils.s3 import get_client, filename_to_s3_key
from utils.logging import getLogger

logger = getLogger()


class Ingester(object):
    def __init__(self, path):
        self.path = path

    def ingest(self):
        logger.info('ingesting {0}'.format(self.path))
        filename = os.path.basename(self.path)
        with open(self.path, 'rb') as f:
            data = f.read()
        key, version = self.upload_to_s3(filename, data)

        logger.info('finished ingesting {0} version {1}'.format(key, version))

    def upload_to_s3(self, filename, data):
        key = filename_to_s3_key(filename)
        content_disposition = 'attachment; filename={}'.format(filename)
        content_type = 'image/fits'
        client = get_client(
            settings.AWS_ACCESS_KEY_ID,
            settings.AWS_SECRET_ACCESS_KEY,
            settings.REGION_NAME
        )
        response = client.put_object(
            Body=data,
            Key=key,
            Bucket=settings.BUCKET,
            ContentDisposition=content_disposition,
            ContentType=content_type
        )
        return key, response['VersionId']
