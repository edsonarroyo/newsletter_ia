import os
import pandas as pd
import csv
import requests


def get_data(start_date, end_date):
	api_url = "https://api.eluniversal.arcpublishing.com/content/v4/search/published?website=dedinero&q=type:story+AND+publish_date:[" + start_date + "+TO+" + end_date + "]&_sourceInclude=publish_date,promo_items.basic.url,promo_items.basic.subtitle,headlines.basic,taxonomy.sections.name,canonical_url,canonical_website&sort=publish_date:desc&size=100"
	#print(api_url)	
	access_token =  os.getenv('arc_token')	
	return api_url, access_token

	#imageID -> promo_items/basic/0/_id [promo_items.basic.url] -> 3Q457ZTAKNETFJKEG5Z26USWCI

def get_content(url):
	api_url = 'https://api.eluniversal.arcpublishing.com/content/v4/stories/?website=dedinero&website_url=' + url + '&_sourceInclude=publish_date,promo_items.basic.url,headlines.basic,taxonomy.sections.name,canonical_url,content_elements'
	print(api_url)
	access_token =  os.getenv('arc_token')	
	return api_url, access_token