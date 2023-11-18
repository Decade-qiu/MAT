# -*- coding: utf-8 -*-
from collections import defaultdict, Counter
from ipaddress import *
import os
from matplotlib import pyplot as plt

# 绘图防止乱码
plt.rcParams['font.sans-serif']='SimHei'
plt.rcParams['axes.unicode_minus']=False
plt.rcParams['ps.useafm'] = True
plt.rcParams['pdf.fonttype'] = 42

current_path = os.path.dirname(os.path.abspath(__file__))
parent_path = os.path.dirname(current_path)

global_bgp_rules = defaultdict(list)
bgp_rule_scale = [115]

def show_ip_cardinality():
    rules = global_bgp_rules[bgp_rule_scale[-1]]
    ip_mask = defaultdict(list)
    for rule in rules:
        ip_mask[(rule[0], rule[1])].append(rule[2])
    ip_mask = sorted(ip_mask.items(), key=lambda x: -len(x[1]))
    for i in range(10):
        print(f"======={ip_mask[i][0]}======")
        for x in ip_mask[i][1]:
            print(x)
    print(f"ip_mask cardinality: {len(ip_mask)} rules num: {len(rules)}")

def get_bgp_rule():
    for i in bgp_rule_scale:
        rule_set = set()
        with open(os.path.join(parent_path, "data/bview.20020722.2337.gz.bgp"), 'r') as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                ori = line
                line = line.split("|")
                ip, mask = line[5].split("/")
                global_bgp_rules[i].append((int(IPv4Address(ip)), int(mask), ori))
                rule_set.add((int(IPv4Address(ip)), int(mask)))
        rule_set = sorted(rule_set, key=lambda x: x[1])
        with open(os.path.join(parent_path, "data/bgp_115k"), 'w') as f:
            for bgp_rule in rule_set:
                f.write(str(bgp_rule[0])+" "+str(bgp_rule[1])+"\n")

def show_ip_distribution():
    plt.figure()
    plt.xlabel(f"ip地址")
    plt.ylabel(f"ip地址重复出现的次数")
    rules = global_bgp_rules[bgp_rule_scale[-1]]
    ip = defaultdict(int)
    for rule in rules:
        ip[(rule[0], rule[1])] += 1
    ip = sorted(ip.items(), key=lambda x: -x[1])
    x, y = [i for i in range(len(ip))], [i[1] for i in ip]
    plt.plot(x, y, label=f"{bgp_rule_scale[-1]}k")
    plt.yticks([1, 2, 3, 4, 5])
    plt.legend()
    plt.savefig(os.path.join(current_path, f"pic/bgp_ip_distribution.jpg"), dpi=800)


def show_bgp_ip_mask_distribution():
    plt.figure()
    plt.ylabel(f"ip掩码长度")
    plt.xlabel(f"rule数量")
    mask_cnt = defaultdict(int)
    rules = global_bgp_rules[bgp_rule_scale[-1]]
    for rule in rules:
        mask_cnt[rule[1]] += 1
    mask_cnt = sorted(mask_cnt.items(), key=lambda x: x[0])
    x, y = [i[0] for i in mask_cnt], [i[1] for i in mask_cnt]
    plt.barh(x, y, label=f"{bgp_rule_scale[-1]}k")
    plt.legend()
    for i in range(len(x)):
        plt.text(y[i], x[i], f" {y[i]/len(rules)*100:.1f}%", fontsize=8, ha='left', va='center')
    y_ticks = [0, 8, 16, 24, 32]
    plt.yticks(y_ticks, y_ticks)
    plt.savefig(os.path.join(current_path, f"pic/bgp_mask_distribution.jpg"), dpi=800)

if __name__ == "__main__":
    get_bgp_rule()
    # show_ip_cardinality()
    # show_ip_distribution()
    # show_bgp_ip_mask_distribution()
    
