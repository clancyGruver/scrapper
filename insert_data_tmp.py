import os.path
import pickle
from datetime import date,timedelta
#from mysql import Mysql
from myquerybuilder import QueryBuilder

class Beletag:
	db = None
	category = None
	date = None
	good_id = None

	def __init__(self, data):
		#current date initialization
		# d = date.today()
		# self.date = str(d.year)+'-'+str(d.month)+'-'+str(d.day)
		# pd = d - timedelta(days=1)
		# self.prev_date = str(pd.year)+'-'+str(pd.month)+'-'+str(pd.day)
		self.date = '2018-4-23'
		self.prev_date = '2018-4-22'

		#Mysql connection initialization
		self.db = QueryBuilder(
			host="localhost",
			user="root",
			passwd="",
			db="scrapping",
			charset="utf8"
		)

		#data scrapping
		category = data['category']
		self.categories(category)

		good = {
			'category_id' : self.category,
			'articul'     : data['articul'],
			'season'      : data['season'],
			'price'       : data['price'] if 'price' in data else 0,
			'complecte'   : data['complecte'],
			'description' : data['description'],
			'site_id'     : data['item']['id'],
			'description' : data['item']['name'],
			'date_add'    : self.date
		}
		self.item(good)

		good_colors = []
		for color in data['colors']:
			for col in color:
				for size in color[col]['size']:
					c = {
						'good_id'    : self.good_id,
						'color_name' : color[col]['name'],
						'size'       : size['name'],
						'count'      : size['count'],
						'date'       : self.date
					}
					good_colors.append(c)
		self.good_params(good_colors)

	def categories(self, cat):
		fields = ('id', 'site_id', 'name')
		table = 'beletag_categories'
		where = {'site_id':cat['id'], 'name':cat['name']}
		categories = self.db.select(fields, table, where)

		if(len(categories) > 0):
			self.category = categories[0]['id']
		else:
			values = {
				'site_id'  : cat['id'],
				'name'     : cat['name'],
				'date_add' : self.date
			}
			self.category = self.db.insert(table, values)

	def item(self, data):
		fields = ('id','articul') #'category_id', 'articul'
		table = 'beletag_goods'
		where = {'category_id':self.category, 'articul':data['articul']}
		goods = self.db.select(fields, table, where)
		if len(goods) > 0:
			self.good_id = goods[0]['id']
		else:
			self.good_id = self.db.insert(table, data)

	def good_params(self, data):
		table = 'beletag_good_params'
		for row in data:
			print(row)
			fields = ('id','count') #'category_id', 'articul'
			where = {
				'good_id':self.good_id, 
				'date':self.prev_date,
				'color_name':row['color_name'],
				'size':row['size']
			}
			item = self.db.one(fields, table, where)
			if type(item) == type(None):
				row['change_prev_day'] = 0
			else:
				row['change_prev_day'] = int(row['count']) - int(item['count'])
			self.db.insert(table, row)


d = date.today()
result_name = 'beletaj-2018-4-23_morning.pkl'
result = []

if os.path.exists(result_name):
	with open(result_name, 'rb') as afile:
		result = pickle.load(afile)
for d in result:
	if type(d) == type(None):
		continue
	Beletag(d)