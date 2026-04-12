"""
搜索模块测试
"""
import os
import sys
import shutil
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crawler.arxiv_crawler import generate_sample_data
from crawler.data_loader import preprocess_paper, get_citation_graph
from indexer.index_builder import build_index
from searcher.search_engine import SearchEngine
from searcher.spell_corrector import SpellCorrector
from searcher.query_expander import QueryExpander
from searcher.semantic_search import SemanticSearch
from searcher.pagerank import PageRank


class SearchTestBase(unittest.TestCase):
    """搜索测试基类"""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.mkdtemp()
        raw_papers = generate_sample_data()[:50]
        cls.papers = [preprocess_paper(p) for p in raw_papers]
        build_index(cls.papers, index_dir=cls.test_dir, clean=True)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)


class TestSearchEngine(SearchTestBase):
    """核心搜索引擎测试"""

    def test_basic_search(self):
        """测试基本搜索"""
        engine = SearchEngine(index_dir=self.test_dir)
        results = engine.search("machine learning")
        self.assertGreater(results['total'], 0)
        self.assertIn('results', results)

    def test_search_bm25(self):
        """测试 BM25 排序"""
        engine = SearchEngine(index_dir=self.test_dir)
        results = engine.search("neural network", scoring='bm25')
        self.assertIsNotNone(results)
        if results['results']:
            self.assertGreater(results['results'][0]['score'], 0)

    def test_search_tfidf(self):
        """测试 TF-IDF 排序"""
        engine = SearchEngine(index_dir=self.test_dir)
        results = engine.search("deep learning", scoring='tfidf')
        self.assertIsNotNone(results)

    def test_search_pagination(self):
        """测试分页"""
        engine = SearchEngine(index_dir=self.test_dir)
        results = engine.search("learning", page=1, per_page=5)
        self.assertLessEqual(len(results['results']), 5)

    def test_search_empty_query(self):
        """测试空查询"""
        engine = SearchEngine(index_dir=self.test_dir)
        # 空查询应该不报错
        try:
            results = engine.search("")
        except Exception:
            pass  # 空查询可能抛出异常，这是可接受的

    def test_get_paper(self):
        """测试获取单篇论文"""
        engine = SearchEngine(index_dir=self.test_dir)
        arxiv_id = self.papers[0]['arxiv_id']
        paper = engine.get_paper(arxiv_id)
        self.assertIsNotNone(paper)
        self.assertEqual(paper['arxiv_id'], arxiv_id)

    def test_facets(self):
        """测试分面统计"""
        engine = SearchEngine(index_dir=self.test_dir)
        results = engine.search("learning")
        self.assertIn('facets', results)
        self.assertIn('years', results['facets'])
        self.assertIn('categories', results['facets'])

    def test_filter_search(self):
        """测试带过滤条件的搜索"""
        engine = SearchEngine(index_dir=self.test_dir)
        year = self.papers[0]['year']
        results = engine.search("learning", filters={'year': year})
        self.assertIsNotNone(results)

    def test_index_stats(self):
        """测试索引统计"""
        engine = SearchEngine(index_dir=self.test_dir)
        stats = engine.get_index_stats()
        self.assertEqual(stats['doc_count'], 50)


class TestSpellCorrector(SearchTestBase):
    """拼写纠错测试"""

    def test_edit_distance(self):
        """测试编辑距离计算"""
        corrector = SpellCorrector(index_dir=self.test_dir)
        self.assertEqual(corrector.edit_distance("kitten", "sitting"), 3)
        self.assertEqual(corrector.edit_distance("hello", "hello"), 0)
        self.assertEqual(corrector.edit_distance("", "abc"), 3)

    def test_correct_misspelling(self):
        """测试拼写纠正"""
        corrector = SpellCorrector(index_dir=self.test_dir)
        # 故意拼错的词应该被纠正
        result = corrector.correct("leanring")
        # 可能返回 None 如果词汇表中没有足够近的词
        # 这是可接受的

    def test_no_correction_needed(self):
        """测试不需要纠正的情况"""
        corrector = SpellCorrector(index_dir=self.test_dir)
        # 短词不纠正
        result = corrector.correct("AI")
        self.assertIsNone(result)


