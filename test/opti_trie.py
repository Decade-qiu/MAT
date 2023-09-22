# # -*- coding: utf-8 -*-
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
from ipaddress import *
# aaa = "[0, 0, 0, 0, 1, []], 
#             [0, 0, 1, 2**32, 1, []], 
#             [1, 2**32, 0, 0, 1, []], 
#             [1, 2**8, 1, 2**8, 1, []], 
#             [1, 2**8, 2**8+1, 2**32, 1, []], 
#             [2**8+1, 2**32, 1, 2**8, 1, []],
#             [2**8+1, 2**16, 2**8+1, 2**16, 1, []], 
#             [2**8+1, 2**16, 2**16+1, 2**32, 1, []], 
#             [2**16+1, 2**32, 2**8+1, 2**16, 1, []],
#             [2**16+1, 2**24, 2**16+1, 2**24, 1, []], 
#             [2**16+1, 2**24, 2**24+1, 2**32, 1, []], 
#             [2**24+1, 2**32, 2**16+1, 2**24, 1, []]"
level = [
    [0, 2**28-1, 0, 2**28-1, 1, []],
    [0, 2**28-1, 2**28, 2**32-1, 1, []],
    [2**28, 2**32-1, 0, 2**28-1, 1, []], 
]
def divideRegion(x_start, x_end, y_start, y_end, x_per_len = 8, y_per_len = 8):
    x_length = x_end - x_start+1  # x 范围的长度
    y_length = y_end - y_start+1  # y 范围的长度
    x_interval = x_length // x_per_len  # x 范围每个区域的长度
    y_interval = y_length // y_per_len  # y 范围每个区域的长度
    if (x_interval == 0):
        x_per_len = 1
        x_interval = x_length
    if (y_interval == 0):
        y_per_len = 1
        y_interval = y_length
    # print(x_interval, y_interval, x_per_len, y_per_len)
    regions = []  # 存储划分后的区域坐标
    x, xe, y, ye = 0, 0, 0, 0
    for i in range(x_per_len):
        for j in range(y_per_len):
            x = x_start + i * x_interval  # 区域左上角 x 坐标
            xe = x+x_interval-1
            y = y_start + j * y_interval  # 区域左上角 y 坐标
            ye = y+y_interval-1
            regions.append([x, xe, y, ye, 1, []])
            if (j == y_per_len-1 and ye < y_end):
                regions.append([x, xe, ye+1, y_end, 1, []])
        if (i == x_per_len-1 and xe < x_end):
            for j in range(y_per_len):
                y = y_start + j * y_interval
                ye = y+y_interval-1
                regions.append([xe+1, x_end, y, ye, 1, []])
                if (j == y_per_len-1 and ye < y_end):
                    regions.append([xe+1, x_end, ye+1, y_end, 1, []])
    return regions
# print("\n".join(str(item) for item in divideRegion(0, 2, 0, 3, 2, 2)))
# exit()

level_depth = 1+4
cur = level
for i in range(level_depth-1):
    tp = []
    for j in range(len(cur)):
        nxt = divideRegion(cur[j][0], cur[j][1], cur[j][2], cur[j][3])
        cur[j][5].extend(nxt)
        tp.extend(nxt)
    cur = tp
level.append([2**28, 2**32-1, 2**28, 2**32-1, 1, []])
cur = [level[-1]]
for i in range(level_depth-1):
    tp = []
    for j in range(len(cur)):
        nxt = divideRegion(cur[j][0], cur[j][1], cur[j][2], cur[j][3], 4, 4)
        cur[j][5].extend(nxt)
        tp.extend(nxt)
    cur = tp

cur = level
for i in range(level_depth):
    tp = []
    print(f"level {i}: {len(cur)}")
    for j in range(len(cur)):
        tp.extend(cur[j][5])
    cur = tp
# exit()

for i in [1, 10, 15, 22][:]:
    rule_set = []
    scale = i
    # insert rules
    print(f"================= scaled {scale}k =================")
    with open('../data/rules_{}k'.format(scale), 'r') as file:
        lines = file.readlines()
        for line in lines:
            line = line.strip()
            rule_set.append(line)
            tp = line.split()
            src_key, src_mask = map(int, tp[0].split('/'))
            assert src_key == (src_key & src_mask)
            src_key &= src_mask
            dst_key, dst_mask = map(int, tp[1].split('/'))
            assert dst_key == (dst_key & dst_mask)
            dst_key &= dst_mask
            src_start, src_end = src_key, src_key + ((1<<32)-1-src_mask)
            dst_start, dst_end = dst_key, dst_key + ((1<<32)-1-dst_mask)
            cur = level
            for i in range(level_depth):
                nxt = []
                for j in range(len(cur)):
                    if ((src_start > cur[j][1] or src_end < cur[j][0]) or (dst_start > cur[j][3] or dst_end < cur[j][2])):
                        continue
                    cur[j][4] += 1
                    nxt.extend(cur[j][5])
                cur = nxt   
    # print level trie structure
    cur = level
    for i in range(level_depth):
        max_b, dx, dy = 0, 0, 0
        nxt = []
        for j in range(len(cur)):
            nxt.extend(cur[j][5])
            if (cur[j][4] != 0):
                if cur[j][4] > max_b:
                    max_b = cur[j][4]
                    dx, dy = i, j
        #         print(f"{'L' if cur[j][4]==0 else ''}{cur[j][4]}", end=" ")
        # print()
        print(f"level {i}: num={len(cur)} max_buckets={max_b}({cur[dy][:-1]})")
        cur = nxt
    # continue
    # packet query
    total_query_rules = 0
    total_packets, add = 0, 0
    hit_map = dict()
    with open('../data/packets_{}k'.format(scale), 'r') as file:
        lines = file.readlines()
        total_packets = len(lines)
        for line in lines:
            line = line.strip()
            tp = line.split()
            src, dst = map(int, tp[1:3])
            cur = level
            for i in range(level_depth):
                nxt = []
                for j in range(len(cur)):
                    if (src >= cur[j][0] and src <= cur[j][1] and dst >= cur[j][2] and dst <= cur[j][3]):
                        nxt.extend(cur[j][5])
                        if (i == level_depth-1): 
                            total_query_rules += cur[j][4]
                            dk = str(i)+" "+str(j)
                            qrange = [IPv4Address(cur[j][0]), IPv4Address(cur[j][1]), IPv4Address(cur[j][2]), IPv4Address(cur[j][3])]
                            if (dk not in hit_map):
                                hit_map[dk] = [1, cur[j][4], [str(ip) for ip in qrange]]
                            else:
                                hit_map[dk][0] += 1
                        break
                cur = nxt
    print("\n".join(str(item) for item in sorted(hit_map.items(), key=lambda x: -x[1][0]*x[1][1])[:10]))
    print(f"total_query_rules={total_query_rules}({total_query_rules/total_packets})")

    