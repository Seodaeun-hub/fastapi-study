import redis

#localhost, post=6379, db=0으로 접속 (default port is 6379) and use database 0
#username, password 없이 설정해보는 예
#여기서 db는 미리 만드는게 아니라 접속할 때 unique 하게 생성된다고 생각.
r_client = redis.Redis(host='localhost', port=6379, db=0)

# db=0 key와 value 설정한 뒤 해당 key값으로 값 추출. 
r_client.set('name', 'FastAPI')
name_value = r_client.get('name')
print(f"Value for 'name' in db 0: {name_value.decode('utf-8')}")
#decode를 안하면 b'FastAPI'라고 출력됨. 그래서 decoding해서 출력하기(FastAPI로 출력됨.)

# db1에 접속
r_client_db1 = redis.Redis(host='localhost', port=6379, db=1)

# db=1 key와 value 설정한 뒤 해당 key값으로 값 추출. 
r_client_db1.set('name', 'Redis')
name_value_db1 = r_client_db1.get('name')
print(f"Value for 'name' in db 1: {name_value_db1.decode('utf-8')}")

# Connection Pool 기반 access
# redis는 connectionpool을 사용할 수 있음.
# close 안해도 됨. 자동으로 종료된다.
redis_pool = redis.ConnectionPool(host='localhost', port=6379, db=0, max_connections=10)
redis_client_pool = redis.Redis(connection_pool=redis_pool)

redis_client_pool.set('name', 'FastAPI')
name_value = redis_client_pool.get('name')
print(f"Value for 'name' in db 0: {name_value.decode('utf-8')}")