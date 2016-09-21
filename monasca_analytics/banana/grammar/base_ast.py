#!/usr/bin/env python

# Copyright (c) 2016 Hewlett Packard Enterprise Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import abc
import six


@six.add_metaclass(abc.ABCMeta)
class ASTNode(object):
    """
    Base class of all ast nodes
    """
    def __init__(self, span):
        """
        Construct an ASTNode
        :type span: Span
        :param span: span for this AST node.
        """
        self.span = span

    @abc.abstractmethod
    def into_unmodified_str(self):
        """
        Returns a simple name for this ASTNode. It should be minimalist
        and user oriented. No span info, no debug info.
        :rtype: str
        :returns: A simple name for that ast node.
        """
        pass

    def __ne__(self, other):
        return not self.__eq__(other)


class Span(object):
    """
    Represent a region of code, used for error reporting.
    Position are absolute within the file.
    """

    def __init__(self, text, lo, hi):
        """
        :type text: str | None
        :param text: Full text of the file
        :type lo: int
        :param lo: position of the beginning of the region
        :type hi: int
        :param hi: position of the end of the region
        """
        self._text = text
        self.lo = lo
        self.hi = hi

    def __str__(self):
        if self._text is not None:
            return self._text[self.lo:self.hi]
        else:
            return '?SPAN?'

    def new_with_offset(self, offset):
        """
        Construct a new Span with an offset applied
        to lo.

        :type offset: int
        :param offset: Offset to apply to lo.
        :rtype: Span
        :return: Returns a new span
        """
        return Span(self._text, self.lo + offset, self.hi)

    def str_from_to(self, to_span):
        """
        Returns a string that start at self and stops at to_span.
        :type to_span: Span
        :param to_span: Span to stop at.
        :rtype: basestring
        :return: Returns the string encapsulating both
        """
        return self._text[self.lo:to_span.hi]

    def get_line(self):
        """
        Returns the line for associated with this span.
        """
        if self._text is not None:
            splitted = self._text.splitlines()
            current_pos = 0
            for line in splitted:
                if current_pos < self.lo < len(line) + current_pos:
                    return line.strip()
                else:
                    current_pos += len(line)
        else:
            return '?LINE?'

    def get_lineno(self):
        """
        Returns the line number of this span.
        """
        if self._text is not None:
            splitted = self._text.splitlines()
            current_pos = 0
            lineno = 0
            for _ in xrange(0, len(splitted)):
                line = splitted[lineno]
                if current_pos < self.lo < len(line) + current_pos:
                    return lineno + 1
                else:
                    current_pos += len(line)
                lineno += 1
            return lineno
        else:
            return -1

DUMMY_SPAN = Span(None, 0, 0)


def from_pyparsing_exception(parse_fatal_exception):
    """
    Convert the provided ParseFatalException into a Span.

    :type parse_fatal_exception: pyparsing.ParseBaseException
    :param parse_fatal_exception: Exception to convert.
    :rtype: Span
    :return: Returns the span mapping to that fatal exception.
    """
    return Span(
        parse_fatal_exception.pstr,
        parse_fatal_exception.loc,
        parse_fatal_exception.loc + 1
    )
