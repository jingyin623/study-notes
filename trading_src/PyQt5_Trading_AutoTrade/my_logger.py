"""
顶级配置项:
version
formatters
filters
handlers
loggers
root
incremental
disable_existing_loggers
"""

import datetime
import os
import logging
import logging.config


def genLogDict(pathname=None):
    if pathname:
        LOGGING_DIR = pathname + "/logs/"  # 日志存放路
        if not os.path.exists(LOGGING_DIR):
            os.mkdir(LOGGING_DIR)
    else:
        LOGGING_DIR = os.path.dirname(__file__) + "/logs/"  # 日志存放路
        if not os.path.exists(LOGGING_DIR):
            os.mkdir(LOGGING_DIR)
    # 日志配置
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        # 格式化器
        'formatters': {
            'standard': {
                'format': '[%(levelname)5s] [%(asctime)s] [%(filename)8s] [%(lineno)3d] > %(message)s'
            },
            'simple': {
                'format': '[%(levelname)5s] [%(asctime)s] > %(message)s'
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'standard'
            },
            'file_handler': {
                 'level': 'DEBUG',
                 'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename': '%s/mylog%s.log' % (LOGGING_DIR, datetime.datetime.today().date()),  # 具体日志文件的名字
                 'formatter': 'standard'
            },
            'analyze': {
                'level': 'DEBUG',
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename': '%s/analyzeData%s.log' % (LOGGING_DIR, datetime.datetime.today().date()),  # 具体日志文件的名字
                'formatter': 'simple'   # simple
            }
        },
        # 日志记录器
        'loggers': {   # 日志分配到哪个handlers中
            'my_logger': {	 # 后面导入时logging.getLogger使用的app_name
                'handlers': ['console', 'file_handler'],
                'level': 'INFO',
                'propagate': True,
            },
            'my_logger1': {  # 后面导入时logging.getLogger使用的app_name
                'handlers': ['analyze'],
                'level': 'INFO',
                'propagate': True,
            }
        }
    }

    return LOGGING


def initLogConf(pathname=None):
    """
    配置日志
    """
    logDict = genLogDict(pathname)
    logging.config.dictConfig(logDict)

