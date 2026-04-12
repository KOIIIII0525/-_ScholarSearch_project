"""
索引模块测试
"""
import os
import sys
import shutil
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from indexer.schema import create_schema, FIELD_BOOSTS
from indexer.index_builder import build_index, get_index
from crawler.arxiv_crawler import generate_sample_data
from crawler.data_loader import preprocess_paper


class TestSchema(unittest.TestCase):
    """Schema 测试"""

    def test_schema_fields(self):
        """测试 Schema 包含所有必需字段"""
        schema = create_schema()
        expected_fields = ['arxiv_id', 'title', 'abstract', 'authors',
                          'categories', 'published', 'year', 'url', 'references']
        for field in expected_fields:
            self.assertIn(field, schema.names())

    def test_field_boosts(self):
        """测试字段权重配置"""
        self.assertIn('title', FIELD_BOOSTS)
        self.assertIn('abstract', FIELD_BOOSTS)
        self.assertGreater(FIELD_BOOSTS['title'], FIELD_BOOSTS['abstract'])


class TestIndexBuilder(unittest.TestCase):
    """索引构建测试"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        # 生成少量测试数据
        papers = generate_sample_data()[:20]
        self.papers = [preprocess_paper(p) for p in papers]

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_build_index(self):
        """测试索引构建"""
        ix = build_index(self.papers, index_dir=self.test_dir, clean=True)
        self.assertIsNotNone(ix)

        with ix.searcher() as searcher:
            self.assertEqual(searcher.doc_count(), 20)

    def test_get_index(self):
        """测试获取已有索引"""
        # 先构建
        build_index(self.papers, index_dir=self.test_dir, clean=True)

        # 再获取
        ix = get_index(index_dir=self.test_dir)
        self.assertIsNotNone(ix)

    def test_get_index_nonexistent(self):
        """测试获取不存在的索引"""
        empty_dir = tempfile.mkdtemp()
        ix = get_index(index_dir=empty_dir)
        self.assertIsNone(ix)
        shutil.rmtree(empty_dir)

    def test_incremental_index(self):
        """测试增量索引"""
        # 先构建初始索引
        ix = build_index(self.papers[:10], index_dir=self.test_dir, clean=True)
        with ix.searcher() as s:
            self.assertEqual(s.doc_count(), 10)

        # 增量添加
        ix = build_index(self.papers[10:20], index_dir=self.test_dir)
        with ix.searcher() as s:
            self.assertEqual(s.doc_count(), 20)


if __name__ == '__main__':
    unittest.main()
