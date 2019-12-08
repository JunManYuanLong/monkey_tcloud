import logging
import os
import platform
import re
import time
import traceback

import prettytable

from .exception import LocalPackageNotFoundException
# from .uiautomator_helper import U2Helper  # no use here
from .utils import Utils

logger = logging.getLogger(__name__)


class AdbTool(object):
    def __init__(self, device_name):
        self.device_name = device_name
        self.command_path = 'adb'
        self.command_args = '-s {}'.format(device_name)
        # self.u2helper = U2Helper(self.device_name)
        pass

    @property
    def system(self):
        return platform.system()

    def output(self, p):
        if p.stdout:
            return Utils.deal_with_python_version(p.stdout.readlines())
        else:
            return Utils.deal_with_python_version(p.stderr.readlines())

    @property
    def adb_command(self):
        return '{} {} '.format(self.command_path, self.command_args)

    def push_file(self, source, target):
        logger.info('({}) 将文件 {} 发送到 {}'.format(self.device_name, source, target))
        cmd = '{} push {} {}'.format(self.adb_command, source, target)
        p = Utils.command_execute(cmd)
        return self.output(p)

    def remove_file(self, file_name):
        logger.info('({}) 开始删除文件 <{}>'.format(self.device_name, file_name))
        if file_name in ['/', '/sdcard'] or not file_name.startswith('/sdcard/'):
            logger.error('({}) 文件名类型不对，无法删除!'.format(self.device_name))
            return False
        cmd = '{} shell rm -rf {}'.format(self.adb_command, file_name)
        p = Utils.command_execute(cmd)
        r = self.output(p)
        if len(r) > 0:
            logger.info(r)
        return True

    def connect_remote_device(self, remote_device_id):
        cmd = '{} connect {}'.format(self.adb_command, remote_device_id)
        p = Utils.command_execute(cmd)
        return self.output(p)

    def pull_file(self, source, target):
        logger.info('({}) 将文件 {} 下载到 {}'.format(self.device_name, source, target))
        cmd = '{} pull {} {}'.format(self.adb_command, source, target)
        p = Utils.command_execute(cmd)
        return self.output(p)

    def check_screen_locked(self, times=1):
        """
        adb shell dumpsys window policy | grep isStatusBarKeyguard 确认是否有锁
        adb shell dumpsys window policy | grep ScreenOn 是否亮屏
        """
        try:
            if times >= 10:
                return False
            logger.info('({}) <尝试{}> 检查设备是否锁屏'.format(self.device_name, times))
            window_policy = Utils.command_execute(
                '{} shell dumpsys window policy'.format(self.adb_command)).stdout.read()

            window_policy = Utils.deal_with_python_version(window_policy)

            locked_status = re.findall(r'isStatusBarKeyguard=(\w+)', window_policy)[0]
            bright_status = re.findall(r'mScreenOnFully=(\w+)', window_policy)[0]

            if locked_status == 'false' and bright_status == 'true':
                logger.info('({}) 设备是正常开锁状态！'.format(self.device_name))
                return True
            elif bright_status == 'false':
                logger.info('({}) 设备锁屏！'.format(self.device_name))
                self.wakeup_screen()
                time.sleep(1)
                self.unlock_screen()
                time.sleep(1)
                return self.check_screen_locked(times=times + 1)
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())
            return self.check_screen_locked(times=times + 1)

    def start_activity(self, package_name, activity_name):
        try:
            activity_name = '{}/{}'.format(package_name, activity_name)
            logger.info('({}) 启动 activity : {}'.format(self.device_name, activity_name))
            cmd = '{} shell am start -W -n {}'.format(self.adb_command, activity_name)
            p = Utils.command_execute(cmd)
            result = self.output(p)
            logger.info(result)
            time.sleep(10)
            current_activity = self.get_current_activity()
            if current_activity == activity_name:
                logger.info('({}) activity 已经启动成功'.format(self.device_name))
                return True
            return result
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())

    def clear_logcat(self):
        logger.info('({}) 清除 logcat log'.format(self.device_name))
        cmd = '{} logcat -c'.format(self.adb_command)
        p = Utils.command_execute(cmd)
        return p

    def start_logcat(self, target):
        logger.info('({}) 打开 logcat log'.format(self.device_name))
        # cmd = '{} logcat -v time > {}'.format(self.adb_command, target)
        # p = Utils.command_execute(cmd)
        return None

    def back_to_home(self):
        cmd = '{} shell input keyevent 3'.format(self.adb_command)
        p = Utils.command_execute(cmd)
        return self.output(p)

    def run_monkey(self, monkey_command):
        try:
            cmd = '{} {}'.format(self.adb_command, monkey_command)
            p = Utils.command_execute(cmd)
            return p
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())


    def run_performance(self, performance_command):
        try:
            cmd = '{}'.format(performance_command)
            p = Utils.command_execute(cmd)
            return p
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())

    def install_package(self, local_package_path, package_name, force_install=False):
        logger.info('({}) 开始安装包 ： {}'.format(self.device_name, local_package_path))
        try:
            if not os.path.exists(local_package_path):
                raise LocalPackageNotFoundException
            if force_install:
                cmd = '{} install -r {} > install_log.log'.format(self.adb_command, local_package_path)
            else:
                cmd = '{} install {} > install_log.log'.format(self.adb_command, local_package_path)

            p = Utils.command_execute(cmd)
            result = self.output(p)
            logger.info('({}) {}'.format(self.device_name, result))

            if self.check_package_installed(package_name):
                # for r in result:
                #     if 'Success' in r:
                #         logger.info('({}) 安装 {} 成功'.format(self.device_name, local_package_path))
                #         return True
                return True
            logger.error('({}) 安装 {} 失败'.format(self.device_name, local_package_path))
            return False
        except Exception as e:
            logger.error('({}) 安装 {} 失败'.format(self.device_name, local_package_path))
            logger.error(e)
            return e

    def uninstall_package(self, package_name):
        logger.info('({}) 开始卸载 ：{}'.format(self.device_name, package_name))
        try:
            if self.check_package_installed(package_name):
                cmd = '{} uninstall {}'.format(self.adb_command, package_name)
                p = Utils.command_execute(cmd)
                result = self.output(p)
                logger.info('({}) {}'.format(self.device_name, result))
                for r in result:
                    if 'Success' in r:
                        logger.info('({}) 卸载 {} 成功'.format(self.device_name, package_name))
                        return True
                logger.error('({}) 卸载 {} 失败 : '.format(self.device_name, package_name))
                return False
            else:
                logger.info('({}) 设备没有安装 {}, 不需要卸载'.format(self.device_name, package_name))
                return True
        except Exception as e:
            logger.error('({}) 卸载 {} 失败 : '.format(self.device_name, package_name))
            return e

    def get_installed_packages(self, show_table=False):
        try:
            cmd = '{} shell pm list packages'.format(self.adb_command)
            p = Utils.command_execute(cmd)
            package_list = self.output(p)
            if show_table:
                logger.info('({}) 获取所有的已安装的包'.format(self.device_name))
                table_packages = prettytable.PrettyTable()
                table_packages.field_names = ["id", "package name"]
                for i, package in enumerate(package_list):
                    row = [i, package]
                    table_packages.add_row(row)
                logger.info('({}) \n {}'.format(self.device_name, table_packages))
            return package_list
        except Exception as e:
            logger.error(e)
            return e

    def check_package_installed(self, package_name):
        for package in self.get_installed_packages():
            if package_name in package:
                return True

        return False

    def check_adb(self):
        if "ANDROID_HOME" in os.environ:
            if self.system == "Windows":
                path = os.path.join(os.environ["ANDROID_HOME"], "platform-tools", "adb.exe")
                if os.path.exists(path):
                    self.command_path = path
                else:
                    raise EnvironmentError("Adb not found in $ANDROID_HOME path: {}".format(os.environ["ANDROID_HOME"]))
            else:
                path = os.path.join(os.environ["ANDROID_HOME"], "platform-tools", "adb")
                if os.path.exists(path):
                    self.command_path = path
                else:
                    raise EnvironmentError(
                        "Adb not found in $ANDROID_HOME path: {}.".format(os.environ["ANDROID_HOME"]))
        else:
            raise EnvironmentError("Adb not found in $ANDROID_HOME path: {}".format(os.environ["ANDROID_HOME"]))

    def get_current_application(self):
        return Utils.command_execute(
            '{} shell dumpsys window w | grep mCurrentFocus'.format(self.adb_command))

    def get_current_package(self):
        p = self.get_current_application()
        result = self.output(p)
        if len(result) > 0:
            return result[0].split(' ')[-1].split('/')[0]
        return None

    def get_package_version(self, package_name):
        logger.info('({}) 获取 安装包 版本信息'.format(self.device_name))
        if self.check_package_installed(package_name):
            cmd = '{} shell dumpsys package {} | grep versionName'.format(self.adb_command, package_name)
            p = Utils.command_execute(cmd)
            r = self.output(p)
            if len(r) > 0:
                temp = r[0].split('=')
                if len(temp) > 0:
                    version = temp[1].strip()
                    logger.info('({}) 版本是 [{}] '.format(self.device_name, version))
                    return version
            return ''
        else:
            logger.info('({}) {} 没有安装!'.format(self.device_name, package_name))
            return None

    def get_current_activity(self):
        p = self.get_current_application()
        result = self.output(p)
        if len(result) > 0:
            names = result[0].split(' ')
            if len(names) > 1:
                activity_name = names[-1]
                if '/' in activity_name:
                    activity = activity_name.split('/')
                    return activity[1].strip() if len(activity) > 1 else activity
        return None

    def get_process(self, package_name):
        if self.system is "Windows":
            pid_command = Utils.command_execute(
                "{} shell ps | grep {}$".format(self.adb_command, package_name)).stdout.readlines()
        else:
            pid_command = Utils.command_execute(
                "{} shell ps | grep -w {}".format(self.adb_command, package_name)).stdout.readlines()

        return Utils.deal_with_python_version(pid_command)

    def process_exists(self, package_name):
        process = self.get_process(package_name)
        return package_name in process

    def get_pid(self, package_name):
        pid_command = self.get_process(package_name)
        if pid_command == '':
            logger.info("The process doesn't exist.")
            return pid_command
        req = re.compile(r"\d+")
        result = str(pid_command).split()
        result.remove(result[0])
        return req.findall(" ".join(result))[0]

    def get_uid(self, pid):
        result = Utils.command_execute("{} shell cat /proc/{}/status".format(self.adb_command, pid)).stdout.readlines()
        result = Utils.deal_with_python_version(result)
        for i in result:
            if 'uid' in i.lower():
                return i.split()[1]

    def get_battery_level(self):
        result = Utils.command_execute('{} shell dumpsys battery'.format(self.adb_command)).stdout.readlines()
        result = Utils.deal_with_python_version(result)
        for r in result:
            if 'level' in r:
                return int(r.split(':')[1])
        return 0

    def get_flow_data_tcp(self, uid):
        tcp_rcv = \
            Utils.command_execute("{} shell cat proc/uid_stat/{}/tcp_rcv".format(self.adb_command, uid)).read().split()[
                0]
        tcp_snd = \
            Utils.command_execute("{} shell cat proc/uid_stat/{}/tcp_snd".format(self.adb_command, uid)).read().split()[
                0]
        return tcp_rcv, tcp_snd

    def get_adb_version(self):
        cmd = '{} version'.format(self.adb_command)
        p = Utils.command_execute(cmd)
        return self.output(p)

    def get_device_list(self):
        try:
            cmd = '{} devices'.format(self.command_path)
            p = Utils.command_execute(cmd)
            result = self.output(p)
            devices = []
            if len(result) > 0 and result[0].startswith('List'):
                for line in result[1:]:
                    if line in ['\n'] or 'un' in line:
                        continue
                    try:
                        device = line.strip().replace('\t', '').split('device')[0]
                    except Exception as e:
                        device = None
                        logger.error(e)
                    if device not in [None, '\n', '\t']:
                        devices.append(device)
            return devices
        except Exception as e:
            logger.info(e)
            logger.info(traceback.format_exc())
            return []

    def check_device_connected(self, device):
        return device in self.get_device_list()

    def get_crash_dump_log(self):
        try:
            cmd = '{} shell cat /sdcard/MonkeyLog/crash-dump.log'.format(self.adb_command)
            p = Utils.command_execute(cmd)
            return self.output(p)
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())

    def unlock_screen(self):
        try:
            cmd = '{} shell input swipe 100 1000 100 20'.format(self.adb_command)
            Utils.command_execute(cmd)
            return True
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())

    def wakeup_screen(self):
        try:
            cmd = '{} shell input keyevent 26'.format(self.adb_command)
            Utils.command_execute(cmd)
            return True
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())

    def get_bug_report_log(self, log_path):
        try:
            cmd = '{} shell bugreport > {}'.format(self.adb_command, log_path)
            p = Utils.command_execute(cmd)
            while p.poll() is None:
                time.sleep(1)

            for file_name in os.listdir("./"):
                if file_name.startswith('bugreport-') and file_name.endswith('.zip'):
                    return file_name
            return log_path
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())

    def reset_bug_report_log(self):
        try:
            logger.info('reset battery stats log now...')
            cmd = '{} shell dumpsys batterystats --reset'.format(self.adb_command)
            p = Utils.command_execute(cmd)
            return self.output(p)
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())

    def set_system_default_input(self, key):
        try:
            if key:
                logger.info('try to set system default input to qjp')
                key_of_qjp = key
                cmd = '{} shell ime enable {}'.format(self.adb_command, key_of_qjp)
                p = Utils.command_execute(cmd)
                logger.info(self.output(p))
                time.sleep(5)
                cmd = '{} shell ime set {}'.format(self.adb_command, key_of_qjp)
                p = Utils.command_execute(cmd)
                logger.info(self.output(p))
                time.sleep(5)
                return True
        except Exception as e:
            logger.error(e)

    def get_memory_info(self, package_name):
        try:
            logger.info('try to get memory information')
            cmd = '{} shell dumpsys meminfo {}'.format(self.adb_command, package_name)
            p = Utils.command_execute(cmd)
            lines = self.output(p)
            # lines = Utils.deal_with_python_version(lines)
            heap_size, heap_alloc = 0, 0
            for line in lines:
                if 'Native Heap' in line:
                    temp = line.split()
                    if len(temp) == 9:
                        heap_size = temp[-3]
                        heap_alloc = temp[-2]
                    break
            heap_size = int(heap_size) if heap_size != '' else 0
            heap_alloc = int(heap_alloc) if heap_alloc != '' else 0
            return heap_size, heap_alloc
        except Exception as e:
            logger.error(e)
            return 0, 0

    def get_cpu(self, package_name):
        try:
            logger.info('try to get cpu information')
            cmd = '{} shell top -n 1 | grep {} '.format(self.adb_command, package_name)
            p = Utils.command_execute(cmd)
            lines = self.output(p)
            # lines = Utils.deal_with_python_version(lines)
            cpu = rss = 0
            for line in lines:
                logger.info(line)
                if package_name in line and f'{package_name}:' not in line:
                    temp = re.findall(r'.* (\w+)% .* (\w+)K (\w+)K .* {}'.format(package_name), line)
                    cpu = temp[0][0]
                    rss = temp[0][2]
                    break
            cpu = int(cpu) if cpu != '' else 0
            rss = int(rss) if rss != '' else 0
            return cpu, rss
        except Exception as e:
            logger.error(e)
            return 0, 0

    def clear_package_cache_data(self, package_name):
        try:
            logger.info('try to clear cache data information')
            cmd = '{} shell pm clear {}'.format(self.adb_command, package_name)
            lines = Utils.command_execute(cmd)
            return lines
        except Exception as e:
            logger.error(e)
