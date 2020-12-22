#!/usr/bin/env python3
""" JTMS - Justification Based Truth Maintenance System """

# pylint: disable=no-member
from enum import Enum
import match
import re
import sys
sys.path.insert(0, '/Users/rachaelkim/Desktop/Pisan_AI project/rip-1/cps')

from term import *



class Support(Enum):
    Enabled_Assumption = 1


class Belief(Enum):
    IN = 1
    OUT = 2


class JTMS():
    def __init__(self, aname):
        self.title = aname
        self.node_counter = 0
        self.just_counter = 0
        self.nodes = []
        self.justs = []
        self.debugging = False
        self.contradictions = []
        self.assumptions = []
        self.checking_contradictions = True

    def __str__(self):
        return "J<%s (%d)>" % (self.title, self.node_counter)

    def make_node(self, datum, isAssumption=False, isContradictory=False):
        n = TMS_Node(datum, isAssumption=isAssumption,
                     isContradictory=isContradictory)
        print("DEBUG")
        print( n.datum)
        print("END")
        n.jtms = self
        self.nodes.append(n)
        if isAssumption:
            self.assumptions.append(n)
        if isContradictory:
            self.contradictions.append(n)
        return n

    def get_node(self, datum):
        print("DEBUG : get_node called - finding ", datum)
        for n in self.nodes:
            if self.debugging:
                print("nodes value: ",n.datum)
            for x in n.datum :
                print("DEBUG " , x)
                if x == [datum] :
                    print("Found")
                    return n
            #if n.datum == datum:
            #    return n
        return None

    def find_alternative_support(self, out_queue):
        if self.debugging:
            print("Looking for alternative supports: %s" %
                  TMS_Node.strList(out_queue))
        for node in out_queue:
            if not node.isIN():
                for just in node.justs:
                    if just.check_justification():
                        just.consequence.install_support(just)

    def enabled_assumptions(self):
        return [f for f in self.assumptions if f.support == Support.Enabled_Assumption]

    def why_nodes(self):
        for n in self.nodes:
            n.why()
            # print("%s %s" % (n.label.name, n))

    def check_for_contradictions(self):
        contras = [n for n in self.contradictions if n.isIN()]
        if contras:
            print("Contradictions are: %s" % TMS_Node.strList(contras))
            self.ask_user_handler(contras)

    def ask_user_handler(self, contradictions):
        self.handle_one_contradiction(contradictions[0])
        self.check_for_contradictions()

    def handle_one_contradiction(self, contra):
        ass = contra.assumptions()
        if not ass:
            print("Contradictory node does not have any assumptions: %s" % contra)
            sys.exit(1)
        print("Contradiction found in %s" % contra)
        num = self.choose_from_nodes(ass, "Choose one to retract> ")
        if num == 0:
            return
        self.retract_assumption(ass[num - 1])

    # 0 to exit loop
    def choose_from_nodes(self, nodes, prompt):
        while True:
            index = 1
            print("\t0. Exit")
            for n in nodes:
                print("\t%s. %s" % (index, n))
                index += 1
            num = input(prompt)
            if not num.isdigit():
                continue
            num = int(num)
            if num >= 0 and num <= len(nodes):
                return num

    def retract_assumption(self, node):
        if node.support == Support.Enabled_Assumption:
            if node.jtms.debugging:
                print("Retracting assumption: %s" % node)
            node.setOUT()
            outs = [node] + node.propagate_outness()
            self.find_alternative_support(outs)

    def explore_network(self, datum):
        n = self.get_node(datum)
        if n is None:
            print("Could not find node: %s" % datum)
            return
        if not n.isIN():
            print("Not believed: %s" % n)
            return
        stack = [n]
        while stack:
            current = stack[-1]
            current.why()
            just = current.support
            if not isinstance(just, Justification):
                print("Justifed by %s" % just)
                stack.pop()
                continue
            antes = just.antecedents
            num = self.choose_from_nodes(antes, "Choose assumption to explore> ")
            if num == 0:
                stack.pop()
            else:
                stack.append(antes[num - 1])


