#!/usr/bin/env python2

from __future__ import print_function

from dateutil import parser
from pymongo import MongoClient
from datetime import datetime

import logging
import requests
import time
import sys

logging.basicConfig(format="%(asctime)s - %(levelname)s : %(message)s",
                    level=logging.INFO)

allowed_keys = [
    "original_id",
    "id_obfuscated",
    "url",
    "name",
    "start_time",
    "timezone",
    "description",
    "venue",
    "lat",
    "lon",
    "is_official",
    "attendee_count",
    "capacity",
    "source"
]


class OfficialConnector(object):

    def __init__(self):
        self.params = {
            'orderby': 'zip_radius',
            'zip_radius[1]': '6000',
            'zip_radius[0]': '78218',
            'radius_unit': 'mi',
            'country': 'US',
            'format': 'json'
        }
        self.url = "https://go.berniesanders.com/page/event/search_results"
        self.map = {
            "id": "original_id",
            "start_dt": "start_time"
        }
        self.db = MongoClient("localhost", 27017).bernie

    def get(self, params=None):
        for x in range(3):
            r = requests.get(self.url, params=self.params)
            if r.status_code == 200:
                return r.json()["results"]
            time.sleep(5)
        print("Could not retrieve events from berniesanders.com")
        sys.exit(1)

    def translate(self, result):
        # Translate normal key names based on map
        result = dict((self.map.get(k, k), v) for (k, v) in result.items())

        # Compile Venue
        address_map = {
            "venue_addr1": "address1",
            "venue_addr2": "address2",
            "venue_addr3": "address3"
        }
        result["venue"] = {
            "name": result["venue_name"],
            "city": result["venue_city"],
            "state": result["venue_state_cd"],
            "zip": result["venue_zip"],
            "location": {
                "lon": float(result["longitude"]),
                "lat": float(result["latitude"])
            }
        }
        result["source"] = "berniesanders.com"
        for k, v in address_map.iteritems():
            try:
                result["venue"][v] = result[k]
            except KeyError:
                pass

        # parse datetime
        result["start_time"] = parser.parse(result["start_time"])
        keys = result.keys()
        for k in keys:
            if k not in allowed_keys:
                result.pop(k)
        return result

    def go(self):
        for result in self.get():
            rec = self.translate(result)
            query = {
                "original_id": rec["original_id"],
                "source": "berniesanders.com"
            }
            if self.db.events.find(query).count() > 0:
                msg = "Updating record for '{0}'."
                logging.info(msg.format(rec["name"]))
                self.db.events.update_one(query, {"$set": rec})
            else:
                msg = "Inserting record for {0}."
                logging.info(msg.format(rec["name"]))
                rec["inserted_at"] = datetime.now()
                self.db.events.insert_one(rec)

if __name__ == "__main__":
    bernie = OfficialConnector()
    bernie.go()
