#!/usr/bin/env python3
""" parsing Tem and Pattern objects"""

import random
import sys

sys.path.insert(0, '/Users/rachaelkim/Desktop/Pisan_AI project/rip-1/jtms')
from jtms import *


VARIABLE_CHAR = '#'
VARIABLE_CHAR2 = '?'

# A term is a symbol or a list of symbols
# x, [x, y [w, a]]
class Term():
    def __init__(self, astr):
        self.data = parse(astr)
        self.isSymbol = not isinstance(self.data, list)

    def __str__(self):
        if len(self.data) == 0:
            return "T<" + self.data[0] + ">"
        return "T<" + list2sentence(self.data) + ">"

    def get(self, i):
        return self.data[i]
    
    def set(self, i, val):
        self.data[i] = val
        
    # bindings should remain {} but kept for compatibility
    def match(self, other):
        return self.data == other.data, {}

# convert [a, b] to (a b)
def list2str(alist):
    if not isinstance(alist, list):
        return str(alist)
    out = "("
    if len(alist) > 0:
        out += list2str(alist[0])
    for i in range(1, len(alist)):
        out += " "
        out += list2str(alist[i])
    out += ")"
    return out

# convert [a, b] to ( a is b )
def list2sentence(alist):
    if not isinstance(alist, list):
        return str(alist)
    #out = "("
    out = ""
    if len(alist) > 0:
        out += list2sentence(alist[0])
    for i in range(1, len(alist)):
        if i == 1 :
            out += " is"
        out += " "
        out += list2sentence(alist[i])
    #out += ")"
    return out


class Pattern(Term):
    def __init__(self, astr):
        super().__init__(astr)

    def match(self, other):
        bindings = {}
        if (isinstance(other, TMS_Node)):
            return match_pat(self.data, other.datum, bindings)
        return match_pat(self.data, other.data, bindings)


# ($ x python-function)
def iscomplex_pattern(lst):
    return len(lst) == 3 and lst[0] == VARIABLE_CHAR

def get_complex_var(lst):
    return VARIABLE_CHAR + lst[1]

def get_complex_func(lst):
    return lst[2]

def make_callable_str(func, param):
    return func + "(" + "'" + param + "'" + ")"

# changing optional variable from bin to bindings
# creates bizzare error where after matching $a to xyz
# the bindings persist
def match_pat(pat1, term1, bindings):
    # print("Attempt match_pat %s %s %s" % (s1, s2, bindings))
    if pat1 == term1:
        return True, bindings
    if iscomplex_pattern(pat1):
        # match complex pattern and check
        var = get_complex_var
        v1 = lookup(var, bindings)
        if v1 is not None and v1 != term1:
            return False, {}
        bound = term1 if v1 is None else v1
        # call python function on matched term
        func = get_complex_func(pat1)
        cmd = make_callable_str(func, bound)
        result = eval(cmd)
        if not result:
            return False, {}
        if v1 is None:
            addbinding(variable_name, term1, bindings)
        return True, bindings          
    if isinstance(pat1, list) and isinstance(term1, list):
        # go through both lists
        if len(pat1) != len(term1):
            return False, {}
        for (x, y) in zip(pat1, term1):
            if not match_pat(x, y, bindings)[0]:
                return False, {}
        return True, bindings
    if not isinstance(pat1, list):
        # match variable to symbol or list
        if not isvariable(pat1):
            return pat1 == term1, bindings
        v1 = lookup(pat1, bindings)
        bindings[pat1] = term1
        if v1 == term1 or (v1 is not None) :  #and not addbinding(pat1, term1, bindings)):
            return True, bindings
        return False, {}
    # one is list and the other is not
    return False, {}


def addbinding(var, val, mybindings):
    assert isvariable(var) and not isvariable(val) 
    # print("Adding binding %s ==> %s" % (var, val))
    mybindings[var] = val
    return val


def lookup(var, mybindings):
    assert isvariable(var)
    val = var[1:]

    return val


# x ==> x AND set isSymbol true
# (x) ==> [x]
# (x a) ==> [x a]
# (x a (b c)) ==> [x a [b c]]
# (x (w y) z (b c)) ==> [x [w y] z [b c]]
# should numbers be treated as special, for now NO

def parse(astr):
    astr = astr.strip()
    if len(astr) == 0:
        raise SyntaxError("{} empty string parse: {} ".format(__file__, astr))
    if astr[0] == '(' and astr[-1] == ')':
        return parse_tuple(astr)
    if isidorvar(astr[0]):
        startparen = astr.find('(')
        if startparen == -1:
            return parse_string(astr)
        else:
            term1 = parse(astr[0:startparen])
            rest = parse(astr[startparen:])
            return [term1, rest]
    raise SyntaxError("{} parse: {} ".format(__file__, astr))


