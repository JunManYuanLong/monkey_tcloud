# import logging
#
# logger = logging.getLogger(__name__)
#
#
# class U2Helper(object):
#     def __init__(self, device_id):
#         self.device_id = device_id
#         self.server = None
#
#     def connect(self):
#         import uiautomator2 as u2
#         self.server = u2.connect(self.device_id)
#
#     def try_to_install_app(self):
#         may_ok_list = '允许'
#         self.server(may_ok_list).click()
