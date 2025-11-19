# 微信公众号文章抓取工具 V2.0

一个功能强大的微信公众号文章抓取和管理工具，支持全文搜索、批量操作、数据导出等功能。

## ⚠️ 免责声明

**本工具仅供学习交流使用，请遵守以下规定：**

- ✅ 仅用于个人学习和研究
- ✅ 遵守微信公众平台相关规定和服务条款
- ✅ 尊重原创内容版权，不得用于商业用途
- ✅ 合理控制抓取频率，避免给服务器造成压力
- ❌ 不得用于批量采集、数据贩卖等违法行为
- ❌ 不得侵犯他人知识产权

**使用本工具即表示您同意：**
- 对使用本工具产生的任何后果自行承担责任
- 开发者不对因使用本工具而产生的任何直接或间接损失负责
- 如因使用本工具违反相关法律法规，后果由使用者自负

## 快速开始

```bash
# 1. 安装依赖
pip3 install -r requirements.txt

# 2. 启动服务
python3 app.py

# 3. 访问 http://127.0.0.1:5001
```

## 核心功能

- 🔍 **智能搜索**：全文搜索 + 高级筛选 + 搜索历史
- 📥 **文章抓取**：自动下载文章和图片，保存为本地HTML
- 📊 **数据管理**：收藏、已读标记、批量操作
- 📤 **数据导出**：导出为Excel，包含完整正文内容
- 🎨 **用户体验**：深色模式、快捷键、搜索导航面板

## 项目结构

```
├── app.py                  # Flask主程序
├── requirements.txt        # Python依赖
├── wechat_scraper/        # 核心模块
│   ├── auth.py            # 微信登录认证
│   ├── crawler.py         # 文章爬取
│   ├── downloader.py      # 文章下载
│   ├── database.py        # 数据库操作
│   ├── logger.py          # 日志系统
│   ├── exceptions.py      # 自定义异常
│   ├── css_template.py    # 文章样式模板
│   └── utils.py           # 工具函数
├── templates/             # 前端模板
│   └── index.html         # Web界面
├── data/                  # 数据库文件
├── output/                # 下载的文章
└── logs/                  # 日志文件
```

---

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 详细文档

### 一、安装与配置

#### 1.1 环境要求

- Python 3.7+
- macOS / Linux / Windows

#### 1.2 安装步骤

```bash
# 克隆项目
cd /path/to/project

# 创建虚拟环境（推荐）
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# 安装依赖
pip3 install -r requirements.txt
```

#### 1.3 依赖说明

```
requests==2.31.0      # HTTP请求
beautifulsoup4==4.12.2 # HTML解析
lxml==4.9.3           # XML解析
flask==3.0.0          # Web框架
pandas==2.1.3         # 数据处理
openpyxl==3.1.2       # Excel操作
```

---

### 二、核心功能详解

#### 2.1 文章抓取

**功能**：
- 支持单个公众号抓取
- 支持批量公众号抓取
- 自动下载文章HTML和图片
- 保存为本地可离线浏览的网页

**使用方法**：
1. 点击"强制重新登录"扫码登录微信
2. 输入公众号名称
3. 选择抓取页数（每页10篇文章）
4. 点击"开始抓取"

**注意事项**：
- 首次使用需要扫码登录
- Cookie会自动保存，下次无需重新登录
- 遇到频率限制会自动等待

#### 2.2 智能搜索系统

##### 2.2.1 基础搜索
- 支持标题和正文内容搜索
- 自动保存最近10次搜索历史
- 点击搜索框查看历史记录
- 快捷键：`Ctrl/Cmd + F`

##### 2.2.2 高级搜索
点击"⚙️ 高级选项"打开高级搜索面板：

- **公众号筛选**：只搜索特定公众号的文章
- **日期范围**：设置开始和结束日期
- **状态筛选**：
  - 全部文章
  - 仅收藏
  - 仅已读
  - 仅未读
- **排序方式**：
  - 日期降序（最新在前）
  - 日期升序（最早在前）

##### 2.2.3 搜索导航面板
打开已下载的文章时，右上角会显示搜索导航面板：

- 显示所有匹配关键字的位置
- 点击列表项快速跳转
- 当前位置高亮显示（橙色背景）
- 可拖拽移动和调整尺寸
- 位置和尺寸自动保存

#### 2.3 数据管理

##### 2.3.1 收藏功能
- 点击文章卡片上的 ☆ 图标收藏
- 已收藏显示为 ⭐
- 在高级搜索中筛选"仅收藏"

##### 2.3.2 已读标记
- 点击文章卡片上的 ○ 图标标记已读
- 已读显示为 ✓
- 在高级搜索中筛选"仅已读"或"仅未读"

