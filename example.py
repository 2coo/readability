from readability import Readability
import urllib.request as urllib

response = urllib.urlopen('http://news.gogo.mn/r/235300')

article =  Readability(str(response.read().decode('utf8'))).parse()
print(article["title"])
# print(article["textContent"])
# for key, value in article.items():
#     print(key)
    # print("#"+key+"#")
    # print("".join(["="]*50))
    # print(value)
    # print("".join(["="]*50))