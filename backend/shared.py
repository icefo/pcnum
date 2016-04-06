import os
import functools
import asyncio
import time


# FILES_PATHS = dict(raw='/media/storage/raw/', compressed='/media/storage/compressed/',
#                    imported='/media/storage/imported/', DVDs='/media/storage/DVDs/',
#                    home_dir=os.getenv('HOME') + '/')

FILES_PATHS = dict(raw='/home/adrien/Documents/tm/raw/', compressed='/home/adrien/Documents/tm/compressed/',
                   imported='/home/adrien/Documents/tm/imported/', DVDs='/home/adrien/Documents/tm/DVDs/',
                   home_dir=os.getenv('HOME') + '/')


def wrap_in_future(func):
    """
    Wrap the function in asyncio.async to make launching async function from blocking function possible

    Args:
        func (function):

    Returns:
        function: wrapper around func
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        asyncio.async(func(*args, **kwargs))
    return wrapper


class TimedKeyDeleteDict(dict):
    """
    This dictionary behave like a normal dictionary except that it deletes key that are older that the timeout set on
     instantiation when they are accessed.

    Notes:
        inspiration: http://stackoverflow.com/questions/3927166/automatically-expiring-variable -- Ant
        inspiration: http://stackoverflow.com/questions/16136979/set-class-with-timed-auto-remove-of-elements -- A. Rodas

    Warnings:
        the 'setdefault' method is not implemented
    """
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

    def get(self, k, d=None):
        key = self.__getitem__(k)
        if key:
            return key
        else:
            return d

    def __iter__(self):
        to_delete = []

        for key in dict.__iter__(self):
            if time.time() < self.__expire_table.get(key, False):
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
        if dict.__contains__(self, key) and time.time() < self.__expire_table.get(key, False):
            return True
        elif dict.__contains__(self, key):
            dict.__delitem__(self, key)
            del self.__expire_table[key]
            return False
        elif self.raise_error:
            raise KeyError(key)

    def __getitem__(self, key):
        if key in self and time.time() < self.__expire_table.get(key, False):
            return dict.__getitem__(self, key)
        elif key in self:
            dict.__delitem__(self, key)
            del self.__expire_table[key]

    def __len__(self):
        for _ in self.__iter__():
            pass
        self.keys()
        return dict.__len__(self)

    def copy(self):
        return self.__class__(self)

    def setdefault(self, key, default=None):
        raise NotImplementedError()
