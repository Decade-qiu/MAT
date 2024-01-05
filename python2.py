# -*- coding: utf-8 -*-
from collections import defaultdict, Counter
import random, heapq, json
import matplotlib.pyplot as plt
from ipaddress import *
from pyecharts import options as opts
from pyecharts.charts import Tree

IMAX = 2**32-1
rule_split_num = 0
rule_ex = 0
rule_set = []
max_rule_num = 64
max_split_num = 64
tcam_rule = 0

def init()->None:
    global rule_split_num, rule_ex, rule_set
    rule_split_num = 0
    rule_ex = 0
    rule_set = []

class Node:
    def __init__(self, src: int, dst: int, smask: int, dmask: int, rule: list)->None:
        self.src = src
        self.dst = dst
        self.smask = smask
        self.dmask = dmask
        self.snxtmk = -1
        self.dnxtmk = -1
        self.rules = []
        self.cnt = 0
        self.children = []
        if (len(rule) > 0): 
            self.rules.append(rule)
    
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

def cal_split_num(node: Node)->int:
    cs_mask, cd_mask = node.snxtmk, node.dnxtmk
    cs_st, cs_ed = node.src, node.src+cal_range(node.smask)
    cd_st, cd_ed = node.dst, node.dst+cal_range(node.dmask)
    assert (cs_ed-cs_st+1)%(cal_range(cs_mask)+1) == 0 and(cs_ed-cs_st+1)%(cal_range(cs_mask)+1) == 0, [node.src, node.smask, node.dst, node.dmask, cs_mask, cd_mask]
    cnt = (cs_ed-cs_st+1)/(cal_range(cs_mask)+1) * (cd_ed-cd_st+1)/(cal_range(cd_mask)+1)
    return int(cnt)

def cal_priority(smask: int, dmask: int)->int:
    return smask+dmask
    # return smask+dmask if smask*dmask==0 else smask*dmask

def split_node(node: Node)->list:
    cs_mask, cd_mask = node.snxtmk, node.dnxtmk
    cs_st, cs_ed = node.src, node.src+cal_range(node.smask)
    cd_st, cd_ed = node.dst, node.dst+cal_range(node.dmask)
    new_rules = []
    for ns_st in range(cs_st, cs_ed+1, cal_range(cs_mask)+1):
        for nd_st in range(cd_st, cd_ed+1, cal_range(cd_mask)+1):
            new_rules.append((ns_st, cs_mask, nd_st, cd_mask))
    return new_rules

def get_subtree(node: Node)->list:
    rules = []
    for child in node.children:
        for rule in child.rules:
            rules.append(rule)
        rules.extend(get_subtree(child))
    return rules

def value_match(t: int, v: list)->bool:
    if (v[2] == 0):
        if (v[0] == 0 or (t&v[1]) == v[0]): return 1^v[3]
        return 0^v[3]
    f = 0
    if (t >= v[0] and t <= v[1]): f = 1
    return f ^ v[3]

def match(proto: int, sport: int, dport: int, rule: tuple)->bool:
    sp_st, sp_ed = map(int, list(str(rule[5]).split(':')))
    dp_st, dp_ed = map(int, list(str(rule[6]).split(':')))
    if (value_match(proto, list((rule[4], 255, 0, rule[7]))) and
        value_match(sport, list((sp_st, sp_ed, 1, rule[8]))) and
        value_match(dport, list((dp_st, dp_ed, 1, rule[9])))):
        return True
    return False

def get_IP(src: int, smask: int, dst: int, dmask: int)->str:
    return f"{IPv4Address(src)}/{smask} {IPv4Address(dst)}/{dmask}"

# def tree2json(node: Node)->None:
#     with open('tree.json', 'w') as file:
#         root = {}
#         tree_dict = root
#         queue = [(tree_dict, node)]
#         while queue:
#             tree_dict, cur = queue.pop(0)
#             tree_dict['name'] = get_IP(cur.src, cur.smask, cur.dst, cur.dmask)
#             tree_dict['value'] = str(cur.cnt)
#             tree_dict['children'] = []
#             for child in cur.children:
#                 tree_dict['children'].append({})
#                 queue.append((tree_dict['children'][-1], child))
#         file.write(json.dumps(root))

