from flask import Flask, render_template, request, jsonify, Response, stream_with_context, send_file, send_from_directory
import threading
import time
import os
import json
import concurrent.futures
import random
from datetime import datetime, timedelta
from wechat_scraper.auth import WeChatAuth
from wechat_scraper.crawler import WeChatCrawler
from wechat_scraper.downloader import WeChatDownloader
from wechat_scraper.database import Database
from wechat_scraper.logger import logger
from wechat_scraper.exceptions import RateLimitError, AccountNotFoundError, NetworkError

app = Flask(__name__)

# Global instances
auth = WeChatAuth()
crawler = None
db = Database()

def get_crawler():
    global crawler
    if crawler:
        return crawler
    
    if auth.load_cookies():
        token, cookies = auth.token, auth.cookies
        crawler = WeChatCrawler(token, cookies)
        return crawler
    return None

@app.route('/output/<path:filename>')
def serve_output(filename):
    highlight = request.args.get('highlight')
    if not highlight or not filename.endswith('.html'):
        return send_from_directory('output', filename)
    
    try:
        file_path = os.path.join('output', filename)
        if not os.path.exists(file_path):
            return "File not found", 404
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 注入增强的高亮和搜索导航脚本
        script = f"""
        <style>
            .search-highlight {{
                background-color: yellow;
                color: black;
                font-weight: bold;
                position: relative;
            }}
            .search-highlight.active {{
                background-color: orange;
                outline: 2px solid red;
            }}
            #searchNavPanel {{
                position: fixed;
                top: 20px;
                right: 20px;
                width: 320px;
                min-width: 250px;
                max-width: 600px;
                max-height: 500px;
                min-height: 200px;
                background: white;
                border: 2px solid #07c160;
                border-radius: 8px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                z-index: 10000;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                resize: both;
                overflow: hidden;
            }}
            #searchNavHeader {{
                background: #07c160;
                color: white;
                padding: 12px 15px;
                font-weight: bold;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-radius: 6px 6px 0 0;
                cursor: move;
                user-select: none;
            }}
            #searchNavClose {{
                cursor: pointer;
                font-size: 20px;
                line-height: 1;
                padding: 0 5px;
            }}
            #searchNavContent {{
                padding: 15px;
                height: calc(100% - 50px);
                overflow-y: auto;
            }}
            .search-result-item {{
                padding: 10px;
                margin: 5px 0;
                background: #f5f5f5;
                border-left: 3px solid #07c160;
                cursor: pointer;
                border-radius: 4px;
                transition: all 0.2s;
            }}
            .search-result-item:hover {{
                background: #e0e0e0;
                transform: translateX(5px);
            }}
            .search-result-item.active {{
                background: #ffd700;
                border-left-color: #ff6600;
            }}
            .search-result-preview {{
                font-size: 13px;
                color: #333;
                line-height: 1.4;
                margin-top: 5px;
            }}
            .search-result-index {{
                display: inline-block;
                background: #07c160;
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 12px;
                margin-right: 8px;
            }}
            .resize-handle {{
                position: absolute;
                width: 15px;
                height: 15px;
                background: #07c160;
                border-radius: 0 0 0 8px;
                bottom: 0;
                right: 0;
                cursor: nwse-resize;
                opacity: 0.7;
            }}
            .resize-handle:hover {{
                opacity: 1;
            }}
            .resize-handle::before {{
                content: '';
                position: absolute;
                bottom: 2px;
                right: 2px;
                width: 10px;
                height: 10px;
                border-right: 2px solid white;
                border-bottom: 2px solid white;
            }}
        </style>
        <script>
            document.addEventListener("DOMContentLoaded", function() {{
                var keyword = "{highlight}";
                if (!keyword) return;
                
                var matches = [];
                var currentIndex = 0;
                
                // 高亮所有匹配项并收集信息
                var body = document.body;
                var walker = document.createTreeWalker(body, NodeFilter.SHOW_TEXT, null, false);
                var node;
                var nodes = [];
                while(node = walker.nextNode()) {{
                    nodes.push(node);
                }}
                
                nodes.forEach(function(node) {{
                    if (node.parentNode.nodeName !== "SCRIPT" && 
                        node.parentNode.nodeName !== "STYLE" && 
                        node.nodeValue.toLowerCase().includes(keyword.toLowerCase())) {{
                        
                        var parent = node.parentNode;
                        var regex = new RegExp("(" + keyword.replace(/[.*+?^${{}}()|[\\\\]\\\\\\\\]/g, '\\\\\\\\$&') + ")", "gi");
                        var parts = node.nodeValue.split(regex);
                        
                        var fragment = document.createDocumentFragment();
                        parts.forEach(function(part, i) {{
                            if (i % 2 === 1) {{
                                var span = document.createElement("span");
                                span.className = "search-highlight";
                                span.textContent = part;
                                span.setAttribute("data-match-index", matches.length);
                                fragment.appendChild(span);
                                
                                // 收集上下文
                                var context = node.nodeValue.substring(
                                    Math.max(0, node.nodeValue.toLowerCase().indexOf(part.toLowerCase()) - 30),
                                    Math.min(node.nodeValue.length, node.nodeValue.toLowerCase().indexOf(part.toLowerCase()) + part.length + 30)
                                );
                                matches.push({{
                                    element: span,
                                    context: context,
                                    text: part
                                }});
                            }} else {{
                                fragment.appendChild(document.createTextNode(part));
                            }}
                        }});
                        parent.replaceChild(fragment, node);
                    }}
                }});
                
                if (matches.length === 0) return;
                
                // 创建搜索导航面板
                var panel = document.createElement("div");
                panel.id = "searchNavPanel";
                panel.innerHTML = `
                    <div id="searchNavHeader">
                        <span>找到 ${{matches.length}} 个匹配项</span>
                        <span id="searchNavClose">×</span>
                    </div>
                    <div id="searchNavContent"></div>
                    <div class="resize-handle"></div>
                `;
                document.body.appendChild(panel);
                
                // 填充搜索结果列表
                var content = document.getElementById("searchNavContent");
                matches.forEach(function(match, index) {{
                    var item = document.createElement("div");
                    item.className = "search-result-item";
                    item.innerHTML = `
                        <div>
                            <span class="search-result-index">${{index + 1}}</span>
                            <strong>${{match.text}}</strong>
                        </div>
                        <div class="search-result-preview">${{match.context}}</div>
                    `;
                    item.onclick = function() {{
                        jumpToMatch(index);
                    }};
                    content.appendChild(item);
                }});
                
                // 跳转到指定匹配项
                function jumpToMatch(index) {{
                    if (index < 0 || index >= matches.length) return;
                    
                    // 移除之前的高亮
                    matches.forEach(function(m) {{
                        m.element.classList.remove("active");
                    }});
                    document.querySelectorAll(".search-result-item").forEach(function(item) {{
                        item.classList.remove("active");
                    }});
                    
                    // 高亮当前项
                    currentIndex = index;
                    matches[index].element.classList.add("active");
                    document.querySelectorAll(".search-result-item")[index].classList.add("active");
                    
                    // 滚动到视图
                    matches[index].element.scrollIntoView({{
                        behavior: "auto",
                        block: "center"
                    }});
                }}
                
                // 关闭按钮
                document.getElementById("searchNavClose").onclick = function() {{
                    panel.style.display = "none";
                }};
                
                // 拖拽移动面板
                var header = document.getElementById("searchNavHeader");
                var isDragging = false;
                var currentX, currentY, initialX, initialY;
                
                header.addEventListener("mousedown", function(e) {{
                    if (e.target.id === "searchNavClose") return;
                    isDragging = true;
                    initialX = e.clientX - panel.offsetLeft;
                    initialY = e.clientY - panel.offsetTop;
                }});
                
                document.addEventListener("mousemove", function(e) {{
                    if (isDragging) {{
                        e.preventDefault();
                        currentX = e.clientX - initialX;
                        currentY = e.clientY - initialY;
                        panel.style.left = currentX + "px";
                        panel.style.top = currentY + "px";
                        panel.style.right = "auto";
                    }}
                }});
                
                document.addEventListener("mouseup", function() {{
                    isDragging = false;
                }});
                
                // 调整尺寸
                var resizeHandle = panel.querySelector(".resize-handle");
                var isResizing = false;
                var startWidth, startHeight, startX, startY;
                
                resizeHandle.addEventListener("mousedown", function(e) {{
                    isResizing = true;
                    startWidth = panel.offsetWidth;
                    startHeight = panel.offsetHeight;
                    startX = e.clientX;
                    startY = e.clientY;
                    e.preventDefault();
                }});
                
                document.addEventListener("mousemove", function(e) {{
                    if (isResizing) {{
                        var newWidth = startWidth + (e.clientX - startX);
                        var newHeight = startHeight + (e.clientY - startY);
                        
                        if (newWidth >= 250 && newWidth <= 600) {{
                            panel.style.width = newWidth + "px";
                        }}
                        if (newHeight >= 200 && newHeight <= 800) {{
                            panel.style.height = newHeight + "px";
                            panel.style.maxHeight = newHeight + "px";
                        }}
                    }}
                }});
                
                document.addEventListener("mouseup", function() {{
                    isResizing = false;
                }});
                
                // 自动跳转到第一个匹配项
                if (matches.length > 0) {{
                    jumpToMatch(0);
                }}
            }});
        </script>
        </body>
        """
        content = content.replace('</body>', script)
        return content
    except Exception as e:
        logger.error(f"Error serving highlighted file: {{e}}")
        return send_from_directory('output', filename)


