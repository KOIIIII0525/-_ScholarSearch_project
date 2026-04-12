"""
Whoosh 索引 Schema 定义
定义论文索引的字段和权重配置
"""
from whoosh.fields import Schema, TEXT, ID, KEYWORD, DATETIME, STORED, NUMERIC
from whoosh.analysis import StemmingAnalyzer, StandardAnalyzer


def create_schema():
    """
    创建论文索引的 Schema

    字段说明:
    - arxiv_id: 论文唯一标识符（ID 类型，不分词）
    - title: 标题（全文索引，带词干提取，权重较高）
    - abstract: 摘要（全文索引，带词干提取）
    - authors: 作者（关键词类型）
    - categories: 分类（关键词类型，用于分面搜索）
    - published: 发表日期
    - year: 发表年份（用于分面搜索）
    - url: 论文链接（存储但不索引）
    - references: 引用关系（存储用于 PageRank）

    使用 BM25F 加权:
    - title 权重 = 3.0（标题匹配更重要）
    - abstract 权重 = 1.0
    """
    # 使用词干提取分析器，适合英文学术文本
    stem_analyzer = StemmingAnalyzer()

    schema = Schema(
        # 唯一标识
        arxiv_id=ID(stored=True, unique=True),

        # 全文搜索字段
        title=TEXT(stored=True, analyzer=stem_analyzer, field_boost=3.0),
        abstract=TEXT(stored=True, analyzer=stem_analyzer),

        # 结构化字段
        authors=TEXT(stored=True, analyzer=StandardAnalyzer()),
        categories=KEYWORD(stored=True, commas=True, scorable=True),

        # 日期与年份
        published=ID(stored=True),
        year=ID(stored=True),

        # 存储字段（不索引）
        url=STORED,
        references=STORED,
    )

    return schema


# BM25F 字段权重配置（在搜索时使用）
FIELD_BOOSTS = {
    'title': 3.0,
    'abstract': 1.0,
    'authors': 2.0,
}
