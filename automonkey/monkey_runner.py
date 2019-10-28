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


class MonkeyRunner(Process):

    def __init__(self, queue, lock, monkey):
        super(MonkeyRunner, self).__init__()
        self.queue = queue
        self.monkey = monkey
        self.lock = lock
        self.daemon = True
        self.logcat = None
        self.adb_tool = None
        self.tcloud = None
        self.anr = 0
        self.crash = 0
        self.local_monkey_path = None
        self.local_logcat_path = None
        self.local_crash_path = None
        self.process = 0

    def run(self):
        try:
            self.init_tools()

            # 开始测试
            self.tcloud.on_task_begin()

            # 测试准备
            self.setup()

            # 测试内容
            self.run_monkey()

            # 测试结束
            self.teardown()

        except DeviceNotConnectedException as d_e:
            logger.error(d_e)
            self.monkey.result.on_device_connect_failed()
            self.tcloud.on_device_connect(False)
        except CheckScreenLockedFailed as c_e:
            logger.error(c_e)
            self.monkey.result.on_check_screen_lock_failed()
            self.tcloud.on_screen_lock(False)
        except InstallAppException as i_e:
            logger.error(i_e)
            self.monkey.result.on_app_install_failed()
            self.tcloud.on_setup_install_app(False)
        except CheckScreenLockedFailed as s_e:
            logger.error(s_e)
            self.monkey.result.on_check_screen_lock_failed()
            self.tcloud.on_screen_lock(False)
        except Exception as e:
            logger.error(e)
            traceback.print_exc()
        finally:
            logger.info('{} 结束测试 设备 {}'.format(self.pid, self.monkey.device.device_id))
            # 测试结束
            self.teardown()
            self.publish_result()

    def run_monkey(self):
        try:
            # 回到桌面
            logger.info('({}) 回到桌面'.format(self.monkey.device.device_id))
            self.adb_tool.back_to_home()

            # 热启动 app
            logger.info('({}) 尝试热启动 app'.format(self.monkey.device.device_id))
            self.monkey.result.start_app_status = self.adb_tool.start_activity(self.monkey.config.package_name,
                                                                               self.monkey.config.default_app_activity)
            self.tcloud.on_start_app(self.monkey.result.start_app_status)

            # 登陆 app
            self.monkey.result.login_app_status = self.try_to_login_app()
            self.tcloud.on_login_app(self.monkey.result.login_app_status)

            monkey_progress = self.run_monkey_cmd(self.monkey.config.run_time)

            time_begin = datetime.now()

            current_anr = 0
            current_crash = 0
            running_status = 1
            running_error_reason = ''
            cancel_flag = False

            while True:

                time_temp = (datetime.now() - time_begin).seconds

                # 检测 monkey_progress 是否
                if monkey_progress.poll() is not None:
                    logger.warning('[{}] monkey stoped early !'.format(self.monkey.device.device_id))
                    logger.info('[{}] try to rerun the monkey!'.format(self.monkey.device.device_id))

                    mins = self.monkey.config.run_time - time_temp // 60

                    if mins <= 0:
                        current_anr, current_crash = self.on_process_crash_anr_changed(time_temp)
                        self.tcloud.on_anr_crash_changed(100, current_anr, current_crash)
                        break
                    monkey_progress = self.run_monkey_cmd(mins)

                # 检测是否 进行了 中断操作
                cancel_flag = self.on_user_cancel()

                if cancel_flag:
                    break

                # 检测 设备连接和锁屏状态
                if isinstance(self.monkey.device.connect(), DeviceNotConnectedException):
                    running_error_reason = 'device {} dis connect'.format(self.monkey.device.device_id)
                    running_status = 2
                    self.tcloud.on_device_disconnect_on_running()
                    break
                self.adb_tool.check_screen_locked()

                # process crash anr 改变
                self.on_process_crash_anr_changed(time_temp)

                # 当 process == 100 , break
                if self.process == 100:
                    break

                time.sleep(5)

            time.sleep(30)  # 此处的需要等待 log 写入

            monkey_logs = []

            # 等待 monkey 结束
            while monkey_progress.poll() is None:
                logger.info('waiting for monkey end...')
                time_temp = (datetime.now() - time_begin).seconds // 60
                if time_temp > 1:
                    # 这里暂时不获取 monkey log
                    # monkey_logs = monkey_progress.stdout.readlines()
                    if monkey_progress.poll() is None:
                        monkey_progress.kill()
                    break
                time.sleep(10)

            # user cancel here
            if cancel_flag:
                self.tcloud.on_user_cancel_stask_success()
            else:
                self.tcloud.on_running_status(running_status, running_error_reason)

            self.monkey.result.log_path = self.logcat.get_logcat_log(monkey_logs)

            activity_all, activity_tested, activity_info = self.get_activity_infos()
            self.monkey.result.activity_info = activity_info
            # update task end info
            self.tcloud.on_task_end(process=self.process, activity_count=len(activity_all),
                                    activity_tested_count=len(activity_tested),
                                    activity_all=str(activity_all), activity_tested=str(activity_tested),
                                    anr_count=current_anr, crash_count=current_crash, crash_rate=0,
                                    exception_count=0, exception_run_time=0, run_time=self.monkey.config.run_time)

            # 重复上传，删除
            # self.analysis_upload_crash_logs()
            self.get_gen_bug_report()
            self.upload_other_report()
            time.sleep(10)

        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())
        finally:
            self.teardown()

    def on_user_cancel(self):
        cancel_status = self.tcloud.get_monkey_cancel_status(self.monkey.task_id)
        logger.info(cancel_status)
        if cancel_status in ['0', 0]:
            logger.warning('[{}] here find the cancel from the tcloud, stop the monkey now!'.
                           format(self.monkey.device.device_id))
            running_error_reason = 'cancel by user!'
            # on user cancel
            self.tcloud.on_user_cancel_task()
            cancel_flag = True
        else:
            cancel_flag = False
        return cancel_flag

    def on_process_crash_anr_changed(self, time_temp):
        logger.info('({}) time now ... {}'.format(self.monkey.device.device_id, time_temp))
        self.process = int(time_temp / (self.monkey.config.run_time * 60.00) * 100.00)
        logger.info('({}) process now : {}'.format(self.monkey.device.device_id, self.process))

        if self.process <= 0:
            self.process = 0

        if self.process >= 100:
            self.process = 100

        current_activity = self.adb_tool.get_current_activity()
        current_battery_level = self.adb_tool.get_battery_level()
        current_anr, current_crash = self.logcat.get_anr_crash_count()

        logger.info(
            '''current information <{}> current activity : {} ; current battery : {}; anr count : {} ;'''
            '''crash count : {}'''.format(datetime.now().strftime('%Y.%m.%d %H:%M:%S'), current_activity,
                                          current_battery_level, current_anr, current_crash))
        self.on_anr_crash_changed(current_anr, current_crash)
        # 这里防止 crash anr 变小，使用系统存储的 anr 和 crash
        current_crash = self.crash
        current_anr = self.anr

        self.tcloud.on_anr_crash_changed(self.process, current_anr, current_crash)
        return current_anr, current_crash

    def run_monkey_cmd(self, run_time=0):
        run_mode = DefaultConfig.MONKEY_MODE_KEY_MAP.get(int(self.monkey.config.run_mode))
        logcat_process = self.logcat.set_logcat(self.local_logcat_path)

        # 开始执行 monkey
        logger.info('({}) 开始运行 monkey 测试'.format(self.monkey.device.device_id))
        logger.info('({}) monkey mode : {}'.format(self.monkey.device.device_id, run_mode))

        command = 'shell CLASSPATH=/sdcard/monkey.jar:/sdcard/framework.jar exec app_process ' \
                  ' /system/bin tv.panda.test.monkey.Monkey -p {} {} --throttle 500 ' \
                  ' --output-directory /sdcard/MonkeyLog --running-minutes {} -v -v > {}'.format(
            self.monkey.config.package_name, run_mode, run_time, self.local_monkey_path)

        logger.info('({}) 开始运行 monkey 测试 [{} 分钟], 日志输出到 {}'.format(
            self.monkey.device.device_id, run_time, self.local_monkey_path))

        monkey_progress = self.adb_tool.run_monkey(command)
        return monkey_progress

    def get_activity_infos(self):
        activity_info = self.logcat.get_activity_test_info(show_in_cmd=True)
        activity_all = activity_info.get('TotalActivity')
        activity_tested = activity_info.get('TestedActivity')
        return activity_all, activity_tested, activity_info

    def analysis_upload_crash_logs(self):
        crash_logs = self.logcat.analysis_crash_anr_log(self.local_crash_path)
        self.tcloud.on_errorlog_upload(crash_logs)

    # 当 anr 或者 crash 改变的时候， 获取并上传 anr crash log，实时显示
    def on_anr_crash_changed(self, anr, crash):
        try:
            if self.anr != anr or self.crash != crash:
                if self.anr < anr or self.crash < crash:
                    logger.info('here anr or crash changed !')
                    self.logcat.get_crash_dump_log()
                    crash_logs = self.logcat.analysis_crash_anr_log(self.local_crash_temp_path, self.anr, self.crash)
                    self.anr = anr
                    self.crash = crash
                    self.tcloud.on_errorlog_upload(crash_logs)
                    return True
            return False
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())

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

            if self.anr > 0 or self.crash > 0:
                self.tcloud.on_report_upload(report_url='{}/monkey/MonkeyLog/crash-dump.log'.format(report_url_pre),
                                             report_type=3)
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())

    def publish_result(self):
        self.lock.acquire()
        self.queue.put(self.monkey)
        self.lock.release()

    def init_tools(self):
        self.adb_tool = AdbTool(self.monkey.device.device_id)
        self.tcloud = TCloud(self.monkey.task_id, self.monkey.device.device_id, self.monkey.monkey_id,
                             self.monkey.tcloud_url)

        self.local_monkey_path = '{}/{}/{}'.format(DefaultConfig.LOCAL_LOGCAT_PATH, self.pid, 'monkey.log')
        self.local_logcat_path = '{}/{}/{}'.format(DefaultConfig.LOCAL_LOGCAT_PATH, self.pid, 'logcat.log')
        self.local_crash_path = '{}/{}/monkey/MonkeyLog/crash-dump.log'.format(DefaultConfig.LOCAL_LOGCAT_PATH,
                                                                               self.pid)
        self.local_crash_temp_path = '{}/{}/crash-dump.log'.format(DefaultConfig.LOCAL_LOGCAT_PATH, self.pid)

    def setup(self):
        try:
            logger.info('{} 开始测试 设备 {}'.format(self.pid, self.monkey.device.device_id))

            # 清除 重建 logs
            self.clear_local_logs()
            self.creat_local_log_path()

            # 连接设备
            self.monkey.result.device_connect_result = self.monkey.device.connect()

            if isinstance(self.monkey.result.device_connect_result, DeviceNotConnectedException):
                raise DeviceNotConnectedException

            self.tcloud.on_device_connect(True)
            # self.adb_tool.u2helper.connect()

            # 锁定机器
            self.tcloud.using_monkey_device(self.monkey.device.device_id)

            # 开启日志
            self.logcat = LogCat(self.monkey.device.device_id, self.pid)

            # 测试开始时间
            self.monkey.result.on_case_begin()

            # 将 monkey.jar 和 framework.jar push 到 /sdcard
            self.adb_tool.push_file('./tools/monkey.jar', '/sdcard/')
            self.adb_tool.push_file('./tools/framework.jar', '/sdcard/')
            self.adb_tool.push_file('./tools/max.config', '/sdcard/')

            if self.monkey.config.install_app_required:

                # 卸载
                self.monkey.result.setup_uninstall_result = self.adb_tool.uninstall_package(
                    self.monkey.config.package_name)
                self.tcloud.on_setup_uninstall_app(self.monkey.result.setup_uninstall_result)

                # 安装 package
                self.monkey.result.setup_install_result = self.adb_tool.install_package(
                    self.monkey.config.local_package_path, self.monkey.config.package_name)
            else:
                self.monkey.result.setup_install_result = True

            self.tcloud.on_setup_install_app(self.monkey.result.setup_install_result)
            if not self.monkey.result.setup_install_result:
                raise InstallAppException

            # 获取 app 版本
            self.monkey.result.app_version = self.adb_tool.get_package_version(self.monkey.config.package_name)

            self.tcloud.on_get_app_version(self.monkey.result.app_version)

            # 检查 设备锁屏状态
            self.monkey.result.check_screen_locked = self.adb_tool.check_screen_locked()

            self.tcloud.on_screen_lock(self.monkey.result.check_screen_locked)

            if not self.monkey.result.check_screen_locked:
                raise CheckScreenLockedFailed

            self.clear_log_on_device()
            time.sleep(5)

        except Exception as e:
            logger.error(e)
            traceback.print_exc()
            raise e

    def teardown(self):
        try:

            logger.info('{} 结束测试 设备 {}'.format(self.pid, self.monkey.device.device_id))
            # 测试结束时间
            self.monkey.result.on_case_end()

            # 卸载 package
            self.monkey.result.teardown_uninstall_result = self.adb_tool.uninstall_package(
                self.monkey.config.package_name)

            self.tcloud.on_teardown_uninstall_app(self.monkey.result.teardown_uninstall_result)

            self.tcloud.release_monkey_device(self.monkey.device.device_id)

            # 断开连接设备
            self.monkey.device.disconnect()
        except Exception as e:
            logger.error(e)
            traceback.print_exc()
        finally:
            self.tcloud.release_monkey_device(self.monkey.device.device_id)

    def clear_log_on_device(self):
        # 移除 设备中原有的 log /sdcard 下的log
        self.adb_tool.remove_file('/sdcard/crash-dump.log')
        self.adb_tool.remove_file('/sdcard/oom-traces.log')
        self.adb_tool.remove_file('/sdcard/MonkeyLog')
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
        logger.info('({}) 尝试 解锁屏幕'.format(self.monkey.device.device_id))
        # TODO

    def try_to_login_app(self):
        logger.info('({}) 尝试 登陆 app {}'.format(self.monkey.device.device_id, self.monkey.config.package_name))
        # TODO
        try:
            if self.monkey.config.login_required:
                logger.info('({}) 使用 [{} ,{}] 尝试登陆'.format(self.monkey.device.device_id,
                                                           self.monkey.config.login_username,
                                                           self.monkey.config.login_password))
                return True
            else:
                logger.info('({}) 不需要登陆'.format(self.monkey.device.device_id))
                return True
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())
            return False