##### 2.3.3 批量操作
1. 点击"☑️ 批量操作"进入批量模式
2. 勾选要操作的文章
3. 使用工具栏按钮：
   - **标记已读**：批量标记为已读
   - **标记未读**：批量标记为未读
   - **删除**：批量删除文章（需确认）
4. 点击"取消选择"退出批量模式

##### 2.3.4 标签系统
- 数据库已支持标签功能
- API端点：`POST /api/articles/<id>/tags`
- 可扩展前端标签管理界面

#### 2.4 数据导出

点击"📥 导出 Excel"按钮导出所有文章数据：

**导出内容**：
- ID
- 公众号名称
- 文章标题
- 发布日期
- 下载状态
- **正文内容**（完整文字）
- 原文链接
- 本地路径

**文件格式**：
- Excel格式（.xlsx）
- 文件名：`wechat_articles_YYYYMMDD_HHMMSS.xlsx`

---

### 三、用户体验功能

#### 3.1 深色模式

**切换方式**：
- 点击右上角"🌙 深色"按钮
- 浅色模式：🌙 深色
- 深色模式：☀️ 浅色

**特性**：
- 完整的深色配色方案
- 自动保存主题偏好
- 刷新页面后保持选择

#### 3.2 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl/Cmd + F` | 聚焦搜索框 |
| `Esc` | 关闭搜索结果/历史面板 |
| `Enter` | 执行搜索（搜索框内） |

#### 3.3 搜索历史

- 自动保存最近10次搜索
- 点击搜索框查看历史
- 点击历史记录快速搜索
- 点击"清除"按钮删除历史

---

### 四、技术架构

#### 4.1 后端架构

**Flask Web框架**：
- 路由管理
- API端点
- 静态文件服务

**核心模块**：
- `auth.py`：微信登录认证，Cookie管理
- `crawler.py`：文章列表爬取，搜狗API调用
- `downloader.py`：文章内容下载，图片下载
- `database.py`：SQLite数据库操作
- `logger.py`：日志系统，文件轮转
- `exceptions.py`：自定义异常类

**数据库设计**：
- `accounts`：公众号信息
- `articles`：文章信息（含收藏、已读、标签）
- `tasks`：抓取任务记录
- `rate_limits`：频率限制记录

**性能优化**：
- 8个数据库索引
- 支持分页查询（limit/offset）
- 多线程下载（最多3个并发）

#### 4.2 前端架构

**技术栈**：
- 原生 HTML/CSS/JavaScript
- 无框架依赖
- 响应式设计

**核心功能**：
- 搜索历史管理（localStorage）
- 深色模式切换（localStorage）
- 批量选择管理（Set）
- 高级搜索面板（动态加载）
- 快捷键监听

**UI组件**：
- 搜索框 + 历史记录
- 高级搜索面板（可折叠）
- 批量操作工具栏（按需显示）
- 文章卡片（收藏/已读图标）
- 搜索导航面板（可拖拽/调整尺寸）

---

### 五、API文档

#### 5.1 认证相关

**检查登录状态**
```
GET /api/status
Response: {
  "logged_in": true/false,
  "rate_limit": {
    "limited": true/false,
    "reset_time": "2025-11-19T20:00:00",
    "remaining_seconds": 3600
  }
}
```

**强制重新登录**
```
POST /api/relogin
Response: {"success": true}
```

#### 5.2 搜索相关

**基础搜索**
```
GET /api/search?q=关键字
Response: [
  {
    "id": 1,
    "title": "文章标题",
    "link": "https://...",
    "publish_date": "2025-11-19",
    "downloaded": true,
    "local_path": "output/...",
    "account_name": "公众号名称",
    "is_favorite": false,
    "is_read": false,
    "tags": []
  }
]
```

**高级搜索**
```
POST /api/search/advanced
Body: {
  "query": "关键字",
  "account_id": 1,
  "date_from": "2025-01-01",
  "date_to": "2025-12-31",
  "sort_by": "date",
  "order": "desc",
  "is_favorite": true,
  "is_read": false,
  "limit": 50,
  "offset": 0
}
```

#### 5.3 数据管理

**切换收藏**
```
POST /api/articles/<id>/favorite
Response: {"success": true}
```

**切换已读**
```
POST /api/articles/<id>/read
Response: {"success": true}
```

**更新标签**
```
POST /api/articles/<id>/tags
Body: {"tags": ["标签1", "标签2"]}
Response: {"success": true}
```

**批量删除**
```
POST /api/articles/batch/delete
Body: {"ids": [1, 2, 3]}
Response: {"success": true, "deleted": 3}
```