@app.route('/api/export')
def export_excel():
    try:
        import pandas as pd
        import io
        
        results = db.get_all_articles_with_account()
        
        # 转换为DataFrame
        data = []
        for r in results:
            # r: id, account_name, title, publish_date, status, link, local_path, content
            data.append({
                "ID": r[0],
                "公众号": r[1],
                "标题": r[2],
                "发布日期": r[3],
                "状态": "✅ 已下载" if r[4] == 'completed' or r[4] == 'success' else "❌ 失败" if r[4] == 'failed' else "⏳ 等待中",
                "正文内容": r[7] if len(r) > 7 and r[7] else "",
                "原文链接": r[5],
                "本地路径": r[6] if r[6] else ""
            })
            
        df = pd.DataFrame(data)
        
        # 创建Excel文件
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='文章列表')
            
        output.seek(0)
        filename = f"wechat_articles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"导出Excel失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def status():
    is_logged_in = auth.load_cookies()
    
    # 检查是否处于频率限制中
    rate_limited = db.is_rate_limited()
    rate_limit_info = None
    
    if rate_limited:
        limit = db.get_latest_rate_limit()
        if limit:
            reset_time = datetime.fromisoformat(limit[4])
            remaining_seconds = (reset_time - datetime.now()).total_seconds()
            rate_limit_info = {
                "limited": True,
                "reset_time": limit[4],
                "remaining_seconds": max(0, int(remaining_seconds))
            }
    
    return jsonify({
        "logged_in": is_logged_in,
        "rate_limit": rate_limit_info or {"limited": False}
    })

