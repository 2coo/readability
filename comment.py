from bs4 import BeautifulSoup, NavigableString, Comment
import re
import time
import math
import copy

class Comment:
	elements = []
	def __init__(self, html, THRESHOLD=75, WHITE_LIST_TAGS=['p']):
		self.html = html
		self.soup = BeautifulSoup(html, 'lxml')
		self.backup = None
		self.THRESHOLD = THRESHOLD
		self.FREQUENCY = []
		self.WHITE_LIST_TAGS=WHITE_LIST_TAGS
		self.positiveRe = ['article','body','content','entry','hentry','main','page','pagination','post','text','blog','story']
	def get_element(self, node):
		index = len(list([1 for sibling in node.previous_siblings if node.name == sibling.name])) + 1
		return '%s:nth-of-type(%s)' % (node.name, index)
	def get_css_path(self, node):
		path = [self.get_element(node)]
		for parent in node.parents:
			if parent.name == 'body':
				break
			parentPath = self.get_element(parent)
			path.insert(0, parentPath)
		path.insert(0, "body")
		return ' > '.join(path)
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
		if element.has_attr('class') or element.has_attr('style'):
			return True
		for child in element.findAll():
			if child.has_attr('class') or child.has_attr('style'):
				return True
		return False
	def getClassAndName(self, element):
		elements=[]
		# print(element)
		# print("### STARTED ###")
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
					# print(err)
					continue
			# if imageLink != 0:
			# 	linkLength = (textLength/imageLink) * 0.8
		return linkLength / textLength
	def getAccuracy(self, element1, element2):
		maxDepth = max(self.getDepth(element1), self.getDepth(element2))
		ACCURACY = 100
		for depth in range(1,maxDepth+1):
			CORRECTED = 0
			element1Children = self.getClassAndName([self.getElementByDepth(element1, depth)])
			element2Children = self.getClassAndName([self.getElementByDepth(element2, depth)])
			DivideLength = max(len(element1Children), len(element2Children))
			### DEPTH EFFECT on accuracy
			effect = 100
			if maxDepth / 2 <= depth:
				effect = 50 / (DivideLength*depth)
			### CLASS AND NAME
			ALREADY_REGISTERED = []
			for element1Child in element1Children:
				for element2Child in element2Children:
					if element1Child['name'] == element2Child['name']:
						# print(element1Child["class"], element2Child["class"])
						maxLength = max(len(element1Child["class"]), len(element2Child["class"]), 1)
						intersection = len(set(element1Child["class"]) & set(element2Child["class"]))
						if intersection == 0 and depth == 1 and len(element1Child["class"]) > 0 and len(element2Child["class"]) > 0:
							return 0
						if intersection == 0 and len(element1Child["class"]) > 0 and len(element2Child["class"]) > 0:
							continue
						elif len(element1Child["class"]) == 0 and len(element2Child["class"]) == 0 and element1Child["name"] not in ALREADY_REGISTERED:
							ALREADY_REGISTERED.append(element1Child["name"])
							CORRECTED += 1
						elif (intersection/maxLength) * 100 > 50:
							CORRECTED += 1
					else:
						CORRECTED-=1
			if CORRECTED == 0:
				ACCURACY = ACCURACY - effect
			else:
				ACCURACY = ACCURACY - (((DivideLength - CORRECTED) * effect) / DivideLength)
		return ACCURACY
	def isEqual(self,el1, el2):
		element1 = str(el1)
		element2 = str(el2)
		if element1 == element2:
			return True
		else:
			if el1.name == el2.name:
				if self.getAccuracy(el1, el2) > self.THRESHOLD:
					return True
			return False
	def hasPositveClass(self, element):
		if element.has_attr('class'):
			for eClass in element['class']:
				for posClass in self.positiveRe:
					if eClass.find(posClass) > 0:
						return True
		for parent in element.parents:
			if parent.name == "body":
				break
			if parent.has_attr('class'):
				for eClass in parent['class']:
					for posClass in self.positiveRe:
						if eClass.find(posClass) > 0:
							# print(posClass)
							# print(eClass)
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
					if child.name not in self.WHITE_LIST_TAGS and child2.name not in self.WHITE_LIST_TAGS:
						if self.containsAnyClassOrStyle(child) and self.containsAnyClassOrStyle(child2):
							if len(list(child.children)) > 0 and len(list(child2.children)) > 0 and self.isEqual(child, child2):
								if self.getLinkDensity(self.backup.select(self.get_css_path(child))[0]) < 0.6 and self.getLinkDensity(self.backup.select(self.get_css_path(child2))[0]) < 0.6:
									child["repeated"]="true"
									child2["repeated"]="true"
		return self.FREQUENCY
	def annotationFrequency(self):
		### REMOVING JUNK TAGS
		JUNK_TAGS = ['script', 'style','head', 'iframe','embed','frameset','frame','map','noscript','noframes','source', 'video']
		for element in self.soup.body.findAll():
			if element.name in JUNK_TAGS:
				element.extract()
		### REMOVE COMMENT ELEMENT
		textNodes = self.soup.findAll(text=lambda text:isinstance(text, Comment))
		for textNode in textNodes:
			textNode.extract()
		### SAVE BACKUP SOUP
		self.backup = copy.copy(self.soup)
		### REMOVE ALL ATTRIBUTE EXCEPT CLASS, STYLE
		whiteList = ['class', 'style']
		for element in self.soup.body.findAll():
			tempAttributes={}
			for index,value in element.attrs.items():
				if index in whiteList:
					tempAttributes[index] = value
			element.attrs = tempAttributes
		# print(self.backup)
		## REMOVE TEXTS
		textNodes = self.soup.findAll(text=lambda text:isinstance(text, NavigableString))
		for textNode in textNodes:
			textNode.extract()
		### ANNOTATION REPEATED BLOCKS
		self.permutation(self.soup.body)
		for element in self.soup.body.findAll():
			if len(list(element.children)) > 1 and not isinstance(element, NavigableString):
				self.permutation(element)
		for repeatedElement in self.soup.findAll(repeated="true"):
			self.FREQUENCY.append(self.get_css_path(repeatedElement))
		
	def removeFrequency(self):
		### START TIMER
		STARTEDTIME = time.time()
		print("REMOVING BLOCKS LIKE COMMENT...")
		### ANNOTATION FREQUENCY
		self.annotationFrequency()
		for repeated in self.FREQUENCY:
			self.backup.select(repeated)[0]["remove"]="true"
		for repeated in self.backup.findAll(remove="true"):
			repeated.extract()
		print(time.time()-STARTEDTIME)
		return self.backup.prettify()