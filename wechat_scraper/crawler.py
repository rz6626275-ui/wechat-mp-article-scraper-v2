import requests
import time
import random
from .logger import logger
from .exceptions import RateLimitError, AccountNotFoundError, NetworkError

class WeChatCrawler:
    def __init__(self, token, cookies):
        self.token = token
        self.cookies = cookies
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": f"https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit_v2&action=edit&isNew=1&type=10&token={token}&lang=zh_CN",
            "Host": "mp.weixin.qq.com",
        }
        self.base_url = "https://mp.weixin.qq.com"
        logger.info(f"初始化爬虫，Token: {token[:10]}...")

    def _randomize_user_agent(self):
        """随机化User-Agent，增强反爬能力"""
        user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        ]
        self.headers["User-Agent"] = random.choice(user_agents)

    def search_account(self, query):
        """
        搜索公众号，返回 (fakeid, nickname, alias) 或抛出异常
        """
        logger.info(f"搜索公众号: {query}")
        self._randomize_user_agent()
        
        search_url = f"{self.base_url}/cgi-bin/searchbiz"
        params = {
            "action": "search_biz",
            "token": self.token,
            "lang": "zh_CN",
            "f": "json",
            "ajax": "1",
            "random": random.random(),
            "query": query,
            "begin": "0",
            "count": "5",
        }

        try:
            response = requests.get(search_url, cookies=self.cookies, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # 检查频率限制
            if "base_resp" in data and data["base_resp"].get("ret") == 200013:
                logger.error(f"触发频率限制: {data}")
                raise RateLimitError("搜索时触发频率限制，请稍后再试")
            
            if "list" in data and len(data["list"]) > 0:
                account = data["list"][0]
                logger.info(f"找到公众号: {account['nickname']} ({account['alias']})")
                return account["fakeid"], account["nickname"], account.get("alias", "")
            else:
                logger.warning(f"未找到公众号: {query}")
                raise AccountNotFoundError(f"未找到公众号: {query}")
                
        except requests.RequestException as e:
            logger.error(f"搜索公众号时网络错误: {e}", exc_info=True)
            raise NetworkError(f"网络请求失败: {e}")
        except RateLimitError:
            raise
        except Exception as e:
            logger.error(f"搜索公众号时发生未知错误: {e}", exc_info=True)
            raise

    def get_articles(self, fakeid, begin=0, count=5):
        """
        获取文章列表，返回 (articles, total_count) 或抛出异常
        """
        logger.debug(f"获取文章列表: fakeid={fakeid}, begin={begin}, count={count}")
        self._randomize_user_agent()
        
        appmsg_url = f"{self.base_url}/cgi-bin/appmsg"
        params = {
            "token": self.token,
            "lang": "zh_CN",
            "f": "json",
            "ajax": "1",
            "action": "list_ex",
            "begin": str(begin),
            "count": str(count),
            "query": "",
            "fakeid": fakeid,
            "type": "9",
        }

        try:
            response = requests.get(appmsg_url, cookies=self.cookies, headers=self.headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            # 检查频率限制
            if "base_resp" in data:
                ret_code = data["base_resp"].get("ret")
                if ret_code == 200013:
                    logger.error(f"触发频率限制: {data}")
                    raise RateLimitError("获取文章列表时触发频率限制")
                elif ret_code != 0:
                    logger.warning(f"API返回非0状态码: {ret_code}, {data}")
            
            if "app_msg_list" in data:
                articles = data["app_msg_list"]
                total_cnt = data.get("app_msg_cnt", 0)
                logger.info(f"成功获取 {len(articles)} 篇文章，总数: {total_cnt}")
                return articles, total_cnt
            else:
                logger.warning(f"响应中没有文章列表: {data}")
                return [], 0
                
        except requests.RequestException as e:
            logger.error(f"获取文章列表时网络错误: {e}", exc_info=True)
            raise NetworkError(f"网络请求失败: {e}")
        except RateLimitError:
            raise
        except Exception as e:
            logger.error(f"获取文章列表时发生未知错误: {e}", exc_info=True)
            raise

    def fetch_all_articles(self, fakeid, max_pages=10):
        """
        分页获取所有文章
        """
        logger.info(f"开始分页获取文章，最多 {max_pages} 页")
        all_articles = []
        count = 5
        begin = 0
        
        for page in range(max_pages):
            logger.info(f"正在抓取第 {page + 1}/{max_pages} 页...")
            
            try:
                articles, total_cnt = self.get_articles(fakeid, begin, count)
                
                if not articles:
                    logger.info("没有更多文章，停止抓取")
                    break
                    
                all_articles.extend(articles)
                logger.debug(f"当前已获取 {len(all_articles)}/{total_cnt} 篇文章")
                
                if len(all_articles) >= total_cnt:
                    logger.info("已获取所有文章")
                    break
                    
                begin += count
                
                # 随机延迟，避免触发频率限制
                delay = random.uniform(2, 5)
                logger.debug(f"等待 {delay:.1f} 秒后继续...")
                time.sleep(delay)
                
            except RateLimitError:
                logger.warning(f"在第 {page + 1} 页触发频率限制，停止抓取，返回已获取的 {len(all_articles)} 篇文章")
                return all_articles, True
            except Exception as e:
                logger.error(f"抓取第 {page + 1} 页时出错: {e}")
                break
        
        logger.info(f"抓取完成，共获取 {len(all_articles)} 篇文章")
        return all_articles, False
