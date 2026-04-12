# ScholarSearch - 学术论文垂直搜索引擎

## 项目简介

ScholarSearch 是一个面向学术论文的垂直搜索引擎，作为 **Information Storage and Retrieval（信息存储与检索）** 课程的综合实践项目。本项目涵盖了信息检索（IR）领域的核心概念和技术，使用 Python Flask + Whoosh 技术栈实现。

## 系统架构

```
┌─────────────────────────────────────────────────────┐
│                   Web 界面 (Flask)                    │
│              搜索首页 / 结果页 / 详情页                │
├─────────────────────────────────────────────────────┤
│                    搜索模块 (Searcher)                │
│  ┌───────────┐ ┌──────────┐ ┌──────────┐           │
│  │ BM25/TF-IDF│ │ 拼写纠错  │ │ 查询扩展  │           │
│  │  核心搜索  │ │ 编辑距离  │ │ WordNet  │           │
│  └───────────┘ └──────────┘ └──────────┘           │
│  ┌───────────┐ ┌──────────┐                         │
│  │ 语义搜索   │ │ PageRank │                         │
│  │ TF-IDF余弦 │ │ 引用图谱  │                         │
│  └───────────┘ └──────────┘                         │
├─────────────────────────────────────────────────────┤
│                    索引模块 (Indexer)                  │
│            Whoosh 倒排索引 + BM25F 加权               │
├─────────────────────────────────────────────────────┤
│                    爬虫模块 (Crawler)                  │
│              arXiv API 论文元数据爬取                  │
└─────────────────────────────────────────────────────┘
```

## 核心 IR 概念与技术实现

### 1. 倒排索引 (Inverted Index)
倒排索引是信息检索系统的核心数据结构。对于每个词项（term），记录包含该词项的文档列表及词频信息。本项目使用 Whoosh 库构建倒排索引，支持多字段索引（标题、摘要、作者等）。

### 2. BM25 排序算法
BM25（Best Matching 25）是基于概率模型的文档排序算法，是 TF-IDF 的改进版本：
- 引入词频饱和函数，避免高词频的过度影响
- 加入文档长度归一化，消除长文档的偏差
- 参数 k1 控制词频饱和速度，b 控制长度归一化程度

### 3. TF-IDF 向量空间模型
- **TF（词频）**：词在文档中出现的频率
- **IDF（逆文档频率）**：log(总文档数 / 包含该词的文档数)
- 用于语义搜索模块中的文档向量化和余弦相似度计算

### 4. PageRank 算法
基于论文引用关系图计算论文重要性分数，核心思想：被更多重要论文引用的论文，其 PageRank 值更高。通过迭代计算收敛到稳定分数，融合到搜索排序中。

### 5. 拼写纠错 (Spelling Correction)
基于编辑距离（Levenshtein Distance）的拼写纠错，提供 "Did you mean?" 建议。

### 6. 查询扩展 (Query Expansion)
基于 WordNet 同义词库的查询扩展，通过添加同义词提高查全率（Recall）。

### 7. 分面搜索 (Faceted Search)
支持按年份、分类等维度进行过滤，帮助用户快速缩小搜索范围。

## 安装与运行

### 环境要求
- Python 3.8+
- pip

### 安装步骤

```bash
# 1. 进入项目目录
cd demo

# 2. 安装 Python 依赖
pip install -r requirements.txt

# 3. 下载 NLTK 数据（查询扩展需要）
python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"

# 4. 生成示例数据集（约500篇CS领域论文，无需网络）
python crawler/arxiv_crawler.py --sample

# 5. 构建倒排索引
python indexer/index_builder.py

# 6. 启动 Flask 服务
python app.py
```

### 访问
浏览器打开 `http://localhost:5000` 即可使用搜索功能。

> **提示**: 首次运行 `python app.py` 时，如果没有数据和索引，系统会自动生成示例数据并构建索引。

### 使用真实 arXiv 数据（可选）

```bash
# 从 arXiv API 爬取真实论文数据（需要网络，约需几分钟）
python crawler/arxiv_crawler.py --max 500

# 重新构建索引
python indexer/index_builder.py --clean
```

## 功能演示

### 基本搜索
- `machine learning` — 搜索包含 "machine learning" 的论文
- `"neural network"` — 短语精确匹配
- `deep AND learning` — 布尔 AND 查询
- `title:transformer` — 指定在标题字段中搜索
- `authors:wang` — 按作者搜索

### 高级功能
- **排序模型切换**：BM25 / TF-IDF 对比
- **查询扩展**：启用后自动添加同义词，扩大搜索范围
- **拼写纠错**：输入错误时自动提示 "Did you mean?"
- **分面过滤**：按年份、分类筛选结果
- **相似论文推荐**：在论文详情页查看语义相似的论文
- **PageRank 排序**：基于引用关系的重要性排序

## 项目结构

```
demo/
├── app.py                       # Flask 主应用
├── config.py                    # 配置文件
├── requirements.txt             # Python 依赖
├── crawler/                     # 爬虫模块
│   ├── arxiv_crawler.py         # arXiv API 爬虫 + 示例数据生成
│   └── data_loader.py           # 数据加载与预处理
├── indexer/                     # 索引模块
│   ├── schema.py                # Whoosh Schema 定义
│   ├── index_builder.py         # 倒排索引构建
│   └── chinese_analyzer.py      # 中文分词分析器 (jieba)
├── searcher/                    # 搜索模块
│   ├── search_engine.py         # 核心搜索 (BM25, TF-IDF, 布尔查询)
│   ├── spell_corrector.py       # 拼写纠错 (编辑距离)
│   ├── query_expander.py        # 查询扩展 (WordNet)
│   ├── semantic_search.py       # 语义搜索 (TF-IDF + 余弦相似度)
│   └── pagerank.py              # PageRank 算法
├── templates/                   # HTML 模板
│   ├── base.html                # 基础模板
│   ├── index.html               # 搜索首页
│   ├── results.html             # 搜索结果页
│   └── paper_detail.html        # 论文详情页
├── static/                      # 静态资源
│   ├── css/style.css
│   └── js/main.js
├── data/                        # 论文数据目录
├── index_dir/                   # Whoosh 索引目录
└── tests/                       # 测试
```

## 技术栈

| 组件 | 技术 |
|------|------|
| Web 框架 | Flask |
| 全文索引 | Whoosh |
| 爬虫 | requests + arXiv API |
| 中文分词 | jieba |
| 同义词库 | NLTK WordNet |
| 向量化 | scikit-learn TfidfVectorizer |
| 数值计算 | NumPy |
