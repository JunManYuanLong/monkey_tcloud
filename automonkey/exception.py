class MonkeyBaseException(Exception):
    pass


class MonkeyTypeErrorException(MonkeyBaseException):
    pass


class FileDownloadErrorException(MonkeyBaseException):
    pass


class CaseBaseException(Exception):
    pass


class CaseTypeErrorException(CaseBaseException):
    pass


class DeviceNotConnectedException(Exception):
    pass


class LocalPackageNotFoundException(Exception):
    pass


class SetUpErrorException(Exception):
    pass


class InstallAppException(Exception):
    pass


class CheckScreenLockedFailed(Exception):
    pass
