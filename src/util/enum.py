'''
Created on 2009-12-28

@author: vsekhar

Adapted from http://code.activestate.com/recipes/67107/
'''

import types, string

class EnumException(Exception):
    pass

class Enum(object):
    '''
    An enumeration class to emulate C-style enums
    '''

    def __init__(self, name, enumList):
        self.__doc__ = name
        lookup = { }
        reverseLookup = { }
        uniqueNames = [ ]
        self._uniqueValues = uniqueValues = [ ]
        self._uniqueId = 0
        for x in enumList:
            if type(x) == tuple:
                x, i = x
                if type(x) != bytes:
                    raise EnumException("enum name is not a string: " + x)
                if type(i) != int:
                    raise EnumException("enum value is not an integer: " + i)
                if x in uniqueNames:
                    raise EnumException("enum name is not unique: " + x)
                if i in uniqueValues:
                    raise EnumException("enum value is not unique for " + x)
                uniqueNames.append(x)
                uniqueValues.append(i)
                lookup[x] = i
                reverseLookup[i] = x
        for x in enumList:
            if type(x) != tuple:
                if type(x) != str:
                    raise EnumException("enum name is not a string: " + x)
                if x in uniqueNames:
                    raise EnumException("enum name is not unique: " + x)
                uniqueNames.append(x)
                i = self.generateUniqueId()
                uniqueValues.append(i)
                lookup[x] = i
                reverseLookup[i] = x
        self.lookup = lookup
        self.reverseLookup = reverseLookup
    def generateUniqueId(self):
        while self._uniqueId in self._uniqueValues:
            self._uniqueId += 1
        n = self._uniqueId
        self._uniqueId += 1
        return n
    def __getattr__(self, attr):
        if attr not in self.lookup:
            raise AttributeError
        return self.lookup[attr]
    
    def __contains__(self, key):
        return (key in self.lookup)
    
    def whatis(self, value):
        return self.reverseLookup[value]
