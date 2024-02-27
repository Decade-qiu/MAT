# -*- coding: utf-8 -*-
from collections import defaultdict
from io import TextIOWrapper
import random

from numpy import double

from python1 import process

IMAX: int = 2**32-1
ITERATOR: int = 0
PACKET_TYPE = tuple[int,int,int,int,int,int]
RULE_TYPE = tuple[int,int,int,int,int,str,str,int,int,int,int]
RULES_SET: list[RULE_TYPE] = []

def init(loop:int)->None:
    global RULES_SET, ITERATOR
    RULES_SET = []
    ITERATOR = loop

class Node:
    def __init__(self, src: int, dst: int, smask: int, dmask: int, rule: list[RULE_TYPE]) -> None:
        self.src: int = src
        self.dst: int = dst
        self.smask: int = smask
        self.dmask: int = dmask
        self.snxtmk: int = -1
        self.dnxtmk: int = -1
        self.rules: list[RULE_TYPE] = []
        self.children: defaultdict[tuple[int,int], list[Node]] = defaultdict(list) 
        for r in rule:
            self.rules.append(r)

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

def cal_rule_range(src: int, smask: int, dst: int, dmask: int)->list[int]:
    return [src, src+cal_range(smask), dst, dst+cal_range(dmask)]

def add_rule(rule: RULE_TYPE, father: Node, subChild: list[Node])->None:
    index = (rule[1], rule[3])
    current = Node(rule[0], rule[2], rule[1], rule[3], [rule])
    father.children[index].append(current)
    for child in subChild:
        cindex = (child.smask, child.dmask)
        current.children[cindex].append(child)
        father.children[cindex].remove(child)

def insert_root(tree: Node, src: int, smask: int, dst: int, dmask: int, rule: RULE_TYPE) -> None:
    is_st, is_ed, id_st, id_ed = cal_rule_range(src, smask, dst, dmask)
    father = Node(0, 0, 0, 0, [])   
    current = tree
    children: list[Node] = []
    for mask in current.children:
        children.extend(current.children[mask])
    flag = 1
    subChild: list[Node] = []
    while len(children) > 0:
        continue_flag = False
        for node in children:
            if node.src == src and node.dst == dst and node.smask == smask and node.dmask == dmask:
                node.rules.append(rule)
                return
            cs_st, cs_ed, cd_st, cd_ed = cal_rule_range(node.src, node.smask, node.dst, node.dmask)
            if is_st <= cs_st and is_ed >= cs_ed and id_st <= cd_st and id_ed >= cd_ed:
                subChild.append(node)
        if len(subChild) > 0:
            break
        for node in children:    
            cs_st, cs_ed, cd_st, cd_ed = cal_rule_range(node.src, node.smask, node.dst, node.dmask)
            if is_st >= cs_st and is_ed <= cs_ed and id_st >= cd_st and id_ed <= cd_ed:
                father = current
                current = node
                continue_flag = True
                break
        if continue_flag:
            children.clear()
            for mask in current.children:
                children.extend(current.children[mask])
        else:
            break
    if flag == 1: 
        add_rule(rule, current, subChild)

def add_tcams(tree: Node, sram_node: list[Node])->None:
    current = sram_node
    while len(current) > 0:
        next = []
        for node in current:
            tree.rules.extend(node.rules)
            # assert len(node.children) <= 1, f"Mask same! {node.children}"
            for mask in node.children:
                next.extend(node.children[mask])
        current = next

def check_intersect(cur: Node, pre: Node)->bool:
    cs_st, cs_ed, cd_st, cd_ed = cal_rule_range(cur.src, cur.smask, cur.dst, cur.dmask)
    ps_st, ps_ed, pd_st, pd_ed = cal_rule_range(pre.src, pre.smask, pre.dst, pre.dmask)
    if (cs_st >= ps_st and cs_st <= ps_ed) or (cs_ed >= ps_st and cs_ed <= ps_ed) or (ps_st >= cs_st and ps_st <= cs_ed) or (ps_ed >= cs_st and ps_ed <= cs_ed):
        if (cd_st >= pd_st and cd_st <= pd_ed) or (cd_ed >= pd_st and cd_ed <= pd_ed) or (pd_st >= cd_st and pd_st <= cd_ed) or (pd_ed >= cd_st and pd_ed <= cd_ed):
            return True
    return False

def small_mask_process(tree: Node, iterate: int) -> None:
    for _ in range(iterate):
        need_remove, need_add = [], []
        for mask in tree.children:
            for node in tree.children[mask]:
                self_cnt, free_cnt, max_cnt = len(node.rules), 0, 0
                for submask in node.children:
                    cur = 0
                    for child in node.children[submask]:
                        free_cnt += len(child.rules)
                        cur += len(child.rules)
                    max_cnt = max(max_cnt, cur)
                if free_cnt >= self_cnt+max_cnt:
                    tree.rules.extend(node.rules)
                    need_remove.append([mask, node])
                    need_add.append(node)   
        for mask, node in need_remove:
            tree.children[mask].remove(node)
        for node in need_add:
            for mask in node.children:
                tree.children[mask].extend(node.children[mask])

