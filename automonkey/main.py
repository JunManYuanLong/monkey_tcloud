#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import logging
import traceback

from .program import ProgramMain

logger = logging.getLogger(__name__)

"""
#  main
"""


def main():
    arg_program = argparse.ArgumentParser(prog='python -m automonkey', add_help=True)

    sub_all_arg_program = arg_program.add_subparsers(dest='all')

    sub_run_arg_program = sub_all_arg_program.add_parser(
        'run',
        help='run monkey with args'
    )

    sub_run_arg_program.add_argument('--package-name', '-pn', dest='package_name', type=str)
    sub_run_arg_program.add_argument('--device-name', '-dn', dest='device_id', type=str)
    sub_run_arg_program.add_argument('--run-time', '-rt', dest='run_time', type=int)
    sub_run_arg_program.add_argument('--app-download-url', '-adu', dest='app_download_url', type=str)
    sub_run_arg_program.add_argument('--run-mode', '-rm', dest='run_mode', type=str)
    sub_run_arg_program.add_argument('--build-belong', '-bb', dest='build_belong', type=str)
    sub_run_arg_program.add_argument('--install-app-required', '-iar', dest='install_app_required', type=str)
    sub_run_arg_program.add_argument('--uninstall-app-required', '-uiar', dest='uninstall_app_required', type=str)
    sub_run_arg_program.add_argument('--system-device', '-sd', dest='system_device', type=str)
    sub_run_arg_program.add_argument('--login-required', '-lr', dest='login_required', type=str)
    sub_run_arg_program.add_argument('--login-username', '-lu', dest='login_username', type=str)
    sub_run_arg_program.add_argument('--login-password', '-lp', dest='login_password', type=str)
    sub_run_arg_program.add_argument('--default-app-activity', '-daa', dest='default_app_activity', type=str)
    sub_run_arg_program.add_argument('--task-id', '-tid', dest='task_id', type=str)
    sub_run_arg_program.add_argument('--monkey-id', '-mid', dest='monkey_id', type=str)
    sub_run_arg_program.add_argument('--tcloud-url', '-turl', dest='tcloud_url', type=str)
    sub_run_arg_program.add_argument('--test-type', '-ttype', dest='test_type', type=str)
    sub_run_arg_program.add_argument('--test-config', '-tconfig', dest='test_config', type=str)

    try:
        args = arg_program.parse_args()
        if hasattr(args, 'device_id') and args.device_id:
            devices = args.device_id.split(',')
            args.device_id = devices
        else:
            logger.error('missing device_id !')
        if hasattr(args, 'task_id') and args.task_id:
            task_ids = args.task_id.split(',')
            args.task_id = {}
            for i, device in enumerate(args.device_id):
                args.task_id[device] = task_ids[i]
        else:
            logger.error('missing task_id !')

        if hasattr(args, 'install_app_required'):
            args.install_app_required = args.install_app_required in ["true", "True"]

        if hasattr(args, 'system_device'):
            args.system_device = args.system_device in ["true", "True"]

        if hasattr(args, 'login_required'):
            args.login_required = args.login_required in ["true", "True"]

        if hasattr(args, 'uninstall_app_required'):
            args.login_required = args.login_required in ["true", "True"]

        logger.info(args)
        program = ProgramMain()
        program.run(args)

    except Exception as e:
        logger.error(e)
        traceback.print_exc()
