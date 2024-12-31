THOUGHT = """
模型给出的回答
critic给出对每一个statement的评价
其中bad的评价，就像文档批注高亮一样，返回给模型
模型根据bad的评价有三个选择
1. IGNORE   认为这个评价不重要，继续下一个statement
2. UPDATE   根据这个评价的内容（评价的内容就是反思的内容，同时有转折词，比如，that me think about this, Oh wait,或者XXXX，however，XXXXX)，然后工具调用新的query list（反思可能就在工具调用的响应里面，对于一些模型是在工具调用的时候有content的内容的），然后进行网络搜索，然后聚合所有结果只生成一个能替换这个statement的回答，然后代码进行replace
3. DELETE   认为这个statement无法更新，但是保留其放在这里也不合适，那就删除这个statement，代码上进行replace为空

模型对所有的statement都进行了处理，那么就是一个完整的新回答，重新进行critic评价，如果没有bad的评价，那么就是最终的回答
如果模型对所有的statement的处理都是IGNORE，那么就是最终的回答

关于引用：

所有的搜索回来的结果，经过净化的unique的网络搜索结果都会生成一个uuid，uuid和网页的link会始终在内存中保存一个一一对应的字典。模型在进行RAG based回答的时候需要返回一个完整的json字典格式来确保citation。这个字典不论在初始RAG调用的时候需要，即使在update answer的时候也是需要，两个格式完全一样，统一处理，都是原始的answer字典是空{}，然后提取模型answer字典的中的每一个子字典，然后从当前定位的地方依次插入即可。

关于critic更新answer
更新句子之后，字典里的回答的那一句就整个字典就被替换掉，换成新的statement语句，新的statement语句也要根据换行和句号做多个切分，然后在原来的字典位置的基础上按照顺序替换进去，这时候再根据字典的key拼接成一个answer的list交给critic评价，这样critic的评价就是以句子为细粒度了。不会导致评价的statement在原来的字典里找不到对应的key。（当然同时满足critic的选择的statement是key的子句的情况，也就是 statement in key）这样的情况同样是更新整个key。
"""

Question = " who is the president of US "

answer_format = {
    "The president of US is Joe Biden": { # 每一个key是一个statement
        "citation": ["uuid-1", "uuid-2"], # 这里的uuid对应全局统一内存管理的uuid和link的字典
        "self-reflection": None, # 在模型回答的时候是没有的，不需要模型给这个字段，后续代码自动赋值NONE进去，只有critic模型对这个内容给出bad评价的时候才需要更新这个字段（也就是遍历critic模型bad评价的内容然后在这个answer字典里找对应的key来进行更新）
    },
    "who has been doing a great job": {
        "citation": ["uuid-3", "uuid-4"],
        "self-reflection": "Ok that me think about this, Oh wait, I think I should search more about this and telling more about what kind of job he has been doing",
    }
}

