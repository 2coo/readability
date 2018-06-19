from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import urllib.request as urllib
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Comment, NavigableString


def Request(orginalurl, timeout=40, javascript=True):
	# url = urllib.unquote(orginalurl)
	# url =urllib.quote(url, safe=':/=&?', encoding="utf-8")
	url = orginalurl
	print(url)

	# print(url)
	hostname = 'http://'+urllib.urlparse(url).hostname
	req = urllib.Request(url, headers={'User-Agent' : "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36"})

	page = urllib.urlopen(req)
	innerHTML = page.read()

	if page.status != 200:
		raise ConnectionError("(ERROR) Connection status code: "+str(page.status))
	else:
		if javascript == True:
			chrome_options = Options()
			chrome_options.add_argument("--headless")
			chrome_options.add_argument('--start-maximized')
			chrome_options.add_argument('--start-fullscreen')
			chrome_options.add_argument('--log-level=3')
			chrome_options.add_argument('--ignore-certificate-errors')

			browser = webdriver.Chrome(chrome_options=chrome_options, executable_path=r'./chromedriver/chromedriver')  
			browser.maximize_window()
			browser.set_page_load_timeout(timeout)
			browser.get(url)
			# blocks = browser.find_elements_by_css_selector("*")
			# for block in blocks:
			# 	location = block.location
			# 	size = block.size
			# 	browser.execute_script("arguments[0].setAttribute('location-x',arguments[1])", block, location["x"])
			# 	browser.execute_script("arguments[0].setAttribute('location-y',arguments[1])", block, location["y"])
			# 	browser.execute_script("arguments[0].setAttribute('location-width',arguments[1])", block, size["width"])
			# 	browser.execute_script("arguments[0].setAttribute('location-height',arguments[1])", block, size["height"])
			innerHTML = browser.execute_script("return document.documentElement.outerHTML;")
			browser.close()
			browser.quit()
			innerHTML = BeautifulSoup(innerHTML, 'html.parser').prettify()

	soup = BeautifulSoup(innerHTML, 'lxml')

	metas = soup.findAll("meta")
	if len(metas) != 0 and metas != None:
		for meta in metas:
			try:
				if meta["http-equiv"] == "refresh":
					meta.extract()
			except KeyError:
				pass

	## css файлууд замыг нь янзалж татаж page.css файл руу бичнэ
	ext_styles = soup.findAll('link', rel="stylesheet")
	ext_cssData = ''
	if len(ext_styles) != 0:
		for css in ext_styles:
			tempUrl = urllib.urlparse(css['href'])
			#Direct Css
			css_url=css['href']
			if css['href'][0] == '/' and css['href'][1] != "/":
				css_url = hostname + css['href']
			elif tempUrl.scheme == "":
				css_url = 'http://' + css['href']

			css['href']=css_url

	else:
		print("No external stylesheets found")

	
	## img тагуудын замыг янзлах
	img_tags = soup.findAll('img')
	if len(img_tags) != 0:
		for img in img_tags:
			try:
				tempUrl = urllib.urlparse(img['src'])
				if img['src'][0] == '/':
					img['src'] = hostname + img['src']
			except Exception as err:
				# print(err)
				pass
	## Pretty
	meta = soup.new_tag("meta")
	meta["charset"]="UTF-8"
	soup.head.insert(0,meta)
	innerHTML = str(soup.prettify())

	return innerHTML


		
