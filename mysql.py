import MySQLdb

class Mysql:
	host="localhost"    # host
	user="root"         # username
	pwd=""           	 # password
	db="scrapping"
	connection = None
	
	def __init__(self, host=None, user=None, pwd=None, db=None):
		if type(host) == type(None):
			host = self.host
		if type(user) == type(None):
			user = self.user
		if type(pwd) == type(None):
			pwd = self.pwd
		if type(db) == type(None):
			db = self.db
		self.connection = MySQLdb.connect(
			host=host,    # your host, usually localhost
			user=user,    # your username
			passwd=pwd,   # your password
			db=db,
			charset="utf8")	

	def __del__(self):
		self.connection.close()

	def select_all(self, table):
		cur = self.connection.cursor()
		cur.execute("SELECT id, site_id, name FROM " + table)
		result = cur.fetchall()
		return result

	def insert():
		pass
		# cur = connection.cursor()
		# cur.execute()
		# result = cur.fetchall()
		# connection.close()
