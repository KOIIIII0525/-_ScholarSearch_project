"""
中文分词分析器 (基于 jieba)
用于支持中文论文的索引和搜索
"""
import jieba
from whoosh.analysis import Tokenizer, Token


class JiebaTokenizer(Tokenizer):
    """基于 jieba 的中文分词器"""

    def __call__(self, value, positions=False, chars=False,
                 keeporiginal=False, removestops=True, start_pos=0,
                 start_char=0, mode='', **kwargs):
        t = Token(positions, chars, removestops=removestops)
        # 使用 jieba 精确模式分词
        words = jieba.cut(value, cut_all=False)

        pos = start_pos
        for word in words:
            word = word.strip()
            if not word:
                continue

            t.original = t.text = word
            t.boost = 1.0

            if positions:
                t.pos = pos
                pos += 1

            if chars:
                t.startchar = start_char
                t.endchar = start_char + len(word)
                start_char = t.endchar

            yield t


def ChineseAnalyzer():
    """返回一个中文分析器实例"""
    return JiebaTokenizer()
