# -*- coding: utf-8 -*-
from collections import defaultdict, Counter
import random, heapq
import matplotlib.pyplot as plt
from ipaddress import *

class Node:
    def __init__(self, src, dst, smask, dmask):
        self.src = src
        self.dst = dst
        self.smask = smask
        self.dmask = dmask
        self.snxtmk = -1
        self.dnxtmk = -1
        self.cnt = 1
        self.children = []

def query_trace(tcam, zero_rule_num, pkts):
    pass

def insert(pq, tree, src, smask, dst, dmask):
    is_st, is_ed = src, src+(2**32-1-smask)
    id_st, id_ed = dst, dst+(2**32-1-dmask)
    for child in tree.children:
        # 1. the child is the same as the insert range
        if child.src == src and child.dst == dst and child.smask == smask and child.dmask == dmask:
            child.cnt += 1
            return
        cs_st, cs_ed = child.src, child.src+(2**32-1-child.smask)
        cd_st, cd_ed = child.dst, child.dst+(2**32-1-child.dmask)
        # 2. insert range is the subset of the child
        if is_st <= cs_st and is_ed >= cs_ed and id_st <= cd_st and id_ed >= cd_ed:
            insert(pq, child, src, smask, dst, dmask)
            return
        # 3. after sort insert range can not be the superset of the child 
        # 4. insert range has no intersection with the child
        if is_ed < cs_st or is_st > cs_ed or id_ed < cd_st or id_st > cd_ed:
            continue
        # 5. insert range has intersection with the child
        # 5.1 get the intersection range
        ns_st, ns_ed = max(is_st, cs_st), min(is_ed, cs_ed)
        nd_st, nd_ed = max(id_st, cd_st), min(id_ed, cd_ed)
        # 5.2 insert the intersection range
        ism, idm = 2**32-1-(ns_ed-ns_st), 2**32-1-(nd_ed-nd_st)
        heapq.heappush(pq, (ism+idm, (ns_st, ism, nd_st, idm)))
        # 5.3 get the left range
        if is_st <= cs_st-1:
            ism, idm = 2**32-1-(cs_st-1-is_st), dmask
            heapq.heappush(pq, ism+idm, (is_st, ism, id_st, idm))
        if is_ed >= cs_ed+1:
            ism, idm = 2**32-1-(is_ed-cs_ed-1), dmask
            heapq.heappush(pq, ism+idm, (cs_ed+1, ism, id_st, idm))
        if id_st <= cd_st-1:
            ism, idm = smask, 2**32-1-(cd_st-1-id_st)
            heapq.heappush(pq, ism+idm, (is_st, ism, id_st, idm))
        if id_ed >= cd_ed+1:
            ism, idm = smask, 2**32-1-(id_ed-cd_ed-1)
            heapq.heappush(pq, ism+idm, (is_st, ism, cd_ed+1, idm))
        return
    # insert range has no intersection with all the children
    # 1. insert range has same mask as the child or parent has no child
    if (len(tree.children) == 0 or (tree.snxtmk == smask and tree.dnxtmk == dmask)): 
        tree.snxtmk = smask
        tree.dnxtmk = dmask
        tree.children.append(Node(src, dst, smask, dmask))
        return
    # 2. otherwise, insert range has different mask as the child
    

def insert_root(pq, tree, src, smask, dst, dmask):
    is_st, is_ed = src, src+(2**32-1-smask)
    id_st, id_ed = dst, dst+(2**32-1-dmask)
    for child in tree.children:    
        # 1. the child is the same as the insert range
        if child.src == src and child.dst == dst and child.smask == smask and child.dmask == dmask:
            child.cnt += 1
            return
        cs_st, cs_ed = child.src, child.src+(2**32-1-child.smask)
        cd_st, cd_ed = child.dst, child.dst+(2**32-1-child.dmask)
        # 2. insert range is the subset of the child
        if is_st <= cs_st and is_ed >= cs_ed and id_st <= cd_st and id_ed >= cd_ed:
            insert(pq, child, src, smask, dst, dmask)
            return
        # 3. after sort insert range can not be the superset of the child 
        # 4. insert range has no intersection with the child
        if is_ed < cs_st or is_st > cs_ed or id_ed < cd_st or id_st > cd_ed:
            continue
        # 5. insert range has intersection with the child
        # 5.1 get the intersection range
        ns_st, ns_ed = max(is_st, cs_st), min(is_ed, cs_ed)
        nd_st, nd_ed = max(id_st, cd_st), min(id_ed, cd_ed)
        # 5.2 insert the intersection range
        # insert(pq, child, ns_st, ns_ed-ns_st, nd_st, nd_ed-nd_st)
        heapq.heappush(pq, (ns_ed-ns_st+nd_ed-nd_st, (ns_st, ns_ed-ns_st, nd_st, nd_ed-nd_st)))
        # 5.3 get the left range
        if is_st <= cs_st-1:
            # insert_root(pq, tree, is_st, 2**32-cs_st+is_st, id_st, dmask)
            heapq.heappush(pq, (2**32-cs_st+is_st+dmask, (is_st, 2**32-cs_st+is_st, id_st, dmask)))
        if is_ed >= cs_ed+1:
            # insert_root(pq, tree, cs_ed+1, 2**32-is_ed+cs_ed, id_st, dmask)
            heapq.heappush(pq, (2**32-is_ed+cs_ed+dmask, (cs_ed+1, 2**32-is_ed+cs_ed, id_st, dmask)))
        if id_st <= cd_st-1:
            # insert_root(pq, tree, src, smask, id_st, 2**32-cd_st+id_st)
            heapq.heappush(pq, (2**32-cd_st+id_st+smask, (src, smask, id_st, 2**32-cd_st+id_st)))
        if id_ed >= cd_ed+1:
            # insert_root(pq, tree, src, smask, cd_ed+1, 2**32-id_ed+cd_ed)
            heapq.heappush(pq, (2**32-id_ed+cd_ed+smask, (src, smask, cd_ed+1, 2**32-id_ed+cd_ed)))
        return
    tree.children.append(Node(src, dst, smask, dmask))

def process(rules):
    # random.shuffle(rules)
    # rules.sort(key=lambda x: x[1] + x[3], reverse=True)
    tree = Node(0, 0, 0, 0)
    pq = []
    for rule in rules:
        heapq.heappush(pq, (rule[1]+rule[3], rule))
    while pq:
        src, smask, dst, dmask = heapq.heappop(pq)[1]
        insert_root(pq, tree, src, smask, dst, dmask)

if __name__ == "__main__":
    for i in [1, 10, 15, 22, 55][:]:
        rule_set = []
        scale = i
        # insert rules
        print(f"================= scaled {scale}k =================")
        tree, zero_rule_num = None, 0
        with open('../data/rules_{}k'.format(scale), 'r') as file:
            rules = file.readlines()
            ip = []
            for rule in rules:
                tp = rule.strip().split()
                src, smask = map(int, tp[0].split('/'))
                dst, dmask = map(int, tp[1].split('/'))
                if (smask == 0 and dmask == 0): 
                    zero_rule_num += 1
                    continue
                ip.append((src, smask, dst, dmask))
            process(ip)
        with open('../data/packets_{}k'.format(scale), 'r') as file:
            pass   