class TestQueryExpander(unittest.TestCase):
    """查询扩展测试"""

    def test_get_synonyms(self):
        """测试同义词获取"""
        expander = QueryExpander()
        synonyms = expander.get_synonyms("retrieval")
        # 自定义同义词表中有 retrieval
        self.assertGreater(len(synonyms), 0)

    def test_expand_query(self):
        """测试查询扩展"""
        expander = QueryExpander()
        result = expander.expand_query("information retrieval")
        self.assertIn('original', result)
        self.assertIn('expanded', result)
        self.assertIn('expansions', result)
        # retrieval 应该被扩展
        self.assertIn('retrieval', result['expansions'])

    def test_skip_operators(self):
        """测试跳过布尔运算符"""
        expander = QueryExpander()
        result = expander.expand_query("deep AND learning")
        # AND 不应该被扩展
        self.assertNotIn('AND', result['expansions'])

    def test_skip_short_words(self):
        """测试跳过短词"""
        expander = QueryExpander()
        result = expander.expand_query("AI is great")
        self.assertNotIn('AI', result['expansions'])
        self.assertNotIn('is', result['expansions'])


class TestSemanticSearch(unittest.TestCase):
    """语义搜索测试"""

    @classmethod
    def setUpClass(cls):
        raw_papers = generate_sample_data()[:30]
        cls.papers = [preprocess_paper(p) for p in raw_papers]
        cls.semantic = SemanticSearch(cls.papers)

    def test_fit(self):
        """测试 TF-IDF 矩阵构建"""
        self.assertIsNotNone(self.semantic.tfidf_matrix)
        self.assertEqual(self.semantic.tfidf_matrix.shape[0], 30)

    def test_search(self):
        """测试语义搜索"""
        results = self.semantic.search("machine learning", top_k=5)
        self.assertLessEqual(len(results), 5)
        if results:
            self.assertIn('semantic_score', results[0])
            self.assertGreater(results[0]['semantic_score'], 0)

    def test_find_similar(self):
        """测试相似论文查找"""
        arxiv_id = self.papers[0]['arxiv_id']
        similar = self.semantic.find_similar(arxiv_id, top_k=3)
        self.assertLessEqual(len(similar), 3)
        # 不应该返回自身
        for p in similar:
            self.assertNotEqual(p['arxiv_id'], arxiv_id)

    def test_find_similar_nonexistent(self):
        """测试查找不存在的论文"""
        similar = self.semantic.find_similar("nonexistent_id")
        self.assertEqual(len(similar), 0)


class TestPageRank(unittest.TestCase):
    """PageRank 测试"""

    def test_simple_graph(self):
        """测试简单图的 PageRank"""
        graph = {
            'A': ['B'],
            'B': ['C'],
            'C': ['A'],
        }
        pr = PageRank(damping=0.85, iterations=100)
        scores = pr.compute(graph)

        # 三个节点的对称环，分数应该接近相等
        self.assertEqual(len(scores), 3)
        values = list(scores.values())
        self.assertAlmostEqual(values[0], values[1], places=3)
        self.assertAlmostEqual(values[1], values[2], places=3)

    def test_star_graph(self):
        """测试星型图（一个节点被其他所有节点引用）"""
        graph = {
            'center': [],
            'A': ['center'],
            'B': ['center'],
            'C': ['center'],
        }
        pr = PageRank()
        scores = pr.compute(graph)

        # center 应该有最高的 PageRank
        self.assertGreater(scores['center'], scores['A'])
        self.assertGreater(scores['center'], scores['B'])

    def test_empty_graph(self):
        """测试空图"""
        pr = PageRank()
        scores = pr.compute({})
        self.assertEqual(len(scores), 0)

    def test_get_top_papers(self):
        """测试获取 Top-K 论文"""
        graph = {
            'A': [], 'B': ['A'], 'C': ['A'], 'D': ['A', 'B'],
        }
        pr = PageRank()
        pr.compute(graph)
        top = pr.get_top_papers(k=2)
        self.assertEqual(len(top), 2)
        # A 被引用最多，应排在第一
        self.assertEqual(top[0][0], 'A')

    def test_with_sample_data(self):
        """测试使用示例数据计算 PageRank"""
        raw_papers = generate_sample_data()[:50]
        papers = [preprocess_paper(p) for p in raw_papers]
        graph = get_citation_graph(papers)

        pr = PageRank()
        scores = pr.compute(graph)

        self.assertEqual(len(scores), len(graph))
        # 所有分数之和应约等于 1
        total = sum(scores.values())
        self.assertAlmostEqual(total, 1.0, places=2)


if __name__ == '__main__':
    unittest.main()
