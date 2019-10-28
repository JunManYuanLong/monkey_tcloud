import json
import logging
import os
import traceback

from .adb import AdbTool
from .config import DefaultConfig
from .utils import Utils

logger = logging.getLogger(__name__)

"""
#  LogCat 
"""


class LogCat(object):

    def __init__(self, device_id, pid):
        super(LogCat, self).__init__()
        self.daemon = True
        self.device_id = device_id
        self.adb_tool = AdbTool(self.device_id)
        self.log_path = '{}/{}'.format(DefaultConfig.LOCAL_LOGCAT_PATH, pid)
        self.bug_report_path = '{}/bug_report'.format(self.log_path)

    # 清除logcat，开启重定向
    def set_logcat(self, target):
        try:
            self.adb_tool.clear_logcat()
            p = self.adb_tool.start_logcat(target)
            return p
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())

    def get_logcat_log(self, log):
        try:
            logger.info('({}) 开始获取 logcat 日志'.format(self.device_id))
            local_log_path = '{}'.format(self.log_path)
            monkey_log_path = '{}/monkey'.format(local_log_path)

            # p = self.adb_tool.start_logcat()
            # log = []
            # step = 1
            # for line in p.stdout.readlines():
            #     log.append(line)
            #     if step == 10000:
            #         break
            #     step += 1

            if not os.path.exists(DefaultConfig.LOCAL_LOGCAT_PATH):
                os.mkdir(DefaultConfig.LOCAL_LOGCAT_PATH)

            if not os.path.exists(self.log_path):
                os.mkdir(self.log_path)

            if not os.path.exists(local_log_path):
                os.mkdir(local_log_path)

            if not os.path.exists(monkey_log_path):
                os.mkdir(monkey_log_path)

            with open('{}/monkey_result_log.log'.format(local_log_path), 'w') as f:
                f.write(str(log))

            # 获取 crash dump log
            self.adb_tool.pull_file('/sdcard/MonkeyLog/oom-traces.log', '{}/'.format(local_log_path))
            self.adb_tool.pull_file('/sdcard/MonkeyLog/', '{}/'.format(monkey_log_path))

            self.get_crash_dump_log()

            logger.info('({}) 成功获取日志'.format(self.device_id))

            log_paths = ['{}/{}'.format(local_log_path, log_name) for log_name in os.listdir(local_log_path)]

            return log_paths

        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())

    def get_crash_dump_log(self):
        logger.info('({}) 开始获取 crash-dump log 日志'.format(self.device_id))
        self.adb_tool.pull_file('/sdcard/MonkeyLog/crash-dump.log', '{}/'.format(self.log_path))

    def analysis_crash_anr_log(self, target, anr_count=-1, crash_count=-1):
        try:
            logger.info('({}) 开始分析 crash dump log {}'.format(self.device_id, target))
            log_name = target
            crash_anr_logs = {}
            i = 0
            anr_i = 0
            crash_i = 0
            if os.path.exists(log_name) and os.path.isfile(log_name):
                with open(log_name, 'r') as f:
                    crash_flag = False
                    oom_flag = False
                    for line in f.readlines():
                        if 'crashend' in line:
                            if crash_flag:
                                i += 1
                            crash_flag = False
                        elif 'crash:' in line:
                            crash_i += 1
                            if crash_i > crash_count:
                                crash_anr_logs[i] = {
                                    'error_type': 'CRASH',
                                    'error_count': 1,
                                    'error_message': []
                                }
                                crash_flag = True
                        if crash_flag:
                            crash_anr_logs[i]['error_message'].append(line)

                        if 'oomend' in line:
                            if oom_flag:
                                i += 1
                            oom_flag = False
                        elif 'oom:' in line:
                            anr_i += 1
                            if anr_i > anr_count:
                                crash_anr_logs[i] = {
                                    'error_type': 'OOM',
                                    'error_count': 1,
                                    'error_message': []
                                }
                                oom_flag = True
                        if oom_flag:
                            crash_anr_logs[i]['error_message'].append(line)

            logger.info('({}) debug log crash here : {}'.format(self.device_id, crash_anr_logs))
            return crash_anr_logs
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())

    def get_oom_trace_logs(self, target):
        try:
            # TODO: 需要分析详情？？？
            logger.info('({}) 开始分析 out of memory log {}'.format(self.device_id, target))
            log_name = target
            crash_anr_logs = {}
            i = 0
            if os.path.exists(log_name) and os.path.isfile(log_name):
                with open(log_name, 'r') as f:
                    crash_flag = False
                    for line in f.readlines():
                        if 'crashend' in line:
                            crash_flag = False
                            i += 1
                        elif 'crash:' in line:
                            crash_anr_logs[i] = {
                                'error_type': 'CRASH',
                                'error_count': 1,
                                'error_message': []
                            }
                            crash_flag = True
                        if crash_flag:
                            crash_anr_logs[i]['error_message'].append(line)
            return crash_anr_logs
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())

    def get_anr_crash_count(self):
        try:
            anr_count = 0
            crash_count = 0
            logs = self.adb_tool.get_crash_dump_log()
            for log in logs:
                if 'ANR' in log:
                    anr_count += 1
                if 'CRASH' in log:
                    crash_count += 1
            return anr_count, crash_count
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())

    def get_activity_test_info(self, show_in_cmd=False):
        try:
            activity_path = '{}/monkey/MonkeyLog/{}'.format(self.log_path, DefaultConfig.ACTIVITY_PATH)
            infos = {
                'TotalActivity': [],
                'TestedActivity': [],
                'Coverage': 0,
                'Sampling': []
            }
            if os.path.exists(activity_path):
                with open(activity_path, 'r') as f:
                    infos = json.load(f)
            else:
                logger.warning('{} not found in local!'.format(activity_path))

            if show_in_cmd:
                keys = infos.keys()
                values = {
                    'TotalActivity': infos.get('TotalActivity', []),
                    'TestedActivity': infos.get('TestedActivity', []),
                    'Coverage': infos.get('Coverage'),
                    'Sampling': infos.get('Sampling')
                }
                Utils.show_info_as_table(keys, values)
            return infos
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())
            return {'error': e}

    def reset_bug_report_log(self):
        self.adb_tool.reset_bug_report_log()

    def get_bug_report_log(self):
        return self.adb_tool.get_bug_report_log(self.bug_report_path)

    def generate_bug_report(self):
        try:
            out = Utils.bug_report_tool(self.bug_report_path)
            print(out)
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())

    def upload_bug_report_log(self):
        if self.log_path.startswith("./"):
            log_path = self.log_path[2:]
            Utils.upload_bug_report_log_to_oss(log_path)
