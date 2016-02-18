#!/usr/bin/env python


class Singleton(type):
    """A singleton metaclass."""

    _instances = {}

    def __call__(self, *args, **kwargs):
        if self not in self._instances:
            self._instances[self] = super(Singleton, self).__call__(*args,
                                                                    **kwargs)
        return self._instances[self]
