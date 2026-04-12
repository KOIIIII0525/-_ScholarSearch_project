"""
arXiv 论文爬虫
使用 arXiv API 按关键词/分类爬取论文元数据
"""
import os
import sys
import json
import time
import re
import requests
import feedparser

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def clean_text(text):
    """清理文本：去除多余空白和换行"""
    if not text:
        return ''
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_arxiv_id(entry):
    """从 entry 的 id URL 中提取 arXiv ID"""
    # 格式: http://arxiv.org/abs/2301.12345v1
    url = entry.get('id', '')
    match = re.search(r'arxiv\.org/abs/(.+?)(?:v\d+)?$', url)
    if match:
        return match.group(1)
    return url.split('/')[-1]


def extract_categories(entry):
    """提取论文分类"""
    tags = entry.get('tags', [])
    return [tag['term'] for tag in tags if 'term' in tag]


def extract_references(entry):
    """
    提取引用的论文 ID（arXiv 元数据中有限的引用信息）
    实际中 arXiv API 不直接提供引用关系，这里从摘要中提取 arXiv ID 作为模拟
    """
    abstract = entry.get('summary', '')
    # 匹配 arXiv ID 模式: 1234.56789 或 hep-th/9901001
    refs = re.findall(r'\b(\d{4}\.\d{4,5})\b', abstract)
    return refs


def parse_entry(entry):
    """解析单条 arXiv 条目为结构化字典"""
    arxiv_id = extract_arxiv_id(entry)
    authors = [author.get('name', '') for author in entry.get('authors', [])]
    categories = extract_categories(entry)
    references = extract_references(entry)

    # 发布日期
    published = entry.get('published', '')
    if published:
        published = published[:10]  # 只保留 YYYY-MM-DD

    return {
        'arxiv_id': arxiv_id,
        'title': clean_text(entry.get('title', '')),
        'abstract': clean_text(entry.get('summary', '')),
        'authors': authors,
        'categories': categories,
        'published': published,
        'url': entry.get('id', ''),
        'references': references,
    }


def crawl_arxiv(query=None, max_papers=None):
    """
    从 arXiv API 爬取论文元数据

    Args:
        query: 搜索查询字符串，默认使用配置中的默认查询
        max_papers: 最大论文数，默认使用配置值

    Returns:
        list[dict]: 论文元数据列表
    """
    query = query or config.DEFAULT_QUERY
    max_papers = max_papers or config.MAX_TOTAL_PAPERS

    papers = []
    start = 0
    batch_size = config.MAX_RESULTS_PER_REQUEST

    print(f"开始爬取 arXiv 论文...")
    print(f"查询: {query}")
    print(f"目标数量: {max_papers}")

    while len(papers) < max_papers:
        params = {
            'search_query': query,
            'start': start,
            'max_results': min(batch_size, max_papers - len(papers)),
            'sortBy': 'submittedDate',
            'sortOrder': 'descending',
        }

        print(f"正在请求第 {start + 1} - {start + params['max_results']} 条...")

        try:
            response = requests.get(config.ARXIV_API_URL, params=params, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            break

        feed = feedparser.parse(response.text)
        entries = feed.entries

        if not entries:
            print("没有更多结果")
            break

        for entry in entries:
            paper = parse_entry(entry)
            papers.append(paper)

        print(f"已爬取 {len(papers)} 篇论文")

        start += len(entries)

        if len(entries) < batch_size:
            break

        # 请求间隔，避免触发限流
        time.sleep(config.REQUEST_DELAY)

    print(f"爬取完成，共 {len(papers)} 篇论文")
    return papers


def save_papers(papers, filepath=None):
    """保存论文数据到 JSON 文件"""
    filepath = filepath or config.PAPERS_JSON
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)

    print(f"数据已保存至 {filepath}")


