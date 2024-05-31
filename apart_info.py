from flask import request
from flask_restful import Resource
from config import Config

import pymysql
import pymysql.cursors
from sshtunnel import SSHTunnelForwarder   

class ApartInfoResource(Resource) :

	def get(self) :
		# data = request.get_json()
		
		with SSHTunnelForwarder(Config.HOST, ssh_username=Config.USERNAME, ssh_password=Config.PASSWORD, remote_bind_address=('127.0.0.1', 3306)) as tunnel:
			try :
				conn = pymysql.connect(host="127.0.0.1", user=Config.USERNAME, password=Config.PASSWORD, database='test_ds', port=tunnel.local_bind_port, charset="utf8")
					
				cursor = conn.cursor(pymysql.cursors.DictCursor)

				query = '''
						SELECT * 
						FROM apart
						ORDER BY date desc
						LIMIT 5; 
						'''

				cursor.execute(query)

				result_list = cursor.fetchall()

			except Exception as e :
				print(f"error : {str(e)}")
				return {"result" : "Fail"}, 500
			
			finally :
				if cursor : cursor.close()
				if conn : conn.close()	

		return {"result" : "success", "result_list" : result_list}, 200
    