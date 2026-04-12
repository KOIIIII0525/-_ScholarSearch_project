"""
数据加载与预处理模块
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def load_papers(filepath=None):
    """
    从 JSON 文件加载论文数据

    Args:
        filepath: JSON 文件路径，默认使用配置中的路径

    Returns:
        list[dict]: 论文元数据列表
    """
    filepath = filepath or config.PAPERS_JSON

    if not os.path.exists(filepath):
        print(f"数据文件不存在: {filepath}")
        print("请先运行爬虫获取数据: python crawler/arxiv_crawler.py --sample")
        return []

    with open(filepath, 'r', encoding='utf-8') as f:
        papers = json.load(f)

    print(f"已加载 {len(papers)} 篇论文")
    return papers


def preprocess_paper(paper):
    """
    预处理单篇论文数据

    Args:
        paper: 论文字典

    Returns:
        dict: 预处理后的论文字典
    """
    processed = paper.copy()

    # 确保必需字段存在
    processed.setdefault('arxiv_id', '')
    processed.setdefault('title', '')
    processed.setdefault('abstract', '')
    processed.setdefault('authors', [])
    processed.setdefault('categories', [])
    processed.setdefault('published', '')
    processed.setdefault('url', '')
    processed.setdefault('references', [])

    # 将列表字段转为字符串，方便索引
    processed['authors_text'] = ', '.join(processed['authors'])
    processed['categories_text'] = ', '.join(processed['categories'])

    # 提取年份
    if processed['published']:
        processed['year'] = processed['published'][:4]
    else:
        processed['year'] = ''

    return processed


def load_and_preprocess(filepath=None):
    """加载并预处理所有论文"""
    papers = load_papers(filepath)
    return [preprocess_paper(p) for p in papers]


def get_citation_graph(papers):
    """
    构建引用关系图

    Args:
        papers: 论文列表

    Returns:
        dict: {arxiv_id: [被引用的 arxiv_id 列表]}
    """
    graph = {}
    id_set = {p['arxiv_id'] for p in papers}

    for paper in papers:
        arxiv_id = paper['arxiv_id']
        refs = [ref for ref in paper.get('references', []) if ref in id_set]
        graph[arxiv_id] = refs

    return graph


if __name__ == '__main__':
    papers = load_and_preprocess()
    if papers:
        print(f"\n示例论文:")
        p = papers[0]
        print(f"  ID: {p['arxiv_id']}")
        print(f"  标题: {p['title']}")
        print(f"  作者: {p['authors_text']}")
        print(f"  分类: {p['categories_text']}")
        print(f"  日期: {p['published']}")

        graph = get_citation_graph(papers)
        total_refs = sum(len(v) for v in graph.values())
        print(f"\n引用关系图: {len(graph)} 节点, {total_refs} 条边")
