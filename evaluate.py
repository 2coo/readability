import re
import sys
import MeCab
import os
import operator

def extract(data):
    m = MeCab.Tagger ("-Ochasen")
    lst = m.parse (data).split('\n')
    rez = []
    for l in lst:
        t=l.split()
        if len(t) > 3:
            rez.append(t[2])
            #print(rez)
    return rez

def evaluate(str1, str2):
    print("Evaluating results with prepared answer")
    e = extract(str1)
    c = extract(str2)
    se = set(e)
    ce = set(c)
    try:
        precision= 100.0 * len( se & ce) / len(se | ce)
    except Exception as err:
        print(err)
        return 0
    return "%0.2f"%(precision)
   

    
