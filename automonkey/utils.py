import logging
import os
import subprocess
import sys
import traceback
from datetime import datetime

import oss2
import prettytable
import requests

from automonkey.config import DefaultConfig
from automonkey.exception import FileDownloadErrorException

logger = logging.getLogger(__name__)

"""
#  工具类
"""


class Utils(object):

    @classmethod
    def command_execute(cls, cmd):
        try:
            if not cmd:
                return False
            logger.info(cmd)
            command_process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                               executable="/bin/bash")
            return command_process
        except Exception as e:
            logger.error(e)
            traceback.print_exc()

    @classmethod
    def bug_report_tool(cls, log_path):
        try:
            if not os.path.exists(log_path):
                return None
            local_path = os.getcwd()
            chk_path = os.path.abspath(os.path.join(local_path, "./tools/check_bug_report/chkbugreport"))
            jar_path = os.path.abspath(os.path.join(local_path, "./tools/check_bug_report"))

            if not os.path.exists(chk_path):
                logger.error('tool path not found at {}'.format(chk_path))
                return None

            os.system('chmod +x {}'.format(chk_path))

            cmd = '{} {} {}'.format(chk_path, log_path, jar_path)
            p = cls.command_execute(cmd)
            return p.stdout.readlines()
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())

    @classmethod
    def show_info_as_table(cls, keys, values):
        # keys list; values list(dict) or dict
        table = prettytable.PrettyTable()
        if isinstance(values, list):
            table.field_names = keys
            for v in values:
                if isinstance(v, list):
                    row = v
                elif isinstance(v, dict):
                    row = v.values()
                table.add_row(row)
        elif isinstance(values, dict):
            table.field_names = ['key', 'value']
            for v in keys:
                row = [v, values.get(v)]
                table.add_row(row)
        logger.info('\n{}'.format(table))

    # 下载 apk 文件
    @classmethod
    def download_apk_from_url(cls, url, target_path, target_name):
        try:
            if not os.path.exists(target_path):
                os.mkdir(target_path)
            if target_name is None:
                date_time_now = datetime.now().strftime('%Y%m%d-%H.%M.%S')
                target_name = '{}.apk'.format(date_time_now)
            elif not target_name.endswith('.apk'):
                target_name = '{}.apk'.format(target_name)

            download_apk_name = os.path.join(target_path, target_name)

            logger.info('开始从 {} 下载到 {}'.format(url, download_apk_name))

            response = requests.get(url=url, verify=False)

            with open(download_apk_name, 'wb') as f:
                f.write(response.content)

            # 下载失败
            if not os.path.exists(download_apk_name):
                logger.error('{} 下载失败!'.format(url))
                raise FileDownloadErrorException

            logger.info('下载成功,保存地址 {}'.format(download_apk_name))

            return download_apk_name
        except Exception as e:
            print(e)
            traceback.print_exc()
            raise e

    @classmethod
    def upload_bug_report_log_to_oss(cls, log_path):
        endpoint = DefaultConfig.OSS_URL
        auth = DefaultConfig.OSS_AUTH
        bucket = oss2.Bucket(auth, endpoint, DefaultConfig.OSS_BUCKET_NAME)
        cls.upload_dir(log_path, bucket)

    @classmethod
    def upload_file_to_oss(cls, local_path, bucket):
        if not bucket:
            endpoint = DefaultConfig.OSS_URL
            auth = DefaultConfig.OSS_AUTH
            bucket = oss2.Bucket(auth, endpoint, DefaultConfig.OSS_BUCKET_NAME)

        now = datetime.now().strftime("%Y-%m-%d")
        build_number = os.environ.get('BUILD_NUMBER')
        remote_file_path = 'monkey/{}/{}/{}'.format(now, build_number, local_path)
        bucket.put_object_from_file('{}'.format(remote_file_path), local_path)

    @classmethod
    def upload_dir(cls, dir_path, bucket):
        if not bucket:
            endpoint = DefaultConfig.OSS_URL
            auth = DefaultConfig.OSS_AUTH
            bucket = oss2.Bucket(auth, endpoint, DefaultConfig.OSS_BUCKET_NAME)

        fs = os.listdir(dir_path)
        dir_path_new = dir_path
        for f in fs:
            file = dir_path_new + "/" + f
            if os.path.isdir(file):
                cls.upload_dir(file, bucket)
            else:
                if 'DS_Store' not in file:
                    print(file)
                    cls.upload_file_to_oss(file, bucket)

    @classmethod
    def deal_with_python_version(cls, data):
        if str(sys.version_info.major) == '3':
            if isinstance(data, list):
                return [d.decode('utf-8') for d in data]
            else:
                return data.decode('utf-8')
        else:
            return data