# def json2pic()->None:
#     with open('tree.json', 'r') as file:
#         root = json.load(file)
#         c = (
#             Tree(init_opts=opts.InitOpts(width="6560px", height="5440px"))
#             .add("", [root], collapse_interval=200, orient="TB",label_opts=opts.LabelOpts(position="top"), is_roam=True)
#             .set_global_opts(title_opts=opts.TitleOpts(title="Tree"))
#         )
#         c.render("tree.html")

def query_trace(tree: Node, p: tuple)->list:
    src, dst, proto, sport, dport, rule_id = p
    node = tree
    match_id, query_node, query_num = 1e9, 0, 0
    for ruless in node.rules:
        # print(node.rules)
        if (len(ruless) == 0): continue
        cs_st, cs_ed = ruless[0], ruless[0]+cal_range(ruless[1])
        cd_st, cd_ed = ruless[2], ruless[2]+cal_range(ruless[3])
        if src >= cs_st and src <= cs_ed and dst >= cd_st and dst <= cd_ed:
            if (match(proto, sport, dport, ruless)):
                match_id = min(match_id, ruless[10])
    children = node.children
    while len(children) > 0:
        next_children = []
        for child in children:
            cs_st, cs_ed = child.src, child.src+cal_range(child.smask)
            cd_st, cd_ed = child.dst, child.dst+cal_range(child.dmask)
            if src >= cs_st and src <= cs_ed and dst >= cd_st and dst <= cd_ed:
                query_node += 1
                query_num += len(child.rules)
                for rule in child.rules:
                    if (match(proto, sport, dport, rule)):
                        match_id = min(match_id, rule[10])
                node = child
                next_children = node.children
                break
        children = next_children
    return [0 if match_id == 1e9 else match_id, query_node, query_num]

def insert_root(pq: list, tree: Node, src: int, smask: int, dst: int, dmask: int, rule: list) -> None:
    global rule_split_num, rule_ex, rule_set
    is_st, is_ed = src, src+cal_range(smask)
    id_st, id_ed = dst, dst+cal_range(dmask)
    father = tree
    node = tree
    children = tree.children
    flag = 0
    while len(children) > 0:
        next_children = []
        for child in children:    
            # 1. the child is the same as the insert range
            if child.src == src and child.dst == dst and child.smask == smask and child.dmask == dmask:
                child.rules.append(rule)
                return
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
                assert 0, "不存在插入的规则覆盖面积比树中的节点大"
            elif is_ed < cs_st or is_st > cs_ed or id_ed < cd_st or id_st > cd_ed:
                # 4. insert range has no intersection with the child
                continue
            else:
                # 5. insert range has intersection with the child
                if is_st>=cs_st and is_ed<=cs_ed:
                    assert id_st<=cd_st and id_ed>=cd_ed, [is_st, is_ed, cs_st, cs_ed, id_st, id_ed, cd_st, cd_ed]
                    per_len = cal_range(cd_mask)+1
                    cnt = (id_ed-id_st+1)/(per_len)
                    assert (id_ed-id_st+1)%(per_len) == 0 and cnt >= 1, [id_ed, id_st, per_len]
                    if (cnt >= max_split_num):
                        tree.cnt += 1
                        tree.rules.append(rule)
                        return
                    rule_split_num += 1
                    rule_ex += cnt
                    for nd_st in range(id_st, id_ed+1, per_len):
                        heapq.heappush(pq, (cal_priority(smask, cd_mask), (is_st, smask, nd_st, cd_mask, rule[4], rule[5], rule[6], rule[7], rule[8], rule[9], rule[10])))
                else:
                    assert id_st>=cd_st and id_ed<=cd_ed, [id_st, id_ed, cd_st, cd_ed]
                    per_len = cal_range(cs_mask)+1
                    cnt = (is_ed-is_st+1)/per_len
                    assert (is_ed-is_st+1)%(per_len) == 0 and cnt >= 1, [is_ed, is_st, per_len]
                    if (cnt >= max_split_num):
                        tree.cnt += 1
                        tree.rules.append(rule)
                        return
                    rule_split_num += 1
                    rule_ex += cnt
                    for ns_st in range(is_st, is_ed+1, per_len):
                        heapq.heappush(pq, (cal_priority(cs_mask, dmask), (ns_st, cs_mask, id_st, dmask, rule[4], rule[5], rule[6], rule[7], rule[8], rule[9], rule[10])))
                return
        children = next_children
    if flag == 1: 
        return
    if node==tree or len(node.children)==0 or (node.snxtmk==smask and node.dnxtmk==dmask):
        node.children.append(Node(src, dst, smask, dmask, rule))
        node.snxtmk = smask
        node.dnxtmk = dmask
    else:
        if (1 or cal_split_num(node) >= max_split_num):
            if (smask==32 and dmask==32):
                prev_insert_rule = get_subtree(node)
                node.children = [Node(src, dst, smask, dmask, rule)]
                node.snxtmk = smask
                node.dnxtmk = dmask
                for rule in prev_insert_rule:
                    # pq.append((cal_priority(rule[1], rule[3]), rule))
                    tree.cnt += 1
                    tree.rules.append(rule) 
            else:
                tree.cnt += 1
                tree.rules.append(rule)
            return
        # delete node from his father's children list
        father.children.remove(node)
        heapq.heappush(pq, (cal_priority(smask, dmask), rule))
        split_rules = split_node(node)
        # print("node split:", node_split_num, len(split_rules), node_ex)
        for new_rule in split_rules:
            for dx in range(len(node.rules)):
                heapq.heappush(pq, (cal_priority(new_rule[1], new_rule[3]), (new_rule[0], new_rule[1], new_rule[2], new_rule[3], node.rules[dx][4], node.rules[dx][5], node.rules[dx][6], node.rules[dx][7], node.rules[dx][8], node.rules[dx][9], node.rules[dx][10])))
        for prev_insert_rule in get_subtree(node):
            heapq.heappush(pq, (cal_priority(prev_insert_rule[1], prev_insert_rule[3]), prev_insert_rule))

