"""
PageRank 模块
基于论文引用关系构建有向图，计算 PageRank 分数
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class PageRank:
    """
    PageRank 算法实现

    原理:
    PageRank 是 Google 创始人 Larry Page 提出的网页重要性评估算法。

    核心思想:
    - 一个网页的重要性取决于链接到它的其他网页的数量和质量
    - 被更多重要网页引用的网页，其 PageRank 值更高

    公式:
    PR(A) = (1-d)/N + d × Σ(PR(Ti)/C(Ti))
    其中:
    - d: 阻尼因子 (damping factor)，通常为 0.85
    - N: 总节点数
    - Ti: 链接到 A 的节点
    - C(Ti): 节点 Ti 的出链数

    在学术论文场景中:
    - 节点 = 论文
    - 边 = 引用关系（论文 A 引用论文 B，则 A → B）
    - 被引用次数多的论文 PageRank 值更高
    """

    def __init__(self, damping=None, iterations=None):
        self.damping = damping or config.PAGERANK_DAMPING
        self.iterations = iterations or config.PAGERANK_ITERATIONS
        self.scores = {}

    def compute(self, citation_graph):
        """
        计算 PageRank 分数

        Args:
            citation_graph: dict, {paper_id: [引用的 paper_id 列表]}
                           注意: A 引用 B 表示 A → B 的有向边

        Returns:
            dict: {paper_id: pagerank_score}
        """
        nodes = list(citation_graph.keys())
        n = len(nodes)

        if n == 0:
            return {}

        node_to_idx = {node: i for i, node in enumerate(nodes)}

        # 构建邻接矩阵（转置：记录入链）
        # M[i][j] = 1/C(j) 如果 j 链接到 i
        M = np.zeros((n, n))

        for source, targets in citation_graph.items():
            source_idx = node_to_idx[source]
            valid_targets = [t for t in targets if t in node_to_idx]
            if valid_targets:
                for target in valid_targets:
                    target_idx = node_to_idx[target]
                    # source 引用 target，表示 source → target
                    # 在 PageRank 中，target 获得 source 的 PR 值的一部分
                    M[target_idx][source_idx] = 1.0 / len(valid_targets)

        # 迭代计算 PageRank
        pr = np.ones(n) / n  # 初始均匀分布
        teleport = (1 - self.damping) / n

        print(f"开始计算 PageRank (节点数: {n}, 阻尼因子: {self.damping})")

        for iteration in range(self.iterations):
            new_pr = teleport + self.damping * M.dot(pr)

            # 处理悬挂节点（没有出链的节点）
            dangling_sum = self.damping * sum(
                pr[node_to_idx[node]]
                for node in nodes
                if not citation_graph.get(node, [])
            ) / n
            new_pr += dangling_sum

            # 检查收敛
            diff = np.abs(new_pr - pr).sum()
            pr = new_pr

            if diff < 1e-8:
                print(f"PageRank 在第 {iteration + 1} 次迭代后收敛 (diff={diff:.2e})")
                break

        # 转换为字典
        self.scores = {nodes[i]: float(pr[i]) for i in range(n)}

        # 打印统计
        scores_arr = np.array(list(self.scores.values()))
        print(f"PageRank 统计: mean={scores_arr.mean():.6f}, "
              f"max={scores_arr.max():.6f}, min={scores_arr.min():.6f}")

        return self.scores

    def get_top_papers(self, k=20):
        """获取 PageRank 值最高的 k 篇论文"""
        sorted_papers = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_papers[:k]

    def get_score(self, paper_id):
        """获取单篇论文的 PageRank 分数"""
        return self.scores.get(paper_id, 0.0)