**批量标记已读**
```
POST /api/articles/batch/read
Body: {"ids": [1, 2, 3], "is_read": true}
Response: {"success": true, "updated": 3}
```

#### 5.4 其他

**获取公众号列表**
```
GET /api/accounts
Response: {
  "accounts": [
    {"id": 1, "name": "公众号名称"}
  ]
}
```

**导出Excel**
```
GET /api/export
Response: Excel文件下载
```

---

### 六、常见问题

#### Q1: 如何解决登录失败？
**A**: 
1. 点击"强制重新登录"
2. 使用微信扫描二维码
3. 确保网络连接正常

#### Q2: 遇到频率限制怎么办？
**A**: 
- 系统会自动检测并等待
- 等待时间通常为1小时
- 页面会显示剩余等待时间

#### Q3: 如何备份数据？
**A**: 
1. 备份 `data/wechat_scraper.db`（数据库）
2. 备份 `output/`（下载的文章）
3. 备份 `wechat_cookies.json`（登录凭证）

#### Q4: 数据库错误如何解决？
**A**: 
```bash
# 删除旧数据库
rm -f data/wechat_scraper.db

# 重启服务，会自动创建新数据库
python3 app.py
```

#### Q5: 如何清理磁盘空间？
**A**: 
1. 使用批量删除功能删除不需要的文章
2. 手动删除 `output/` 下的文件夹
3. 清理 `logs/` 下的旧日志文件

---

### 七、开发指南

#### 7.1 添加新功能

**后端API**：
1. 在 `app.py` 添加路由
2. 在 `database.py` 添加数据库方法
3. 测试API端点

**前端功能**：
1. 在 `index.html` 添加UI元素
2. 添加JavaScript函数
3. 调用后端API

#### 7.2 数据库迁移

添加新字段：
```python
# 在 database.py 的 init_database 方法中
cursor.execute('''
    ALTER TABLE articles 
    ADD COLUMN new_field TEXT
''')
```

添加索引：
```python
cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_new_field 
    ON articles(new_field)
''')
```

#### 7.3 日志调试

查看日志：
```bash
# 查看主日志
tail -f logs/scraper_YYYYMMDD.log

# 查看错误日志
tail -f logs/error_YYYYMMDD.log
```

---

### 八、文件说明

#### 8.1 核心文件

| 文件 | 作用 | 说明 |
|------|------|------|
| `app.py` | Flask主程序 | Web服务、API路由 |
| `requirements.txt` | Python依赖 | 项目所需的包 |
| `wechat_cookies.json` | 登录凭证 | 自动生成，勿删除 |

#### 8.2 核心模块

| 文件 | 作用 | 说明 |
|------|------|------|
| `auth.py` | 认证模块 | 微信登录、Cookie管理 |
| `crawler.py` | 爬虫模块 | 文章列表爬取 |
| `downloader.py` | 下载模块 | 文章和图片下载 |
| `database.py` | 数据库模块 | SQLite操作 |
| `logger.py` | 日志模块 | 日志记录和轮转 |
| `exceptions.py` | 异常模块 | 自定义异常类 |
| `css_template.py` | 样式模块 | 文章CSS模板 |
| `utils.py` | 工具模块 | 通用工具函数 |

#### 8.3 数据目录

| 目录 | 作用 | 说明 |
|------|------|------|
| `data/` | 数据库文件 | SQLite数据库 |
| `output/` | 下载的文章 | 按公众号分类 |
| `logs/` | 日志文件 | 按日期分类 |
| `templates/` | 前端模板 | HTML文件 |

---

### 九、更新日志

#### V2.0 (2025-11-19)
- ✅ 全面优化16项功能
- ✅ 智能搜索系统（历史、高级搜索、导航面板）
- ✅ 数据管理（收藏、已读、批量操作）
- ✅ 性能优化（数据库索引、分页）
- ✅ 用户体验（深色模式、快捷键）
- ✅ 数据导出（Excel含正文）

#### V1.0 (2025-11-18)
- 基础文章抓取功能
- 简单搜索
- 本地存储

---

### 十、许可证

本项目采用 MIT License 开源协议。

详见 [LICENSE](LICENSE) 文件。

**简要说明**：
- ✅ 可以自由使用、修改、分发
- ✅ 可以用于商业项目（但请遵守免责声明）
- ✅ 需要保留版权声明
- ❌ 作者不承担任何责任和担保

---

### 十一、贡献

欢迎提交 Issue 和 Pull Request！

**贡献指南**：
1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

**文档更新**：2025-11-19  
**版本**：V2.0

