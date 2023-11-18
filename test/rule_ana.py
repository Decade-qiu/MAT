# # -*- coding: utf-8 -*-
from collections import defaultdict, Counter
from ipaddress import *
from matplotlib import colors
from mpl_toolkits.mplot3d import Axes3D
import os, numpy as np, matplotlib.pyplot as plt

# 绘图防止乱码
plt.rcParams['font.sans-serif']='SimHei'
plt.rcParams['axes.unicode_minus']=False
plt.rcParams['ps.useafm'] = True
plt.rcParams['pdf.fonttype'] = 42

current_path = os.path.dirname(os.path.abspath(__file__))
parent_path = os.path.dirname(current_path)

global_total_rules = defaultdict(list)
rule_scale = [1, 10, 15, 55]
rule_field = [("src", 0), ("dst", 1), ("protocol", 2), ("sport", 3), ("dport", 4)]


def get_prefix(mask):
    return str(bin(int(mask))[2:].count('1'))

def get_rules():
    for i in rule_scale:
        with open(os.path.join(parent_path, f"data/rules_{i}k"), "r") as f:
            lines = f.readlines()
            for line in lines:
                tp = line.strip().split()
                src, smask = map(int, tp[0].split('/'))
                dst, dmask = map(int, tp[1].split('/'))
                assert src == (src & smask)
                assert dst == (dst & dmask)
                proto = int(tp[2])
                sport_start, sport_end = map(int, tp[3].split(':'))
                dport_start, dport_end = map(int, tp[4].split(':'))
                f1, f2, f3 = int(tp[5]), int(tp[6]), int(tp[7])
                match_rule_id = int(tp[8])
                if (f1 == 1 or f2 == 1 or f3 == 1):
                    continue
                global_total_rules[i].append((src, smask, dst, dmask, proto, sport_start, sport_end, dport_start, dport_end, f1, f2, f3, match_rule_id))

def show_field_cardinality():
    for i in rule_scale:
        src_set, dst_set, proto_set, sport_set, dport_set = set(), set(), set(), set(), set()
        print(f"================= scaled {i}k =================")
        for rule in global_total_rules[i]:
            src_set.add((rule[0], rule[1]))
            dst_set.add((rule[2], rule[3]))
            proto_set.add(rule[4])
            sport_set.add((rule[5], rule[6]))
            dport_set.add((rule[7], rule[8]))
        print(f"src cardinality: {len(src_set)}")
        print(f"dst cardinality: {len(dst_set)}")
        print(f"proto cardinality: {len(proto_set)}")
        print(f"sport cardinality: {len(sport_set)}")
        print(f"dport cardinality: {len(dport_set)}")
        print()
        # break

def show_field_distribution():
    field_data = [[], [], [], [], []]
    for scale in rule_scale:
        rules = global_total_rules[scale]
        src_cnt, dst_cnt, proto_cnt, sport_cnt, dport_cnt = defaultdict(int), defaultdict(int), defaultdict(int), defaultdict(int), defaultdict(int)
        src_mask, dst_mask = defaultdict(set), defaultdict(set)
        for rule in rules:
            src_cnt[(rule[0], rule[1])] += 1
            src_mask[rule[0]].add(rule[1])
            dst_cnt[(rule[2], rule[3])] += 1
            dst_mask[rule[2]].add(rule[3])
            proto_cnt[rule[4]] += 1
            sport_cnt[(rule[5], rule[6])] += 1
            dport_cnt[(rule[7], rule[8])] += 1
        src_cnt = sorted(src_cnt.items(), key=lambda x: -x[1])
        dst_cnt = sorted(dst_cnt.items(), key=lambda x: -x[1])
        proto_cnt = sorted(proto_cnt.items(), key=lambda x: -x[1])
        sport_cnt = sorted(sport_cnt.items(), key=lambda x: -x[1])
        dport_cnt = sorted(dport_cnt.items(), key=lambda x: -x[1])
        src_mask = sorted(src_mask.items(), key=lambda x: -len(x[1]))
        dst_mask = sorted(dst_mask.items(), key=lambda x: -len(x[1]))
        # 画出分布图
        field_data[0].append(([i for i in range(len(src_cnt))], [i[1] for i in src_cnt]))
        field_data[1].append(([i for i in range(len(dst_cnt))], [i[1] for i in dst_cnt]))
        field_data[2].append(([i for i in range(len(proto_cnt))], [i[1] for i in proto_cnt]))
        field_data[3].append(([i for i in range(len(sport_cnt))], [i[1] for i in sport_cnt]))
        field_data[4].append(([i for i in range(len(dport_cnt))], [i[1] for i in dport_cnt]))
    for field_name, field_id in rule_field:
        plt.figure()
        plt.xlabel(field_name)
        plt.ylabel(f"{field_name}重复出现的次数")
        for i in range(len(rule_scale)):
            scale = rule_scale[i]
            x, y = field_data[field_id][i]
            plt.plot(x, y, label=f"{scale}k")     
            # plt.bar(x, y, label=f"{scale}k")
        plt.legend()
        plt.savefig(os.path.join(current_path, f"pic/{field_name}_distribution.jpg"), dpi=800)


