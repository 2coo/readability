from bs4 import BeautifulSoup, NavigableString
import re
import copy

class Readability:
	div_to_p_elems=[ "a", "blockquote", "dl", "div", "img", "ol", "p", "pre", "table", "ul", "select" ]

	REGEXES = {
	    'unlikelyCandidatesRe': re.compile('combx|comment|community|disqus|extra|foot|header|menu|remark|rss|shoutbox|sidebar|sponsor|ad-break|agegate|pagination|pager|popup|tweet|twitter', re.I),
	    'okMaybeItsACandidateRe': re.compile('and|article|body|column|main|shadow', re.I),
	    'positiveRe': re.compile('article|body|content|entry|hentry|main|page|pagination|post|text|blog|story', re.I),
	    'negativeRe': re.compile('combx|comment|com-|contact|foot|footer|footnote|masthead|media|meta|outbrain|promo|related|scroll|shoutbox|sidebar|sponsor|shopping|tags|tool|widget', re.I),
	    'divToPElementsRe': re.compile('<(a|blockquote|dl|div|img|ol|p|pre|table|ul)', re.I),
	    #'replaceBrsRe': re.compile('(<br[^>]*>[ \n\r\t]*){2,}',re.I),
	    #'replaceFontsRe': re.compile('<(\/?)font[^>]*>',re.I),
	    #'trimRe': re.compile('^\s+|\s+$/'),
	    #'normalizeRe': re.compile('\s{2,}/'),
	    #'killBreaksRe': re.compile('(<br\s*\/?>(\s|&nbsp;?)*){1,}/'),
	    'videoRe': re.compile('https?:\/\/(www\.)?(youtube|vimeo)\.com', re.I),
	    'attributeRe': re.compile('blog|post|article', re.I),
	    #skipFootnoteLink:      /^\s*(\[?[a-z0-9]{1,2}\]?|^|edit|citation needed)\s*$/i,
	}

	def __init__(self, html, preserveUnlikelyCandidates = False):
		self.html = html
		self.preserveUnlikelyCandidates = preserveUnlikelyCandidates
		self.soup = None

	def minify(self, html):
		minified = re.sub('\n+','\n',re.sub('<!--.*?-->','',re.sub('<script.*?</script>','',re.sub('<script.*?[^>]*</script>','',re.sub('<!--[^>]*-->','',re.sub(' <','<',re.sub('> ','>',re.sub('> <','><',re.sub(' +',' ',re.sub('\t','',html)))))))).strip()))
		return minified
		
	def RepresentsInt(self, s):
	    try: 
	        int(s)
	        return True
	    except ValueError:
	        return False

	def getClassWeight(self, node):
		weight = 0

		if node.has_attr('class'):
			classNames = ' '.join(node['class'])
			if self.REGEXES['negativeRe'].search(classNames):
				weight -= 25
			if self.REGEXES['positiveRe'].search(classNames):
				weight += 25
		if node.has_attr('id') and not self.RepresentsInt(node['id']):
			if self.REGEXES['negativeRe'].search(node['id']):
				weight -= 25
			if self.REGEXES['positiveRe'].search(node['id']):
				weight += 25
		return weight

	def initializeNode(self, node):
		node['readability-score']=0

		score_weight = {
				'article': 10,
				'section': 8,
				'div': 5,
				'pre': 3,
				'td': 3,
				'blockquote': 3,
				'address': -3,
				'ol': -3,
				'ul': -3,
				'dl': -3,
				'dd': -3,
				'dt': -3,
				'li': -3,
				'form': -3,
				'h1': -5,
				'h2': -5,
				'h3': -5,
				'h4': -5,
				'h5': -5,
				'h6': -5,
				'th': -5,
		}
		node['readability-score'] += score_weight.get(node.name, 0)

		if node.has_attr('itemscope'):
			node['readability-score'] += 5
			if node.has_attr('itemtype') and self.REGEXES['attributeRe'].search(node['itemtype']):
				node['readability-score'] += 30
		node['readability-score'] += self.getClassWeight(node)

	def getInnerText(self, elem):
		textContent = str(elem.text).strip()
		textContent = textContent.replace('\s{2,}/g',' ')
		return textContent.strip()

	def getLinkDensity(self, elem):
		textLength = len(self.getInnerText(elem))
		if textLength == 0:
			return 0
		linkLength=0
		for atag in elem.findAll("a"):
			try:
				if atag['href'][0] == "#":
					continue
				linkLength += len(self.getInnerText(atag))
			except KeyError:
				continue
		return linkLength / textLength

	# def get_own_textContent(element):
	# 	textContent=''
	# 	if not isinstance(element, NavigableString):
	# 		if hasattr(element, 'children'):
	# 			for child in element.children:
	# 				if isinstance(child, NavigableString):
	# 					textContent+=str(child);
	# 	if textContent == '':
	# 		return None
	# 	else:
	# 		return re.sub('\n+','\n', textContent.strip())

	def grabArticle(self):
		html = self.minify(self.html)
		self.soup = BeautifulSoup(html, 'html.parser')
		for node in self.soup.findAll():
			continueFlag = False
			if not self.preserveUnlikelyCandidates:
				classNames = ''
				if node.has_attr('class'):
					classNames = ' '.join(node['class'])
				idName = ''
				if node.has_attr('id'):
					idName=node['id']
				unlikelyMatchString = classNames + idName
				if self.REGEXES['unlikelyCandidatesRe'].search(unlikelyMatchString) and not self.REGEXES['okMaybeItsACandidateRe'].search(unlikelyMatchString) and node.name != 'html' and node.name != 'body':
					node.extract()
					continueFlag = True

			if not continueFlag and node.name == "div":
				if not self.REGEXES['divToPElementsRe'].search(str(node)):
					node.name = "p"
				else:
					for child in node.children:
						if isinstance(child, NavigableString) and str(child).strip() != "":
							new_p = self.soup.new_tag('p')
							new_p.append(str(child))
							child.insert_before(new_p)
							child.extract()

		candidates = []
		for paragraph in self.soup.findAll('p'):
			parentNode = paragraph.parent
			grandParentNode = parentNode.parent
			InnerText = self.getInnerText(paragraph)

			# print("##########")
			# print(parentNode)

			if len(InnerText) < 25:
				continue
			if not parentNode.has_attr('readability-score'):
				self.initializeNode(parentNode)
				candidates.append(parentNode)
			if not grandParentNode.has_attr('readability-score'):
				self.initializeNode(grandParentNode)
				candidates.append(grandParentNode)

			contentScore = 0

			# Add a point for the paragraph itself as a base.
			contentScore += 1

			# For every 100 characters in this paragraph, add another point. Up to 3 points.
			contentScore += min(len(InnerText) / 100, 3)
			# Add the score to the parent. The grandparent gets half.
			parentNode['readability-score'] += contentScore;
			grandParentNode['readability-score'] += contentScore / 2;

		topCandidate = None
		# get top candidate
		for candidate in candidates:
			candidate['readability-score'] = candidate['readability-score'] * (1 - self.getLinkDensity(candidate))
			if not topCandidate or candidate['readability-score'] > topCandidate['readability-score']:
				topCandidate = candidate


		'''
		Now that we have the top candidate, look through its siblings for content that might also be related.
		Things like preambles, content split by ads that we removed, etc.   
		'''

		if topCandidate:
			articleContent = self.soup.new_tag('div')
			articleContent['id'] = 'readability-content'
			
			siblingsScoreThreshold = max(10, topCandidate['readability-score'] * 0.2);

			siblingNodes = topCandidate.parent.children

			for siblingNode in siblingNodes:
				if not isinstance(siblingNode, NavigableString):
					append = False

					if siblingNode == topCandidate:
						append = True

					if siblingNode.has_attr('readability-score') and siblingNode['readability-score'] >= siblingsScoreThreshold:
						append = True

					if siblingNode.name == "p":
						linkDensity = self.getLinkDensity(siblingNode)
						nodeContent = self.getInnerText(siblingNode)
						nodeLength = len(nodeContent)

						if nodeLength > 80 and linkDensity == 0 and re.search('/\.( |$)/', nodeContent):
							append = True

					if append:
						articleContent.append(copy.copy(siblingNode))
			return articleContent
		else:
			return topCandidate
	def get_scored_html(self):
		self.grabArticle()
		return self.soup