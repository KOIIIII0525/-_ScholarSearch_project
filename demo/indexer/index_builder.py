"""
索引构建模块
读取论文数据，构建 Whoosh 倒排索引
"""
import os
import sys
import shutil

from whoosh.index import create_in, open_dir, exists_in
from whoosh.writing import BufferedWriter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from indexer.schema import create_schema
from crawler.data_loader import load_and_preprocess


def build_index(papers=None, index_dir=None, clean=False):
    """
    构建 Whoosh 倒排索引

    Args:
        papers: 论文数据列表，若为 None 则从文件加载
        index_dir: 索引存储目录
        clean: 是否清空已有索引重新构建

    Returns:
        whoosh.index.Index: 构建好的索引对象
    """
    index_dir = index_dir or config.INDEX_DIR
    os.makedirs(index_dir, exist_ok=True)

    if papers is None:
        papers = load_and_preprocess()
        if not papers:
            print("没有论文数据，请先运行爬虫")
            return None

    schema = create_schema()

    # 清空或创建索引
    if clean and os.path.exists(index_dir):
        shutil.rmtree(index_dir)
        os.makedirs(index_dir)

    if exists_in(index_dir):
        ix = open_dir(index_dir)
        print(f"打开已有索引: {index_dir}")
    else:
        ix = create_in(index_dir, schema)
        print(f"创建新索引: {index_dir}")

    # 批量写入文档
    writer = ix.writer()
    count = 0

    for paper in papers:
        try:
            writer.update_document(
                arxiv_id=paper['arxiv_id'],
                title=paper['title'],
                abstract=paper['abstract'],
                authors=paper.get('authors_text', ', '.join(paper.get('authors', []))),
                categories=', '.join(paper.get('categories', [])),
                published=paper.get('published', ''),
                year=paper.get('year', paper.get('published', '')[:4] if paper.get('published') else ''),
                url=paper.get('url', ''),
                references=paper.get('references', []),
            )
            count += 1
        except Exception as e:
            print(f"索引论文 {paper.get('arxiv_id', '?')} 失败: {e}")

    writer.commit()
    print(f"索引构建完成: {count} 篇论文已索引")
    print(f"索引目录: {index_dir}")

    # 打印索引统计信息
    with ix.searcher() as searcher:
        print(f"索引文档数: {searcher.doc_count()}")
        # 打印部分词项统计
        reader = ix.reader()
        print(f"title 字段词项数: {reader.field_length('title')}")
        print(f"abstract 字段词项数: {reader.field_length('abstract')}")

    return ix


def get_index(index_dir=None):
    """获取已有索引，若不存在则返回 None"""
    index_dir = index_dir or config.INDEX_DIR
    if exists_in(index_dir):
        return open_dir(index_dir)
    return None


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='构建论文索引')
    parser.add_argument('--clean', action='store_true', help='清空并重新构建索引')
    args = parser.parse_args()

    ix = build_index(clean=args.clean)
    if ix:
        print("\n索引构建成功!")
