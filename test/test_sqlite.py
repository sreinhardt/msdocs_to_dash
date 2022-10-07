#!env python3

import logging
import pytest

from msdocs_to_dash.sqlite import Type

def test_type():
    assert str(Type.Plugin) == "Plugin"
    assert Type.from_str("plugin") == Type.Plugin
    assert Type.from_str("super thingy plugin function macro") == Type.Plugin