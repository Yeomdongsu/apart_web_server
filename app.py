from flask import Flask
from flask_restful import Api
from config import Config
from apart_info import ApartInfoResource

app = Flask(__name__)
# CORS(app)

# 환경변수 세팅
app.config.from_object(Config)

# JWT 매니저를 초기화
# jwt = JWTManager(app)

api = Api(app)

api.add_resource(ApartInfoResource, "/apart")

if __name__ == "__main__" : 
    app.run()