import scrapy
from readability import Readability
import json
import os
from hashlib import md5
from datetime import datetime

class GogoSpider(scrapy.Spider):
    name = 'ikon_spider'
    robotstxt_obey = True
    download_delay = 0.5
    user_agent = 'giva-crawler-for-nlp (giva9712@gmail.com)'
    autothrottle_enabled = True
    httpcache_enabled = True
    

    def start_requests(self):
        start_urls = [
            # ('http://news.gogo.mn/i/2/more' , "politics"  ), # улс төр
            # ('http://news.gogo.mn/i/3/more' , "economy"   ), # эдийн засаг
            # ('http://news.gogo.mn/i/7/more' , "society"   ), # нийгэм
            # ('http://news.gogo.mn/i/4/more', "health"    ), # эрүүл мэнд
            # ('http://news.gogo.mn/i/72/more' , "world"     ), # дэлхийд
            ('http://news.gogo.mn/i/6876/more' , "technology"), # технологи
            # ('http://news.gogo.mn/i/6/more', "sport") # спорт
        ]
        now = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        for index, url_tuple in enumerate(start_urls):
            url      = url_tuple[0]
            category = url_tuple[1]
            yield scrapy.FormRequest(url, meta={'category': category, "lastdate": now}, callback=self.parse_initial_links, formdata={
                "lastdate": now
            })

    def parse_initial_links(self, response):
        url = response.url
        min_data = datetime.strptime(str(response.meta.get('lastdate', str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))), '%Y-%m-%d %H:%M:%S')
        category = response.meta.get('category', 'default')

        for link in response.xpath("//*[contains(@class, 'news-thumb')]//a[1]"):
            yield response.follow(link, self.parse_article, meta={'category': response.meta.get('category', 'default')})

        for date in response.xpath("//*[contains(@class, 'news-thumb')]//*[contains(@class, 'busad')]//*[@class='date']/@data"):
            fdate = datetime.strptime(date.extract(), '%Y-%m-%d %H:%M:%S')
            if min_data > fdate:
                min_data = fdate
        
        yield scrapy.FormRequest(url, meta={'category': category, "lastdate": min_data}, callback=self.parse_initial_links, formdata={
                "lastdate": str(min_data)
            })

    def parse_article(self, response):
        news =  Readability(str(response.body.decode('utf8'))).parse()
        if not news['title']:
            print("Could not find the title!", response.url)
        else:
            # get category that i given [politics, economy, society, health, world, technology]
            news_category = response.meta.get('category', 'default')

            output = {
                **news,
                "ikon_category": news_category
            }
            pjoin = os.path.join
            file_path = pjoin('./corpuses_gogo', news_category)
            os.makedirs(file_path, exist_ok=True)
            with open(pjoin(file_path, md5(news['title'].encode('utf-8')).hexdigest()+".json"), 'w') as outfile:
                json.dump(output, outfile, ensure_ascii=False)








            
