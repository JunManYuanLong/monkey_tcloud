import logging
import traceback

from .adb import AdbTool
from .exception import DeviceNotConnectedException

logger = logging.getLogger(__name__)

"""
#  设备操作
#  包括 连接设备， 断开设备
#  其他
"""


class Device(object):

    def __init__(self):
        self.device_id = ''
        self.system_device = True
        self.adb_tool = None

    def constructor(self, config, ):
        self.device_id = config.get('device_id')
        self.system_device = config.get('system_device')
        self.adb_tool = AdbTool(self.device_id)

    @property
    def info(self):
        return {
            'device_id': self.device_id,
            'system_device': self.system_device,
        }

    def connect(self):
        try:
            # connect stuff
            logger.info('开始连接设备 {}'.format(self.device_id))
            adb_version = self.adb_tool.get_adb_version()
            logger.info('Adb Version is : {}'.format(adb_version))
            all_devices = self.adb_tool.get_device_list()
            logger.info('all devices : {} '.format(all_devices))

            if self.adb_tool.check_device_connected(self.device_id):
                logger.info('设备 {} 连接成功！'.format(self.device_id))
                return True
            else:
                logger.info('设备 {} 不在设备列表中!'.format(self.device_id))
                raise DeviceNotConnectedException
        except DeviceNotConnectedException as device_error:
            logger.error(device_error)
            return device_error
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())
            return False

    def disconnect(self):
        try:
            # connect stuff
            # TODO: need disconnect or not???
            pass

        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())
