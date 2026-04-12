"""
核心搜索引擎模块
支持 BM25 排序、布尔查询、短语查询、字段查询、分面搜索
"""
import os
import sys

from whoosh.index import open_dir
from whoosh.qparser import MultifieldParser, QueryParser, OrGroup
from whoosh.qparser.plugins import FuzzyTermPlugin
from whoosh.scoring import BM25F, TF_IDF
from whoosh import sorting

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from indexer.schema import FIELD_BOOSTS


class SearchEngine:
    """核心搜索引擎"""

    def __init__(self, index_dir=None):
        self.index_dir = index_dir or config.INDEX_DIR
        self.ix = open_dir(self.index_dir)
        self.pagerank_scores = {}

    def set_pagerank_scores(self, scores):
        """设置 PageRank 分数用于排序融合"""
        self.pagerank_scores = scores

    def search(self, query_str, page=1, per_page=None, scoring='bm25',
               fields=None, filters=None, sort_by=None):
        """
        执行搜索

        Args:
            query_str: 查询字符串
            page: 页码（从 1 开始）
            per_page: 每页结果数
            scoring: 评分模型 ('bm25' 或 'tfidf')
            fields: 搜索字段列表
            filters: 分面过滤条件 dict, e.g. {'year': '2023', 'categories': 'cs.AI'}
            sort_by: 排序方式 ('relevance', 'date', 'pagerank')

        Returns:
            dict: {
                'results': [论文结果列表],
                'total': 总结果数,
                'page': 当前页,
                'total_pages': 总页数,
                'query': 查询字符串,
                'facets': 分面统计,
                'correction': 拼写纠正建议,
            }
        """
        per_page = per_page or config.RESULTS_PER_PAGE
        fields = fields or ['title', 'abstract', 'authors']

        # 选择评分模型
        if scoring == 'tfidf':
            weighting = TF_IDF()
        else:
            weighting = BM25F(B=config.BM25_B, K1=config.BM25_K1, **{
                f'{field}_B': FIELD_BOOSTS.get(field, 1.0) for field in fields
            })

        with self.ix.searcher(weighting=weighting) as searcher:
            # 构建查询解析器
            parser = MultifieldParser(fields, self.ix.schema, group=OrGroup)
            parser.add_plugin(FuzzyTermPlugin())

            try:
                query = parser.parse(query_str)
            except Exception:
                # 如果解析失败，使用简单查询
                query = parser.parse(query_str.replace(':', ' '))

            # 应用过滤条件
            filter_query = None
            if filters:
                from whoosh.query import And, Term
                filter_terms = []
                for field, value in filters.items():
                    if value:
                        filter_terms.append(Term(field, value))
                if filter_terms:
                    filter_query = And(filter_terms)

            # 执行搜索
            results = searcher.search_page(
                query,
                page,
                pagelen=per_page,
                filter=filter_query,
            )
            results.results.fragmenter.maxchars = 300
            results.results.fragmenter.surround = 50

            # 获取拼写纠正建议
            correction = None
            corrected = searcher.correct_query(query, query_str)
            if corrected.query != query:
                correction = corrected.string

            # 提取结果
            result_list = []
            for hit in results:
                paper = {
                    'arxiv_id': hit['arxiv_id'],
                    'title': hit['title'],
                    'abstract': hit['abstract'],
                    'authors': hit['authors'],
                    'categories': hit['categories'],
                    'published': hit['published'],
                    'year': hit.get('year', ''),
                    'url': hit.get('url', ''),
                    'score': hit.score,
                    # 高亮摘要
                    'highlight_title': hit.highlights('title') or hit['title'],
                    'highlight_abstract': hit.highlights('abstract') or hit['abstract'][:300],
                }

                # 融合 PageRank 分数
                if self.pagerank_scores:
                    pr = self.pagerank_scores.get(hit['arxiv_id'], 0)
                    paper['pagerank'] = pr
                    paper['combined_score'] = (
                        (1 - config.PAGERANK_WEIGHT) * hit.score +
                        config.PAGERANK_WEIGHT * pr * 100
                    )
                else:
                    paper['pagerank'] = 0
                    paper['combined_score'] = hit.score

                result_list.append(paper)

            # 如果使用 PageRank 排序，重新排序
            if sort_by == 'pagerank' and self.pagerank_scores:
                result_list.sort(key=lambda x: x['combined_score'], reverse=True)
            elif sort_by == 'date':
                result_list.sort(key=lambda x: x['published'], reverse=True)

            # 构建分面统计
            facets = self._build_facets(searcher, query, filter_query)

            total = len(results)
            total_pages = (total + per_page - 1) // per_page

            return {
                'results': result_list,
                'total': total,
                'page': page,
                'total_pages': total_pages,
                'query': query_str,
                'facets': facets,
                'correction': correction,
            }

    def _build_facets(self, searcher, query, filter_query=None):
        """构建分面统计（年份、分类）"""
        facets = {'years': {}, 'categories': {}}

        try:
            # 获取所有匹配结果用于分面统计
            results = searcher.search(query, limit=None, filter=filter_query)

            for hit in results:
                # 年份分面
                year = hit.get('year', '')
                if year:
                    facets['years'][year] = facets['years'].get(year, 0) + 1

                # 分类分面
                cats = hit.get('categories', '')
                if cats:
                    for cat in cats.split(','):
                        cat = cat.strip()
                        if cat:
                            facets['categories'][cat] = facets['categories'].get(cat, 0) + 1

            # 排序
            facets['years'] = dict(sorted(facets['years'].items(), reverse=True))
            facets['categories'] = dict(sorted(
                facets['categories'].items(), key=lambda x: x[1], reverse=True
            )[:20])  # 只保留前 20 个分类

        except Exception as e:
            print(f"分面统计失败: {e}")

        return facets

    def get_paper(self, arxiv_id):
        """根据 arXiv ID 获取单篇论文"""
        with self.ix.searcher() as searcher:
            from whoosh.query import Term
            results = searcher.search(Term('arxiv_id', arxiv_id))
            if results:
                hit = results[0]
                return {
                    'arxiv_id': hit['arxiv_id'],
                    'title': hit['title'],
                    'abstract': hit['abstract'],
                    'authors': hit['authors'],
                    'categories': hit['categories'],
                    'published': hit['published'],
                    'year': hit.get('year', ''),
                    'url': hit.get('url', ''),
                    'references': hit.get('references', []),
                }
        return None

    def get_index_stats(self):
        """获取索引统计信息"""
        with self.ix.searcher() as searcher:
            return {
                'doc_count': searcher.doc_count(),
                'doc_count_all': searcher.doc_count_all(),
            }
