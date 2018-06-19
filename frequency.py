from bs4 import BeautifulSoup, NavigableString, Comment
import re
import time
import math
import copy

WHITE_LIST_TAGS = ['p']
THRESHOLD=75
	
def getDepth(soup, depth=1, maxDepth = 0):
	maxDepth = max(depth, maxDepth)
	for node in soup.children:
		maxDepth = getDepth(node, depth + 1, maxDepth)
	return maxDepth
def getElementByDepth(element, depth):
	elements=[]
	if depth == 1:
		elements.append(element)
		return elements
	maxDepth = getDepth(element)
	for child in element.findAll():
		if (maxDepth - getDepth(child)) == depth-1:
			elements.append(child)
	return elements
def containsAnyClassOrStyle(element):
	# print(element)
	if element.has_attr('class') or element.has_attr('style'):
		return True
	for child in element.findAll():
		if not isinstance(child, NavigableString):
			if child.has_attr('class') or child.has_attr('style'):
				return True
	return False
def getClassAndName(element):
	elements=[]
	for el in element[0]:
		classes = []
		if el.has_attr('class'):
			classes = el['class']
		elements.append({'name': el.name, 'class': classes})
	return elements
def getInnerText(elem):
	textContent = str(elem.text).strip()
	textContent = re.sub(' +',' ', textContent)
	return textContent

def getLinkDensity(elem):
	textLength = len(getInnerText(elem))
	if textLength == 0:
		return 0

	linkLength=0

	if elem.name == "a":
		if elem['href'][0] == "#":
			return 0
		# if len(list(elem.findAll('img'))) > 0:
			# linkLength = textLength * 0.8
		linkLength += len(getInnerText(elem))
	else:
		imageLink = 0
		for atag in elem.findAll("a"):
			try:
				if atag['href'][0] == "#":
					continue
				# if len(list(atag.findAll('img'))) > 0:
				# 	imageLink+=1
				linkLength += len(getInnerText(atag))
			except Exception as err:
				print(err)
				continue
		# if imageLink != 0:
		# 	linkLength = (textLength/imageLink) * 0.8
	return linkLength / textLength
def getAccuracy(element1, element2):
	maxDepth = max(getDepth(element1), getDepth(element2))
	ACCURACY = 100
	for depth in range(1,maxDepth+1):
		if maxDepth/2 < depth and depth > 1:
			return ACCURACY
		### DEPTH EFFECT on accuracy
		effect = 100
		
		CORRECTED = 0
		element1Children = getClassAndName([getElementByDepth(element1, depth)])
		element2Children = getClassAndName([getElementByDepth(element2, depth)])
		DivideLength = max(len(element1Children), len(element2Children))
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
		print(CORRECTED)
		if CORRECTED == 0:
			ACCURACY = ACCURACY - effect
		else:
			ACCURACY = ACCURACY - (((DivideLength - CORRECTED) * effect) / DivideLength)
	# print("ACCURACY:",ACCURACY)
	return ACCURACY
def clearElement(element):
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

def isEqual(el1, el2):
	element1 = clearElement(el1)
	element2 = clearElement(el2)
	if str(element1) == str(element2):
		return True
	else:
		if element1.name == element2.name:
			print("#######")
			print(element1)
			print("..........")
			print(element2)
			accuracy = getAccuracy(element1, element2)
			print(accuracy)
			if accuracy > THRESHOLD:
				return True
		return False

def permutation(element):
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
					if child.name not in WHITE_LIST_TAGS and child2.name not in WHITE_LIST_TAGS:
						if containsAnyClassOrStyle(child) and containsAnyClassOrStyle(child2):
							if len(list(child.children)) > 0 and len(list(child2.children)) > 0 and isEqual(child, child2):
								child.extract()
								child2.extract()
def removeFrequency(soup):
	### START TIMER
	# STARTEDTIME = time.time()
	# soup = BeautifulSoup(html, 'html.parser')
	# print("REMOVING REPEATED BLOCKS...")
	### REMOVING JUNK TAGS
	JUNK_TAGS = ['script', 'style','head', 'iframe','embed','frameset','frame','map','noscript','noframes','source', 'video']
	for element in soup.body.findAll():
		if element.name in JUNK_TAGS:
			element.extract()
	### REMOVE COMMENT ELEMENT
	commentNodes = soup.findAll(text=lambda text:isinstance(text, Comment))
	for commentNode in commentNodes:
		commentNode.extract()
	permutation(soup.body)
	for element in soup.body.findAll():
		if not isinstance(element, NavigableString) and len(list(element.children)) > 1:
			permutation(element)

	# print(time.time()-STARTEDTIME)

	return soup