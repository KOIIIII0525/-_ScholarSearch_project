"""
ScholarSearch 配置文件
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据目录
DATA_DIR = os.path.join(BASE_DIR, 'data')
PAPERS_JSON = os.path.join(DATA_DIR, 'papers.json')

# 索引目录
INDEX_DIR = os.path.join(BASE_DIR, 'index_dir')

# 爬虫配置
ARXIV_API_URL = 'http://export.arxiv.org/api/query'
DEFAULT_QUERY = 'cat:cs.IR OR cat:cs.CL OR cat:cs.AI OR cat:cs.LG'
MAX_RESULTS_PER_REQUEST = 100
MAX_TOTAL_PAPERS = 500
REQUEST_DELAY = 3  # 秒，避免触发 API 限流

# 搜索配置
RESULTS_PER_PAGE = 10
MAX_SUGGESTIONS = 5
BM25_B = 0.75
BM25_K1 = 1.5

# PageRank 配置
PAGERANK_DAMPING = 0.85
PAGERANK_ITERATIONS = 100
PAGERANK_WEIGHT = 0.3  # PageRank 分数在最终排序中的权重

# 语义搜索配置
SEMANTIC_TOP_K = 10

# Flask 配置
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5000
FLASK_DEBUG = True
SECRET_KEY = os.environ.get('SCHOLARSEARCH_SECRET_KEY', 'dev-only-change-me')
