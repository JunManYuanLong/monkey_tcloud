import logging
import os
import traceback
from multiprocessing import Queue, Lock

import prettytable

from automonkey.config import DefaultConfig
from .case import Case
from .exception import CaseTypeErrorException, FileDownloadErrorException
from .monkey_runner import MonkeyRunner
from .tcloud_update import TCloud
from .utils import Utils

logger = logging.getLogger(__name__)

"""
#  Runer
#  运行 Case
"""


class Runner(object):

    def __init__(self):
        self.queue = None
        self.lock = None
        self.tcloud = None
        pass

    def show_system_information(self):
        pass

    def run(self, case):
        try:
            if not isinstance(case, Case):
                logger.error('Need Case Here, not {}'.format(type(case)))
                raise CaseTypeErrorException

            self.show_system_information()

            # 测试开始时间
            case.result.on_case_begin()

            self.setup(case)

            if case.case_type == 1:
                self.run_monkeys(case.cases)
            elif case.case_type == 2:
                self.run_performance(case.cases)


        except Exception as e:
            logger.error(e)
            traceback.print_exc()

    def run_monkeys(self, monkeys):
        try:
            if not isinstance(monkeys, list):
                logger.error('Need list Here, not {}'.format(type(monkeys)))
                raise TypeError

            self.tcloud.on_monkey_begin(os.environ.get('BUILD_URL'))

            process_list = []
            for monkey in monkeys:
                process = MonkeyRunner(self.queue, self.lock, monkey)
                process_list.append(process)

            for process in process_list:
                process.start()

            table_process = prettytable.PrettyTable()
            table_process.field_names = ["process id", "device id"]
            for process in process_list:
                row = [process.pid, process.monkey.device.device_id]
                table_process.add_row(row)
            logger.info('\n{}'.format(table_process))

            results = []
            while True:
                if len(results) == len(process_list):
                    break
                if not self.queue.empty():
                    results.append(self.queue.get())

            for result in results:
                print(result.info)

        except FileDownloadErrorException as f_e:
            logger.error(f_e)
            logger.error(traceback.format_exc())
            self.tcloud.on_download_app(False)
        except Exception as e:
            logger.error(e)
            traceback.print_exc()
        finally:
            self.tcloud.on_monkey_end()

    def run_performance(self, performances):
        try:
            if not isinstance(performances, list):
                logger.error('Need list Here, not {}'.format(type(performances)))
                raise TypeError

            self.tcloud.on_monkey_begin(os.environ.get('BUILD_URL'))

            process_list = []
            for performance in performances:
                process = PerformanceRunner(self.queue, self.lock, performance)
                process_list.append(process)

            for process in process_list:
                process.start()

            table_process = prettytable.PrettyTable()
            table_process.field_names = ["process id", "device id"]
            for process in process_list:
                row = [process.pid, process.performance.device.device_id]
                table_process.add_row(row)
            logger.info('\n{}'.format(table_process))

            results = []
            while True:
                if len(results) == len(process_list):
                    break
                if not self.queue.empty():
                    results.append(self.queue.get())

            for result in results:
                print(result.info)

        except FileDownloadErrorException as f_e:
            logger.error(f_e)
            logger.error(traceback.format_exc())
            self.tcloud.on_download_app(False)
        except Exception as e:
            logger.error(e)
            traceback.print_exc()
        finally:
            self.tcloud.on_monkey_end()

    # 初始化
    def setup(self, case):
        try:
            if not isinstance(case, Case):
                logger.error('Need Case Here, not {}'.format(type(case)))
                raise CaseTypeErrorException

            self.tcloud = TCloud(0, 0, monkey_id=case.monkey_id, tcloud_url=case.tcloud_url)

            # 下载文件
            download_package = Utils.download_apk_from_url(case.app_download_url, DefaultConfig.LOCAL_APP_PATH, None)

            self.tcloud.on_download_app(True)
            case.bind_local_package_to_monkey(download_package)

            # 初始化 queue 用于多进程通信
            self.queue = Queue(-1)
            # 初始化 lock 用于 多进程
            self.lock = Lock()

            return download_package

        except Exception as e:
            logger.error(e)
            traceback.print_exc()
            raise e
