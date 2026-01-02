import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://www.google.com")
        print(f"Crawl Success: {result.success}")
        if result.success:
            # Updated from markdown_v2 to markdown
            print("Content Snippet:", result.markdown.raw_markdown[:100])

if __name__ == "__main__":
    asyncio.run(main())