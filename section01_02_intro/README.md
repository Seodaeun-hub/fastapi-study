# Section 01~02 요약: FastAPI 개발환경 & 기본 앱 구조

# 섹션1 : 강의 소개 및 실습 환경 구축
- python 가상 환경 구성 및 FastAPI 설치

# 섹션1 퀴즈 정리
- FastAPI의 주요 성능 특징은 비동기 기반의 고성능이다.
- FastAPI 애플리케이션을 실행할 때 주로 사용하는 서버 유형은 ASGI 서버이다.
- FastAPI 개발 시 가상 환경 설정을 권장하는 주된 이유는 무엇일까요? 프로젝트별 종속성을 분리 관리하기 위함.
- 이 강의에서 파이썬 가상 환경 관리를 위해 추천하는 도구는 무엇인가요? Conda
- Uvicorn 서버 실행 시 코드 변경사항 저장 시 자동 재시작 기능을 활성화하는 옵션은 무엇인가요? --reload

# 섹션2 퀴즈 정리
- 많은 동시 요청 처리 시 FastAPI 성능 장점은 무엇일까요? 비동기 처리 지원
- FastAPI가 자동으로 생성하는 API 문서화 및 테스트 도구는 무엇일까요? Swagger UI
- FastAPI는 들어온 HTTP 요청을 어떤 기준으로 해당 함수와 연결하나요? HTTP 메소드와 경로
- main.py 파일의 app 인스턴스를 Uvicorn으로 실행하는 기본 명령어는 무엇일까요? uvicorn main:app
-  FastAPI 경로 작업 함수에서 Python 딕셔너리를 반환할 때 기본 응답 형식은 무엇일까요? JSON
# 서버 실행
uvicorn main:app --reload

# Swagger UI
API들을 브라우저 기반에서 편기하게 관리 및 문서화, 테스트 할 수 있는 기능 제공
->Swagger: http://127.0.0.1:8000/docs
