'''
Created on 2009-12-31
'''

def merge_dict(d1, d2, cmp=lambda a,b: a<b):
    d2 = d2.copy()
    for k1 in d1:
        try:
            if cmp(d1[k1], d2[k1]):
                d2[k1] = d1[k1]
        except KeyError:
            d2[k1] = d1[k1]
    return d2
