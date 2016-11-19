#!d:\\python27 python2.7
# -*- coding: utf8 -*-
# powermesh定义的RS编解码算法, 暂时没有找到python版本的开源好用的RS编解码器, 找到的一个reedsolo 0.3不知道是什么鬼

def rsencode_recover(vector):
    # 对RS编码后的向量恢复, 将vector分成20个元素一组的n组, 每组提取前10个元素组成新的vector返回
    # 最后一组如长度为20, 提取前10个, 如小于20, 提取
    
    n = len(vector) % 20
    assert(n == 0 or n > 10), "error vector length"
    
    if n > 0:
        last_group_dec = vector[-n:-10]
        vector = vector[:-n]
    else:
        last_group_dec = []
    
    return [vector[i] for i in range(len(vector)) if (i % 20 < 10)] + last_group_dec
    
def rsdecode_vec(rs_vec):
    # 暂时先用recover替代, 有时间再做rs解码版本
    # 暂时先说这么多jib
    return rsencode_recover(rs_vec)
    
if __name__ == "__main__":
    import time
    print rsencode_recover(range(1, 53))
    
    print u"结束"
    
    
