from argparse import Namespace

from .case import Case

"""
#  Loader ： 将参数转化为 Config， 并构建 Case
"""


class Loader(object):

    def __init__(self):
        self.params = {
            'monkey_id': '',
            'device': [],
            'monkey': {
                'config': {}
            },
            'config': {}
        }

    def parse_args_to_dict(self, args):
        if isinstance(args, Namespace):
            self.params['monkey_id'] = args.monkey_id
            self.params['task_ids'] = args.task_id
            self.params['tcloud_url'] = args.tcloud_url

            self.params['build_belong'] = args.build_belong
            self.params['app_download_url'] = args.app_download_url
            self.params['test_type'] = args.test_type
            # 构建 case dict
            self.params['case'] = {
                'config': {
                    'run_mode': args.run_mode,
                    'package_name': args.package_name,
                    'app_download_url': args.app_download_url,
                    'default_app_activity': args.default_app_activity,
                    'run_time': args.run_time,
                    'login_required': args.login_required,
                    'login_password': args.login_password,
                    'login_username': args.login_username,
                    'install_app_required': args.install_app_required,
                    'test_config': args.test_config
                }
            }

            self.params['devices'] = [
                {'device_id': id, 'system_device': args.system_device} for id in
                args.device_id
            ]

    def constructor_case(self):
        case = Case()
        case.constructor(self.params)
        return case

    def run(self, args):
        self.parse_args_to_dict(args)
        return self.constructor_case()
