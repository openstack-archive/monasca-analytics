#!/usr/bin/env python


class DepCheck(object):
    """Dependency checks."""

    def __init__(self, dep_check):
        self._dep_check = dep_check

    def __call__(self, node):
        res = True
        for dep in node.dependencies:
            res = res and self._dep_check(dep)
        return res and len(node.dependencies) > 0


class AnyDepCheck(object):
    """Dependency checks."""

    def __init__(self, dep_check):
        self._dep_check = dep_check

    def __call__(self, node):
        for dep in node.dependencies:
            if self._dep_check(dep):
                return True
        return False


class TrueCheck(object):
    """This dep check always pass."""

    def __call__(self, *_):
        return True


class EqCheck(object):
    """Check that the node has the appropriate state."""

    def __init__(self, state):
        self._state = state

    def __call__(self, node):
        return node.state == self._state


class NeqCheck(object):
    """Check that the node has the appropriate state."""

    def __init__(self, state):
        self._state = state

    def __call__(self, node):
        return node.state != self._state


class OrCheck(object):
    """Combine two check in an or expression."""

    def __init__(self, c1, c2, c3=None):
        self._c1 = c1
        self._c2 = c2
        self._c3 = c3

    def __call__(self, node):
        if self._c3 is None:
            return self._c1(node) or self._c2(node)
        else:
            return self._c1(node) or self._c2(node) or self._c3(node)


class AndCheck(object):
    """Combine two check in an or expression."""

    def __init__(self, c1, c2):
        self._c1 = c1
        self._c2 = c2

    def __call__(self, node):
        return self._c1(node) and self._c2(node)
