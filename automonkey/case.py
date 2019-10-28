from .device import Device
from .monkey import MonkeyCase
from .result import CaseResult

"""
#  运行的 Case
#  runner 运行的基本操作单位
"""


class Case(object):

    def __init__(self):
        self.name = ''
        self.monkey_cases = []
        self.monkey_id = ''
        self.task_ids = ''
        self.app_download_url = ''
        self.tcloud_url = ''
        self.result = CaseResult()

    def constructor(self, inputs):
        self.monkey_id = inputs.get('monkey_id')
        self.task_ids = inputs.get('task_ids')
        self.app_download_url = inputs.get('app_download_url')
        self.tcloud_url = inputs.get('tcloud_url')

        for device_dict in inputs.get('devices'):
            device = Device()
            device.constructor(device_dict)

            monkey = MonkeyCase()
            monkey.constructor(inputs.get('monkey'), device, self.monkey_id, self.task_ids.get(device.device_id),
                               self.tcloud_url)

            self.monkey_cases.append(monkey)

    @property
    def info(self):
        return {
            'monkey_cases': [monkey.info for monkey in self.monkey_cases],
            'result': self.result.info,
            'monkey_id': self.monkey_id,
            'task_ids': self.task_ids,
            'app_download_url': self.app_download_url,
            'tcloud_url': self.tcloud_url
        }

    def bind_local_package_to_monkey(self, local_package_path):
        for monkey in self.monkey_cases:
            monkey.config.local_package_path = local_package_path
