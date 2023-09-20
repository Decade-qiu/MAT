# # -*- coding: utf-8 -*-
from collections import defaultdict, Counter
import matplotlib.pyplot as plt

# for i in [1, 10 ,22 ,55]:
#     rule_set = []
#     scale = i
#     with open('../data/rules_{}k'.format(scale), 'r') as file:
#         lines = file.readlines()
#         for line in lines:
#             rule_set.append(line.strip())
#     key_dic = defaultdict(int)
#     sfull_cnt, dfull_cnt = 0, 0
#     srange_cnt, drange_cnt = 0, 0
#     sexact_cnt, dexact_cnt = 0, 0
#     srange_ex, drange_ex = 0, 0
#     src, dst, proto, sport, dport = defaultdict(int), defaultdict(int), defaultdict(int), defaultdict(int), defaultdict(int)
#     for rule in rule_set:
#         tp = rule.split()
#         keyi, maski = map(lambda x: hex(int(x))[2:], tp[0].split('/'))
#         a = [int(t) for t in tp[3].split(':')]
#         b = [int(t) for t in tp[4].split(':')]
#         key = ""
#         key += " "+tp[0]
#         key += " "+tp[1]
#         # key += " "+tp[2]
#         # key += " "+tp[3]
#         # if (tp[1]=='0/0'): continue
#         key += " "+tp[4]
#         if(b[0] != b[1]): key_dic[key] += 1
#         src[tp[0]] += 1
#         dst[tp[1]] += 1
#         proto[tp[2]] += 1
#         sport[tp[3]] += 1
#         dport[tp[4]] += 1
#         if (a[0] == a[1]): sexact_cnt += 1
#         elif (a[0] == 0 and a[1] == 65535): sfull_cnt += 1
#         else: 
#             srange_cnt += 1
#             srange_ex += a[1]-a[0]
#             # print(tp[3])
#         if (b[0] == b[1]): dexact_cnt += 1
#         elif (b[0] == 0 and b[1] == 65535): dfull_cnt += 1
#         else: 
#             drange_cnt += 1
#             drange_ex += b[1]-b[0]
#             # print(tp[4])
#     # print(len(key_dic))
#     cnt = [i for i in key_dic.values()]
#     freq = Counter(cnt)
#     freq = sorted(freq.items(), key=lambda x: x[0])
#     axlab = [k[0] for k in freq]
#     ax = [i for i in range(1, len(axlab)+1)]
#     ay = [k[1] for k in freq]
#     # x = [i for i in range(8)]
#     # y = [ay[i] for i in range(3)]
#     # y.extend([ay[i] for i in range(len(ay)-5, len(ay))])
#     # xlab = [axlab[i] for i in range(3)]
#     # xlab.extend([axlab[i] for i in range(len(axlab)-5, len(axlab))])
#     xlab = axlab
#     x = ax
#     y = ay
#     # print(x, y, xlab)
#     # x为横坐标 y为纵坐标 画柱状图
#     total_rule = 0
#     figure = plt.figure(figsize=(25, 10))
#     plt.subplots_adjust(left=0.03, right=0.93, bottom=0.05, top=0.93)
#     plt.bar(x=x, height=y, width=0.8)
#     plt.xticks(ticks=x, labels=xlab, rotation=0, fontsize=18)
#     for i in range(len(x)):
#         plt.text(x[i], y[i], str(y[i]), ha='center', va='bottom')
#         total_rule += xlab[i]*y[i]
#     plt.savefig("./pic/rule_{}k_freq.png".format(scale))
#     # for [k, v] in key_dic.items():
#     #     if (v == max(cnt)):
#     #         print(k, v)
#     print(scale, len(key_dic), total_rule)
#     print("sport: ", sexact_cnt, srange_cnt, sfull_cnt, srange_ex)
#     print("dport: ", dexact_cnt, drange_cnt, dfull_cnt, drange_ex)

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
total_Z = [0 for i in range(0, 2**32+1)]
for i in [1, 10, 22, 55]:
    scale = i
    fig = plt.figure()
    ax = fig.gca(projection='3d') 
    src_p_set = set()
    dst_p_set = set()
    X = []
    Y = []
    for i in range(0, 33):
        for j in range(0, 33):
            X.append(i)
            Y.append(j)
    Z = [0 for i in range(0, 33*33)]
    total_rule_num = 0
    with open('../data/rules_{}k'.format(scale), 'r') as file:
        lines = file.readlines()
        total_rule_num = len(lines)
        for line in lines:
            cur = line.strip().split()
            src_plen = bin(int(cur[0].split('/')[1])).count('1')
            dst_plen = bin(int(cur[1].split('/')[1])).count('1')
            Z[src_plen*33+dst_plen] += 1
            src_p_set.add(src_plen)
            dst_p_set.add(dst_plen)
    height = np.zeros_like(Z) 
    width = depth = 0.5 
    ax.bar3d(X, Y, height, width, depth, Z, shade=True)
    ax.set_xticks([0, 8, 16, 24, 32])  
    ax.set_yticks([0, 8, 16, 24, 32])  
    ax.set_xlabel('src_prefix_length')
    ax.set_ylabel('dst_prefix_length')
    ax.set_zlabel('rule_num')
    plt.savefig("./pic/rule_{}k_prefix.png".format(scale))
    # print(len(src_p_set), len(dst_p_set))
    cnt = []
    for i in range(0, 33):
        for j in range(0, 33):
            cnt.append([i, j, Z[i*33+j]])
            total_Z[i*33+j] += Z[i*33+j]/total_rule_num
    cnt.sort(key=lambda x: x[2], reverse=True)
    sum_v, sum_pr = 0, 0.0
    for i in range(0, 10):
        if (cnt[i][2] == 0): break
        sum_v += cnt[i][2]
        sum_pr += cnt[i][2]/total_rule_num
        # print(f"({cnt[i][0]}, {cnt[i][1]}) {cnt[i][2]} {cnt[i][2]/total_rule_num:.7%}")
        print(f"({cnt[i][0]}, {cnt[i][1]})", end=" ")
    print()
