from __future__ import print_function

from datetime import datetime
from dateutil import parser
from pymongo import MongoClient
from BeautifulSoup import BeautifulSoup
from HTMLParser import HTMLParser

import logging
import requests
import types
import time
import sys

logging.basicConfig(format="%(asctime)s - %(levelname)s : %(message)s",
                    level=logging.INFO)


def replace_with_newlines(element):
    text = ''
    for elem in element.recursiveChildGenerator():
        if isinstance(elem, types.StringTypes):
            text += elem.strip()
        elif elem.name == 'br':
            text += '\n'
    return text


class OfficialArticleConnector(object):
    def __init__(self):
        self.url = "https://berniesanders.com/daily/page/5/"
        self.html = HTMLParser()
        self.db = MongoClient("localhost", 27017).bernie

    def get(self):
        for x in range(3):
            r = requests.get(self.url)
            if r.status_code == 200:
                return r.text
            else:
                time.sleep(5)
        return False

    def retrieve_article(self, url):
        for x in range(3):
            r = requests.get(url)
            if "https://berniesanders.com" not in r.url:
                return r.url, r.url
            if r.status_code == 200:
                soup = BeautifulSoup(r.text)
                content = soup.article
                paragraphs = [self.html.unescape(replace_with_newlines(p))
                              for p in content.findAll("p")]
                text = "\n\n".join(paragraphs)
                html = "".join([str(p) for p in content.findAll("p")])
                return text, html
        return False, False

    def go(self):
        html = self.get()
        if not html:
            print("ERROR: Could not retrieve articles")
            sys.exit(1)
        soup = BeautifulSoup(html)
        content = soup.find("section", {"id": "content"})
        for article in content.findAll("article"):
            rec = {
                "inserted_at": datetime.now(),
                "created_at": parser.parse(article.time["datetime"]),
                "source": "berniesanders.com",
                "type": "DemocracyDaily",
                "excerpt_html": str(article.find(
                    "div", {"class": "excerpt"}).p),
                "excerpt": self.html.unescape(
                    article.find(
                        "div", {"class": "excerpt"}).p.text),
                "title": article.h2.text,
                "article_category": article.h1.string.strip(),
                "url": article.h2.a["href"]
            }
            if article.img is not None:
                rec["image_url"] = article.img["src"]
            query = {"title": rec["title"], "type": "DemocracyDaily"}
            if not self.db.articles.find(query).limit(1).count():
                text, html = self.retrieve_article(rec["url"])
                rec["body"], rec["body_html"] = text, html
                msg = "Inserting '{0}', created {1}"
                logging.info(msg.format(rec["title"], str(rec["created_at"])))
                self.db.articles.insert_one(rec)

o = OfficialArticleConnector()
o.go()
