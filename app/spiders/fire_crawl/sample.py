from firecrawl import Firecrawl


firecrawl = Firecrawl(api_key="fc-867f64e9458c4be48745cced28be1c0a")


def scrap_sample(url):
    # Scrape a website:
    doc = firecrawl.scrape(url, formats=["markdown", "html"])
    print(doc)
    return doc


# 通过提示词获取内容；
def scrap_with_prompt(url, prompt):
    result = firecrawl.scrape(
        'https://firecrawl.dev',
        formats=[{
            "type": "json",
            "prompt": prompt
        }],
        only_main_content=False,
        timeout=120000
    )

    print(result)
    return result


if __name__ == '__main__':
    url = "https://www.baidu.com"
    # url = "https://piaofang.maoyan.com/dashboard-ajax?orderType=0&uuid=19781d653bbc8-0650a47c0ac5fa8-18525636-16a7f0-19781d653bbc8&timeStamp=1757055691280&User-Agent=TW96aWxsYS81LjAgKE1hY2ludG9zaDsgSW50ZWwgTWFjIE9TIFggMTBfMTVfNykgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzEzOS4wLjAuMCBTYWZhcmkvNTM3LjM2&index=466&channelId=40009&sVersion=2&signKey=3e399a4c7d11c3b271cfaffc73406bde&WuKongReady=h5"
    # scrap_sample(url)
    scrap_with_prompt(url, "Extract the company mission from the page.")
