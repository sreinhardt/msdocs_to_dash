#!env python3

import logging
import pytest

from msdocs_to_dash.sqlite import Type

def test_type():
    assert str(Type.Plugin) == "Plugin"
    assert Type.from_str("plugin") == Type.Plugin
    assert Type.from_str("super thingy plugin function macro") == Type.Plugin

def test_default_type():
    assert Type.from_str("Active Directory Domain Services") == Type.Category
    assert Type.from_str("adsprop.h header") == Type.Library