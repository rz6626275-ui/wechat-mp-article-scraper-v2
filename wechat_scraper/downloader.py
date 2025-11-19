import requests
import os
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .utils import sanitize_filename, create_dir
from .css_template import WECHAT_CSS
from .logger import logger
from .exceptions import DownloadError, ContentParseError, NetworkError
from .database import Database

class WeChatDownloader:
    def __init__(self, output_dir="output", max_retries=3, cookies=None, account_id=None):
        self.output_dir = output_dir
        create_dir(self.output_dir)
        self.images_dir = os.path.join(self.output_dir, "images")
        create_dir(self.images_dir)
        self.max_retries = max_retries
        self.cookies = cookies
        self.account_id = account_id
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        self.db = Database()
        logger.info(f"初始化下载器，输出目录: {output_dir}, account_id: {account_id}")
    
    def is_downloaded(self, article_url):
        """检查文章是否已下载（通过数据库）"""
        article = self.db.get_article_by_link(article_url)
        if article and article[7]:  # downloaded字段
            logger.debug(f"文章已下载: {article_url}")
            return True
        return False
    
    def download_image(self, url, filename, retry_count=0):
        """下载图片"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            filepath = os.path.join(self.images_dir, filename)
            with open(filepath, "wb") as f:
                f.write(response.content)
            logger.debug(f"图片下载成功: {filename}")
            return filepath
        except Exception as e:
            if retry_count < self.max_retries:
                logger.warning(f"下载图片失败，正在重试 ({retry_count + 1}/{self.max_retries}): {url}")
                time.sleep(2)
                return self.download_image(url, filename, retry_count + 1)
            else:
                logger.error(f"下载图片失败(已达最大重试次数): {url}, 错误: {e}")
                return None

    def download_article(self, article_url, title, date, retry_count=0):
        """
        下载文章，返回 (success, article_id, image_count, error_message)
        """
        # 检查是否已下载
        if self.is_downloaded(article_url):
            logger.info(f"跳过重复文章: {title}")
            return True, None, 0, None
        
        # 添加文章记录到数据库
        article_id = self.db.add_article(
            account_id=self.account_id,
            title=title,
            link=article_url,
            publish_date=date
        )
        
        try:
            logger.info(f"开始下载文章: {title}")
            
            response = requests.get(article_url, headers=self.headers, cookies=self.cookies, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "lxml")
            
            # Extract content div
            content_div = soup.find("div", {"id": "js_content"})
            if not content_div:
                content_div = soup.find("div", {"class": "rich_media_content"})
            
            if not content_div:
                content_div = soup.find("div", {"id": "img-content"})

            if not content_div:
                # 检查是否是验证页面或错误页面
                if "验证" in soup.title.text if soup.title else "":
                    error_msg = f"遇到验证页面: {title}"
                elif "访问受限" in soup.text:
                    error_msg = f"访问受限: {title}"
                else:
                    debug_content = soup.prettify()[:500].replace("\n", " ")
                    error_msg = f"无法找到内容: {title}. 页面预览: {debug_content}..."
                
                logger.error(error_msg)
                self.db.mark_article_failed(article_id, error_msg)
                raise ContentParseError(error_msg)

            # 检查内容长度
            text_content = content_div.get_text(strip=True)
            
            # 保存纯文本内容到数据库（用于全文搜索）
            if text_content:
                self.db.update_article_content(article_id, text_content)
            
            if len(text_content) < 50 and not content_div.find("img"):
                body_content = soup.find("body")
                if body_content and len(body_content.get_text(strip=True)) > 200:
                    warning_msg = f"警告: 主要内容容器为空，但页面包含其他内容: {title}"
                else:
                    warning_msg = f"警告: 文章内容似乎为空或过短: {title}"
                logger.warning(warning_msg)

            # Remove hidden styles
            if content_div.has_attr('style'):
                del content_div['style']
            
            content_div['style'] = "visibility: visible !important; opacity: 1 !important;"
            
            # Process images
            imgs = content_div.find_all("img")
            img_count = len(imgs)
            logger.debug(f"找到 {img_count} 张图片")
            
            for i, img in enumerate(imgs):
                src = img.get("data-src")
                if not src:
                    src = img.get("src")
                    if not src or src.startswith("data:"):
                        continue
                
                fmt = img.get("data-type", "jpg")
                img_filename = f"{sanitize_filename(title)}_{i}.{fmt}"
                
                local_path = self.download_image(src, img_filename)
                
                if local_path:
                    relative_path = os.path.join("images", img_filename)
                    img["src"] = relative_path
                    if img.has_attr("data-src"):
                        del img["data-src"]
                    img["style"] = "width: 100% !important; height: auto !important; visibility: visible !important;"

            # Create HTML
            html_content = f"""
            <!DOCTYPE html>
            <html lang="zh-CN">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{title}</title>
                {WECHAT_CSS}
            </head>
            <body>
                <div class="page-container">
                    <h1 class="article-title">{title}</h1>
                    <div class="article-meta">
                        <span class="account-name">公众号文章</span>
                        <span class="publish-time">{date}</span>
                    </div>
                    <hr>
                    {str(content_div)}
                </div>
            </body>
            </html>
            """
            
            filename = f"{date}_{sanitize_filename(title)}.html"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            # 标记为已下载
            self.db.mark_article_downloaded(article_id, filepath, img_count)
            
            logger.info(f"文章下载成功: {title}, 图片数: {img_count}")
            return True, article_id, img_count, None

        except ContentParseError as e:
            return False, article_id, 0, str(e)
        except Exception as e:
            error_msg = f"下载文章时出错: {e}"
            logger.error(error_msg, exc_info=True)
            
            # 重试逻辑
            if retry_count < self.max_retries:
                logger.info(f"正在重试 ({retry_count + 1}/{self.max_retries})...")
                time.sleep(3)
                return self.download_article(article_url, title, date, retry_count + 1)
            else:
                self.db.mark_article_failed(article_id, error_msg)
                logger.error(f"下载失败(已达最大重试次数): {title}")
                return False, article_id, 0, error_msg
