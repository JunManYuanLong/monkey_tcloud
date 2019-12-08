#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import logging
import traceback
from datetime import datetime

import requests

from .config import DefaultConfig

logger = logging.getLogger(__name__)


class TCloud(object):

    def __init__(self, task_id, device_id, monkey_id, tcloud_url, process=0):
        self.task_id = task_id
        self.monkey_id = monkey_id
        self.device_id = device_id
        self.tcloud_url = tcloud_url if tcloud_url is not None else DefaultConfig.TCLOUD_URL
        self.anr = 0
        self.crash = 0
        self.process = process

    # monkey update
    def on_get_app_version(self, version):
        if version is not None:
            self.update_monkey(app_version=version)

    def on_download_app(self, status):
        if status:
            download_app_status = 1
            self.update_monkey(download_app_status=download_app_status)
        else:
            download_app_status = 2
            end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.update_monkey(download_app_status=download_app_status)

    def on_monkey_end(self, ):
        end_time = datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
        self.update_monkey(process=100, end_time=end_time)

    def on_monkey_begin(self, jenkins_url):
        self.update_monkey(jenkins_url=jenkins_url)

    # task update
    def on_task_begin(self):
        process = 0
        begin_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.update_task(process=process, begin_time=begin_time)

    def on_task_end(self, process=None, activity_count=None, activity_tested_count=None, activity_all=None,
                    activity_tested=None, anr_count=None, crash_count=None, crash_rate=None, exception_count=None,
                    exception_run_time=None, run_time=None):
        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.update_task(process=process, end_time=end_time, activity_count=activity_count, anr_count=anr_count,
                         activity_tested_count=activity_tested_count, activity_all=activity_all,
                         crash_count=crash_count,
                         activity_tested=activity_tested, crash_rate=crash_rate, exception_count=exception_count,
                         exception_run_time=exception_run_time, run_time=run_time)

    def on_running_status(self, status, error_msg):
        self.update_task(running_error_reason=error_msg, running_status=status)

    def on_device_connect(self, status):
        if status:
            device_connect_status = 1
            self.update_task(device_connect_status=device_connect_status)
        else:
            device_connect_status = 2
            end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.update_task(process=100, activity_count=0, activity_tested_count=0, activity_all='',
                             activity_tested='', anr_count=0, crash_count=0, crash_rate=0, exception_count=0,
                             exception_run_time=0, setup_install_app_status=0,
                             setup_uninstall_app_status=0, start_app_status=0, login_app_status=0,
                             teardown_uninstall_app_status=0, end_time=end_time, run_time=0,
                             device_connect_status=device_connect_status, screen_lock_status=0)

    def on_screen_lock(self, status):
        if status:
            screen_lock_status = 1
            self.update_task(screen_lock_status=screen_lock_status)
        else:
            screen_lock_status = 2
            end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.update_task(process=100, activity_count=0, activity_tested_count=0, activity_all='',
                             activity_tested='', anr_count=0, crash_count=0, crash_rate=0, exception_count=0,
                             exception_run_time=0, setup_install_app_status=0,
                             setup_uninstall_app_status=0, start_app_status=0, login_app_status=0,
                             teardown_uninstall_app_status=0, end_time=end_time, run_time=0,
                             screen_lock_status=screen_lock_status)

    def on_setup_uninstall_app(self, status):
        if status:
            setup_uninstall_app_status = 1
            self.update_task(setup_uninstall_app_status=setup_uninstall_app_status)
        else:
            setup_uninstall_app_status = 2
            self.update_task(process=100, activity_count=0, activity_tested_count=0, activity_all='',
                             activity_tested='', anr_count=0, crash_count=0, crash_rate=0, exception_count=0,
                             exception_run_time=0, setup_uninstall_app_status=setup_uninstall_app_status,
                             start_app_status=0, login_app_status=0, teardown_uninstall_app_status=0, run_time=0)

    def on_setup_install_app(self, status):
        if status:
            setup_install_app_status = 1
            self.update_task(setup_install_app_status=setup_install_app_status)
        else:
            setup_install_app_status = 2
            end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.update_task(process=100, activity_count=0, activity_tested_count=0, activity_all='',
                             activity_tested='', anr_count=0, crash_count=0, crash_rate=0, exception_count=0,
                             exception_run_time=0, setup_install_app_status=setup_install_app_status,
                             start_app_status=0, login_app_status=0, teardown_uninstall_app_status=0,
                             end_time=end_time, run_time=0)

    def on_start_app(self, status):
        if status:
            start_app_status = 1
            self.update_task(start_app_status=start_app_status)
        else:
            start_app_status = 2
            end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.update_task(process=100, activity_count=0, activity_tested_count=0, activity_all='',
                             activity_tested='', anr_count=0, crash_count=0, crash_rate=0, exception_count=0,
                             exception_run_time=0, start_app_status=start_app_status, login_app_status=0,
                             teardown_uninstall_app_status=0, end_time=end_time, run_time=0)

    def on_login_app(self, status):
        if status:
            login_app_status = 1
            self.update_task(login_app_status=login_app_status)
        else:
            login_app_status = 2
            end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.update_task(process=100, activity_count=0, activity_tested_count=0, activity_all='',
                             activity_tested='', anr_count=0, crash_count=0, crash_rate=0, exception_count=0,
                             exception_run_time=0, login_app_status=login_app_status, teardown_uninstall_app_status=0,
                             end_time=end_time, run_time=0)

    def on_teardown_uninstall_app(self, status):
        if status:
            teardown_uninstall_app_status = 1
            self.update_task(teardown_uninstall_app_status=teardown_uninstall_app_status)
        else:
            teardown_uninstall_app_status = 2
            end_time = datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
            self.update_task(process=100, activity_count=0, activity_tested_count=0, activity_all='',
                             activity_tested='', anr_count=0, crash_count=0, crash_rate=0, exception_count=0,
                             exception_run_time=0, teardown_uninstall_app_status=teardown_uninstall_app_status,
                             run_time=0)

    # on user cancel
    def on_user_cancel_task(self):
        self.update_task(current_stage=1000)

    # on user cancel success
    def on_user_cancel_stask_success(self):
        self.update_task(current_stage=1001)

    # on device_not connect on running
    def on_device_disconnect_on_running(self):
        self.update_task(current_stage=1002)

    # 当 anr crash process 发生改变时 上传
    def on_anr_crash_changed(self, process, anr, crash):
        if self.anr != anr or self.crash != crash or self.process != process:
            self.anr = anr
            self.crash = crash
            self.process = process
            self.update_task(process=process, anr_count=anr, crash_count=crash)

    # upload errorlog
    def on_errorlog_upload(self, logs):
        for key in logs.keys():
            log = logs.get(key)
            self.upload_log(int(self.monkey_id), int(self.task_id), log.get('error_type'),
                            json.dumps(log.get('error_message')), log.get('error_count'))

    # upload report
    def on_report_upload(self, report_url, report_type):
        self.upload_report(int(self.monkey_id), int(self.task_id), report_url, report_type)

    def update_monkey(self, end_time=None, process=None, jenkins_url=None, status=None, app_version=None,
                      begin_time=None, report_url=None, run_time=None, actual_run_time=None, download_app_status=None):
        try:
            logger.info('({}) update monkey'.format(self.device_id))
            request_data_template = {
                "begin_time": begin_time,
                "process": process,
                "jenkins_url": jenkins_url,
                "status": status,
                "app_version": app_version,
                "report_url": report_url,
                "end_time": end_time,
                "run_time": run_time,
                "actual_run_time": actual_run_time,
                "download_app_status": download_app_status
            }
            request_data = {}

            for key in request_data_template.keys():
                value = request_data_template.get(key)
                if value is not None:
                    request_data[key] = value

            logger.info(request_data)

            request_url = '{}/v1/monkey/{}'.format(self.tcloud_url, self.monkey_id)

            response = requests.request(method='POST', url=request_url, json=request_data)

            if response.ok:
                logger.info(response.text)
                logger.info('({}) update monkey <{}> success'.format(self.device_id, self.monkey_id))
                return True
            return False
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())
            return False

    def update_task(self, process=None, begin_time=None, activity_count=None, activity_tested_count=None,
                    activity_all=None, activity_tested=None, anr_count=None, crash_count=None, crash_rate=None,
                    exception_count=None, exception_run_time=None,
                    setup_install_app_status=None, setup_uninstall_app_status=None, start_app_status=None,
                    login_app_status=None, teardown_uninstall_app_status=None, end_time=None, run_time=None,
                    device_connect_status=None, screen_lock_status=None, running_status=None,
                    running_error_reason=None, current_stage=None):
        try:
            logger.info('({}) update task'.format(self.device_id))
            request_data_template = {
                "begin_time": begin_time,
                "process": process,
                "activity_count": activity_count,
                "activity_tested_count": activity_tested_count,
                "activity_all": activity_all,
                "activity_tested": activity_tested,
                "anr_count": anr_count,
                "crash_count": crash_count,
                "crash_rate": crash_rate,
                "exception_count": exception_count,
                "exception_run_time": exception_run_time,
                "device_connect_status": device_connect_status,
                "screen_lock_status": screen_lock_status,
                "setup_install_app_status": setup_install_app_status,
                "setup_uninstall_app_status": setup_uninstall_app_status,
                "start_app_status": start_app_status,
                "login_app_status": login_app_status,
                "teardown_uninstall_app_status": teardown_uninstall_app_status,
                "end_time": end_time,
                "run_time": run_time,
                "running_status": running_status,
                "running_error_reason": running_error_reason,
                "current_stage": current_stage,
            }
            request_data = {}

            for key in request_data_template.keys():
                value = request_data_template.get(key)
                if value is not None:
                    request_data[key] = value

            logger.info(request_data)

            request_url = '{}/v1/monkey/devicestatus/{}'.format(self.tcloud_url, self.task_id)

            response = requests.request(method='POST', url=request_url, json=request_data)

            if response.ok:
                logger.info(response.text)
                logger.info('({}) update task <{}> success'.format(self.device_id, self.task_id))
                return True
            return False

        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())
            return False

    def upload_log(self, monkey_id=None, task_id=None, error_type=None, error_message=None, error_count=None):
        try:
            logger.info('({}) upload log'.format(self.device_id))
            request_data_template = {
                'monkey_id': monkey_id,
                'task_id': task_id,
                'error_type': error_type,
                'error_message': error_message,
                'error_count': error_count
            }
            request_data = {}

            for key in request_data_template.keys():
                value = request_data_template.get(key)
                if value is not None:
                    request_data[key] = value

            logger.info(request_data)

            request_url = '{}/v1/monkey/errorlog'.format(self.tcloud_url)

            response = requests.request(method='POST', url=request_url, json=request_data)

            if response.ok:
                logger.info(response.text)
                logger.info('({}) upload log success'.format(self.device_id))
                return True
            return False

        except Exception as e:
            logger.error(e)
            traceback.print_exc()
            return False

    def upload_report(self, monkey_id=None, task_id=None, report_url=None, report_type=None):
        try:
            logger.info('({}) upload report'.format(self.device_id))
            request_data_template = {
                'monkey_id': monkey_id,
                'task_id': task_id,
                'report_url': report_url,
                'report_type': report_type
            }
            request_data = {}

            for key in request_data_template.keys():
                value = request_data_template.get(key)
                if value is not None:
                    request_data[key] = value

            logger.info(request_data)

            request_url = '{}/v1/monkey/report'.format(self.tcloud_url)

            response = requests.request(method='POST', url=request_url, json=request_data)

            if response.ok:
                logger.info(response.text)
                logger.info('({}) upload report success'.format(self.device_id))
                return True
            return False

        except Exception as e:
            logger.error(e)
            traceback.print_exc()
            return False

    def get_monkey_cancel_status(self, task_id):
        try:
            logger.info('({}) get monkey cancel status {}'.format(self.device_id, task_id))

            request_url = '{}/v1/monkey/cancel?task_id={}'.format(self.tcloud_url, task_id)

            response = requests.request(method='GET', url=request_url)
            if response.ok:
                logger.info(response.json())
                return response.json().get('data').get('cancel_status')
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())

    def using_monkey_device(self, serial):
        try:
            logger.info('using monkey device now!')
            request_data = {
                'serial': serial
            }
            request_url = '{}/v1/monkey/device/using'.format(self.tcloud_url)

            response = requests.request(method='POST', url=request_url, json=request_data)
            if response.ok:
                logger.info(response.json())
                return True

        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())

    def release_monkey_device(self, serial):
        try:
            logger.info('release monkey device now!')
            request_data = {
                'serial': serial
            }
            request_url = '{}/v1/monkey/device/release'.format(self.tcloud_url)

            response = requests.request(method='POST', url=request_url, json=request_data)
            if response.ok:
                logger.info(response.json())
                return True

        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())

    def upload_realtime_log(self, performance_test_id, cpu, rss, heap_size, heap_alloc):
        try:
            logger.info('upload realtime log now!')
            request_data = {
                'cpu': str(cpu),
                'rss': str(rss),
                'heap_size': str(heap_size),
                'heap_alloc': str(heap_alloc),
            }
            request_url = '{}/v1/performance/realtime/{}'.format(self.tcloud_url, performance_test_id)

            response = requests.request(method='POST', url=request_url, json=request_data)
            if response.ok:
                logger.info(response.json())
                return response.json()
        except Exception as e:
            logger.error(e)

    def create_performance_test(self, run_type, run_time):
        try:
            logger.info('create_performance_test now!')
            request_data = {
                'performance_id': int(self.task_id),
                'run_type': run_type,
                'run_time': run_time
            }
            request_url = '{}/v1/performance/test'.format(self.tcloud_url)

            response = requests.request(method='POST', url=request_url, json=request_data)
            if response.ok:
                logger.info(response.json())
                return response.json().get('data')[0].get('id')
        except Exception as e:
            logger.error(e)
            return 0

    def calculate_performance_test(self, performance_test_id):
        try:
            logger.info('calculate performance test average and top now now!')
            request_url = '{}/v1/performance/test/calculate/{}'.format(self.tcloud_url, performance_test_id)
            response = requests.request(method='GET', url=request_url)
            if response.ok:
                logger.info(response.json())
                return response.json()
        except Exception as e:
            logger.error(e)
            return 0
