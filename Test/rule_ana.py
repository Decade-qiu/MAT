import collections
import matplotlib.pyplot as plt
# read rule files 
for i in range(1, 23, 7):
    rule_set = []
    scale = i
    # if (i == 11): scale = 15
    # if (i == 12): scale = 22
    with open('../data/rules_{}k'.format(scale), 'r') as file:
        lines = file.readlines()
        for line in lines:
            rule_set.append(line.strip())
    src_dic = {}
    cx = cy = 0
    for rule in rule_set:
        tp = rule.split()
        src = tp[1]
        src += " "+tp[4]
        # src += " "+tp[4]
        # src += " "+tp[2]
        a = [int(t) for t in tp[4].split(':')]
        if (a[0] == a[1]): cx += 1
        else: cy += 1
        if src not in src_dic:
            src_dic[src] = 1
        else:
            src_dic[src] += 1
    cnt = [i for i in src_dic.values()]
    freq = collections.Counter(cnt)
    xlab = [k for k in freq.keys()]
    x = [i for i in range(1, len(xlab)+1)]
    y = [freq[k] for k in x]
    # x为横坐标 y为纵坐标 画柱状图
    plt.bar(x=x, height=y)
    plt.xticks(ticks=x, labels=xlab)
    plt.savefig("rule_freq.png")
    print(scale, min(cnt), max(cnt), cx, cy)