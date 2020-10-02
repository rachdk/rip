#!/usr/bin/env python3
""" Term """

import py_compile
import importlib
import os

def isNewerFile(f1, f2):
    m1 = os.path.getmtime(f1)
    m2 = os.path.getmtime(f2)
    return m1 > m2

def compileFile(fname, force = False, ):
    print("Compiling %s ..." % fname, end='')
    fname = fname + ".py"
    cname = fname + "c"
    if force or not os.path.isfile(cname) or isNewerFile(fname, cname):
        py_compile.compile(fname, cfile=cname)
        print("done")
    else:
        print("skipped")

def execFunction(moduleName, fName):
    if fName not in dir(moduleName):
        print("Error: No function named %s in %s" % (fName, moduleName))
    f0 = getattr(moduleName, fName)
    return f0()

def loadFile(fname):
    print("Loading %s ..." % fname)
    # compileFile(fname)
    scenario = importlib.import_module(fname)
    return scenario
    # print("Scenario is %s" % scenario.__dict__['func0'])
    # print("All functions %s" % dir(scenario))
    # f0 = getattr(scenario, "func0")
    # f0()
    # print("Module name: %s " % scenario.__dict__['__name__'])
    # eval("func0")
    # scenario.__dict__['func0']
    # exec("func0", scenario.__dict__)
    fname = fname + ".py"
    cname = fname + "c"
    # exec(open(fname).read())

if __name__ == "__main__":
    # run_tests()
    # compileFile("test")
    mod = loadFile("test")
    execFunction(mod, "func0")
    # eval("func0")