class TMS_Node():
    def __init__(self, datum, isAssumption=False, isContradictory=False):
        self.index = 0
        self.datum = parse(datum)
        self.label = Belief.OUT
        self.support = None
        self.justs = []
        self.consequences = []
        self.mark = None
        self.isContradictory = isContradictory
        self.isAssumption = isAssumption
        self.inRules = []
        self.outRules = []
        self.jtms: JTMS = None

    def __str__(self):
        return "N<%s>" % self.datum

    @staticmethod
    def strList(lst):
        return str([x.datum for x in lst])

    def isPremise(self):
        return self.support is not None and\
            self.support != Support.Enabled_Assumption and\
            self.support.antecedents == []

    def isIN(self):
        return self.label == Belief.IN

    def isOUT(self):
        return self.label == Belief.OUT

    def assume(self):
        if not self.isAssumption:
            if self.jtms.debugging:
                print("Converting into assumption node: " + self)
            self.isAssumption = True
        self.enableAssumption()

    def contradict(self):
        j = self.jtms
        if not self.isContradictory:
            if j.debugging:
                print("Making contradictory node: " + self)
            self.isContradictory = True
            j.contradictions.append(self)
            j.check_for_contradictions()

    def justify(self, informant, antecedents):
        consequence = self
        j = self.jtms
        j.node_counter += 1
        index = j.node_counter
        just = Justification(index=index, informant=informant,
                             consequence=consequence, antecedence=antecedents)
        j.justs.append(just)
        for n in antecedents:
            n.consequences.append(just)
        if j.debugging:
            print("Justifying %s by %s using %s" %
                  (self, informant, TMS_Node.strList(antecedents)))
        if antecedents or self.isOUT():
            if just.check_justification():
                consequence.install_support(just)
            consequence.support = just
        j.check_for_contradictions()

    def support_node(self, just):
        self.setIN(just)
        self.propagate_inness()

    def propagate_inness(self):
        j = self.jtms
        queue = [self]
        while queue:
            n = queue.pop()
            if j.debugging:
                print("\tPropagating belief in: %s" % n)
            for just in n.consequences:
                if just.check_justification():
                    next_node = just.consequence
                    next_node.setIN(just)
                    queue.append(next_node)

    def propagate_outness(self):
        j = self.jtms
        queue = [self]
        out_queue = []
        while queue:
            n = queue.pop()
            if j.debugging:
                print("\tPropagating disbelief in: %s" % n)
            for just in n.consequences:
                next_node = just.consequence
                if just == next_node.support:
                    next_node.setOUT()
                    out_queue.append(next_node)
                    queue.append(next_node)
        return out_queue

    def setIN(self, reason):
        if self.jtms.debugging:
            print("Making %s in via %s " % (self, reason))
        self.label = Belief.IN
        self.support = reason
        for rule in self.inRules:
            # enqueu the rule
            print("enqueu rule: " + rule)
        self.inRules = []

    def setOUT(self):
        if self.jtms.debugging:
            print("Retracting belief in: %s" % self)
        self.support = []
        self.label = Belief.OUT
        for rule in self.outRules:
            # enqueu the rule
            print("enqueu rule: " + rule)
        self.outRules = []

    def retract_assumption(self):
        if self.support == Support.Enabled_Assumption:
            if self.jtms.debugging:
                print("Retracting belief in: %s" % self)
            self.setOUT()
            outs = [self] + self.propagate_outness()
            self.jtms.find_alternative_support(outs)

    def enable_assumption(self):
        assert self.isAssumption
        if self.jtms.debugging:
            print("Enabling assumption: %s" % self)
        if self.support == Support.Enabled_Assumption:
            if self.jtms.debugging:
                print("Already enabled assumption: %s" % self)
        elif self.isOUT():
            reason = Support.Enabled_Assumption
            self.setIN(reason)
            self.propagate_inness()
        elif self.support.antecedents: #not?
            if self.jtms.debugging:
                print("Already supported assumption: %s" % self)
        else:
            if self.jtms.debugging:
                print("Not sure how this is supported: %s" % self)
            self.support = Support.Enabled_Assumption
            sys.exit(1)

    def assumptions(self):
        if self.jtms.debugging:
            print("Looking for assumptions of: %s" % self)
        q = [self]
        marker = object()
        assumptions = []
        while q:
            n = q.pop()
            if n.mark is marker:
                continue
            if n.support == Support.Enabled_Assumption:
                assumptions.append(n)
            elif n.isIN():
                q += n.support.antecedents
            n.mark = marker
        return assumptions

    def install_support(self, just):
        self.setIN(just)
        self.propagate_inness()

    def why(self):
        if self.isOUT():
            print("%s is OUT" % self)
            return
        if self.support == Support.Enabled_Assumption:
            print("%s is an enabled assumption" % self)
        else:
            print("%s is in via %s on %s" %(self, self.support.informant, TMS_Node.strList(self.support.antecedents)))