@app.route('/api/accounts')
def get_accounts():
    """获取已抓取的公众号列表（从数据库）"""
    try:
        accounts = db.get_all_accounts()
        account_list = []
        
        for acc in accounts:
            account_list.append({
                "id": acc[0],
                "name": acc[1],
                "nickname": acc[3],
                "total_articles": acc[6],
                "last_scraped": acc[5]
            })
        
        return jsonify({"accounts": account_list})
    except Exception as e:
        logger.error(f"获取公众号列表失败: {e}", exc_info=True)
        return jsonify({"accounts": [], "error": str(e)})

@app.route('/api/articles/<int:account_id>')
def get_articles(account_id):
    """获取公众号的文章列表"""
    try:
        articles = db.get_articles_by_account(account_id)
        article_list = []
        
        for art in articles:
            article_list.append({
                "id": art[0],
                "title": art[2],
                "link": art[3],
                "publish_date": art[5],
                "downloaded": bool(art[7]),
                "filepath": art[9],
                "status": art[11]
            })
        
        return jsonify({"articles": article_list})
    except Exception as e:
        logger.error(f"获取文章列表失败: {e}", exc_info=True)
        return jsonify({"articles": [], "error": str(e)})

@app.route('/api/login', methods=['POST'])
def login():
    global crawler
    try:
        token, cookies = auth.login()
        if token and cookies:
            crawler = WeChatCrawler(token, cookies)
            logger.info("登录成功")
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "登录失败"}), 401
    except Exception as e:
        logger.error(f"登录失败: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/relogin', methods=['POST'])
def relogin():
    global crawler
    try:
        if os.path.exists("wechat_cookies.json"):
            os.remove("wechat_cookies.json")
        
        token, cookies = auth.login()
        if token and cookies:
            crawler = WeChatCrawler(token, cookies)
            logger.info("重新登录成功")
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "重新登录失败"}), 401
    except Exception as e:
        logger.error(f"重新登录失败: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

def download_article_wrapper(downloader, article, index, total):
    """下载单篇文章的包装函数"""
    time.sleep(random.uniform(1, 3))
    
    title = article.get('title', 'Untitled')
    link = article.get('link')
    date = time.strftime("%Y-%m-%d", time.localtime(article.get('update_time')))
    
    success, article_id, img_count, error = downloader.download_article(link, title, date)
    
    if success:
        return f"[{index}/{total}] ✓ 完成: {title}"
    else:
        return f"[{index}/{total}] ✗ 失败: {title} ({error})"

def process_account(account_name, pages):
    """处理单个公众号的抓取任务"""
    crawler_instance = get_crawler()
    if not crawler_instance:
        yield "错误: 未登录或 Cookies 已过期\n"
        return

    # 创建任务记录
    task_id = db.create_task(account_name, 'single', pages)
    
    try:
        yield f"正在搜索: {account_name}...\n"
        
        # 搜索公众号
        try:
            fakeid, nickname, alias = crawler_instance.search_account(account_name)
        except RateLimitError as e:
            # 记录频率限制
            db.record_rate_limit(account_name)
            db.complete_task(task_id, 'failed', str(e))
            yield f"⚠️ 触发频率限制！请等待30分钟后再试。\n"
            return
        except AccountNotFoundError as e:
            db.complete_task(task_id, 'failed', str(e))
            yield f"错误: {e}\n"
            return
        
        # 添加/更新公众号记录
        account_id = db.add_account(account_name, fakeid, nickname, alias)
        
        yield f"正在抓取文章列表 (前 {pages} 页)...\n"
        
        # 获取文章列表
        try:
            articles = crawler_instance.fetch_all_articles(fakeid, max_pages=int(pages))
        except RateLimitError as e:
            db.record_rate_limit(account_name)
            db.complete_task(task_id, 'failed', str(e))
            yield f"⚠️ 触发频率限制！请等待30分钟后再试。\n"
            return
        
        yield f"找到 {len(articles)} 篇文章\n"
        
        if not articles:
            db.complete_task(task_id, 'completed')
            return

        # 更新公众号统计
        db.update_account_stats(account_id, len(articles))
        
        # 下载文章
        yield "开始下载文章...\n"
        downloader = WeChatDownloader(
            output_dir=f"output/{account_name}",
            cookies=auth.cookies,
            account_id=account_id
        )
        
        downloaded_count = 0
        failed_count = 0
        
        max_workers = 2
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for i, article in enumerate(articles):
                future = executor.submit(download_article_wrapper, downloader, article, i + 1, len(articles))
                futures.append(future)
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    yield f"{result}\n"
                    
                    if "✓" in result:
                        downloaded_count += 1
                    else:
                        failed_count += 1
                    
                    # 更新任务进度
                    db.update_task_progress(task_id, len(articles), downloaded_count, failed_count)
                    
                except Exception as e:
                    logger.error(f"下载任务出错: {e}", exc_info=True)
                    yield f"下载出错: {e}\n"
                    failed_count += 1

        # 完成任务
        db.complete_task(task_id, 'completed')
        
        yield f"\n公众号 {account_name} 处理完成!\n"
        yield f"成功: {downloaded_count} 篇, 失败: {failed_count} 篇\n"
        yield "-" * 30 + "\n"
        
    except Exception as e:
        logger.error(f"处理公众号时发生错误: {e}", exc_info=True)
        db.complete_task(task_id, 'failed', str(e))
        yield f"发生错误: {e}\n"

@app.route('/api/scrape', methods=['POST'])
def scrape():
    data = request.json
    task_type = data.get('type')
    pages = int(data.get('pages', 1))
    
    def generate():
        try:
            if task_type == 'single':
                name = data.get('name')
                yield from process_account(name, pages)
            elif task_type == 'batch':
                accounts = data.get('accounts', [])
                for i, name in enumerate(accounts):
                    yield f"\n=== 开始处理第 {i+1}/{len(accounts)} 个公众号: {name} ===\n"
                    yield from process_account(name, pages)
                    
                    if i < len(accounts) - 1:
                        delay = random.randint(30, 60)
                        yield f"\n等待 {delay} 秒后继续下一个公众号...\n"
                        time.sleep(delay)
            
            yield "\n所有任务执行完毕。\n"
        except Exception as e:
            logger.error(f"抓取任务出错: {e}", exc_info=True)
            yield f"\n发生严重错误: {e}\n"

    return Response(stream_with_context(generate()), mimetype='text/plain')

@app.route('/api/search')
def search_articles():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    results = db.search_articles(query)
    articles = []
    for r in results:
        articles.append({
            "id": r[0],
            "title": r[1],
            "link": r[2],
            "publish_date": r[3],
            "downloaded": bool(r[4]),
            "local_path": r[5],
            "account_name": r[6],
            "is_favorite": bool(r[7]) if len(r) > 7 else False,
            "is_read": bool(r[8]) if len(r) > 8 else False,
            "tags": r[9].split(',') if len(r) > 9 and r[9] else []
        })
    return jsonify(articles)

@app.route('/api/articles/<int:article_id>/favorite', methods=['POST'])
def toggle_favorite_api(article_id):
    db.toggle_favorite(article_id)
    return jsonify({"success": True})

@app.route('/api/articles/<int:article_id>/read', methods=['POST'])
def toggle_read_api(article_id):
    db.toggle_read(article_id)
    return jsonify({"success": True})

@app.route('/api/articles/<int:article_id>/tags', methods=['POST'])
def update_tags_api(article_id):
    data = request.json
    tags = data.get('tags', [])
    db.update_tags(article_id, tags)
    return jsonify({"success": True})

@app.route('/api/articles/batch/delete', methods=['POST'])
def batch_delete_api():
    data = request.json
    article_ids = data.get('ids', [])
    if article_ids:
        db.batch_delete_articles(article_ids)
    return jsonify({"success": True, "deleted": len(article_ids)})

@app.route('/api/articles/batch/read', methods=['POST'])
def batch_mark_read_api():
    data = request.json
    article_ids = data.get('ids', [])
    is_read = data.get('is_read', True)
    if article_ids:
        db.batch_mark_read(article_ids, is_read)
    return jsonify({"success": True, "updated": len(article_ids)})


if __name__ == '__main__':
    import webbrowser
    
    def open_browser():
        time.sleep(1.5)
        webbrowser.open('http://127.0.0.1:5001')
    
    # 只有在 reloader 子进程中才打开浏览器,避免双开
    # WERKZEUG_RUN_MAIN 环境变量在 reloader 进程中为 'true'
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        logger.info("启动 Web 服务 V2...")
        print("启动 Web 服务 V2...")
        print("请在浏览器访问: http://127.0.0.1:5001")
        print("正在自动打开浏览器...")
        threading.Thread(target=open_browser, daemon=True).start()
    
    app.run(debug=True, port=5001)

