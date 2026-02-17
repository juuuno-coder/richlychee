"""웹 크롤링 모듈."""

from richlychee.crawler.base import BaseCrawler
from richlychee.crawler.static import StaticCrawler
from richlychee.crawler.dynamic import DynamicCrawler

__all__ = ["BaseCrawler", "StaticCrawler", "DynamicCrawler"]
