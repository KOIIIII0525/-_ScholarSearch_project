"""
爬虫模块测试
"""
import os
import sys
import json
import unittest
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crawler.arxiv_crawler import (
    clean_text, extract_arxiv_id, parse_entry,
    generate_sample_data, save_papers
)
from crawler.data_loader import load_papers, preprocess_paper, get_citation_graph


class TestArxivCrawler(unittest.TestCase):
    """arXiv 爬虫测试"""

    def test_clean_text(self):
        """测试文本清理"""
        self.assertEqual(clean_text("hello  world"), "hello world")
        self.assertEqual(clean_text("  spaces  "), "spaces")
        self.assertEqual(clean_text("line\n\nbreak"), "line break")
        self.assertEqual(clean_text(""), "")
        self.assertEqual(clean_text(None), "")

    def test_extract_arxiv_id(self):
        """测试 arXiv ID 提取"""
        entry = {'id': 'http://arxiv.org/abs/2301.12345v1'}
        self.assertEqual(extract_arxiv_id(entry), '2301.12345')

        entry2 = {'id': 'http://arxiv.org/abs/2301.12345'}
        self.assertEqual(extract_arxiv_id(entry2), '2301.12345')

    def test_generate_sample_data(self):
        """测试示例数据生成"""
        papers = generate_sample_data()
        self.assertEqual(len(papers), 500)

        # 检查必需字段
        paper = papers[0]
        self.assertIn('arxiv_id', paper)
        self.assertIn('title', paper)
        self.assertIn('abstract', paper)
        self.assertIn('authors', paper)
        self.assertIn('categories', paper)
        self.assertIn('published', paper)
        self.assertIn('references', paper)

        # 检查数据类型
        self.assertIsInstance(paper['authors'], list)
        self.assertIsInstance(paper['categories'], list)
        self.assertIsInstance(paper['references'], list)

    def test_save_and_load_papers(self):
        """测试数据保存和加载"""
        papers = generate_sample_data()[:10]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            tmpfile = f.name

        try:
            save_papers(papers, tmpfile)
            loaded = load_papers(tmpfile)
            self.assertEqual(len(loaded), 10)
            self.assertEqual(loaded[0]['arxiv_id'], papers[0]['arxiv_id'])
        finally:
            os.unlink(tmpfile)


class TestDataLoader(unittest.TestCase):
    """数据加载器测试"""

    def test_preprocess_paper(self):
        """测试论文预处理"""
        paper = {
            'arxiv_id': '2301.00001',
            'title': 'Test Paper',
            'abstract': 'Test abstract',
            'authors': ['Alice', 'Bob'],
            'categories': ['cs.AI', 'cs.LG'],
            'published': '2023-01-15',
        }
        processed = preprocess_paper(paper)

        self.assertEqual(processed['authors_text'], 'Alice, Bob')
        self.assertEqual(processed['categories_text'], 'cs.AI, cs.LG')
        self.assertEqual(processed['year'], '2023')

    def test_preprocess_missing_fields(self):
        """测试缺少字段时的预处理"""
        paper = {'arxiv_id': '123'}
        processed = preprocess_paper(paper)

        self.assertEqual(processed['title'], '')
        self.assertEqual(processed['abstract'], '')
        self.assertEqual(processed['authors'], [])

    def test_citation_graph(self):
        """测试引用关系图构建"""
        papers = [
            {'arxiv_id': 'A', 'references': ['B', 'C']},
            {'arxiv_id': 'B', 'references': ['C']},
            {'arxiv_id': 'C', 'references': []},
        ]
        graph = get_citation_graph(papers)

        self.assertEqual(len(graph), 3)
        self.assertEqual(graph['A'], ['B', 'C'])
        self.assertEqual(graph['B'], ['C'])
        self.assertEqual(graph['C'], [])

    def test_citation_graph_filters_invalid(self):
        """测试引用图过滤无效引用"""
        papers = [
            {'arxiv_id': 'A', 'references': ['B', 'X']},
            {'arxiv_id': 'B', 'references': []},
        ]
        graph = get_citation_graph(papers)
        self.assertEqual(graph['A'], ['B'])  # X 不在数据集中，被过滤


if __name__ == '__main__':
    unittest.main()
