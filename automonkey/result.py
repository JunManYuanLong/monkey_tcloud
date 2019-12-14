#!/usr/bin/python
# -*- coding: utf-8 -*-

import traceback
from datetime import datetime

from .config import MonkeyConfig

"""
#  运行的 Case 的 结果
#  每个 Case 有多个 MonkeyCase
#  MonkeyCase 的结果
#  每个对应 一个 device
"""


class CaseResult(object):

    def __init__(self):
        self.begin_time = ''
        self.end_time = ''
        self.result = ''
        self.reason = ''
        self.crash = {}
        self.anr = {}

    @property
    def info(self):
        return {
            'begin_time': self.begin_time,
            'end_time': self.end_time,
            'result': self.result,
            'reason': self.reason,
            'crash': self.crash,
            'anr': self.anr
        }

    def on_case_begin(self):
        self.begin_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def on_case_end(self):
        self.end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

"""
#  monkey 运行结果
"""


class MonkeyCaseResult(object):

    def __init__(self):
        self.begin_time = ''
        self.end_time = ''
        self.result = ''
        self.reason = ''
        self.device_connect_result = ''
        self.setup_install_result = ''
        self.setup_uninstall_result = ''
        self.screen_lock_result = ''
        self.start_app_status = ''
        self.login_app_status = ''
        self.teardown_uninstall_result = ''
        self.crash = {}
        self.anr = {}
        self.check_screen_locked = ''
        self.log_path = ''
        self.activity_info = {}
        self.app_version = ''

    @property
    def info(self):
        return {
            'begin_time': self.begin_time,
            'end_time': self.end_time,
            'result': self.result,
            'reason': self.reason,
            'crash': self.crash,
            'anr': self.anr,
            'setup_install_result': self.setup_install_result,
            'setup_uninstall_result': self.setup_uninstall_result,
            'teardown_uninstall_result': self.teardown_uninstall_result,
            'device_connect_result': self.device_connect_result,
            'check_screen_locked': self.check_screen_locked,
            'screen_lock_result': self.screen_lock_result,
            'start_app_status': self.start_app_status,
            'login_app_status': self.login_app_status,
            'log_path': self.log_path,
            'activity_info': self.activity_info,
            'app_version': self.app_version
        }

    def on_case_begin(self):
        self.begin_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def on_case_end(self):
        self.end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def on_app_install_failed(self):
        self.setup_install_result = False
        self.on_check_screen_lock_failed()

    def on_device_connect_failed(self):
        self.device_connect_result = False
        self.on_setup_app_uninstall_failed()

    def on_setup_app_uninstall_failed(self):
        self.setup_uninstall_result = False
        self.on_app_install_failed()

    def on_teardown_app_uninstall_failed(self):
        self.teardown_uninstall_result = False
        self.on_case_end()

    def on_check_screen_lock_failed(self):
        self.check_screen_locked = False
        self.on_teardown_app_uninstall_failed()


class PerformanceCaseResult(object):

    def __init__(self):
        self.begin_time = ''
        self.end_time = ''
        self.result = ''
        self.reason = ''
        self.device_connect_result = ''
        self.setup_install_result = ''
        self.setup_uninstall_result = ''
        self.screen_lock_result = ''
        self.start_app_status = ''
        self.login_app_status = ''
        self.teardown_uninstall_result = ''
        self.check_screen_locked = ''
        self.log_path = ''
        self.app_version = ''

    @property
    def info(self):
        return {
            'begin_time': self.begin_time,
            'end_time': self.end_time,
            'result': self.result,
            'reason': self.reason,
            'setup_install_result': self.setup_install_result,
            'setup_uninstall_result': self.setup_uninstall_result,
            'teardown_uninstall_result': self.teardown_uninstall_result,
            'device_connect_result': self.device_connect_result,
            'check_screen_locked': self.check_screen_locked,
            'screen_lock_result': self.screen_lock_result,
            'start_app_status': self.start_app_status,
            'login_app_status': self.login_app_status,
            'log_path': self.log_path,
            'app_version': self.app_version
        }

    def on_case_begin(self):
        self.begin_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def on_case_end(self):
        self.end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def on_app_install_failed(self):
        self.setup_install_result = False
        self.on_check_screen_lock_failed()

    def on_device_connect_failed(self):
        self.device_connect_result = False
        self.on_setup_app_uninstall_failed()

    def on_setup_app_uninstall_failed(self):
        self.setup_uninstall_result = False
        self.on_app_install_failed()

    def on_teardown_app_uninstall_failed(self):
        self.teardown_uninstall_result = False
        self.on_case_end()

    def on_check_screen_lock_failed(self):
        self.check_screen_locked = False
        self.on_teardown_app_uninstall_failed()
