"""
查询扩展模块
基于 WordNet 同义词的查询扩展
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

try:
    import nltk
    from nltk.corpus import wordnet

    # 确保下载 WordNet 数据
    try:
        wordnet.synsets('test')
    except LookupError:
        nltk.download('wordnet', quiet=True)
        nltk.download('omw-1.4', quiet=True)

    WORDNET_AVAILABLE = True
except ImportError:
    WORDNET_AVAILABLE = False


class QueryExpander:
    """
    查询扩展器

    原理:
    1. 对查询中的每个关键词，通过 WordNet 查找同义词
    2. 将同义词添加到查询中，使用 OR 连接
    3. 扩展后的查询能匹配更多相关文档，提高查全率（Recall）

    例如: "information retrieval" 扩展为
          "(information OR data OR info) (retrieval OR recovery OR search)"
    """

    def __init__(self):
        self.enabled = WORDNET_AVAILABLE
        # 学术常见同义词映射（手动补充）
        self.custom_synonyms = {
            'retrieval': ['search', 'finding', 'querying'],
            'classification': ['categorization', 'labeling', 'sorting'],
            'detection': ['identification', 'recognition', 'discovery'],
            'generation': ['creation', 'synthesis', 'production'],
            'segmentation': ['partitioning', 'division', 'splitting'],
            'embedding': ['representation', 'encoding', 'vectorization'],
            'optimization': ['tuning', 'improvement', 'enhancement'],
            'prediction': ['forecasting', 'estimation', 'inference'],
            'clustering': ['grouping', 'partitioning'],
            'summarization': ['summary', 'abstraction', 'condensation'],
        }

    def get_synonyms(self, word, max_synonyms=3):
        """
        获取一个词的同义词

        Args:
            word: 输入词
            max_synonyms: 最大同义词数

        Returns:
            list[str]: 同义词列表
        """
        synonyms = set()

        # 从自定义同义词表查找
        if word.lower() in self.custom_synonyms:
            synonyms.update(self.custom_synonyms[word.lower()])

        # 从 WordNet 查找
        if self.enabled:
            for syn in wordnet.synsets(word):
                for lemma in syn.lemmas():
                    name = lemma.name().replace('_', ' ')
                    if name.lower() != word.lower():
                        synonyms.add(name.lower())

        # 去除与原词相同的
        synonyms.discard(word.lower())

        return list(synonyms)[:max_synonyms]

    def expand_query(self, query_str, max_synonyms=2):
        """
        扩展查询

        Args:
            query_str: 原始查询字符串
            max_synonyms: 每个词最大同义词数

        Returns:
            dict: {
                'original': 原始查询,
                'expanded': 扩展后的查询字符串,
                'expansions': {词: [同义词列表]},
            }
        """
        words = query_str.strip().split()
        expanded_parts = []
        expansions = {}

        for word in words:
            # 跳过布尔运算符和短词
            if word.upper() in ('AND', 'OR', 'NOT') or len(word) <= 2:
                expanded_parts.append(word)
                continue

            # 跳过带引号的短语
            if word.startswith('"') or word.endswith('"'):
                expanded_parts.append(word)
                continue

            synonyms = self.get_synonyms(word, max_synonyms)
            if synonyms:
                # 构建 OR 查询组
                group = [word] + synonyms
                expanded_parts.append(f"({' OR '.join(group)})")
                expansions[word] = synonyms
            else:
                expanded_parts.append(word)

        expanded_query = ' '.join(expanded_parts)

        return {
            'original': query_str,
            'expanded': expanded_query,
            'expansions': expansions,
        }
