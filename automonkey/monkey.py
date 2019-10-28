from .config import MonkeyConfig
from .device import Device
from .result import MonkeyCaseResult

"""
#  MonkeyCase, 每个 device 对应一个 MonkeyCase
#  monkey_runner 运行的基本单位
"""


class MonkeyCase(object):

    def __init__(self):
        self.config = MonkeyConfig()
        self.device = Device()
        self.result = MonkeyCaseResult()
        self.task_id = ''  # monkey 的 MonkeyDevice数据的 id
        self.monkey_id = ''  # 此次 monkey 的 id
        self.tcloud_url = ''

    def constructor(self, config, device, monkey_id, task_id, tcloud_url):
        if isinstance(config, dict):
            config_dict = config.get('config')
            self.config.constructor(config_dict)
        if isinstance(device, Device):
            self.device = device

        self.task_id = task_id
        self.monkey_id = monkey_id
        self.tcloud_url = tcloud_url

    @property
    def info(self):
        return {
            'config': self.config.info,
            'device': self.device.info,
            'result': self.result.info,
            'task_id': self.task_id,
            'monkey_id': self.monkey_id,
            'tcloud_url': self.tcloud_url
        }