def show_ip_mask_distribution():
    for i in rule_field[:2]:
        field_name, field_id = i
        plt.figure()
        plt.ylabel(f"{field_name}掩码长度")
        plt.xlabel(f"rule数量")
        rules = global_total_rules[rule_scale[-1]]
        mask_cnt = defaultdict(int)
        for rule in rules:
            mask = get_prefix(rule[field_id*2+1])
            mask_cnt[mask] += 1
        mask_cnt = sorted(mask_cnt.items(), key=lambda x: x[0])
        x, y = [i[0] for i in mask_cnt], [i[1] for i in mask_cnt]
        plt.barh(x, y, label=f"{rule_scale[-1]}k")
        plt.legend()
        for i in range(len(x)):
            plt.text(y[i], x[i], f" {y[i]/len(rules)*100:.1f}%", fontsize=8, ha='left', va='center')
        y_ticks = [0, 8, 16, 24, 32]
        plt.yticks(y_ticks, y_ticks)
        plt.savefig(os.path.join(current_path, f"pic/{field_name}_mask_distribution.jpg"), dpi=800)


def show_src_dst_tuple_mask_3D_distribution():
    scale = rule_scale[-1]
    fig = plt.figure()
    ax = fig.gca(projection='3d') 
    X = []
    Y = []
    for i in range(0, 33):
        for j in range(0, 33):
            X.append(i)
            Y.append(j)
    Z = [0 for i in range(0, 33*33)]
    for line in global_total_rules[scale]:
        src_plen = get_prefix(line[1])
        dst_plen = get_prefix(line[3])
        Z[src_plen*33+dst_plen] += 1
    max_count = max(Z[:-1])
    cmap = plt.cm.get_cmap('coolwarm')
    height = np.zeros_like(Z) 
    width = depth = 0.5 
    ax.bar3d(X, Y, height, width, depth, Z, color=cmap(np.array(Z)/max_count))
    ax.grid(True)
    plt.title('Source-Destination Prefix Length Distribution', fontsize=14, fontweight='bold')
    ax.set_xticks([0, 8, 16, 24, 32])  
    ax.set_yticks([0, 8, 16, 24, 32])  
    ax.set_xlabel('src_prefix_len')
    ax.set_ylabel('dst_prefix_len')
    ax.set_zlabel('rule_num')
    ax.view_init(elev=30, azim=-45)
    # fig.set_size_inches(9, 7)
    fig.savefig(os.path.join(current_path, f"pic/src_dst_tuple_mask_3D_distribution.jpg"), dpi=800)
        
def show_port_distribution():
    for i in rule_field[3:]:
        field_name, field_id = i
        rules = global_total_rules[rule_scale[-1]]
        range_port, exact_port, all_range = 0, 0, 0
        sp_range = 0
        for rule in rules:
            port_start, port_end = rule[field_id*2-1], rule[field_id*2]
            if port_start == port_end:
                exact_port += 1
            elif port_start==0 and port_end==65535:
                all_range += 1
            elif port_start==1024 and port_end==65535:
                range_port += 1
            else:
                sp_range += 1
        plt.figure()
        plt.pie([exact_port, all_range, range_port, sp_range], labels=['exact_port', 'all_range', 'range_port', 'sp_range'], autopct='%1.1f%%', pctdistance=0.8, labeldistance=1.1)
        plt.savefig(os.path.join(current_path, f"pic/{field_name}_port_pie.jpg"), dpi=800)

