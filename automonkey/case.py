from automonkey.performance import PerformanceCase
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
        self.cases = []
        self.case_type = 1
        self.monkey_id = ''
        self.task_ids = ''
        self.app_download_url = ''
        self.tcloud_url = ''
        self.result = CaseResult()
        self.test_config = ''

    def constructor(self, inputs):
        self.monkey_id = inputs.get('monkey_id')
        self.task_ids = inputs.get('task_ids')
        self.app_download_url = inputs.get('app_download_url')
        self.tcloud_url = inputs.get('tcloud_url')

        for device_dict in inputs.get('devices'):
            device = Device()
            device.constructor(device_dict)
            if inputs.get('test_type') == 'monkey':
                self.case_type = 1
            elif inputs.get('test_type') == 'performance':
                self.case_type = 2
            for device_dict in inputs.get('devices'):
                device = Device()
                device.constructor(device_dict)
                if self.case_type == 1:
                    case = MonkeyCase()
                elif self.case_type == 2:
                    case = PerformanceCase()

                case.constructor(inputs.get('case'), device, self.monkey_id, self.task_ids.get(device.device_id),
                                 self.tcloud_url)
                self.cases.append(case)

    @property
    def info(self):
        return {
            'cases': [monkey.info for monkey in self.cases],
            'result': self.result.info,
            'monkey_id': self.monkey_id,
            'task_ids': self.task_ids,
            'app_download_url': self.app_download_url,
            'tcloud_url': self.tcloud_url,
            'case_type': self.case_type
        }

    def bind_local_package_to_monkey(self, local_package_path):
        for monkey in self.cases:
            monkey.config.local_package_path = local_package_path
