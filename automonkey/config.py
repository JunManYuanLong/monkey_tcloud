import oss2

"""
#  MonkeyConfig
#  所有的配置信息, 是从 jenkins job 中读取过来的信息，在 loader 中进行 构建
"""


class DefaultConfig(object):
    RUN_MODE_MIX = 1
    RUN_MODE_DFS = 2
    RUN_MODE_TROY = 3
    RUN_MODE_OTHER = 4

    MONKEY_MIX_MODE = ' --uiautomatormix '
    MONKEY_DFS_MODE = ' --uiautomatordfs '
    MONKEY_TROY_MODE = '  --uiautomatortroy '

    MONKEY_MODE_KEY_MAP = {
        RUN_MODE_MIX: MONKEY_MIX_MODE,
        RUN_MODE_DFS: MONKEY_DFS_MODE,
        RUN_MODE_TROY: MONKEY_TROY_MODE
    }

    RUN_TIME_DEFAULT = 120  # minutes

    RUN_TIME_SPLIT = 5

    LOCAL_APP_PATH = './packages'  # 本地保存 apk 的路径

    LOCAL_LOGCAT_PATH = './logcat'  # logcat 路径

    KEY_MAP = ['package_name', 'device_id', 'run_time', 'app_download_url', 'run_mode',
               'build_belong', 'task_id', 'system_device', 'login_username',
               'login_password', 'default_app_activity', 'monkey_id', 'login_required',
               'install_app_required']

    ACTIVITY_PATH = 'max.activity.statistics.log'

    TCLOUD_URL = 'http://localhost:8080/v1/monkey'  # Tcloud 对应的地址,可以作为参数传入

    OSS_URL = ''  # OSS url

    OSS_MONKEY_URL = ''  # monkey oss url 存储报告地址

    OSS_AUTH = oss2.Auth('username', 'password')  # oss auth

    OSS_BUCKET_NAME = ''  # oss bucket name


class MonkeyConfig(object):

    def __init__(self):
        self.run_mode = ''
        self.package_name = ''
        self.default_app_activity = ''
        self.run_time = ''
        self.local_package_path = ''
        self.login_required = ''
        self.login_username = ''
        self.login_password = ''
        self.install_app_required = ''
        self.uninstall_app_required = ''

    def constructor(self, config):
        if isinstance(config, dict):
            self.run_mode = config.get('run_mode') or DefaultConfig.RUN_MODE_MIX
            self.run_time = config.get('run_time') or DefaultConfig.RUN_TIME_DEFAULT
            self.default_app_activity = config.get('default_app_activity')
            self.package_name = config.get('package_name')
            self.login_required = config.get('login_required')
            self.login_username = config.get('login_username')
            self.login_password = config.get('login_password')
            self.install_app_required = config.get('install_app_required')
            self.uninstall_app_required = config.get('uninstall_app_required')

    @property
    def info(self):
        return {
            'run_mode': self.run_mode,
            'package_name': self.package_name,
            'default_app_activity': self.default_app_activity,
            'run_time': self.run_time,
            'local_package_path': self.local_package_path,
            'login_required': self.login_required,
            'login_username': self.login_username,
            'login_password': self.login_password,
            'install_app_required': self.install_app_required,
            'uninstall_app_required': self.uninstall_app_required
        }


class PerformanceConfig(object):

    def __init__(self):
        self.run_mode = ''
        self.package_name = ''
        self.default_app_activity = ''
        self.run_time = ''
        self.local_package_path = ''
        self.login_required = ''
        self.login_username = ''
        self.login_password = ''
        self.install_app_required = ''
        self.uninstall_app_required = ''
        self.test_envs = {}

    def constructor(self, config):
        if isinstance(config, dict):
            self.run_mode = config.get('run_mode') or DefaultConfig.RUN_MODE_MIX
            self.run_time = config.get('run_time') or DefaultConfig.RUN_TIME_DEFAULT
            self.default_app_activity = config.get('default_app_activity')
            self.package_name = config.get('package_name')
            self.login_required = config.get('login_required')
            self.login_username = config.get('login_username')
            self.login_password = config.get('login_password')
            self.install_app_required = config.get('install_app_required')
            self.test_envs = config.get('test_config')
            self.uninstall_app_required = config.get('uninstall_app_required')

    @property
    def info(self):
        return {
            'run_mode': self.run_mode,
            'package_name': self.package_name,
            'default_app_activity': self.default_app_activity,
            'run_time': self.run_time,
            'local_package_path': self.local_package_path,
            'login_required': self.login_required,
            'login_username': self.login_username,
            'login_password': self.login_password,
            'install_app_required': self.install_app_required,
            'test_envs': self.test_envs,
            'uninstall_app_required': self.uninstall_app_required
        }
