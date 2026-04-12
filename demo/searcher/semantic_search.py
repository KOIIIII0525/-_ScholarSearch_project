"""
语义搜索模块
使用 TF-IDF 向量 + 余弦相似度实现语义相似论文推荐
"""
import os
import sys
import json

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class SemanticSearch:
    """
    语义搜索引擎

    原理:
    1. 使用 TF-IDF 将论文文本向量化
       - TF (词频): 词在文档中出现的频率
       - IDF (逆文档频率): log(总文档数 / 包含该词的文档数)
       - TF-IDF = TF × IDF
    2. 计算查询向量与文档向量的余弦相似度
       - cos(θ) = (A · B) / (|A| × |B|)
    3. 返回最相似的文档

    与 BM25 的区别:
    - BM25 基于概率模型，有饱和函数和文档长度归一化
    - TF-IDF 余弦相似度基于向量空间模型
    - 两者可以互补使用
    """

    def __init__(self, papers=None):
        self.papers = []
        self.vectorizer = TfidfVectorizer(
            max_features=10000,
            stop_words='english',
            ngram_range=(1, 2),  # 使用 uni-gram 和 bi-gram
            sublinear_tf=True,   # 使用 1 + log(tf) 替代 tf
        )
        self.tfidf_matrix = None
        self.paper_ids = []

        if papers:
            self.fit(papers)

    def fit(self, papers):
        """
        构建 TF-IDF 向量矩阵

        Args:
            papers: 论文列表
        """
        self.papers = papers
        self.paper_ids = [p['arxiv_id'] for p in papers]

        # 合并标题和摘要作为文档内容
        documents = [
            f"{p['title']} {p['abstract']}"
            for p in papers
        ]

        self.tfidf_matrix = self.vectorizer.fit_transform(documents)
        print(f"TF-IDF 矩阵: {self.tfidf_matrix.shape}")
        print(f"词汇表大小: {len(self.vectorizer.vocabulary_)}")

    def search(self, query, top_k=None):
        """
        语义搜索：找到与查询最相似的论文

        Args:
            query: 查询字符串
            top_k: 返回前 k 个结果

        Returns:
            list[dict]: [(paper, similarity_score), ...]
        """
        if self.tfidf_matrix is None:
            return []

        top_k = top_k or config.SEMANTIC_TOP_K

        # 将查询转为 TF-IDF 向量
        query_vec = self.vectorizer.transform([query])

        # 计算余弦相似度
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        # 获取 top-k 索引
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if similarities[idx] > 0:
                paper = self.papers[idx].copy()
                paper['semantic_score'] = float(similarities[idx])
                results.append(paper)

        return results

    def find_similar(self, arxiv_id, top_k=None):
        """
        找到与指定论文最相似的论文

        Args:
            arxiv_id: 目标论文的 arXiv ID
            top_k: 返回前 k 个结果

        Returns:
            list[dict]: 相似论文列表
        """
        if self.tfidf_matrix is None:
            return []

        top_k = top_k or config.SEMANTIC_TOP_K

        # 找到目标论文的索引
        try:
            idx = self.paper_ids.index(arxiv_id)
        except ValueError:
            return []

        # 计算与所有论文的余弦相似度
        paper_vec = self.tfidf_matrix[idx]
        similarities = cosine_similarity(paper_vec, self.tfidf_matrix).flatten()

        # 获取 top-k 索引（排除自身）
        top_indices = np.argsort(similarities)[::-1]
        results = []
        for i in top_indices:
            if i != idx and similarities[i] > 0:
                paper = self.papers[i].copy()
                paper['semantic_score'] = float(similarities[i])
                results.append(paper)
                if len(results) >= top_k:
                    break

        return results

    def get_tfidf_explanation(self, query, arxiv_id):
        """
        获取 TF-IDF 评分的解释（用于教学展示）

        Args:
            query: 查询字符串
            arxiv_id: 论文 ID

        Returns:
            dict: TF-IDF 评分详情
        """
        if self.tfidf_matrix is None:
            return {}

        try:
            idx = self.paper_ids.index(arxiv_id)
        except ValueError:
            return {}

        query_vec = self.vectorizer.transform([query])
        doc_vec = self.tfidf_matrix[idx]

        feature_names = self.vectorizer.get_feature_names_out()

        # 获取查询和文档中非零特征
        query_features = {}
        for i in query_vec.nonzero()[1]:
            query_features[feature_names[i]] = float(query_vec[0, i])

        doc_features = {}
        for i in doc_vec.nonzero()[1]:
            if feature_names[i] in query_features:
                doc_features[feature_names[i]] = float(doc_vec[0, i])

        similarity = float(cosine_similarity(query_vec, doc_vec)[0, 0])

        return {
            'similarity': similarity,
            'query_terms': query_features,
            'matching_terms': doc_features,
        }
