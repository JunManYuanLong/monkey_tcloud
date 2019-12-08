#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import logging
import os
import time
import traceback
from datetime import datetime
from multiprocessing import Process

from automonkey.config import DefaultConfig
from .adb import AdbTool
from .exception import DeviceNotConnectedException, InstallAppException, CheckScreenLockedFailed
from .logcat import LogCat
from .tcloud_update import TCloud
from .utils import Utils

logger = logging.getLogger(__name__)

"""
#  MonkeyRunner ， 多进程
"""


class PerformanceRunner(Process):

    def __init__(self, queue, lock, performance):
        super(PerformanceRunner, self).__init__()
        self.queue = queue
        self.performance = performance
        self.lock = lock
        self.daemon = True
        self.logcat = None
        self.adb_tool = None
        self.tcloud = None
        self.process = 0

    def run(self):
        try:
            self.init_tools()

            # 开始测试
            self.tcloud.on_task_begin()

            # 测试准备
            self.setup()

            # 测试内容
            self.run_performances()

            # 测试结束
            self.teardown()

        except DeviceNotConnectedException as d_e:
            logger.error(d_e)
            self.performance.result.on_device_connect_failed()
            self.tcloud.on_device_connect(False)
        except CheckScreenLockedFailed as c_e:
            logger.error(c_e)
            self.performance.result.on_check_screen_lock_failed()
            self.tcloud.on_screen_lock(False)
        except InstallAppException as i_e:
            logger.error(i_e)
            self.performance.result.on_app_install_failed()
            self.tcloud.on_setup_install_app(False)
        except CheckScreenLockedFailed as s_e:
            logger.error(s_e)
            self.performance.result.on_check_screen_lock_failed()
            self.tcloud.on_screen_lock(False)
        except Exception as e:
            logger.error(e)
            traceback.print_exc()
        finally:
            logger.info('{} 结束测试 设备 {}'.format(self.pid, self.performance.device.device_id))
            # 测试结束
            self.teardown()
            self.publish_result()

    def get_performance_airtest_scripts(self):
        try:
            # os.system('rm -rf ./performancetest')
            # os.system('git clone http://mengwei@git.innotechx.com/scm/~mengwei/performancetest.git ./performancetest')
            os.system('cp -rf ./performancetest/* ./')
        except Exception as e:
            logger.error(e)

    def run_performances(self):
        try:
            if os.path.exists(self.performance.config.test_envs):
                if not os.path.exists(self.performance.config.test_envs):
                    logger.error('config {} not found at local!'.format(self.performance.config.test_envs))
                with open(self.performance.config.test_envs, 'r') as f:
                    self.performance.config.test_envs = json.load(f)
            logger.info(self.performance.config.test_envs)
            tests_count = len(self.performance.config.test_envs.get('tests'))
            run_count = 0
            for test_env in self.performance.config.test_envs.get('tests'):
                if self.on_user_cancel():
                    break
                self.adb_tool.clear_package_cache_data(self.performance.config.package_name)
                self.setup_air_test()
                self.run_performance(test_env, self.performance.config.test_envs.get('root'), tests_count, run_count)
                run_count += 1

            # user cancel here
            if self.on_user_cancel():
                self.tcloud.on_user_cancel_stask_success()

        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())

    def run_performance(self, test_env, root_path, tests_count, run_count):
        try:
            test_name = test_env.get('name')
            test_path = '{}/{}'.format(root_path, test_env.get('path'))

            self.performance_test_id = self.tcloud.create_performance_test(test_name, self.performance.config.run_time)
            performance_progress = self.run_performance_cmd(test_path, test_name)

            time_begin = datetime.now()

            running_status = 1
            running_error_reason = ''
            cancel_flag = False

            time.sleep(60)

            while True:

                time_temp = (datetime.now() - time_begin).seconds

                # 检测 performance progress 是否
                if performance_progress.poll() is not None:
                    logger.warning('[{}] performance stopped early !'.format(self.performance.device.device_id))
                    logger.info('[{}] try to rerun the performance!'.format(self.performance.device.device_id))

                    mins = self.performance.config.run_time - time_temp // 60

                    if mins <= 0:
                        break
                    performance_progress = self.run_performance_cmd(test_path, test_name)

                # 检测是否 进行了 中断操作
                cancel_flag = self.on_user_cancel()

                if cancel_flag:
                    break

                # 检测 设备连接和锁屏状态
                if isinstance(self.performance.device.connect(), DeviceNotConnectedException):
                    running_error_reason = 'device {} dis connect'.format(self.performance.device.device_id)
                    running_status = 2
                    self.tcloud.on_device_disconnect_on_running()
                    break
                self.adb_tool.check_screen_locked()
                self.get_cpu_rss_heap()
                self.on_process_changed(time_temp, tests_count, run_count)
                # 当 process == 100 , break
                if self.process == 100:
                    break

                # time.sleep(1)

            time.sleep(30)  # 此处的需要等待 log 写入

            monkey_logs = []

            # 等待 monkey 结束
            while performance_progress.poll() is None:
                logger.info('waiting for monkey end...')
                time_temp = (datetime.now() - time_begin).seconds // 60
                if time_temp > 1:
                    if performance_progress.poll() is None:
                        performance_progress.kill()
                    break
                time.sleep(10)

            # user cancel here
            if cancel_flag:
                self.tcloud.on_user_cancel_stask_success()
            elif running_status == 2:
                self.tcloud.on_running_status(running_status, running_error_reason)

            self.performance.result.log_path = self.logcat.get_logcat_log(monkey_logs)

            # calculate every test's average and top
            self.tcloud.calculate_performance_test(self.performance_test_id)
            # 重复上传，删除
            # self.get_gen_bug_report()
            # self.upload_other_report()
            time.sleep(10)

        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())
        # finally:
        #     self.teardown()

    def get_cpu_rss_heap(self):
        cpu, rss = self.adb_tool.get_cpu(self.performance.config.package_name)
        heap_size, heap_alloc = self.adb_tool.get_memory_info(self.performance.config.package_name)
        logger.info([cpu, rss, heap_size, heap_alloc])
        self.tcloud.upload_realtime_log(self.performance_test_id, cpu, rss, heap_size, heap_alloc)

    def on_user_cancel(self):
        cancel_status = self.tcloud.get_monkey_cancel_status(self.performance.task_id)
        logger.info(cancel_status)
        if cancel_status in ['0', 0]:
            logger.warning('[{}] here find the cancel from the tcloud, stop the performance now!'.
                           format(self.performance.device.device_id))
            running_error_reason = 'cancel by user!'
            # on user cancel
            self.tcloud.on_user_cancel_task()
            cancel_flag = True
        else:
            cancel_flag = False
        return cancel_flag

    def run_performance_cmd(self, case_path, test_name):
        # 开始执行
        logger.info('({}) 开始运行 performance 测试'.format(self.performance.device.device_id))

        command = 'python3 -m airtest run {} --device Android://127.0.0.1:5037/{} ' \
            '> {}_{}.log'.format(case_path, self.performance.device.device_id, self.local_performance_path, test_name)
        logger.info('({}) 开始运行 性能 测试'.format(self.performance.device.device_id))

        monkey_progress = self.adb_tool.run_performance(command)
        return monkey_progress

    def setup_air_test(self):
        if self.performance.config.test_envs.get('setup') is not None:
            logger.info('({}) 开始运行 性能 测试 init'.format(self.performance.device.device_id))
            case_path = '{}/{}'.format(self.performance.config.test_envs.get('root'),
                                       self.performance.config.test_envs.get('setup').get('path'))
            command = 'python3 -m airtest run {} --device Android://127.0.0.1:5037/{} ' \
                      ''.format(case_path, self.performance.device.device_id)
            p = self.adb_tool.run_performance(command)
            result = self.adb_tool.output(p)
            logger.info("\n".join(result))
        self.adb_tool.set_system_default_input(key=self.performance.config.test_envs.get('setup').get('input'))

    # 获取并生成 bug report（adb bug report)
    def get_gen_bug_report(self):
        try:
            self.logcat.get_bug_report_log()
            self.logcat.generate_bug_report()
            self.logcat.upload_bug_report_log()

            now = datetime.now().strftime("%Y-%m-%d")
            build_number = os.environ.get('BUILD_NUMBER')
            report_url = '{}/monkey/{}/{}/logcat/{}/bug_report_out/index.html'.format(DefaultConfig.OSS_MONKEY_URL,
                                                                                      now, build_number, self.pid)
            report_type = 1
            self.tcloud.on_report_upload(report_url, report_type)
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())

    def upload_other_report(self):
        try:
            now = datetime.now().strftime("%Y-%m-%d")
            build_number = os.environ.get('BUILD_NUMBER')
            # monkey.log
            report_url_pre = '{}/monkey/{}/{}/logcat/{}'.format(DefaultConfig.OSS_MONKEY_URL, now, build_number,
                                                                self.pid)

            self.tcloud.on_report_upload(report_url='{}/monkey.log'.format(report_url_pre), report_type=2)

        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())

    def publish_result(self):
        self.lock.acquire()
        self.queue.put(self.performance)
        self.lock.release()

    def init_tools(self):
        self.adb_tool = AdbTool(self.performance.device.device_id)
        self.tcloud = TCloud(self.performance.task_id, self.performance.device.device_id, self.performance.monkey_id,
                             self.performance.tcloud_url)

        self.local_performance_path = '{}/{}/{}'.format(DefaultConfig.LOCAL_LOGCAT_PATH, self.pid, 'performance')
        self.local_logcat_path = '{}/{}/{}'.format(DefaultConfig.LOCAL_LOGCAT_PATH, self.pid, 'logcat.log')

    def on_process_changed(self, time_temp, test_count, run_count):
        logger.info('({}) time now ... {}'.format(self.performance.device.device_id, time_temp))
        self.process = int(time_temp / (self.performance.config.run_time * 60.00) * 100.00)
        logger.info('({}) process now : {}'.format(self.performance.device.device_id, self.process))

        if self.process <= 0:
            self.process = 0

        if self.process >= 100:
            self.process = 100

        logger.info(
            '''current information <{}> {}'''.format(datetime.now().strftime('%Y.%m.%d %H:%M:%S'), self.process))
        self.tcloud.on_anr_crash_changed((run_count * 100 + self.process)//test_count, 0, 0)

    def setup(self):
        try:
            logger.info('{} 开始测试 设备 {}'.format(self.pid, self.performance.device.device_id))

            # 清除 重建 logs
            self.clear_local_logs()
            self.creat_local_log_path()

            # 连接设备
            self.performance.result.device_connect_result = self.performance.device.connect()

            if isinstance(self.performance.result.device_connect_result, DeviceNotConnectedException):
                raise DeviceNotConnectedException

            self.tcloud.on_device_connect(True)

            # 锁定机器
            self.tcloud.using_monkey_device(self.performance.device.device_id)

            # 开启日志
            self.logcat = LogCat(self.performance.device.device_id, self.pid)

            # 测试开始时间
            self.performance.result.on_case_begin()

            if self.performance.config.uninstall_app_required:
                # 卸载
                self.performance.result.setup_uninstall_result = self.adb_tool.uninstall_package(
                    self.performance.config.package_name)
                self.tcloud.on_setup_uninstall_app(self.performance.result.setup_uninstall_result)

            if self.performance.config.install_app_required:
                # 安装 package
                self.performance.result.setup_install_result = self.adb_tool.install_package(
                    self.performance.config.local_package_path, self.performance.config.package_name)
            else:
                self.performance.result.setup_install_result = True

            self.tcloud.on_setup_install_app(self.performance.result.setup_install_result)
            if not self.performance.result.setup_install_result:
                raise InstallAppException

            # 获取 app 版本
            self.performance.result.app_version = self.adb_tool.get_package_version(
                self.performance.config.package_name)

            self.tcloud.on_get_app_version(self.performance.result.app_version)

            # 检查 设备锁屏状态
            self.performance.result.check_screen_locked = self.adb_tool.check_screen_locked()

            self.tcloud.on_screen_lock(self.performance.result.check_screen_locked)

            if not self.performance.result.check_screen_locked:
                raise CheckScreenLockedFailed

            self.clear_log_on_device()
            time.sleep(5)

            # 回到桌面
            logger.info('({}) 回到桌面'.format(self.performance.device.device_id))
            self.adb_tool.back_to_home()
            self.get_performance_airtest_scripts()
            time.sleep(5)

            # 热启动 app
            logger.info('({}) 尝试热启动 app'.format(self.performance.device.device_id))
            self.performance.result.start_app_status = True
            self.tcloud.on_start_app(self.performance.result.start_app_status)

            # 登陆 app 没有用到！
            self.performance.result.login_app_status = self.try_to_login_app()
            self.tcloud.on_login_app(self.performance.result.login_app_status)

        except Exception as e:
            logger.error(e)
            traceback.print_exc()
            raise e

    def teardown(self):
        try:
            # update task end info
            self.tcloud.on_task_end(process=self.process, run_time=self.performance.config.run_time)

            logger.info('{} 结束测试 设备 {}'.format(self.pid, self.performance.device.device_id))
            # 测试结束时间
            self.performance.result.on_case_end()

            if self.performance.config.uninstall_app_required:
                # 卸载 package
                self.performance.result.teardown_uninstall_result = self.adb_tool.uninstall_package(
                    self.performance.config.package_name)
            else:
                self.performance.result.teardown_uninstall_result = True

            self.tcloud.on_teardown_uninstall_app(self.performance.result.teardown_uninstall_result)

            self.tcloud.release_monkey_device(self.performance.device.device_id)

            self.tcloud.on_running_status(status=1, error_msg='')

            # 断开连接设备
            self.performance.device.disconnect()
        except Exception as e:
            logger.error(e)
            traceback.print_exc()
        finally:
            self.tcloud.release_monkey_device(self.performance.device.device_id)

    def clear_log_on_device(self):
        # 移除 设备中原有的 log /sdcard 下的log
        self.logcat.reset_bug_report_log()

    def clear_local_logs(self):
        # 移除本地logcat 目录
        logger.info('移除 logcat 目录')
        Utils.command_execute('rm -rf ./logcat')

    def creat_local_log_path(self):
        logger.info('初始化 log 目录')

        Utils.command_execute('mkdir -p logcat')
        Utils.command_execute('mkdir -p logcat/{}'.format(self.pid))

    def try_to_unlock_screen(self):
        logger.info('({}) 尝试 解锁屏幕'.format(self.performance.device.device_id))
        # TODO

    def try_to_login_app(self):
        logger.info('({}) 尝试 登陆 app {}'.format(self.performance.device.device_id, self.performance.config.package_name))
        # TODO
        try:
            if self.performance.config.login_required:
                logger.info('({}) 使用 [{} ,{}] 尝试登陆'.format(self.performance.device.device_id,
                                                           self.performance.config.login_username,
                                                           self.performance.config.login_password))
                return True
            else:
                logger.info('({}) 不需要登陆'.format(self.performance.device.device_id))
                return True
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())
            return False
