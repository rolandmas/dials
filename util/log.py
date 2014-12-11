#!/usr/bin/env python
#
# log.py
#
#  Copyright (C) 2013 Diamond Light Source
#
#  Author: James Parkhurst
#
#  This code is distributed under the BSD license, a copy of which is
#  included in the root directory of this package.

from __future__ import division

def config(verbosity=1, info='', debug=''):
  ''' Configure the logging. '''
  import logging.config

  # Debug or not
  if verbosity > 1:
    level = 'DEBUG'
  else:
    level = 'INFO'

  # Set the handlers to use
  if verbosity > 0:
    handlers = ['stream']
  else:
    handlers = []
  if info is not None and info != '':
    handlers.append('file_info')
  else:
    info = 'dials.info.log'
  if debug is not None and debug != '':
    handlers.append('file_debug')
  else:
    debug = 'dials.debug.log'

  # Configure the logging
  logging.config.dictConfig({

    'version' : 1,
    'disable_existing_loggers' : False,

    'formatters' : {
      'standard' : {
        'format' : '%(message)s'
      },
      'extended' : {
        'format' : '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
      },
    },

    'handlers' : {
      'stream' : {
        'level' : level,
        'class' : 'logging.StreamHandler',
        'formatter' : 'standard',
      },
      'file_debug' : {
        'level' : 'DEBUG',
        'class' : 'logging.FileHandler',
        'formatter' : 'standard',
        'filename' : debug,
        'mode' : 'w'
      },
      'file_info' : {
        'level' : 'INFO',
        'class' : 'logging.FileHandler',
        'formatter' : 'standard',
        'filename' : info,
        'mode' : 'w'
      }
    },

    'loggers' : {
      '' : {
        'handlers' : handlers,
        'level' : 'DEBUG',
        'propagate' : True
      }
    }
  })

def config_simple_stdout():
  ''' Configure the logging. '''
  import logging.config

  # Configure the logging
  logging.config.dictConfig({

    'version' : 1,
    'disable_existing_loggers' : False,

    'formatters' : {
      'standard' : {
        'format' : '%(message)s'
      }
    },

    'handlers' : {
      'stream' : {
        'level' : 'DEBUG',
        'class' : 'logging.StreamHandler',
        'formatter' : 'standard',
      }
    },

    'loggers' : {
      '' : {
        'handlers' : ['stream'],
        'level' : 'DEBUG',
        'propagate' : True
      }
    }
  })


class LoggerIO(object):
  ''' Wrap the logger with file type object '''

  def __init__(self, level):
    self.level = level

  def write(self, buf):
    from logging import log
    log(self.level, buf)

  def flush(self):
    pass


def info_handle():
  from logging import INFO
  return LoggerIO(INFO)


def debug_handle():
  from logging import DEBUG
  return LoggerIO(DEBUG)