def find_matching_endparen(astr, start):
    assert astr[start] == '(' and astr.find(')', start) != -1
    index = start
    parens = 0
    while index < len(astr):
        ch = astr[index]
        if ch == '(':
            parens += 1
        if ch == ')':
            parens -= 1
            if parens == 0:
                count = start
                while count < index:
                    count += 1
                return index
        index += 1
    return -1

# () ==> []
# (a, b) ==> [a, b]
# (a, (b, c)) ==> [a, [b , c]]
def parse_tuple(astr):
    assert astr[0] == '(' and astr[-1] == ')'
    out = []
    start = 1
    current = 1
    finish = len(astr)
    # read up to , ( )
    while current < finish:
        ach = astr[current]
        # TODO: simplify
        if ach.isalpha() or ach == VARIABLE_CHAR or ach in "0123456789.-+?":
            current += 1
            continue
        if ach == ')' or ach == ' ':
            if (start != current):
                out.append(parse(astr[start:current]))
            current += 1
            start = current
            if ach == ')' and current < finish:
                raise SyntaxError("{} parse_tuple: {} ".format(__file__, astr))
            continue
        if ach == '(':
            if (start != current):
                out.append(parse(astr[start:current]))
            endparen = find_matching_endparen(astr, current)
            # endparen = astr.find(')', current)
            if endparen == -1:
                raise SyntaxError("{} parse_tuple: {} ".format(__file__, astr))
            out.append(parse(astr[current:endparen+1]))
            current = endparen + 1
            start = current
            continue
        raise SyntaxError("{} unexpected character {} in parse_tuple: {} ".format(__file__, ach, astr))
    return out


def parse_string(astr):
    bad_chars = [ch for ch in astr if not isidorvar(ch)]
    if bad_chars:
        raise SyntaxError("{} bad_chars %s parse_string: {} ".format(__file__, bad_chars, astr))
    return astr


def isidorvar(ch):
    return ch == VARIABLE_CHAR or isidentifier(ch) or ch == VARIABLE_CHAR2


def isidentifier(ch):
    return ch.isalnum() or ch in ".-+" or ch == "_"


def isvariable(astr):
    return len(astr) > 1 and astr[0] == VARIABLE_CHAR or VARIABLE_CHAR2

def test2():
    t1 = Term ("(rule (Graduate-Student ?x) (assert (and (Underpaid ?x) (Overworked ?x)))) ")
    print(t1)
    p1 = Pattern("Graduate-Student Robbie")
    print(str(p1.match(t1)))



def run_tests():
    """
    for s in ["xabc", "(x a b)", "  (  ) ", "(a b c)", "(x (y z))",
              "(q (w e) r    s t    (    y  uwx)   )    ", "(a (  ))", "(a (23 b))"]:
        print("\t%s ==> %s" % (s, parse(s)))
    t1 = Term("(a (23 b))")
    t2 = Term("(a (23 b))")
    print("t1 matches itself: %s" % str(t1.match(t1)))
    print("t1 matches t2: %s" % str(t1.match(t2)))
    assert t1.match(t1)[0] and t1.match(t2)[0]
    """

    t3 = Term("abc")
    p3 = Pattern("?xyz")
    print("p3 matches t3: %s" % str(p3.match(t3)))
    print("t3 NOT matches p3: %s" % str(t3.match(p3)))
    assert p3.match(t3)[0] and not t3.match(p3)[0]

"""
    p1 = Pattern("(?x (23 ?y))")
    print("p1 matches t1: %s" % str(p1.match(t1)))
    print("t1 NOT matches p1: %s" % str(t1.match(p1)))
    assert p1.match(t1)[0] and not t1.match(p1)[0]

    p2 = Pattern("(?x ?z)")
    print("p2 matches t1: %s" % str(p2.match(t1)))
    assert p2.match(t1)[0]
"""

# d is not like a local variable being set to {}
# it is a global dict whose value gets modified
# testbug called with q {}
# testbug called with r {'q': 35}
# testbug called with s {'q': 35, 'r': 64}


def test_optional_variables_are_mutable(a, d={}):
    print("testbug called with %s %s" % (a, d))
    d[a] = round(random.random() * 100)


def bug():
    test_optional_variables_are_mutable('q')
    test_optional_variables_are_mutable('r')
    test_optional_variables_are_mutable('s')


if __name__ == "__main__":
    run_tests()
    
