#!/usr/bin/env python3
""" match """

from enum import Enum
import sys

# There are two kinds of variables.
# Element variables match a single element of a list.
# Segment variables match a (perhaps empty) piece of a list.
# Element variables have the form ($ <var name> <optional restriction>)
# where <var name> is a symbol, and the restriction is a one-place
# procedure which returns True if the potential binding satisfies it.
# Segment variables are like element variables, but start with $$


class Variables():
    Element = '$'
    Segment = '$$'

class Bindings(Enum):
    Fail = 1

def isElementVar(x):
    # print("isElementVar: %s is %s" %(x, isinstance(x, list) and len(x) > 0 and x[0] == Variables.Element))
    return isinstance(x, list) and len(x) > 0 and x[0] == Variables.Element

def isSegmentVar(x):
    return isinstance(x, list) and len(x) > 0 and x[0] == Variables.Segment

def variableRestriction(x):
    if isinstance(x, list) and len(x) == 3:
        return x[2]
    return None

def bind_element_variable(var, value, mybindings):
    mybindings[var] = value
    return mybindings

def bind_segment_variable(var, begin, end, mybindings):
    mybindings[var] = tuple(begin, end)

def lookup(var, mybindings):
    # print("lookup %s in %s" %(var, mybindings))
    val = mybindings.get(var)
    return val

def variable_name(pat):
    return pat[1]

def match(pattern, data):
    bindings = {}
    return match_lst(pattern, data, bindings)

def match_lst(pattern, data, bindings):
    # print("match_lst: \n\t%s \n\t%s \n\t%s" %(pattern, data, bindings))
    if bindings == Bindings.Fail:
        return bindings
    if pattern == data:
        return bindings
    if not isinstance(pattern, list):
        return Bindings.Fail
    if isElementVar(pattern):
        return match_lst_element_var(pattern, data, bindings)
    if isSegmentVar(pattern[0]):
        return match_lst_pattern_var(pattern, data, bindings)
    nextBindings = match_lst(pattern[0], data[0], bindings)
    # print("match_lst nextBindings: %s" %(nextBindings))
    return match_lst(pattern[1:], data[1:], nextBindings)

def match_lst_element_var(pattern, data, bindings):
    # print("match_lst_element_var: \n\t%s\n\t%s\n\t%s" %(pattern, data, bindings))
    var = variable_name(pattern)
    entry = lookup(var, bindings)
    if entry is not None:
        return bindings if entry == data else Bindings.Fail
    predicate = variableRestriction(pattern)
    if predicate is None or funcall(predicate, data):
        return bind_element_variable(var, data, bindings)
    return Bindings.Fail

def match_lst_segment_var(pattern, data, bindings):
    var = variable_name(pattern)
    entry = lookup(var, bindings)
    if entry is None:
        return bind_segment_variable(variable_name(pattern), data, bindings)
    if entry == data:
        return bindings
    return Bindings.Fail

def funcall(predicate, data):
    # print("funcall: %s" % predicate)
    if hasattr(predicate, '__call__'):
        # print("Calling: %s" % predicate)
        result = predicate(data)
    else:
        txt = "{predicate}(\"{data}\")".format(predicate=predicate, data=data)
        # print("Eval: %s" % txt)
        result = eval(txt)
    return result

def makePredicate(func, arg1):
    def single(x):
        return func(arg1, x)
    return single

def predicateTrue(x):
    # print("called predicateTrue with %s" % x)
    return True

def greater(x, y):
    # print("called greater with %s %s" % (x, y))
    return x > y

def test1():
    pat = ['a', ['$', 'x'], 'c']
    dat = ['a', 'b', 'c']
    bindings = match(pat, dat)
    assert lookup('x', bindings) == 'b'
    pat = ['a', ['$', 'x'], ['$', 'x']]
    dat = ['a', 'b', 'c']
    bindings = match(pat, dat)
    assert bindings == Bindings.Fail
    pat = ['a', ['b', ['$', 'x']], ['$', 'x']]
    dat = ['a', ['b', 'c'], 'c']
    bindings = match(pat, dat)
    assert lookup('x', bindings) == 'c'
    pat = ['a', ['$', 'x', 'predicateTrue'], ['$', 'x']]
    dat = ['a', 'b', 'b']
    bindings = match(pat, dat)
    assert lookup('x', bindings) == 'b'
    lessThan20 = makePredicate(greater, 20)
    lessThan1 = makePredicate(greater, 1)
    pat = ['a', ['$', 'x', lessThan20], 'b']
    dat = ['a', 10, 'b']
    bindings = match(pat, dat)
    assert lookup('x', bindings) == 10
    pat = ['a', ['$', 'x', lessThan1], 'b']
    bindings = match(pat, dat)
    assert bindings == Bindings.Fail
    

if __name__ == "__main__":
    test1()