def select_root(tree: Node) -> None:
    nodes: list[Node] = []
    for mask in tree.children:
        nodes.extend(tree.children[mask])
    cluster: defaultdict[int, list[Node]] = defaultdict(list)
    for cur in nodes:
        insert_index = len(cluster)
        for index, subnodes in cluster.items():
            is_intersect = False
            for pre in subnodes:
                is_intersect |= check_intersect(cur, pre) 
                if is_intersect: break
            if not is_intersect:
                insert_index = index
                break
        cluster[insert_index].append(cur)
    max_index, max_num = map(int, [-1, 0])
    for index, subnodes in cluster.items():
        if len(subnodes) > max_num:
            if max_index != -1:
                add_tcams(tree, cluster[max_index])
            max_num = len(subnodes)
            max_index = index
        else:
            add_tcams(tree, subnodes)
    tree.children.clear()
    for node in cluster[max_index]:
        index = (node.smask, node.dmask)
        tree.children[index].append(node)

def DP(tree: Node, cur: Node) -> int:
    max_rule_num: int = 0
    sram_node: list[Node] = []
    sram_mask: tuple[int, int] = (0, 0)
    for mask in cur.children:
        subNode = cur.children[mask]
        cur_cnt: int = 0
        for node in subNode:
            cur_cnt += DP(tree, node)
        if cur_cnt > max_rule_num:
            if len(sram_node) != 0:
                add_tcams(tree, sram_node)
            max_rule_num = cur_cnt
            sram_node = subNode
            sram_mask = mask
        else:
            add_tcams(tree, subNode)
    cur.children.clear()
    cur.children[sram_mask] = sram_node
    cur.snxtmk, cur.dnxtmk = sram_mask
    return max_rule_num + len(cur.rules)

def build(rules: list[RULE_TYPE]) -> Node:
    global RULES_SET
    RULES_SET = rules
    tree: Node = Node(0, 0, 0, 0, [])
    for rule in rules:
        src, smask, dst, dmask = rule[0], rule[1], rule[2], rule[3]
        if (smask <= 0 or dmask <= 0):
            tree.rules.append(rule)
        else:
            insert_root(tree, src, smask, dst, dmask, rule)
    small_mask_process(tree, ITERATOR)
    select_root(tree)
    for mask in tree.children:
        for subNode in tree.children[mask]:
            DP(tree, subNode)
    return tree

def write(info: str, mode: int, file: TextIOWrapper) -> None:
    if mode == 0:
        print(info)
    else:
        file.write(info+"\n")

def print_info(tree: Node) -> None:
    depth, width, total = map(int, [0, 0, 0])
    rule_same, rule_total = map(int, [0, 0])
    tcams_rule, virtual_node = len(tree.rules), 0
    per_layer_rule: list[int] = []
    per_layer_mask: list[defaultdict[tuple[int,int],int]] = []
    q: list[Node] = []
    for mask in tree.children:
        q.extend(tree.children[mask])
        virtual_node += len(tree.children[mask])
    tcams_rule += virtual_node
    file = open("info.txt", "a")
    mode = 1
    write(f"\n{len(RULES_SET)}", mode, file)
    write(f"TCAM\tVirtual: {virtual_node}\tTotal: {tcams_rule}", mode, file)
    while q:
        sz = len(q)
        width = max(width, sz)
        depth += 1
        total += sz
        cur_rule = 0
        cur_mask = defaultdict(int)
        while sz:
            node = q.pop(0)
            cur_mask[(node.smask, node.dmask)] += len(node.rules)
            sz -= 1
            assert len(node.children) <= 1, f"Mask same! {node.children}"
            for mask in node.children:
                q.extend(node.children[mask])
            rule_same = max(rule_same, len(node.rules))
            rule_total += len(node.rules)
            cur_rule += len(node.rules)
        per_layer_mask.append(cur_mask)
        per_layer_rule.append(cur_rule)
    write(f"SRAM\tMax_same: {rule_same}\tTotal: {rule_total}",mode,file)
    assert tcams_rule+rule_total-virtual_node == len(RULES_SET), f"total rule not equal! {tcams_rule+rule_total} {virtual_node} {len(RULES_SET)}"
    write(f"Tree\t"+"  ".join(f'{"L"+str(i)+": "+str(v):9}' for i, v in enumerate(map(str, per_layer_rule))), 1, file)
    return
    for i in range(depth):
        cur_mask = sorted(per_layer_mask[i].items(), key=lambda x: x[1], reverse=True)
        write(f"L{i}", mode, file)
        write(f"\t".join(str(m[0])+":"+str(m[1]) for m in cur_mask[:5]), mode, file)
        write(f"\t".join(str(m[0])+":"+str(m[1]) for m in cur_mask[5:10]), mode, file)
    # TCAM
    per_mask_num: defaultdict[tuple, int] = defaultdict(int)
    for rule in tree.rules:
        mask = (rule[1], rule[3])
        per_mask_num[mask] += 1
    write(f"TCAM\t"+"  ".join(f'{str(k)+":"+str(v):9}' for k, v in sorted(per_mask_num.items(), key=lambda x: x[1], reverse=True)), 1, file)
    write(f"{sum([i[1] for i in per_mask_num.items()])}", 1, file)