# total_cnt = []
# for i in range(0, 33):
#     for j in range(0, 33):
#         total_cnt.append([i, j, total_Z[i*33+j]])
# total_cnt.sort(key=lambda x: x[2], reverse=True)
# for i in range(0, 10):
#     print(f"({total_cnt[i][0]}, {total_cnt[i][1]})", end=" ")
# print()

# src_st = [8, 12, 16, 18, 20, 22, 24, 26, 28, 30, 32]
# src_st = [8, 16, 24, 28, 32]
# dst_st = [8, 12, 16, 22, 24, 26, 27, 28, 29, 31, 32]
# dst_st = [8, 16, 24, 28, 32]
# for i in [1, 10, 15, 22, 55]:
#     scale = i
#     rule_num = 0
#     src = defaultdict(int)
#     src_ori = defaultdict(int)
#     dst = defaultdict(int)
#     dst_ori = defaultdict(int)
#     src_diff_map = defaultdict(dict)
#     dst_diff_map = defaultdict(dict)
#     src_add = dst_add = 0
#     src_sum = dst_sum = 0
#     with open('../data/rules_{}k'.format(scale), 'r') as file:
#         lines = file.readlines()
#         rule_num = len(lines)
#         for line in lines:
#             cur = line.strip().split()
#             src_plen = bin(int(cur[0].split('/')[1])).count('1')
#             dst_plen = bin(int(cur[1].split('/')[1])).count('1')
#             if (src_plen != 0): 
#                 src_sum += 1
#                 src_ori[src_plen] += 1
#                 for prefix in src_st:
#                     if (prefix >= src_plen):
#                         src[prefix] += 1
#                         src_add += ((1 << (prefix-src_plen))-1)
#                         for add in range(1 << (prefix-src_plen)):
#                             ex_key = int(cur[0].split('/')[0]) + add << (32 - prefix)
#                             if (ex_key not in src_diff_map[prefix]):
#                                 src_diff_map[prefix][ex_key] = 1
#                             else:
#                                 src_diff_map[prefix][ex_key] += 1
#                         break
#             if (dst_plen != 0): 
#                 dst_sum += 1
#                 dst_ori[dst_plen] += 1
#                 for prefix in dst_st:
#                     if (prefix >= dst_plen):
#                         dst[prefix] += 1
#                         dst_add += ((1 << (prefix-dst_plen))-1)
#                         for add in range(1 << (prefix-dst_plen)):
#                             ex_key = int(cur[1].split('/')[0]) + add << (32 - prefix)
#                             if (ex_key not in dst_diff_map[prefix]):
#                                 dst_diff_map[prefix][ex_key] = 1
#                             else:
#                                 dst_diff_map[prefix][ex_key] += 1
#                         break
#     print(f"Scale: {scale}k")
#     src_worst, dst_worst = 0, 0
#     for k in src_st:
#         # print(f"src prefix: {k}")
#         cur = src_diff_map[k]
#         for [p, v] in sorted(cur.items(), key=lambda x: -x[1]):
#             print(f"({p},{v})", end=" ")
#             src_worst += v
#             break
#         # print()
#     for k in dst_st:
#         # print(f"dst prefix: {k}")
#         cur = dst_diff_map[k]
#         for [p, v] in sorted(cur.items(), key=lambda x: -x[1]):
#             print(f"({p},{v})", end=" ")
#             dst_worst += v
#             break
#         # print()
#     print("Worst query rules:", f"({src_worst},{rule_num}({src_add}),{src_worst/(rule_num+src_add):.3%})", f"({dst_worst},{rule_num}({dst_add}),{dst_worst/(rule_num+dst_add):.3%})")
#     print(f"extends src: {src_add}, {src_sum} {src_add/src_sum:.3%}")
#     print(f"extends dst: {dst_add}, {dst_sum} {dst_add/dst_sum:.3%}")
#     # for s in src_cnt:
#     #     print(f"({s[0]},{s[1]})", end=" ")
#     # print()
#     # for d in dst_cnt:
#     #     print(f"({d[0]},{d[1]})", end=" ")
#     # print()