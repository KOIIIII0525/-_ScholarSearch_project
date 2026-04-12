"""
ScholarSearch - 学术论文垂直搜索引擎
Flask 主应用入口
"""
import os
import sys

from flask import Flask, render_template, request, jsonify

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
from indexer.index_builder import get_index, build_index
from crawler.data_loader import load_and_preprocess, get_citation_graph
from crawler.arxiv_crawler import generate_sample_data, save_papers
from searcher.search_engine import SearchEngine
from searcher.spell_corrector import SpellCorrector
from searcher.query_expander import QueryExpander
from searcher.semantic_search import SemanticSearch
from searcher.pagerank import PageRank

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# 全局组件（延迟初始化）
search_engine = None
spell_corrector = None
query_expander = None
semantic_search = None
pagerank = None


def initialize():
    """初始化所有搜索组件"""
    global search_engine, spell_corrector, query_expander, semantic_search, pagerank

    # 检查是否有数据，没有则生成示例数据
    if not os.path.exists(config.PAPERS_JSON):
        print("未找到论文数据，正在生成示例数据集...")
        papers = generate_sample_data()
        save_papers(papers)

    # 检查是否有索引，没有则构建
    ix = get_index()
    if ix is None:
        print("未找到索引，正在构建...")
        papers = load_and_preprocess()
        ix = build_index(papers, clean=True)

    # 初始化搜索引擎
    search_engine = SearchEngine()

    # 初始化拼写纠错
    try:
        spell_corrector = SpellCorrector()
        print("拼写纠错模块已加载")
    except Exception as e:
        print(f"拼写纠错模块加载失败: {e}")

    # 初始化查询扩展
    query_expander = QueryExpander()
    print(f"查询扩展模块已加载 (WordNet: {'可用' if query_expander.enabled else '不可用'})")

    # 加载论文数据用于语义搜索和 PageRank
    papers = load_and_preprocess()

    # 初始化语义搜索
    try:
        semantic_search = SemanticSearch(papers)
        print("语义搜索模块已加载")
    except Exception as e:
        print(f"语义搜索模块加载失败: {e}")

    # 计算 PageRank
    try:
        citation_graph = get_citation_graph(papers)
        pagerank = PageRank()
        pr_scores = pagerank.compute(citation_graph)
        search_engine.set_pagerank_scores(pr_scores)
        print("PageRank 模块已加载")
    except Exception as e:
        print(f"PageRank 模块加载失败: {e}")


@app.route('/')
def index():
    """搜索首页"""
    stats = {}
    if search_engine:
        stats = search_engine.get_index_stats()
    return render_template('index.html', stats=stats)


@app.route('/search')
def search():
    """搜索结果页"""
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    scoring = request.args.get('scoring', 'bm25')
    sort_by = request.args.get('sort', 'relevance')
    expand = request.args.get('expand', '0') == '1'
    year_filter = request.args.get('year', '')
    category_filter = request.args.get('category', '')

    if not query:
        return render_template('results.html', results=None, query='')

    # 查询扩展
    expansion_info = None
    search_query = query
    if expand and query_expander:
        expansion_info = query_expander.expand_query(query)
        if expansion_info['expansions']:
            search_query = expansion_info['expanded']

    # 拼写纠正
    correction = None
    if spell_corrector:
        correction = spell_corrector.correct(query)

    # 构建过滤条件
    filters = {}
    if year_filter:
        filters['year'] = year_filter
    if category_filter:
        filters['categories'] = category_filter

    # 执行搜索
    results = search_engine.search(
        search_query,
        page=page,
        scoring=scoring,
        filters=filters,
        sort_by=sort_by,
    )

    # 覆盖拼写纠正（如果搜索引擎也提供了）
    if not correction and results.get('correction'):
        correction = results['correction']

    return render_template(
        'results.html',
        results=results,
        query=query,
        search_query=search_query,
        scoring=scoring,
        sort_by=sort_by,
        expand=expand,
        expansion_info=expansion_info,
        correction=correction,
        year_filter=year_filter,
        category_filter=category_filter,
    )


@app.route('/paper/<arxiv_id>')
def paper_detail(arxiv_id):
    """论文详情页"""
    paper = search_engine.get_paper(arxiv_id)
    if not paper:
        return render_template('paper_detail.html', paper=None)

    # 获取相似论文
    similar_papers = []
    if semantic_search:
        similar_papers = semantic_search.find_similar(arxiv_id, top_k=5)

    # 获取 PageRank 分数
    pr_score = 0
    if pagerank:
        pr_score = pagerank.get_score(arxiv_id)

    return render_template(
        'paper_detail.html',
        paper=paper,
        similar_papers=similar_papers,
        pagerank_score=pr_score,
    )


@app.route('/api/search')
def api_search():
    """搜索 API（JSON 格式）"""
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    scoring = request.args.get('scoring', 'bm25')

    if not query:
        return jsonify({'error': '请提供查询关键词', 'results': []})

    results = search_engine.search(query, page=page, scoring=scoring)
    return jsonify(results)


@app.route('/api/suggest')
def api_suggest():
    """拼写建议 API"""
    word = request.args.get('q', '').strip()
    if not word or not spell_corrector:
        return jsonify({'suggestions': []})

    suggestions = spell_corrector.suggest(word)
    return jsonify({'suggestions': suggestions})


@app.route('/api/similar/<arxiv_id>')
def api_similar(arxiv_id):
    """相似论文推荐 API"""
    if not semantic_search:
        return jsonify({'similar': []})

    similar = semantic_search.find_similar(arxiv_id, top_k=5)
    return jsonify({'similar': similar})


if __name__ == '__main__':
    print("=" * 60)
    print("ScholarSearch - 学术论文垂直搜索引擎")
    print("=" * 60)

    initialize()

    print(f"\n服务启动于 http://localhost:{config.FLASK_PORT}")
    print("=" * 60)

    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG,
    )
