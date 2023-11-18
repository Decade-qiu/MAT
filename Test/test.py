
zero_th = [
    [2332608, 3932406, 2692618, 3911404],
    [2210851, 3264289, 4077729, 4632201],
    [2994418, 2994418, 2514270, 3057416],
    [4391541, 3159898, 3586021, 4630434],
    [2595967, 3177641, 2829696, 2826775]
]

# 计算zero_th的平均值 不用np
def cal(a):
    x = []
    for i in range(len(a[0])):
        sum = 0
        for j in range(len(a)):
            sum += a[j][i]
        x.append(sum/len(a))
    return x

print(cal(zero_th))