# 비밀번호 해싱 함수 생성
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# 데이터프레임 생성 - 사용자 리스트 정의
import pandas as pd

data = {
    'username': ['admin', 'user1', 'guest'],
    'password': ['admin', 'pass1', 'guest'],
    'role': ['admin', 'user', 'guest']
}

df = pd.DataFrame(data)

# 비밀번호 해싱
df['password'] = df['password'].apply(hash_password)

# 데이터프레임 출력
# print(df)

# SQLite 연결 및 데이터 저장
import sqlite3

# SQLite 데이터베이스에 연결 (파일이 존재하지 않으면 새로 생성됩니다)
conn = sqlite3.connect('user_data.db')

# 데이터프레임을 SQLite 데이터베이스에 저장
df.to_sql('users', conn, if_exists='replace', index=False)

# 연결 종료
conn.close()
