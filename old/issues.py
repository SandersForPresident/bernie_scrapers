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


class IssueConnector(object):

    def __init__(self):
        self.url = "https://berniesanders.com/issues/feed/"
        self.html = HTMLParser()
        self.db = MongoClient("localhost", 27017).bernie

    def get(self):
        for x in range(3):
            r = requests.get(self.url)
            if r.status_code == 200:
                items = BeautifulSoup(r.text).findAll("item")
                recs = []
                for item in items:
                    rec = {
                        "inserted_at": datetime.now(),
                        "title": self.html.unescape(item.title.text),
                        "created_at": parser.parse(item.pubdate.text),
                        "source": "berniesanders.com",
                        "article_type": "Issues",
                        "description_html": item.description.text,
                        "description": self.html.unescape(
                            BeautifulSoup(item.description.text).p.text),
                        "url": item.link.nextSibling
                    }
                    recs.append(rec)
                return recs
            print(r.status_code)
            time.sleep(5)
        return False

    def retrieve(self, rec):
        for x in range(3):
            r = requests.get(rec["url"])
            if r.status_code == 200:
                soup = BeautifulSoup(r.text).find("section", {"id": "content"})
                while soup.article.style is not None:
                    soup.article.style.extract()
                rec["body_html"] = str(soup.article)
                text = []
                for elem in soup.article.recursiveChildGenerator():
                    if isinstance(elem, types.StringTypes):
                        text.append(self.html.unescape(elem.strip()))
                    elif elem.name == 'br':
                        text.append("")
                rec["body"] = "\n".join(text)
                return rec
        return False

    def go(self):
        urls = self.get()
        if not urls:
            print("ERROR: Could not retrieve issues.")
            sys.exit(1)
        for url in urls:
            rec = self.retrieve(url)
            query = {
                "title": rec["title"],
                "article_type": rec["article_type"]
            }
            if not self.db.articles.find(query).limit(1).count():
                msg = "Inserting '{0}', created {1}"
                logging.info(msg.format(rec["title"], str(rec["created_at"])))
                self.db.articles.insert_one(rec)

if __name__ == "__main__":
    i = IssueConnector()
    i.go()
