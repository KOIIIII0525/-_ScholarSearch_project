/**
 * ScholarSearch - 前端交互脚本
 */

// 高级搜索选项切换
function toggleAdvanced() {
    var options = document.getElementById('advanced-options');
    if (options.style.display === 'none') {
        options.style.display = 'flex';
    } else {
        options.style.display = 'none';
    }
}

// 搜索输入自动补全/建议
document.addEventListener('DOMContentLoaded', function() {
    var searchInput = document.getElementById('search-input');
    if (!searchInput) return;

    // 搜索框获得焦点时的视觉反馈
    searchInput.addEventListener('focus', function() {
        this.parentElement.style.boxShadow = '0 2px 8px rgba(66, 133, 244, 0.2)';
    });

    searchInput.addEventListener('blur', function() {
        this.parentElement.style.boxShadow = 'none';
    });

    // 按 Enter 提交搜索
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            this.closest('form').submit();
        }
    });
});

// 平滑滚动到顶部
function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// 搜索结果页面加载完成后的处理
document.addEventListener('DOMContentLoaded', function() {
    // 高亮当前页码
    var pageLinks = document.querySelectorAll('.page-link');
    pageLinks.forEach(function(link) {
        link.addEventListener('click', function() {
            scrollToTop();
        });
    });
});