def show_src_dst_distribution():
    plt.figure()
    plt.xlabel(f"src-dst tuple")
    plt.ylabel(f"src-dst tuple重复出现的次数")
    for scale in rule_scale:
        rules = global_total_rules[scale]
        src_dst_tuple = defaultdict(int)
        for rule in rules:
            src_dst_tuple[(rule[0], rule[1], rule[2], rule[3])] += 1
        src_dst_tuple = sorted(src_dst_tuple.items(), key=lambda x: -x[1])
        x, y = [i for i in range(len(src_dst_tuple))], [i[1] for i in src_dst_tuple]
        plt.scatter(x, y, label=f"{scale}k", s=2)
    plt.legend()
    plt.savefig(os.path.join(current_path, f"pic/src_dst_tuple_distribution.jpg"), dpi=800)

def show_port_tuple_distribution():
    rules = global_total_rules[rule_scale[-1]]
    binary_binary, binary_interval, binary_ternary = 0, 0, 0
    interval_binary, interval_interval, interval_ternary = 0, 0, 0
    ternary_binary, ternary_interval, ternary_ternary = 0, 0, 0
    for rule in rules:
        sport_start, sport_end = rule[5], rule[6]
        dport_start, dport_end = rule[7], rule[8]
        if sport_start == sport_end:
            if dport_start == dport_end:
                binary_binary += 1
            elif dport_start==0 and dport_end==65535:
                binary_ternary += 1
            else:
                binary_interval += 1
        elif sport_start==0 and sport_end==65535:
            if dport_start == dport_end:
                ternary_binary += 1
            elif dport_start==0 and dport_end==65535:
                ternary_ternary += 1
            else:
                ternary_interval += 1
        else:
            if dport_start == dport_end:
                interval_binary += 1
            elif dport_start==0 and dport_end==65535:
                interval_ternary += 1
            else:
                interval_interval += 1
    labels = ['(Binary,Binary)', '(Binary,Interval)', '(Binary,Ternary)', '(Interval,Binary)', '(Interval,Interval)', '(Interval,Ternary)', '(Ternary,Binary)', '(Ternary,Interval)', '(Ternary,Ternary)']
    sizes = [binary_binary, binary_interval, binary_ternary, interval_binary, interval_interval, interval_ternary, ternary_binary, ternary_interval, ternary_ternary]
    tp = zip(sizes, labels)
    tp = sorted(tp, key=lambda x: -x[0])
    sizes, labels = [i[0] for i in tp], [i[1] for i in tp]
    fig, ax = plt.subplots()
    total_sum, maxv = sum(sizes), max(sizes)
    explode = [0.05*i for i in range(len(sizes))]
    ax.pie(sizes, labels=None, startangle=90, autopct='%1.1f%%', pctdistance=0.8, explode=explode)
    ax.axis('equal')
    plt.legend(labels, loc='upper right', bbox_to_anchor=(1.1, 0.3), fontsize=8)
    plt.savefig(os.path.join(current_path, f"pic/port_tuple_pie.jpg"), dpi=800)

def splitRange(start, end, L):
    res = []
    mask = ((1 << 16)-1) ^ ((1 << L)-1)
    while 1:
        if start&mask == end&mask:
            res.append((start, end))
            break
        else:
            res.append((start, start|((1<<L)-1)))
            start = start|((1<<L)-1)
            start += 1
    return res

def show_src_dst_port_distribution():
    plt.figure()
    L = 4
    prefix_mask = (((1 << 16)-1) ^ ((1 << L)-1))
    for scale in rule_scale[0:1]:
        scale = rule_scale[-1]
        rules = global_total_rules[scale]
        src_dst_tuple = defaultdict(list)
        src_dst_no_exact_tuple = defaultdict(list)
        src_dst_port_split = defaultdict(dict)
        for rule in rules:
            key = str(IPv4Address(rule[0])) + '/' + get_prefix(rule[1]) + '-' + str(IPv4Address(rule[2])) + '/' + get_prefix(rule[3])
            dport_st, dport_ed = rule[7], rule[8]
            src_dst_tuple[key].append(rule[4:9])
            if key not in src_dst_no_exact_tuple:
                src_dst_no_exact_tuple[key] = []
            if (dport_st != dport_ed):
                src_dst_no_exact_tuple[key].append(tuple(list(rule[4:9])+[rule[-1]]))
            key_tuple = src_dst_port_split[key]
            if (dport_ed - dport_st+1 > (1<<L)):
                continue
            for (st, ed) in splitRange(dport_st, dport_ed, L):
                index = st & prefix_mask
                assert index == (ed & prefix_mask)
                if index not in key_tuple:
                    key_tuple[index] = []
                key_tuple[index].append((st, ed, rule[4:9], rule[-1]))
        src_dst_tuple = sorted(src_dst_tuple.items(), key=lambda x: -len(x[1]))
        src_dst_no_exact_tuple = sorted(src_dst_no_exact_tuple.items(), key=lambda x: -len(x[1]))
        for key in src_dst_port_split:
            print(f"================={key}=================")
            for p_tuple in src_dst_port_split[key]:
                print(f"-----------------port {p_tuple}-----------------")
                sorted_p_tuple = sorted(src_dst_port_split[key][p_tuple], key=lambda x: x[0])
                for (st, ed, rule, id) in sorted_p_tuple:
                    print(f"{st}-{ed} {rule} {id}")

