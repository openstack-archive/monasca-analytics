#!/usr/bin/env python

"""A list of functions to validate web_service models."""

import schema


def action_model(value):
    """Validates the data against action_model schema."""
    action_model_schema = schema.Schema({
        "action": schema.And(basestring, lambda o: not o.startswith("_"))
    })

    return action_model_schema.validate(value)
