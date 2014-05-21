from xml.dom import minidom
from urllib import urlopen
from bs4 import BeautifulSoup
from pprint import pprint
import pandas as pd
from datetime import datetime

class Company:
	def __init__(self, cik):
		self.cik = cik
		self.documents = []
		self.data = {}
		url_string = "http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK="+self.cik+"&type=10-%25&dateb=&owner=exclude&start=0&count=400&output=atom"
		xml_file = urlopen(url_string)
		self.xml = minidom.parse(xml_file)

	def get_company_info(self):
		pass

	def get_documents(self):
		"""
		Crawls edgar to get a list of all 10-Q/K XBRL files
		"""
		xml = self.xml

		mapping = {	'name':'conformed-name',
					'fiscal_year':'fiscal-year-end',
					'state_location':'state-location',
					'state_incorporation':'state-of-incorporation',
					'sic':'assigned-sic',
					'sic_desc':'assigned-sic-desc',
					'cik':'cik' }

		for k, v in mapping.iteritems():
			try:
				self.data[k] = xml.getElementsByTagName(v)[0].firstChild.nodeValue
			except:
				pass

		document_list = xml.getElementsByTagName('entry')
		for document in document_list: 
			try: 
				parent = document.getElementsByTagName('content')[0]
				xbrl_href = parent.getElementsByTagName('xbrl_href')[0].firstChild.nodeValue
				doc = Document(parent)
				self.documents.append(doc)
			except IndexError: #no xbrl data
				pass

	def __is_quarterly__(self, start, end):
		date_format = "%Y-%m-%d"
		start = datetime.strptime(start, date_format)
		end = datetime.strptime(end, date_format)
		delta = end - start
		if delta.days <= 30 * 6:
			return True
		else:
			return False

	def get_series_from_id(self, xbrl_id):
		'''
		returns a dataframe with all of the series available from the xbrl_id provided
		'''
		if len(self.documents) == 0:
			self.get_documents()
		if len(self.documents) == 0:
			raise Exception("No data available from Edgar")
		documents = self.documents

		processed = {}
		for document in documents:
			datas = document.get_item(xbrl_id)
			if len(datas) == 0:
				raise Exception("Error extracting data from documents")
			for data in datas:
				if not data['segment']:
					data['segment'] = 'root'
				series_name = data['segment']
				if data['segment'] not in processed:
					processed[series_name] = {}
				if 'start' in data:
					if self.__is_quarterly__(data['start'], data['end']):
						processed[series_name][data['end']] = data['value']
				else:
					processed[series_name][data['end']] = data['value']
		return pd.DataFrame(processed)


class Document:
	'''
	Represents data about a filing
	'''
	def __init__(self, filing):
		'''
		filing must be an XML node representing an Edgar filing
		'''
		self.data = {}
		self.data['filing_date'] = filing.getElementsByTagName('filing-date')[0].firstChild.nodeValue
		self.data['filing_type'] = filing.getElementsByTagName('filing-type')[0].firstChild.nodeValue
		self.data['filing_url'] = filing.getElementsByTagName('filing-href')[0].firstChild.nodeValue
		self.data['xbrl_url'] = self.__get_xbrl_url__()

	def __get_xbrl_url__(self):
		filing = urlopen(self.data['filing_url']).read()
		soup = BeautifulSoup(filing)
		xbrl_table = soup.findAll('table', attrs={'summary':"Data Files"})[0]
		return 'http://www.sec.gov'+xbrl_table.findAll('a')[0]['href']

	def __get_context_period__(self, soup, contextRef):
		contexts = soup.getElementsByTagNameNS('*','context')
		period = None
		for context in contexts:
			if context.attributes['id'].value == contextRef:
				try: #stock
					period = context.getElementsByTagNameNS('*','instant')[0].firstChild.nodeValue
					period = {'end': period}
				except: #flow
					start = context.getElementsByTagNameNS('*','startDate')[0].firstChild.nodeValue
					end = context.getElementsByTagNameNS('*','endDate')[0].firstChild.nodeValue
					period = {'start': start, 'end': end}
		return period

	def __get_segment__(self, soup, contextRef):
		contexts = soup.getElementsByTagNameNS('*','context')
		segment = None
		for context in contexts:
			if context.attributes['id'].value == contextRef:
				try:
					segment = context.getElementsByTagNameNS('*','explicitMember')[0].firstChild.nodeValue
				except:
					pass
		return segment

	def get_item(self, code):
		d = self.data['xbrl_url']
		xbrl_data = urlopen(d)
		soup = minidom.parse(xbrl_data)

		datapoints = []
		for point in soup.getElementsByTagNameNS('*',code):
			contextRef = point.attributes['contextRef'].value
			period = self.__get_context_period__(soup, contextRef)
			period['value'] = point.firstChild.nodeValue
			period['contextRef'] = contextRef
			period['segment'] = self.__get_segment__(soup, contextRef)
			datapoints.append(period)
		return datapoints

	def __str__(self):
		return str(self.data)

#data = Company('MSFT')
#print data.get_series_from_id('Assets')['root']