def verfiy_dataset_distribution():
    for scale in rule_scale:
        rules = global_total_rules[scale]
        hard_cnt = 0
        for rule in rules:
            src, smask, dst, dmask, proto, sport_start, sport_end, dport_start, dport_end, f1, f2, f3, match_rule_id = rule
            assert src == (src & smask)
            assert dst == (dst & dmask)
            assert f1+f2+f3 == 0
            if (dport_start==0 and dport_end==65535) or (dport_start==1024 and dport_end==65535): 
                if not (sport_start==sport_end or (sport_start==0 and sport_end==65535) or (sport_start==1024 and sport_end==65535)):
                    hard_cnt += 1
                    pass
            else:
                assert sport_start==sport_end or (sport_start==0 and sport_end==65535) or (sport_start==1024 and sport_end==65535)
        print(f"{hard_cnt} {len(rules)} {hard_cnt/len(rules)*100:.1f}%")


def show_src_dst_sport_dport_distribution():
    for scale in rule_scale[len(rule_scale)-1:len(rule_scale)]:
        rules = global_total_rules[scale]
        src_dst_tuple = defaultdict(list)
        exact_dport = 0
        exact_dport_es, exact_dport_rs, exact_dport_ts = 0, 0, 0
        exact_dport_urs = 0
        for rule in rules:
            # if not (rule[7] == rule[8]): continue
            # if not (rule[7]==0 and rule[8]==65535): continue
            # if not (rule[7]==1024 and rule[8]==65535): continue
            if ((rule[7] == rule[8]) or (rule[7]==0 and rule[8]==65535) or (rule[7]==1024 and rule[8]==65535)): continue
            key = (rule[0], rule[1], rule[2], rule[3], rule[4], rule[7], rule[8])
            src_dst_tuple[key].append(rule)
            exact_dport += 1
            if (rule[5] == rule[6]): 
                exact_dport_es += 1
                # key = (rule[0], rule[1], rule[2], rule[3], rule[5], rule[6],rule[7], rule[8])
                # src_dst_tuple[key].append(rule)
            elif (rule[5] == 0 and rule[6] == 65535): 
                exact_dport_ts += 1
                key = (rule[0], rule[1], rule[2], rule[3], rule[7], rule[8])
                # src_dst_tuple[key].append(rule)
            elif (rule[5] == 1024 and rule[6] == 65535):
                exact_dport_rs += 1
                # key = (rule[0], rule[1], rule[2], rule[3], rule[7], rule[8])
                # src_dst_tuple[key].append(rule)
            else:
                exact_dport_urs += 1
                # key = (rule[0], rule[1], rule[2], rule[3], rule[5], rule[6], rule[7], rule[8])
                # src_dst_tuple[key].append(rule)
        print(f"{exact_dport_es/exact_dport*100:.3f}% {exact_dport_ts/exact_dport*100:.3f}% {exact_dport_rs/exact_dport*100:.3f}% {exact_dport_urs/exact_dport*100:.3f}%")
        maxv, rule, cnt = 0, None, 0
        for (k, v) in src_dst_tuple.items():
            # if (len(v) != 1): cnt += 1
            if (len(v) > maxv):
                if (v[0][7]==0 and v[0][8]==1023): continue
                maxv = len(v)
                rule = v
        print(f"======={scale}k=======")
        print(len(rule))
        for i in rule:
            print(i)


if __name__ == "__main__":
    get_rules()
    # show_field_cardinality()
    # show_field_distribution()
    # show_ip_mask_distribution()
    # show_src_dst_tuple_mask_3D_distribution()
    # show_src_dst_distribution()
    # show_port_distribution()
    # show_port_tuple_distribution()
    show_src_dst_port_distribution()
    # show_src_dst_sport_dport_distribution()
    # verfiy_dataset_distribution()
    

