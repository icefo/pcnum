__author__ = 'adrien'
import os
import functools
import asyncio
import time

FILES_PATHS = {'raw': '/home/adrien/Documents/tm/raw/', 'compressed': '/home/adrien/Documents/tm/compressed/',
               'imported': '/home/adrien/Documents/tm/imported/', 'home_dir': os.getenv('HOME') + '/'}


def async_call(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        asyncio.async(func(*args, **kwargs))
    return wrapper


# inspiration: http://stackoverflow.com/questions/3927166/automatically-expiring-variable -- Ant
# inspiration: http://stackoverflow.com/questions/16136979/set-class-with-timed-auto-remove-of-elements -- A. Rodas
class AutoKeyDeleteDict(dict):
    def __init__(self, timeout, raise_error=False):
        dict.__init__(self)
        self.timeout = timeout
        self.raise_error = raise_error
        self.__expire_table = {}

    def keys(self):
        for key in self.__iter__():
            yield key

    def values(self):
        for key in self.__iter__():
            yield dict.__getitem__(self, key)

    def items(self):
        for key in self.__iter__():
            yield key, dict.__getitem__(self, key)

    def __iter__(self):
        to_delete = []

        for key in dict.__iter__(self):
            if time.time() < self.__expire_table.get(key, 0):
                yield key
            else:
                to_delete.append(key)

        for key in to_delete:
            dict.__delitem__(self, key)
            del self.__expire_table[key]

    def __setitem__(self, key, value, timeout=None):
        dict.__setitem__(self, key, value)
        if not timeout:
            timeout = self.timeout
        self.__expire_table[key] = time.time() + timeout

    def __delitem__(self, key):
        if key in self:
            dict.__delitem__(self, key)
            del self.__expire_table[key]

    def pop(self, key, d=None):
        if key in self:
            result = self[key]
            dict.__delitem__(self, key)
            del self.__expire_table[key]
            return result

    def __contains__(self, key):
        if dict.__contains__(self, key) and time.time() < self.__expire_table.get(key, 0):
            return True
        elif dict.__contains__(self, key):
            dict.__delitem__(self, key)
            del self.__expire_table[key]
            return False
        elif self.raise_error:
            raise KeyError(key)

    def __getitem__(self, key):
        if key in self:
            return dict.__getitem__(self, key)

    def __len__(self):
        self.keys()
        return dict.__len__(self)

    def copy(self):
        return self.__class__(self)

    def setdefault(self, key, default=None):
        raise NotImplementedError()
