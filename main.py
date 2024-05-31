import requests
from config import Config
from file_reader_parser import read_file, parse_lines_to_dict
import xml.etree.ElementTree as ET

import pymysql
import pymysql.cursors
from sshtunnel import SSHTunnelForwarder   

# 아파트 매매 정보(주소)로 위도 경도 구하는 함수(카카오 로컬 API) 
def get_lat_lng(address, LatLngServiceKey):
    response = requests.get(f"https://dapi.kakao.com/v2/local/search/address.json?query={address}", headers={"Authorization": LatLngServiceKey})
    
    if response.status_code == 200:
        result = response.json()
        if result['documents']:
            latitude, longitude = result['documents'][0]['address']['y'], result['documents'][0]['address']['x']
            return latitude, longitude 
    return None, None

# API KEY (공공데이터 포털 - 아파트 매매 정보 API)
PublicDataServiceKey = Config.PublicDataServiceKey
# API KEY (카카오 - 주소로 위도 경도 구하는 API)
LatLngServiceKey = Config.LatLngServiceKey

# 지역코드(도로명시군구코드)
LAWD_CD = Config.LAWD_CD
# 계약월
DEAL_YMD = Config.DEAL_YMD
# 한 페이지 결과 수
# numOfRows = Config.numOfRows
numOfRows = 50
# 페이지 번호
# pageNo = Config.pageNo
pageNo = 5

# 파일 읽기
lines = read_file("./region_code.txt")

# 줄을 파싱하여 딕셔너리(key : 지역코드, value : 시군구)로 가공
result_dict = parse_lines_to_dict(lines)

xml_data = requests.get(f"http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcAptTradeDev?ServiceKey={PublicDataServiceKey}&LAWD_CD={LAWD_CD}&DEAL_YMD={DEAL_YMD}&numOfRows={numOfRows}&pageNo={pageNo}")

root = ET.fromstring(xml_data.text)

item_list = root.findall('.//item')

with SSHTunnelForwarder(Config.HOST, ssh_username=Config.USERNAME, ssh_password=Config.PASSWORD, remote_bind_address=('127.0.0.1', 3306)) as tunnel:
	try :
		conn = pymysql.connect(host="127.0.0.1", user=Config.USERNAME, password=Config.PASSWORD, database='test_ds', port=tunnel.local_bind_port, charset="utf8")
			
		cursor = conn.cursor(pymysql.cursors.DictCursor)

		for item in item_list :
			price = item.find("거래금액").text # 가격
			transactionType = item.find("거래유형").text # ex) 중개거래
			constructionYear = item.find("건축년도").text # 지어진 연도
			year = item.find("년").text # 판매된 연도
			# roadName = item.find("도로명").text # 도로명 ex) 아카데미로
			buildingMainCode = item.find("도로명건물본번호코드").text # ex) 446 
			buildingSubCode = item.find("도로명건물부번호코드").text # 나머지(부속건물이 있는 경우)
			dong = item.find("동").text # 아파트 동 번호가 있는 경우
			legalDong = item.find("법정동").text # ex) 송도동
			apartment = item.find("아파트").text # 아파트명
			month = item.find("월").text # 판매 날짜(월)
			day = item.find("일").text # 판매 날짜(일)
			area = item.find("전용면적").text # 면적
			lotNumber = item.find("지번").text # ex) 397-8
			regionCode = item.find("지역코드").text # 위 LAWD_CD와 같음
			floor = item.find("층").text # 몇 층인지

			# 가공 작업
			price = price.replace(",", "").replace("'", "").strip() + "0000"
			legalDong = legalDong.strip()
			regionCode = result_dict.get(regionCode, "알 수 없는 지역코드")
			address = f"{regionCode} {legalDong} {lotNumber}"

			# 아파트 주소로 위도/경도 찾기
			lat, lng = get_lat_lng(address, LatLngServiceKey)
			
			if lat is None and lng is None : 
				print(f"{address} 주소로 위도 경도를 찾을 수 없습니다.")
				continue

			# if buildingSubCode == "00000" : roadName = f"{roadName} {buildingMainCode}"
			# else : roadName = f"{roadName} {buildingMainCode}-{buildingSubCode}"	
			
			if dong != " " : 
				print(f"{year}년 {month}월 {day}일 {address} [위도/경도 : {lat}, {lng}] 면적 {area}의 {dong}동 {apartment}아파트({floor}층)가 {price}원에 {transactionType}로 판매되었습니다. 건축년도 : {constructionYear}")
			else :
				print(f"{year}년 {month}월 {day}일 {address} [위도/경도 : {lat}, {lng}] 면적 {area}의 {apartment}아파트({floor}층)가 {price}원에 {transactionType}로 판매되었습니다. 건축년도 : {constructionYear}")

			query = '''
					INSERT IGNORE INTO apart 
					(date, address, latitude, longitude, area, apartment, floor, price, transactionType, constructionYear) 
					VALUES 
					(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
					'''
			record = (f"{year}-{month}-{day}", address, lat, lng, area, apartment, floor, price, transactionType, constructionYear)

			cursor.execute(query, record)

			conn.commit()

	except Exception as e :
		print(f"error : {str(e)}")
	
	finally :
		if cursor : cursor.close()
		if conn : conn.close()	

