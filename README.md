# DeepROS Platform

ROS 도메인 관리 시스템을 위한 FastAPI 기반 Python Backend와 MQTT Broker입니다.

## 기능

### Backend API
- **ROS 도메인 관리**: ROS 도메인의 생성, 조회, 수정, 삭제
- **노드 관리**: ROS 노드(topic, service, action)의 CRUD 작업
- **노드 연결 관리**: 노드 간 연결 정보 관리
- **메시지 로깅**: 노드 간 통신 메시지 기록 및 조회
- **RESTful API**: 완전한 REST API 제공
- **자동 문서화**: Swagger UI 및 ReDoc 지원

### MQTT Broker
- **MQTT 3.1.1 Protocol**: 완전한 MQTT 프로토콜 지원
- **WebSocket Support**: MQTT over WebSocket 지원
- **ROS Integration**: ROS 도메인 관리 전용 통합 기능
- **Authentication**: 사용자명/비밀번호 인증
- **TLS/SSL Support**: 보안 연결 지원
- **Retained Messages**: MQTT retained 메시지 지원
- **Wildcard Subscriptions**: + 및 # 와일드카드 구독 지원
- **QoS Levels**: QoS 0, 1, 2 레벨 지원
- **Session Management**: 지속적 세션 및 clean session 지원
- **Statistics & Monitoring**: 내장 통계 및 모니터링

### ROS Data Storage System
- **Message Recording**: ROS 메시지 기록 및 메타데이터 저장
- **Message Playback**: 기록된 메시지 재생 및 필터링
- **Session Management**: 명명된 세션으로 기록 관리
- **Advanced Indexing**: 시간 기반 및 내용 기반 인덱싱
- **Compression**: 다중 압축 알고리즘 (gzip, zlib, bz2, lzma)
- **Message Validation**: ROS 메시지 및 메타데이터 검증
- **Search & Analytics**: 고급 검색 및 통계 기능
- **SQLite Storage**: 경량 임베디드 데이터베이스

## 기술 스택

### Backend API
- **Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Package Manager**: uv
- **Migration**: Alembic
- **Testing**: pytest

### MQTT Broker
- **Protocol**: MQTT 3.1.1
- **Async I/O**: asyncio
- **WebSocket**: websockets
- **MQTT Client**: asyncio-mqtt, paho-mqtt
- **Authentication**: Built-in username/password
- **TLS/SSL**: Python ssl module

### ROS Data Storage System
- **Database**: SQLite
- **ORM**: SQLAlchemy
- **Async I/O**: asyncio
- **Compression**: gzip, zlib, bz2, lzma
- **CLI**: argparse
- **Validation**: Custom validation framework

## 설치 및 실행

### 1. 환경 설정

```bash
# uv 설치 (Windows)
pip install uv

# 프로젝트 클론
git clone <repository-url>
cd DeepROS-Platform

# 가상환경 생성 및 의존성 설치
uv sync
```

### 2. 환경 변수 설정

```bash
# .env 파일 생성
cp env.example .env

# .env 파일 편집
# DATABASE_URL=postgresql://username:password@localhost:5432/deepros_db
```

### 3. 데이터베이스 설정

```bash
# PostgreSQL 데이터베이스 생성
createdb deepros_db

# 마이그레이션 실행
uv run alembic upgrade head
```

### 4. 애플리케이션 실행

#### Backend API 실행
```bash
# 개발 서버 실행
uv run uvicorn app.main:app --reload

# 또는
uv run python -m app.main
```

#### MQTT Broker 실행
```bash
# 기본 설정으로 브로커 실행
python -m Broker.main

# 커스텀 포트로 실행
python -m Broker.main --mqtt-port 1884

# 인증 활성화로 실행
python -m Broker.main --enable-auth

# 디버그 로깅으로 실행
python -m Broker.main --log-level DEBUG
```

#### ROS Data Storage System 실행
```bash
# 기록 시작
python -m data.main record --name "test_session" --topics "/cmd_vel,/odom"

# 기록 재생
python -m data.main play --session-id 1

# 세션 목록 조회
python -m data.main list

# 세션 정보 조회
python -m data.main info --session-id 1

# 메시지 검색
python -m data.main search --topics "/cmd_vel" --start-time 1234567890

# 통계 조회
python -m data.main stats
```

## API 문서

### Backend API 문서
서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### MQTT Broker 문서
브로커 관련 상세 문서는 [Broker/README.md](Broker/README.md)를 참조하세요.

### ROS Data Storage System 문서
데이터 저장 시스템 관련 상세 문서는 [data/README.md](data/README.md)를 참조하세요.

## API 엔드포인트

### 도메인 관리
- `GET /api/v1/domains/` - 도메인 목록 조회
- `POST /api/v1/domains/` - 도메인 생성
- `GET /api/v1/domains/{id}` - 도메인 상세 조회
- `PUT /api/v1/domains/{id}` - 도메인 수정
- `DELETE /api/v1/domains/{id}` - 도메인 삭제

### 노드 관리
- `GET /api/v1/nodes/` - 노드 목록 조회
- `POST /api/v1/nodes/` - 노드 생성
- `GET /api/v1/nodes/{id}` - 노드 상세 조회
- `PUT /api/v1/nodes/{id}` - 노드 수정
- `DELETE /api/v1/nodes/{id}` - 노드 삭제

### 연결 관리
- `GET /api/v1/connections/` - 연결 목록 조회
- `POST /api/v1/connections/` - 연결 생성
- `GET /api/v1/connections/{id}` - 연결 상세 조회
- `PUT /api/v1/connections/{id}` - 연결 수정
- `DELETE /api/v1/connections/{id}` - 연결 삭제

### 메시지 관리
- `GET /api/v1/messages/` - 메시지 목록 조회
- `POST /api/v1/messages/` - 메시지 생성
- `GET /api/v1/messages/{id}` - 메시지 상세 조회
- `DELETE /api/v1/messages/{id}` - 메시지 삭제

## 개발

### 테스트 실행

#### Backend API 테스트
```bash
# 모든 테스트 실행
uv run pytest

# 특정 테스트 파일 실행
uv run pytest tests/test_api.py

# 커버리지와 함께 실행
uv run pytest --cov=app
```

#### MQTT Broker 테스트
```bash
# 브로커 테스트 실행
python -m Broker.test_broker
```

#### ROS Data Storage System 테스트
```bash
# 데이터 저장 시스템 테스트 실행
python -m data.test_data
```

### 코드 포맷팅

```bash
# Black으로 코드 포맷팅
uv run black app tests

# isort로 import 정렬
uv run isort app tests
```

### 타입 체크

```bash
# mypy로 타입 체크
uv run mypy app
```

## 데이터베이스 스키마

### 주요 테이블

1. **ros_domains**: ROS 도메인 정보
2. **nodes**: ROS 노드 정보 (topic, service, action)
3. **node_connections**: 노드 간 연결 정보
4. **node_messages**: 메시지 로깅

### 샘플 데이터

`scripts/` 폴더에 샘플 데이터가 포함되어 있습니다:

- `001-create-tables.sql`: 테이블 생성 스크립트
- `002-insert-sample-data.sql`: 샘플 데이터 삽입
- `003-create-indexes-and-views.sql`: 인덱스 및 뷰 생성

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.