class Justification():
    def __init__(self, index, informant, consequence, antecedence):
        self.index = index
        self.informant = informant
        self.consequence = consequence
        self.antecedents = antecedence

    def __str__(self):
        return "Just<" + self.informant + ">"

    def check_justification(self):
        return self.consequence.isOUT() and all(n.isIN() for n in self.antecedents)

class NewAssumption():
    def __init__(self, datum):
        self.datum = datum
# A^B ==> F
# B^C ==> E
# A^E ==> G
# D^E ==> G


"""
Objects:
    JTMS
    Node <- Assumption?

Things to study :
    isIn() ?
    isOut() ?
    why_node
    make_node
"""


def test1():
    j = JTMS("Hello")
    j.debugging = True
    for ch in "abcdefg":
        j.make_node(ch, isAssumption=True)
    j.get_node('f').justify('j1', [j.get_node('a'), j.get_node('b')])
    j.get_node('e').justify('j2', [j.get_node('b'), j.get_node('c')])
    j.get_node('g').justify('j3', [j.get_node('a'), j.get_node('e')])
    j.get_node('g').justify('j4', [j.get_node('d'), j.get_node('e')])
    j.get_node('a').enable_assumption()
    j.get_node('b').enable_assumption()
    j.get_node('f').enable_assumption()
    assert j.get_node('f').isIN()
    j.get_node('c').enable_assumption()
    assert j.get_node('e').isIN()
    assert j.get_node('g').isIN()
    j.why_nodes()
    return j

def test2():
    j = test1()
    contra = j.make_node('Loser', isContradictory=True)
    contra.justify('j5', [j.get_node('e'), j.get_node('f')])
    j.why_nodes()

def test3():
    j = test1()
    j.explore_network('e')

def rule1(j):
    print("Rule1 has executed")
    # [Graduate-Student ?x]
    pat = Pattern('((Graduate-Student)(?x))')
    newTerm = Term('((Graduate-Student)(Robbie))')
    j.make_node('((Graduate-Student)(Robbie))', isAssumption=True)
    j.make_node('((Graduate-Student)((underpaid)(overworked))', isAssumption=True)
    j.make_node('(a)', isAssumption=True)
    testNode = j.get_node('Graduate-Student')
    print("DEBUG : get_node result - ", testNode)
    print(newTerm)
    count = 0
    print("Pattern : ", pat)
    for node in j.nodes:
        print("[", count, "] ", node.datum)
        count += 1
        bindings = pat.match( node )
        print("Bindings %s" % bindings[0])
    # bindings = match(pat, dat)
    # assert lookup('x', bindings) == 'b's
    return True

def rule2(j):
    print("Rule2 has executed")
    return True

def testRule():
    j = JTMS("Hello")
    j.debugging = True
    '''
    for ch in "abcdefg":
        j.make_node(ch, isAssumption=True)
    j.get_node('f').justify('j1', [j.get_node('a'), j.get_node('b')])
    j.get_node('e').justify('j2', [j.get_node('b'), j.get_node('c')])
    j.get_node('g').justify('j3', [j.get_node('a'), j.get_node('e')])
    j.get_node('g').justify('j4', [j.get_node('d'), j.get_node('e')])
    j.get_node('a').enable_assumption()
    j.get_node('b').enable_assumption()
    assert j.get_node('f').isIN()
    j.get_node('c').enable_assumption()
    assert j.get_node('e').isIN()
    assert j.get_node('g').isIN()
    # j.why_nodes()
    '''
    rules = ["rule1", "rule2"]
    for ruleName in rules:
        globals()[ruleName](j)
    return j

def mockTest():
    escape = False
    try:
        assert escape
    except AssertionError:
        print("ASSERTION ERROR")
    count = 0
    while escape != True :
        print(escape)
        count += 1
        if count == 5:
            escape = True
        username = input("Enter Username: ")
        if username == "exit":
            escape = True

if __name__ == "__main__":
    #test1()
    #print (" DEBUG : end of test ")
    #test2()
    #print (" DEBUG : end of test ")
    #test2()
    #print (" DEBUG : end of test ")
    testRule()
    #mockTest()
