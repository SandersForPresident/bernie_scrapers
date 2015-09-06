## Bernie Scrapers

This repository contains the scrapers used by ES4BS to import events and articles (and any other additional data) into the Mongo DB source of truth.

#### Deploy

Scrapers are triggered by scraper_scheduler using docker to isolate the code. All scrapers should utilize the Scraper base class, and will be executed 2 at a time every 20 minutes. Dead scrapers are left for 24 hours for logging purposes.