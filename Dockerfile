FROM python:2.7

RUN pip install BeautifulSoup	\
	docker-py 					\
	pymongo 					\
	python-dateutil 			\
	requests					\
	schedule 					\
	pyyaml

COPY ./scraper_scheduler.py /bin/scraper_scheduler.py

CMD ["/bin/scraper_scheduler.py"]
