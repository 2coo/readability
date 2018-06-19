from bs4 import BeautifulSoup, NavigableString, Comment
import re
import time
import math
import copy

class Cleaner:
	elements = []
	def __init__(self, html, THRESHOLD=75, WHITE_LIST_TAGS=['p']):
		self.html = html
		self.soup = BeautifulSoup(html, 'lxml')
		self.backup = None
		self.THRESHOLD = THRESHOLD
		self.FREQUENCY = []
		self.WHITE_LIST_TAGS=WHITE_LIST_TAGS
		self.positiveRe = ['article','body','content','entry','hentry','main','page','pagination','post','text','blog','story']
	def getDepth(self, soup, depth=1, maxDepth = 0):
		maxDepth = max(depth, maxDepth)
		for node in soup.children:
			maxDepth = self.getDepth(node, depth + 1, maxDepth)
		return maxDepth
	def getElementByDepth(self, element, depth):
		elements=[]
		if depth == 1:
			elements.append(element)
			return elements
		maxDepth = self.getDepth(element)
		for child in element.findAll():
			if (maxDepth - self.getDepth(child)) == depth-1:
				elements.append(child)
		return elements
	def containsAnyClassOrStyle(self, element):
		# print(element)
		if element.has_attr('class') or element.has_attr('style'):
			return True
		for child in element.findAll():
			if not isinstance(child, NavigableString):
				if child.has_attr('class') or child.has_attr('style'):
					return True
		return False
	def getClassAndName(self, element):
		elements=[]
		for el in element[0]:
			classes = []
			if el.has_attr('class'):
				classes = el['class']
			elements.append({'name': el.name, 'class': classes})
		return elements
	def getInnerText(self, elem):
		textContent = str(elem.text).strip()
		textContent = re.sub(' +',' ', textContent)
		return textContent

	def getLinkDensity(self, elem):
		textLength = len(self.getInnerText(elem))
		if textLength == 0:
			return 0

		linkLength=0

		if elem.name == "a":
			if elem['href'][0] == "#":
				return 0
			# if len(list(elem.findAll('img'))) > 0:
				# linkLength = textLength * 0.8
			linkLength += len(self.getInnerText(elem))
		else:
			imageLink = 0
			for atag in elem.findAll("a"):
				try:
					if atag['href'][0] == "#":
						continue
					# if len(list(atag.findAll('img'))) > 0:
					# 	imageLink+=1
					linkLength += len(self.getInnerText(atag))
				except Exception as err:
					print(err)
					continue
			# if imageLink != 0:
			# 	linkLength = (textLength/imageLink) * 0.8
		return linkLength / textLength
	def getAccuracy(self, element1, element2):
		maxDepth = max(self.getDepth(element1), self.getDepth(element2))
		ACCURACY = 100
		for depth in range(1,maxDepth+1):
			### DEPTH EFFECT on accuracy
			effect = 100
			
			CORRECTED = 0
			element1Children = self.getClassAndName([self.getElementByDepth(element1, depth)])
			element2Children = self.getClassAndName([self.getElementByDepth(element2, depth)])
			DivideLength = max(len(element1Children), len(element2Children))
			if maxDepth/2 < depth:
				effect = 100 / (depth*DivideLength)
			### CLASS AND NAME
			ALREADY_REGISTERED = []
			for element1Child in element1Children:
				for element2Child in element2Children:
					if element1Child['name'] == element2Child['name']:
						# print(element1Child["class"], element2Child["class"])
						maxLength = max(len(element1Child["class"]), len(element2Child["class"]), 1)
						intersection = len(set(element1Child["class"]) & set(element2Child["class"]))
						# print(intersection)
						if intersection == 0 and depth == 1 and len(element1Child["class"]) > 0 and len(element2Child["class"]) > 0:
							return 0
						if intersection == 0 and len(element1Child["class"]) > 0 and len(element2Child["class"]) > 0:
							continue
						elif len(element1Child["class"]) == 0 and len(element2Child["class"]) == 0 and element1Child["name"] not in ALREADY_REGISTERED:
							ALREADY_REGISTERED.append(element1Child["name"])
							CORRECTED += 1
						elif (intersection/maxLength) * 100 >= 50:
							CORRECTED += 1
					else:
						CORRECTED-=1
			# print(CORRECTED)
			if CORRECTED == 0:
				ACCURACY = ACCURACY - effect
			else:
				ACCURACY = ACCURACY - (((DivideLength - CORRECTED) * effect) / DivideLength)
		# print("ACCURACY:",ACCURACY)
		return ACCURACY
	def clearElement(self, element):
		tempElement = copy.copy(element)
		textNodes = tempElement.findAll(text=lambda text:isinstance(text, NavigableString))
		for textNode in textNodes:
			textNode.extract()
		### REMOVE ALL ATTRIBUTE EXCEPT CLASS, STYLE
		whiteList = ['class', 'style']
		tempAttributes={}
		for index,value in tempElement.attrs.items():
			if index in whiteList:
				tempAttributes[index] = value
		tempElement.attrs = tempAttributes
		
		for element in tempElement.findAll():
			tempAttributes={}
			for index,value in element.attrs.items():
				if index in whiteList:
					tempAttributes[index] = value
			element.attrs = tempAttributes

		return tempElement

	def isEqual(self,el1, el2):
		element1 = self.clearElement(el1)
		element2 = self.clearElement(el2)
		if str(element1) == str(element2):
			return True
		else:
			if element1.name == element2.name:
				# print("#######")
				# print(element1)
				# print("..........")
				# print(element2)
				accuracy = self.getAccuracy(element1, element2)
				# print(accuracy)
				if accuracy > self.THRESHOLD:
					return True
			return False

	def permutation(self, element):
		childrenLength = len(list(element.children));
		sameElements = []
		# sameElements.append(0)
		for index, child in enumerate(element.children):
			if index == childrenLength:
				break
			if index in sameElements:
				continue
			for index2, child2 in enumerate(element.children):
				if index < index2 and not index2 in sameElements:
					if not isinstance(child, NavigableString) and not isinstance(child2, NavigableString):
						if child.name not in self.WHITE_LIST_TAGS and child2.name not in self.WHITE_LIST_TAGS:
							if self.containsAnyClassOrStyle(child) and self.containsAnyClassOrStyle(child2):
								if len(list(child.children)) > 0 and len(list(child2.children)) > 0 and self.isEqual(child, child2):
									# print("#########")
									# print(child)
									# print(self.getLinkDensity(child))
									# # print(self.getInnerText(child))
									# print(".......")
									# print(child2)
									# print(self.getLinkDensity(child2))
									# print(self.getInnerText(child2))
									### Its will remove like comment (less link density repeated block)
									# if self.getLinkDensity(child) < 0.6 and self.getLinkDensity(child2) < 0.6:
										
									child.extract()
									child2.extract()
									### Its only remove like relative news, repeated link news (more link density repeated block)
									# if self.getLinkDensity(child) > 0.6 and self.getLinkDensity(child2) > 0.6:
									# 	child.extract()
									# 	child2.extract()
	def removeFrequency(self):
		### START TIMER
		STARTEDTIME = time.time()
		print("REMOVING REPEATED BLOCKS...")
		### REMOVING JUNK TAGS
		JUNK_TAGS = ['script', 'style','head', 'iframe','embed','frameset','frame','map','noscript','noframes','source', 'video']
		for element in self.soup.body.findAll():
			if element.name in JUNK_TAGS:
				element.extract()
		### REMOVE COMMENT ELEMENT
		commentNodes = self.soup.findAll(text=lambda text:isinstance(text, Comment))
		for commentNode in commentNodes:
			commentNode.extract()
		self.permutation(self.soup.body)
		for element in self.soup.body.findAll():
			if not isinstance(element, NavigableString) and len(list(element.children)) > 1:
				self.permutation(element)

		print(time.time()-STARTEDTIME)

		return self.soup.prettify()
		