import os
from unittest.mock import patch
import unittest

from ocs_ingester.s3 import S3Service
from ocs_ingester.utils.fits import File

FITS_PATH = os.path.join(
    os.path.dirname(__file__),
    'test_files/fits/'
)
OTHER_PATH = os.path.join(
    os.path.dirname(__file__),
    'test_files/other/'
)
FITS_FILE = os.path.join(
    FITS_PATH,
    'coj1m011-kb05-20150219-0125-e90.fits.fz'
)
PDF_FILE = os.path.join(
    OTHER_PATH,
    'cptnrs03-fa13-20150219-0001-e92-summary.pdf'
)


def mocked_s3_object(*args, **kwargs):
    class MockS3Object:
        class Object:
            def __init__(self, *args, **kwargs):
                pass

            def put(self, *args, **kwargs):
                return {'ETag': '"fakemd5"', 'VersionId': 'fakeversion'}

            def get(self, *args, **kwargs):
                return {'Body': open(FITS_FILE, 'rb'), 'ContentDisposition': 'attachment: filename=thing.fits.fz'}

    return MockS3Object()


class TestS3(unittest.TestCase):
    def setUp(self):
        self.s3 = S3Service('')

    def test_basename_to_hash(self):
        fits_dict = {'SITEID': 'coj', 'INSTRUME': 'kb05', 'DATE-OBS': '2015-02-19T13:56:05.261', 'OBSTYPE': 'EXPOSE'}
        with open(FITS_FILE, 'rb') as fileobj:
            self.assertEqual(
                'coj/kb05/20150219/raw/coj1m011-kb05-20150219-0125-e90.fits.fz',
                self.s3.file_to_s3_key(File(fileobj), fits_dict)
            )

    def test_bpm_obstype_basename_to_hash(self):
        fits_dict = {'SITEID': 'coj', 'INSTRUME': 'kb05', 'DATE-OBS': '2015-02-19T13:56:05.261', 'OBSTYPE': 'BPM'}
        with open(FITS_FILE, 'rb') as fileobj:
            self.assertEqual(
                'coj/kb05/bpm/coj1m011-kb05-20150219-0125-e90.fits.fz',
                self.s3.file_to_s3_key(File(fileobj), fits_dict)
            )

    def test_pdf_obstype_basename_to_hash(self):
        fits_dict = {'SITEID': 'cpt', 'INSTRUME': 'nres03',
                     'DATE-OBS': '2015-02-19T13:56:05.261', 'OBSTYPE': 'EXPOSE', 'RLEVEL': 92}
        with open(PDF_FILE, 'rb') as fileobj:
            self.assertEqual(
                'cpt/nres03/20150219/processed/cptnrs03-fa13-20150219-0001-e92-summary.pdf',
                self.s3.file_to_s3_key(File(fileobj, file_metadata=fits_dict), fits_dict)
            )

    def test_bpm_filename_basename_to_hash(self):
        fits_dict = {'SITEID': 'coj', 'INSTRUME': 'kb05', 'DATE-OBS': '2015-02-19T13:56:05.261', 'OBSTYPE': 'EXPOSE'}
        with open(FITS_FILE, 'rb') as fileobj:
            self.assertEqual(
                'coj/kb05/bpm/coj1m011-kb05-20150219-0125-bpm.fits.fz',
                self.s3.file_to_s3_key(File(fileobj, path='coj1m011-kb05-20150219-0125-bpm.fits.fz'), fits_dict)
            )

    def test_pdf_filename_basename_to_hash(self):
        fits_dict = {'SITEID': 'cpt', 'INSTRUME': 'nres03',
                     'DATE-OBS': '2015-02-19T13:56:05.261', 'OBSTYPE': 'EXPOSE', 'RLEVEL': 92}
        with open(PDF_FILE, 'rb') as fileobj:
            self.assertEqual(
                'cpt/nres03/20150219/processed/cptnrs03-fa13-20150219-0001-e92-summary.pdf',
                self.s3.file_to_s3_key(File(fileobj,
                                            path='cptnrs03-fa13-20150219-0001-e92-summary.pdf',
                                            file_metadata=fits_dict), fits_dict)
            )

    def test_processed_basename_to_hash(self):
        fits_dict = {'SITEID': 'coj', 'INSTRUME': 'kb05', 'DATE-OBS': '2015-02-19T13:56:05.261', 'OBSTYPE': 'EXPOSE', 'RLEVEL': 91}
        with open(FITS_FILE, 'rb') as fileobj:
            self.assertEqual(
                'coj/kb05/20150219/processed/coj1m011-kb05-20150219-0125-e90.fits.fz',
                self.s3.file_to_s3_key(File(fileobj), fits_dict)
            )

    def test_extension_to_content_type(self):
        self.assertEqual('image/fits', self.s3.extension_to_content_type('.fits'))
        self.assertEqual('application/x-tar', self.s3.extension_to_content_type('.tar.gz'))
        self.assertEqual('', self.s3.extension_to_content_type('.png'))

    def test_strip_quotes_from_etag(self):
        self.assertEqual('fakemd5', self.s3.strip_quotes_from_etag('"fakemd5"'))
        self.assertIsNone(self.s3.strip_quotes_from_etag('"wrong'))

    @patch('boto3.resource', side_effect=mocked_s3_object)
    def test_upload_file(self, s3_mock):
        fits_dict = {'SITEID': 'tst', 'INSTRUME': 'inst01', 'DATE-OBS': '2019-10-11T00:11:22.123'}
        with open(FITS_FILE, 'rb') as fileobj:
            self.s3.upload_file(File(fileobj), fits_dict)
        self.assertTrue(s3_mock.called)

    @patch('boto3.resource', side_effect=mocked_s3_object)
    def test_get_file(self, s3_mock):
        fileobj = self.s3.get_file('s3://somebucket/thing')
        self.assertTrue(s3_mock.called)
        self.assertEqual(fileobj.name, 'thing.fits.fz')
