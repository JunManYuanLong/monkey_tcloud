import logging

from .config import DefaultConfig
from .loader import Loader
from .recorder import Recorder
from .runner import Runner
from .utils import Utils

logger = logging.getLogger(__name__)

"""
#  ProgramMain 主程序
#  通过 Loader 解析参数 构建 CaseConfig 和 MonkeyConfig
#  通过 Config 构建 Case 和
#  启动和控制 runner 的运行
#  通过 Recorder 解析 CaseResult
#  通过 ...
"""


class ProgramMain(object):

    def __init__(self):
        self.loader = Loader()
        self.runner = Runner()
        self.recorder = Recorder()

    def run(self, args):
        self.show_args_info(args)
        case = self.loader.run(args)
        logger.info(case.info)
        self.runner.run(case)

    def show_args_info(self, args):
        keys = ["parameters id", "key", "Value"]
        values = []
        for i, arg in enumerate(DefaultConfig.KEY_MAP):
            row = [i, arg, getattr(args, arg)]
            values.append(row)
        Utils.show_info_as_table(keys, values)
