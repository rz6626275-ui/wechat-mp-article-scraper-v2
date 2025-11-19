WECHAT_CSS = """
<style>
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji";
        line-height: 1.6;
        color: #333;
        background-color: #f2f2f2;
        margin: 0;
        padding: 0;
    }
    .page-container {
        max-width: 677px;
        margin: 0 auto;
        background-color: #fff;
        padding: 20px 40px;
        min-height: 100vh;
    }
    @media screen and (max-width: 768px) {
        .page-container {
            padding: 15px;
            width: 100%;
            box-sizing: border-box;
        }
    }
    h1.article-title {
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 14px;
        line-height: 1.4;
        color: #333;
    }
    .article-meta {
        margin-bottom: 22px;
        line-height: 20px;
        font-size: 15px;
        color: rgba(0,0,0,0.3);
    }
    .article-meta span {
        margin-right: 8px;
    }
    .article-meta .account-name {
        color: #576b95;
        font-weight: 400;
    }
    #js_content {
        visibility: visible !important;
        overflow: hidden;
        color: #333;
        font-size: 17px;
        text-align: justify;
        word-wrap: break-word;
        -webkit-hyphens: auto;
        -ms-hyphens: auto;
        hyphens: auto;
    }
    #js_content p {
        margin: 0 0 16px;
        min-height: 1em;
    }
    #js_content img {
        max-width: 100% !important;
        height: auto !important;
        display: block;
        margin: 10px auto;
        border-radius: 4px;
    }
    blockquote {
        padding-left: 10px;
        border-left: 3px solid #dbdbdb;
        color: rgba(0,0,0,0.5);
        font-size: 15px;
        margin: 1em 0;
    }
    a {
        color: #576b95;
        text-decoration: none;
    }
    a:hover {
        text-decoration: underline;
    }
    hr {
        border: 0;
        border-top: 1px solid #eee;
        margin: 20px 0;
    }
</style>
"""
