from flask import request
from flask_restful import Resource
from config import Config
from mysql_connection import get_connection   

class ApartInfoResource(Resource) :

	def get(self) :
		# data = request.get_json()
		
		try :
			conn = get_connection()
				
			cursor = conn.cursor(dictionary=True)

			query = '''
					SELECT * 
					FROM apart
					ORDER BY id desc
					LIMIT 5; 
					'''

			cursor.execute(query)

			result_list = cursor.fetchall()

			for i, row in enumerate(result_list) :
				result_list[i]["createdAt"] = row["createdAt"].isoformat()

		except Exception as e :
			print(f"error : {str(e)}")
			return {"result" : "Fail"}, 500
		
		finally :
			if cursor : cursor.close()
			if conn : conn.close()	

		return {"result" : "success", "result_list" : result_list, "count" : len(result_list)}, 200
    