import gevent.monkey
gevent.monkey.patch_all()
import requests
import os.path
import pickle
import re
from datetime import date, timedelta
from bs4 import BeautifulSoup
import grequests

class Proxy(object):
	proxy_url = "http://spys.one/en/http-proxy-list/"
	proxy_list = []
	d = date.today()
	f_name = 'proxies_'+str(d.year)+'_'+str(d.month)+'_'+str(d.day)+'.txt'
	pd = d - timedelta(days=1)
	f_prev_name = 'proxies_'+str(pd.year)+'_'+str(pd.month)+'_'+str(pd.day)+'.txt'

	def __init__(self):
		payload = {'xpp':5,'xf1':0,'xf2':0,'xf4':0,'xf5':0}
		r = requests.post(self.proxy_url, data=payload)
		html = r.content
		soup = BeautifulSoup(html, 'html.parser')
		result = soup.find_all('tr', class_="spy1x")
		scripts = soup.find_all("script")
		script = scripts[2].string.split(';')[:-1]
		script_dict = {}
		for s in script:
			sss = s.split('=')
			script_dict[sss[0]] = sss[1]

		result = result[1:]
		result2 = soup.find_all('tr', class_="spy1xx")
		result = result + result2
		for row in result:
			txt = row.find('td').find('font',class_="spy14").text 
			ip = re.compile('(([2][5][0-5]\.)|([2][0-4][0-9]\.)|([0-1]?[0-9]?[0-9]\.)){3}(([2][5][0-5])|([2][0-4][0-9])|([0-1]?[0-9]?[0-9]))')
			match = ip.search(txt)
			ip = match.group()
			port = txt[match.span()[1]+44:-1].split('+')
			port_digits = ''
			for p in port:
				p = p[1:-1].split('^')
				port_digits += script_dict[p[0]].split('^')[0]
			self.proxy_list.append({'ip':ip, 'port':port_digits})

	def get_proxy(self):
		if self.check_proxies_file():
			return self.get_proxies_from_file()
		result = []
		total_proxy = len(self.proxy_list)
		print('Всего ' + str(total_proxy) + ' проксей')
		reqs = []
		proxy_list_count = len(self.proxy_list)
		counter_start = 0
		counter_end = 20
		while counter_start < proxy_list_count:
			current_dict = self.proxy_list[counter_start:counter_end]
			print("from {} to {}".format(counter_start, counter_end))
			print(current_dict)
			print()
			for proxy in current_dict:
				reqs.append(grequests.get('http://ipv4bot.whatismyipaddress.com/', proxies={'http':'http://' + proxy['ip']+':'+proxy['port']}, timeout=10))
			responses = grequests.map(reqs)
			for resp in responses:
				if (resp is not None) and (len(resp.text) < 16) and (resp.status_code == 200):
					for x in current_dict:
						if x['ip'] == resp.text:						
							result.append("{}:{}".format(x['ip'], x['port']))
			counter_start += 20
			counter_end += 20

		if os.path.exists(self.f_prev_name):
			with open(self.f_prev_name,'rb') as f:
				result.extend(pickle.load(f))
		result = set(result)
		result = list(result)
		self.save(result)
		return result

	def save(self, data):
		with open(self.f_name,'wb') as f:
			pickle.dump(data, f)	

	def check_proxies_file(self):
		if os.path.exists(self.f_name):
			return True
		else:
			return False

	def get_proxies_from_file(self):
		with open(self.f_name,'rb') as f:
			d = pickle.load(f)
		return d


# proxy = Proxy()
# proxy = proxy.get_proxy()
# print(proxy)
# r = requests.get('http://speed-tester.info/check_ip.php',proxies={'http':proxy})
# print(r.content)
