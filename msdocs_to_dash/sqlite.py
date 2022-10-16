#!env python3

from dataclasses import dataclass, field
import logging
from enum import Enum, auto
import os
import sys
import regex
import sqlite3
from sqlite3 import Connection, Cursor

@dataclass
class SqLiteDb():
    path: str
    db: Connection = field(init=False,repr=False)
    cur: Cursor = field(init=False,repr=False)

    def __post_init__(self):
        self.db = sqlite3.connect(self.path)
        self.cur = self.db.cursor()
    
    @staticmethod
    def new(path):
        if os.path.exists(path):
            os.remove(path)
        db = SqLiteDb(path)
        db.cur.execute('CREATE TABLE searchIndex(id INTEGER PRIMARY KEY, name TEXT, type TEXT, path TEXT);')
        db.cur.execute('CREATE UNIQUE INDEX anchor ON searchIndex (name, type, path);')
        return db
    
    @staticmethod
    def open(path):
        return SqLiteDb(path)
    
    def close(self):
        self.db.commit()
        self.db.close()
    
    def insert(self, name, rec_type, path):
        if not isinstance(name, str):
            name = str(name)
        if not isinstance(rec_type, str):
            rec_type = str(rec_type)
        if not isinstance(path, str):
            path = str(path)
        # was try/excepted without catching anything
        self.cur.execute('SELECT rowid FROM searchIndex WHERE path = ?', (path,))
        dbpath = self.cur.fetchone()
        self.cur.execute('SELECT rowid FROM searchIndex WHERE name = ?', (name,))
        dbname = self.cur.fetchone()

        if dbpath is None and dbname is None:
            self.cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?,?,?)', (name, rec_type, path))
            logging.info(f"Created {name} record")
        else:
            logging.debug(f'{name} record exists')

class Type(Enum):
    Annotation = auto()
    Attribute = auto()
    Binding = auto()
    Builtin = auto()
    Callback = auto()
    Category = auto()
    Class = auto()
    Command = auto()
    Component = auto()
    Constant = auto()
    Constructor = auto()
    Define = auto()
    Delegate = auto()
    Diagram = auto()
    Directive = auto()
    Element = auto()
    Entry = auto()
    Enum = auto()
    Environment = auto()
    Error = auto()
    Event = auto()
    Exception = auto()
    Extension = auto()
    Field = auto()
    File = auto()
    Filter = auto()
    Framework = auto()
    Function = auto()
    Global = auto()
    Guide = auto()
    Hook = auto()
    Instance = auto()
    Instruction = auto()
    Interface = auto()
    Keyword = auto()
    Library = auto()
    Literal = auto()
    Macro = auto()
    Method = auto()
    Mixin = auto()
    Modifier = auto()
    Module = auto()
    Namespace = auto()
    Notation = auto()
    Object = auto()
    Operator = auto()
    Option = auto()
    Package = auto()
    Parameter = auto()
    Plugin = auto()
    Procedure = auto()
    Property = auto()
    Protocol = auto()
    Provider = auto()
    Provisioner = auto()
    Query = auto()
    Record = auto()
    Resource = auto()
    Sample = auto()
    Section = auto()
    Service = auto()
    Setting = auto()
    Shortcut = auto()
    Statement = auto()
    Struct = auto()
    Style = auto()
    Subroutine = auto()
    Tag = auto()
    Test = auto()
    Trait = auto()
    Type = auto()
    Union = auto()
    Value = auto()
    Variable = auto()
    Word = auto()

    def __str__(self):
        return self.name
    
    @staticmethod
    def from_str(text):
        # MS seems to layer names, such as "callback function"
        # so we need to search for individual words that match names
        # and see which is left-most to the start of the string
        match = (sys.maxsize,None)
        for member in Type.__members__.items(): # (name, variant)
            # allow icase, plural, and mid/end of line
            found = regex.search(f"(^|\s){member[0]}s?(\s|$)", text, regex.IGNORECASE)
            if found and found.start() < match[0]:
                match = (found.start(), member[1]) # (int, variant)
        return match[1] # variant or None
    
    @staticmethod
    def default():
        return Type.Category

