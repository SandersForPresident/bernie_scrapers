#!/usr/bin/env python2

import requests


class ZipCode (object):

    def __init__(self, zipcode):
        self.zipcode = zipcode
        self.es_hit = self.get(self.zipcode)
        self.data = self.es_hit["hits"]["hits"][0]["_source"]
        self.lat = self.data["location"]["lat"]
        self.lon = self.data["location"]["lon"]
        self.city = self.data["primary_city"]
        self.state = self.data["state"]

    def get_latlon(self):
        u = 'http://search.berniesanders.tech/geolocation/postal/_search?q={}'
        r = requests.get(u.format(self.zipcode))
        return r.json()["hits"]['hits']["_source"]["location"]

    def get_events(self, location, start_dt, end_dt):
        payload = {
            "query": {
                "filtered": {
                    "query": {
                        "match_all": {}
                    },
                    "filter": {
                        "geo_distance": {
                            "distance": "100mi",
                            "location": {
                                "lat": location['lat'],
                                "lon": location['lon']
                            }
                        }
                    }
                }
            },
            "post_filter": {
                "range": {
                    "start_day": {
                        "gte": "2015-08-21",
                        "lte": "2015-12-23"
                    }
                }
            }
        }
        r = requests.post(
            "http://search.berniesanders.tech/events/_search",
            data=payload
        )
        return r.json()