def value_match(t: int, v: list)->bool:
    if (v[2] == 0):
        if (v[0] == 0 or (t&v[1]) == v[0]): return 1^v[3]
        return 0^v[3]
    f = 0
    if (t >= v[0] and t <= v[1]): f = 1
    return f ^ v[3]

def match(proto: int, sport: int, dport: int, rule: RULE_TYPE)->bool:
    sp_st, sp_ed = map(int, list(str(rule[5]).split(':')))
    dp_st, dp_ed = map(int, list(str(rule[6]).split(':')))
    if (value_match(proto, list((rule[4], 255, 0, rule[7]))) and
        value_match(sport, list((sp_st, sp_ed, 1, rule[8]))) and
        value_match(dport, list((dp_st, dp_ed, 1, rule[9])))):
        return True
    return False

def query_trace(tree: Node, pkt: PACKET_TYPE) -> tuple[int, int, int]:
    src, dst, proto, sport, dport, rule_id = pkt
    node = tree
    match_id, q_node, q_rule = map(int, [1e9, 0, 0])
    for ruless in tree.rules:
        if (len(ruless) == 0): continue
        cs_st, cs_ed, cd_st, cd_ed = cal_rule_range(ruless[0], ruless[1], ruless[2], ruless[3])
        if src >= cs_st and src <= cs_ed and dst >= cd_st and dst <= cd_ed:
            if (match(proto, sport, dport, ruless)):
                match_id = min(match_id, ruless[10])
    mask_tuples = node.children
    while len(mask_tuples) > 0:
        # assert len(mask_tuples) <= 1, f"Mask same! {mask_tuples}"
        next_mask_tuples: defaultdict[tuple[int,int], list[Node]] = defaultdict(list)
        for mask in mask_tuples:
            for child in mask_tuples[mask]:
                cs_st, cs_ed, cd_st, cd_ed = cal_rule_range(child.src, child.smask, child.dst, child.dmask)
                if src >= cs_st and src <= cs_ed and dst >= cd_st and dst <= cd_ed:
                    q_node += 1
                    q_rule += len(child.rules)
                    for rule in child.rules:
                        if (match(proto, sport, dport, rule)):
                            match_id = min(match_id, rule[10])
                    node = child
                    next_mask_tuples = node.children
                    break
        mask_tuples = next_mask_tuples
    return (0 if match_id == int(1e9) else match_id, q_node, q_rule)

if __name__ == "__main__":
    open("info.txt", "w").close()
    for loop in range(2, 3):
        file = open("info.txt", "a")
        file.write(f"==========iterate time: {loop}==========\n")
        file.close()
        for i in [1325, 295, 10,22,55,88,95,112,135,141,182,202][:1]:
            scale = i
            print(f"================= scaled {scale}k =================")
            init(loop)
            with open('rules_{}k'.format(scale), 'r') as file:
                rules = file.readlines()
                random.shuffle(rules)
                ip: list[RULE_TYPE] = []
                for rule in rules:
                    tp = rule.strip().split()
                    src, smask = map(int, tp[0].split('/'))
                    dst, dmask = map(int, tp[1].split('/'))
                    ip.append((src, countOnes(smask), dst, countOnes(dmask), int(tp[2]), tp[3], tp[4], int(tp[5]), int(tp[6]), int(tp[7]), int(tp[8])))
                tree = build(ip)
                print_info(tree)
                print("Build tree!")
                continue    
                with open('packets_{}k'.format(scale), 'r') as file:
                    pkts = file.readlines()
                    print("Query trace!")
                    err, query_node, query_rule = 0, 0, 0
                    for p in pkts:
                        pkt_id = int(p.strip().split()[0][3:])
                        pkt_bd: tuple[int,...] = tuple(map(int, p.strip().split()[1:]))
                        pkt: PACKET_TYPE = (pkt_bd[0], pkt_bd[1], pkt_bd[2], pkt_bd[3], pkt_bd[4], pkt_id if len(pkt_bd)<6 else pkt_bd[5])
                        match_id, q_node, q_rule = query_trace(tree, pkt)
                        if (match_id != pkt[-1]): 
                            err += 1
                        query_node += q_node
                        query_rule += q_rule
                    print(f"err: {err}, Node：{query_node/len(pkts):.2f} avg_num：{query_rule/len(pkts):.2f}")