def generate_sample_data():
    """
    生成示例数据集（约500篇），用于离线演示。
    模拟 CS 领域的论文元数据，包含人工构造的引用关系。
    """
    import random
    random.seed(42)

    topics = [
        ("information retrieval", "cs.IR"),
        ("natural language processing", "cs.CL"),
        ("machine learning", "cs.LG"),
        ("artificial intelligence", "cs.AI"),
        ("computer vision", "cs.CV"),
        ("deep learning", "cs.LG"),
        ("neural networks", "cs.NE"),
        ("data mining", "cs.DB"),
    ]

    title_templates = [
        "A Novel Approach to {topic} Using {method}",
        "Improving {topic} with {method}: A Comprehensive Study",
        "{method} for Enhanced {topic}",
        "Survey of {topic}: From {method} to Modern Approaches",
        "Efficient {method} Methods in {topic}",
        "Deep {method} for {topic}: Challenges and Opportunities",
        "Towards Better {topic} via {method}",
        "Rethinking {topic}: A {method} Perspective",
        "Scalable {method} for Large-Scale {topic}",
        "Self-Supervised {method} for {topic}",
    ]

    methods = [
        "Transformer Models", "Graph Neural Networks", "Attention Mechanisms",
        "Contrastive Learning", "Reinforcement Learning", "Transfer Learning",
        "Knowledge Distillation", "Federated Learning", "Meta-Learning",
        "Prompt Engineering", "Few-Shot Learning", "Active Learning",
        "Generative Adversarial Networks", "Variational Autoencoders",
        "Bayesian Optimization", "Ensemble Methods",
    ]

    abstract_templates = [
        "In this paper, we propose a novel approach to {topic} that leverages {method}. "
        "Our method achieves state-of-the-art results on multiple benchmarks, "
        "demonstrating significant improvements over existing approaches. "
        "Specifically, we introduce a new architecture that combines {method} with "
        "advanced optimization techniques. Experimental results on standard datasets "
        "show that our approach outperforms previous methods by a large margin.",

        "We present a comprehensive study of {method} applied to {topic}. "
        "Through extensive experiments, we demonstrate that {method} can significantly "
        "improve performance in {topic} tasks. We also provide theoretical analysis "
        "of why {method} is particularly effective for this domain. Our findings "
        "suggest new directions for future research in this area.",

        "This survey provides an overview of recent advances in {topic}, "
        "with a particular focus on {method}. We categorize existing approaches "
        "into several families and analyze their strengths and weaknesses. "
        "We also identify key challenges and promising future directions. "
        "Our analysis covers over 100 papers published in the last five years.",

        "{topic} has seen remarkable progress with the advent of {method}. "
        "In this work, we explore how {method} can be adapted to address "
        "the unique challenges of {topic}. We propose several novel techniques "
        "and evaluate them on diverse benchmarks. Results indicate substantial "
        "improvements in both accuracy and efficiency.",
    ]

    first_names = [
        "Wei", "Yun", "Jia", "Ming", "Xiao", "Hao", "Li", "Chen",
        "John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert",
        "Alice", "Bob", "Chris", "Diana", "Eric", "Frank", "Grace",
    ]
    last_names = [
        "Wang", "Zhang", "Li", "Chen", "Liu", "Yang", "Huang", "Wu",
        "Smith", "Johnson", "Brown", "Davis", "Wilson", "Taylor", "Clark",
        "Anderson", "Thomas", "Moore", "Martin", "Lee", "Kim", "Park",
    ]

    papers = []
    for i in range(500):
        topic_name, category = random.choice(topics)
        method = random.choice(methods)
        title = random.choice(title_templates).format(topic=topic_name, method=method)
        abstract = random.choice(abstract_templates).format(topic=topic_name, method=method)

        # 生成作者
        num_authors = random.randint(1, 5)
        authors = []
        for _ in range(num_authors):
            name = f"{random.choice(first_names)} {random.choice(last_names)}"
            authors.append(name)

        # 生成日期 (2020-2024)
        year = random.randint(2020, 2024)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        published = f"{year}-{month:02d}-{day:02d}"

        # 生成 arXiv ID
        arxiv_id = f"{year % 100}{month:02d}.{10000 + i:05d}"

        # 额外分类
        categories = [category]
        if random.random() > 0.5:
            extra_cat = random.choice(topics)[1]
            if extra_cat != category:
                categories.append(extra_cat)

        # 引用关系：引用之前的论文
        references = []
        if i > 10:
            num_refs = random.randint(0, min(5, i - 1))
            ref_indices = random.sample(range(max(0, i - 50), i), num_refs)
            references = [papers[j]['arxiv_id'] for j in ref_indices]

        papers.append({
            'arxiv_id': arxiv_id,
            'title': title,
            'abstract': abstract,
            'authors': authors,
            'categories': categories,
            'published': published,
            'url': f'https://arxiv.org/abs/{arxiv_id}',
            'references': references,
        })

    return papers


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='arXiv 论文爬虫')
    parser.add_argument('--query', type=str, default=None, help='搜索查询')
    parser.add_argument('--max', type=int, default=None, help='最大论文数')
    parser.add_argument('--sample', action='store_true', help='生成示例数据（不需要网络）')
    args = parser.parse_args()

    if args.sample:
        print("生成示例数据集...")
        papers = generate_sample_data()
    else:
        papers = crawl_arxiv(query=args.query, max_papers=args.max)

    save_papers(papers)
    print(f"共保存 {len(papers)} 篇论文")
