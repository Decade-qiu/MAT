# -*- coding: utf-8 -*-
from collections import defaultdict, Counter
import random, heapq
import matplotlib.pyplot as plt
from ipaddress import *

IMAX = 2**32-1
rule_split_num, node_split_num = 0, 0
rule_ex, node_ex = 0, 0

class Node:
    def __init__(self, src: int, dst: int, smask: int, dmask: int)->None:
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

def check(x: int)->bool:
    x = IMAX-x+1
    x -= x&-x
    return x == 0

def countOnes(n: int)->int:
    if (not check(n)):
        assert False, f"{n} can not be a mask!"
    count = 0
    while (n != 0):
        n = n & (n - 1)
        count += 1
    return count

def cal_range(mask: int)->int:
    assert mask >= 0 and mask <= 32, f"mask: {mask}"
    return (1<<(32-mask))-1

def split_node(node: Node)->list:
    cs_mask, cd_mask = node.snxtmk, node.dnxtmk
    cs_st, cs_ed = node.src, node.src+cal_range(node.smask)
    cd_st, cd_ed = node.dst, node.dst+cal_range(node.dmask)
    new_rules = []
    for ns_st in range(cs_st, cs_ed, cal_range(cs_mask)+1):
        for nd_st in range(cd_st, cd_ed, cal_range(cd_mask)+1):
            new_rules.append((ns_st, cs_mask, nd_st, cd_mask))
    return new_rules

def get_subtree(node: Node)->list:
    children = []
    for child in node.children:
        children.append((child.src, child.smask, child.dst, child.dmask))
        children.extend(get_subtree(child))
    return children
    
def insert_root(pq: list, tree: Node, src: int, smask: int, dst: int, dmask: int) -> None:
    global rule_split_num, node_split_num, rule_ex, node_ex
    is_st, is_ed = src, src+cal_range(smask)
    id_st, id_ed = dst, dst+cal_range(dmask)
    node = tree
    father = None
    children = tree.children
    flag = 0
    while len(children) > 0:
        next_children = []
        for child in children:    
            # 1. the child is the same as the insert range
            if child.src == src and child.dst == dst and child.smask == smask and child.dmask == dmask:
                child.cnt += 1
                flag = 1
                break
            cs_mask, cd_mask = child.smask, child.dmask
            cs_st, cs_ed = child.src, child.src+cal_range(child.smask)
            cd_st, cd_ed = child.dst, child.dst+cal_range(child.dmask)
            if is_st >= cs_st and is_ed <= cs_ed and id_st >= cd_st and id_ed <= cd_ed:
                # 2. insert range is the subset of the child
                father = node
                node = child
                next_children = node.children
                break
            elif is_st <= cs_st and is_ed >= cs_ed and id_st <= cd_st and id_ed >= cd_ed:
                # 3. after sort insert range can not be the superset of the child 
                assert False, [["插入的规则覆盖面积比树中的节点大"]]
            elif is_ed < cs_st or is_st > cs_ed or id_ed < cd_st or id_st > cd_ed:
                # 4. insert range has no intersection with the child
                continue
            else:
                # 5. insert range has intersection with the child
                if is_st>=cs_st and is_ed<=cs_ed:
                    per_len = cal_range(cd_mask)+1
                    cnt = (id_ed-id_st+1)/(per_len)
                    if(cnt < 0): assert False, [[cnt, id_ed, id_st, per_len]]
                    if (cnt >= 512):
                        tree.cnt += 1
                        return
                    rule_split_num += 1
                    rule_ex += cnt
                    print("rule split:", rule_split_num, add_num, rule_ex)
                    # print(str(IPv4Address(src)), smask, IPv4Address(dst), dmask)
                    # print(str(IPv4Address(child.src)), child.smask, str(IPv4Address(child.dst)), child.dmask)
                    # if add_num >= 4096: exit()
                    for nd_st in range(id_st, id_ed, cal_range(cd_mask)+1):
                        heapq.heappush(pq, (smask+cd_mask, (is_st, smask, nd_st, cd_mask)))
                else:
                    add_num = (is_ed-is_st+1)/(cal_range(cs_mask)+1)
                    if (add_num < 0): assert False, [[add_num, is_ed, is_st, cal_range(cs_mask)+1]]
                    if (add_num >= 512):
                        tree.cnt += 1
                        return
                    rule_split_num += 1
                    rule_ex += add_num
                    print("rule split:", rule_split_num, add_num, rule_ex)
                    # print(str(IPv4Address(src)), smask, IPv4Address(dst), dmask)
                    # print(str(IPv4Address(child.src)), child.smask, str(IPv4Address(child.dst)), child.dmask)
                    # if add_num >= 4096: exit()
                    for ns_st in range(is_st, is_ed, cal_range(cs_mask)+1):
                        heapq.heappush(pq, (cs_mask+dmask, (ns_st, cs_mask, id_st, dmask)))
                flag = 1
                break
        children = next_children
    if flag == 1: 
        return
    if node==tree or len(node.children)==0 or (node.snxtmk==smask and node.dnxtmk==dmask):
        node.children.append(Node(src, dst, smask, dmask))
        node.snxtmk = smask
        node.dnxtmk = dmask
    else:
        # print("==================================")
        # print(str(IPv4Address(src)), smask, IPv4Address(dst), dmask)
        # print(str(IPv4Address(node.src)), node.smask, str(IPv4Address(node.dst)), node.dmask, node.snxtmk, node.dnxtmk)
        heapq.heappush(pq, (smask+dmask, (src, smask, dst, dmask)))
        return
        # delete node from his father's children list
        father.children.remove(node)
        split_rules = split_node(node)
        if (len(split_rules) >= 512):
            tree.cnt += 1
            return
        node_split_num += 1
        node_ex += len(split_rules)
        print("node split:", node_split_num, len(split_rules), node_ex)
        for new_rule in split_rules:
            heapq.heappush(pq, (new_rule[1]+new_rule[3], new_rule))
        for prev_insert_rule in get_subtree(node):
            heapq.heappush(pq, (prev_insert_rule[1]+prev_insert_rule[3], prev_insert_rule))


def process(rules):
    # random.shuffle(rules)
    # rules.sort(key=lambda x: x[1] + x[3], reverse=True)
    tree = Node(0, 0, 0, 0)
    pq = []
    for rule in rules:
        heapq.heappush(pq, (rule[1]+rule[3], rule))
    cnt = 0
    while pq:
        src, smask, dst, dmask = heapq.heappop(pq)[1]
        # print(cnt, len(pq))
        insert_root(pq, tree, src, smask, dst, dmask)
        cnt += 1
    print(tree.cnt)

if __name__ == "__main__":
    for i in [1, 10, 15, 22, 55][:1]:
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
                ip.append((src, countOnes(smask), dst, countOnes(dmask)))
            process(ip)
        with open('../data/packets_{}k'.format(scale), 'r') as file:
            pass   