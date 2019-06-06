import scrapy
from readability import Readability
import json
import os
from hashlib import md5

class IkonSpider(scrapy.Spider):
    name = 'ikon_spider'
    robotstxt_obey = True
    download_delay = 0.5
    user_agent = 'giva-crawler-for-nlp (giva9712@gmail.com)'
    autothrottle_enabled = True
    httpcache_enabled = True

    def start_requests(self):
        start_urls = [
            ('http://ikon.mn/l/1' , "politics"  ), # улс төр
            ('http://ikon.mn/l/2' , "economy"   ), # эдийн засаг
            ('http://ikon.mn/l/3' , "society"   ), # нийгэм
            ('http://ikon.mn/l/16', "health"    ), # эрүүл мэнд
            ('http://ikon.mn/l/4' , "world"     ), # дэлхийд
            ('http://ikon.mn/l/7' , "technology"), # технологи
        ]
        for index, url_tuple in enumerate(start_urls):
            url      = url_tuple[0]
            category = url_tuple[1]
            yield scrapy.Request(url, meta={'category': category})

    def parse(self, response):
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
            file_path = pjoin('./corpuses_ikon', news_category)
            os.makedirs(file_path, exist_ok=True)
            with open(pjoin(file_path, md5(news['title'].encode('utf-8')).hexdigest()+".json"), 'w') as outfile:
                json.dump(output, outfile, ensure_ascii=False)

        for next_page in response.xpath("//*[contains(@class, 'nlitem')]//a"):
            yield response.follow(next_page, self.parse, meta={'category': response.meta.get('category', 'default')})

        for next_page in response.xpath("//*[contains(@class, 'ikon-right-dir')]/parent::a"):
            yield response.follow(next_page, self.parse, meta={'category': response.meta.get('category', 'default')})








            