def bfs(node: Node)->None:
    max_child_num, max_depth, max_width, total_node, max_same_rule = 0, 0, 0, 0, 0
    q = [i for i in node.children]
    while q:
        sz = len(q)
        max_width = max(max_width, sz)
        max_depth += 1
        total_node += sz
        while sz:
            node = q.pop(0)
            sz -= 1
            q.extend(node.children)
            max_same_rule = max(max_same_rule, len(node.rules))
            max_child_num = max(max_child_num, len(node.children))
    print(f"max_depth: {max_depth}, max_width: {max_width}, max_child_num: {max_child_num}, total_node: {total_node}, max_same_rule: {max_same_rule}")

def process(rules: list) -> Node:
    global rule_set
    rule_set = rules
    tree = Node(0, 0, 0, 0, [])
    pq = []
    for rule in rules:
        heapq.heappush(pq, (cal_priority(rule[1], rule[3]), rule))
    cnt = 0
    while pq:
        rule = heapq.heappop(pq)[1]
        src, smask, dst, dmask = rule[0:4]
        if (smask == 0 and dmask == 0):
            tree.rules.append(rule)
            continue
        insert_root(pq, tree, src, smask, dst, dmask, rule)
        cnt += 1
    print(f"TCAM:{len(tree.rules)}({len(tree.children)}), Total_rules:{cnt}, rule_split:{rule_split_num}, rule_add:{rule_ex}")
    bfs(tree)
    return tree

if __name__ == "__main__":
    for i in [1, 10, 22, 55][:4]:
        scale = i
        print(f"================= scaled {scale}k =================")
        init()
        with open('rules_{}k'.format(scale), 'r') as file:
            rules = file.readlines()
            ip = []
            for rule in rules:
                tp = rule.strip().split()
                src, smask = map(int, tp[0].split('/'))
                dst, dmask = map(int, tp[1].split('/'))
                ip.append((src, countOnes(smask), dst, countOnes(dmask), int(tp[2]), tp[3], tp[4], int(tp[5]), int(tp[6]), int(tp[7]), int(tp[8])))
            with open('packets_{}k'.format(scale), 'r') as file:
                pkts = file.readlines()
                tree = process(ip)
                # break
                continue
                print("Query trace!")
                err, query_node, query_num = 0, 0, 0
                for p in pkts:
                    pkt_id = p.strip().split()[0]
                    p = tuple(map(int, p.strip().split()[1:]))
                    match_id, q_node, q_num = query_trace(tree, p)
                    if (match_id != p[-1]): 
                        err += 1
                        print(pkt_id, p, match_id)
                    query_node += q_node
                    query_num += q_num
                print(f"err: {err}, avg_node: {query_node/len(pkts)}, avg_num: {query_num/len(pkts)}")