"""
拼写纠错模块
基于编辑距离的拼写纠错，提供 "Did you mean?" 建议
"""
import os
import sys
from collections import Counter

from whoosh.index import open_dir

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class SpellCorrector:
    """
    基于编辑距离的拼写纠错器

    原理:
    1. 从索引中提取词汇表
    2. 对查询中的每个词计算与词汇表中词的编辑距离
    3. 返回编辑距离最小且频率最高的候选词
    """

    def __init__(self, index_dir=None):
        self.index_dir = index_dir or config.INDEX_DIR
        self.ix = open_dir(self.index_dir)
        self.vocab = self._build_vocab()

    def _build_vocab(self):
        """从索引中提取词汇表及其频率"""
        vocab = Counter()
        reader = self.ix.reader()

        for field_name in ['title', 'abstract']:
            try:
                for term in reader.field_terms(field_name):
                    freq = reader.frequency(field_name, term)
                    vocab[term] += freq
            except Exception:
                pass

        return vocab

    def edit_distance(self, s1, s2):
        """
        计算两个字符串的编辑距离（Levenshtein Distance）

        使用动态规划算法:
        - 插入一个字符: +1
        - 删除一个字符: +1
        - 替换一个字符: +1
        """
        m, n = len(s1), len(s2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i - 1] == s2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = min(
                        dp[i - 1][j] + 1,     # 删除
                        dp[i][j - 1] + 1,     # 插入
                        dp[i - 1][j - 1] + 1  # 替换
                    )

        return dp[m][n]

    def candidates(self, word, max_dist=2):
        """
        生成拼写纠正候选词

        Args:
            word: 待纠正的词
            max_dist: 最大编辑距离

        Returns:
            list[tuple]: [(candidate_word, distance, frequency), ...]
        """
        word = word.lower()
        results = []

        # 如果词在词汇表中，不需要纠正
        if word in self.vocab:
            return []

        for term, freq in self.vocab.items():
            if abs(len(term) - len(word)) > max_dist:
                continue
            dist = self.edit_distance(word, term)
            if 0 < dist <= max_dist:
                results.append((term, dist, freq))

        # 按编辑距离升序、频率降序排序
        results.sort(key=lambda x: (x[1], -x[2]))
        return results[:config.MAX_SUGGESTIONS]

    def correct(self, query_str):
        """
        对查询字符串进行拼写纠正

        Args:
            query_str: 原始查询字符串

        Returns:
            str or None: 纠正后的查询字符串，若无需纠正返回 None
        """
        words = query_str.lower().split()
        corrected_words = []
        has_correction = False

        for word in words:
            # 跳过布尔运算符和短词
            if word.upper() in ('AND', 'OR', 'NOT') or len(word) <= 2:
                corrected_words.append(word)
                continue

            candidates = self.candidates(word, max_dist=2)
            if candidates:
                corrected_words.append(candidates[0][0])
                has_correction = True
            else:
                corrected_words.append(word)

        if has_correction:
            return ' '.join(corrected_words)
        return None

    def suggest(self, word, n=5):
        """
        对单个词给出拼写建议

        Args:
            word: 待纠正的词
            n: 返回建议数量

        Returns:
            list[str]: 建议词列表
        """
        candidates = self.candidates(word)
        return [c[0] for c in candidates[:n]]
