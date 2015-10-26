__author__ = 'adrien'
import os
import functools
import asyncio

FILES_PATHS = {'raw': '/home/adrien/Documents/tm/raw/', 'compressed': '/home/adrien/Documents/tm/compressed/',
               'imported': '/home/adrien/Documents/tm/imported/', 'home_dir': os.getenv('HOME') + '/'}


def async_call(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        asyncio.async(func(*args, **kwargs))
    return wrapper
