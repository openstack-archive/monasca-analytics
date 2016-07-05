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

# This file is an adaptation of BytecodeAssembler:
#
#   http://peak.telecommunity.com/DevCenter/BytecodeAssembler#toc
#
# It has been adapted to match the requirements of monasca_analytics

import sys


def enclosing_frame(frame=None, level=3):
    """Get an enclosing frame that skips DecoratorTools callback code"""
    frame = frame or sys._getframe(level)
    while frame.f_globals.get('__name__') == __name__:
        frame = frame.f_back
    return frame


def decorate_assignment(callback, depth=2, frame=None):
    """Invoke 'callback(frame,name,value,old_locals)' on next assign in 'frame'

    The frame monitored is determined by the 'depth' argument, which gets
    passed to 'sys._getframe()'.  When 'callback' is invoked, 'old_locals'
    contains a copy of the frame's local variables as they were before the
    assignment took place, allowing the callback to access the previous value
    of the assigned variable, if any.  The callback's return value will become
    the new value of the variable.  'name' is the name of the variable being
    created or modified, and 'value' is its value (the same as
    'frame.f_locals[name]').

    This function also returns a decorator function for forward-compatibility
    with Python 2.4 '@' syntax.  Note, however, that if the returned decorator
    is used with Python 2.4 '@' syntax, the callback 'name' argument may be
    'None' or incorrect, if the 'value' is not the original function (e.g.
    when multiple decorators are used).
    """
    frame = enclosing_frame(frame, depth + 1)
    oldtrace = [frame.f_trace]
    old_locals = frame.f_locals.copy()

    def tracer(frm, event, arg):
        if event == 'call':
            # We don't want to trace into any calls
            if oldtrace[0]:
                # ...but give the previous tracer a chance to, if it wants
                return oldtrace[0](frm, event, arg)
            else:
                return None

        try:
            if frm is frame and event != 'exception':
                # Aha, time to check for an assignment...
                for k, v in frm.f_locals.items():
                    if k not in old_locals or old_locals[k] is not v:
                        break
                else:
                    # No luck, keep tracing
                    return tracer

                # Got it, fire the callback, then get the heck outta here...
                frm.f_locals[k] = callback(frm, k, v, old_locals)

        finally:
            # Give the previous tracer a chance to run before we return
            if oldtrace[0]:
                # And allow it to replace our idea of the "previous" tracer
                oldtrace[0] = oldtrace[0](frm, event, arg)

        uninstall()
        return oldtrace[0]

    def uninstall():
        # Unlink ourselves from the trace chain.
        frame.f_trace = oldtrace[0]
        sys.settrace(oldtrace[0])

    # Install the trace function
    frame.f_trace = tracer
    sys.settrace(tracer)

    def do_decorate(f):
        # Python 2.4 '@' compatibility; call the callback
        uninstall()
        frame = sys._getframe(1)
        return callback(
            frame, getattr(f, '__name__', None), f, frame.f_locals
        )

    return do_decorate
