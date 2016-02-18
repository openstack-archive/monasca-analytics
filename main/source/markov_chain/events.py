#!/usr/bin/env python


class Trigger(object):
    """A trigger generate events when a particular graph state is reached."""

    def __init__(self, node_check, prob_check, event_builder):
        """Create a new trigger.

        :param node_check: function (main.source.markov_chain.base.StateNode)
        -> bool -- Checker function that will return true if the node has an
        appropriate type
        :param prob_check: function (int) -> bool -- A probability check that
        can return true or false with a random chance
        :param event_builder: function (main.source.markov_chain.base.
        StateNode)-> Event -- Event builder that receive the node and use
        the state to return an event.
        """
        self._prob_check = prob_check
        self._node_check = node_check
        self._event_builder = event_builder

    def apply_on(self, node, hour_of_day):
        """
        :param node: main.source.markov_chain.base.StateNode
        :param hour_of_day: int
        """
        if self._prob_check(hour_of_day) and self._node_check(node):
            return self._event_builder(node)
        return None


class Event(object):

    def __init__(self, msg, ident):
        """
        :param msg: str
        :param ident: str
        """
        self.id = ident
        self.msg = msg


class EventBuilder(object):

    def __init__(self, msg):
        """
        :param msg: str
        """
        self._msg = msg

    def __call__(self, node):
        """
        :param node: main.source.markov_chain.base.StateNode
        """
        return Event(self._msg, str(node.id()))
