# Drug Detection Backend

AI 기반 마약 탐지 시스템의 백엔드 서버입니다.

FastAPI와 MongoDB를 기반으로 구축되었으며, 관리자 인증, 탐지 결과 관리, 알림 기능 및 AI 모델 연동을 위한 API를 제공합니다.

---

## 프로젝트 개요

본 프로젝트는 텍스트 및 이미지 기반 마약 탐지 모델의 결과를 관리하고, 관리자가 탐지 결과를 검토할 수 있는 웹 서비스의 백엔드 서버입니다.

주요 기능은 다음과 같습니다.

* 관리자 회원가입 및 로그인
* JWT 기반 인증 및 권한 관리
* 탐지 결과 저장 및 조회
* 탐지 결과 검토 상태 관리
* AI 모델 연동을 위한 API 제공
* MongoDB 기반 데이터 관리

---

## 기술 스택

### Backend

* FastAPI
* Python 3.12
* Pydantic v2

### Database

* MongoDB
* PyMongo (AsyncMongoClient)

### Authentication

* JWT (Access Token / Refresh Token)
* HTTPBearer
* bcrypt

### Development

* Uvicorn
* Docker

---

## 프로젝트 구조

```text
app
├── api
│   └── v1
│       ├── auth.py
│       ├── admins.py
│       └── detections.py
│
├── core
│   ├── config.py
│   ├── database.py
│   └── security.py
│
├── models
│   ├── admin.py
│   └── detection.py
│
├── schemas
│   ├── admin.py
│   ├── auth.py
│   └── detection.py
│
├── services
│
├── utils
│
└── main.py
```

---

## 주요 기능

### 관리자 인증

* 회원가입
* 로그인
* JWT Access Token 발급
* JWT Refresh Token 발급
* 인증된 사용자 정보 조회

### 탐지 결과 관리

* 탐지 결과 저장
* 탐지 결과 목록 조회
* 탐지 결과 상세 조회
* 검토 상태 변경
* 관리자별 탐지 기록 조회

### 보안

* bcrypt 기반 비밀번호 암호화
* JWT 기반 인증
* HTTPBearer 인증
* 토큰 만료 검증
* 예외 처리 및 인증 오류 응답

---

## 실행 방법

### 1. 저장소 클론

```bash
git clone https://github.com/HelI-OKitty/drug-detection-backend.git

cd drug-detection-backend
```

### 2. 가상환경 생성

```bash
python -m venv venv
```

### 3. 가상환경 실행

Windows

```bash
venv\Scripts\activate
```

Mac / Linux

```bash
source venv/bin/activate
```

### 4. 패키지 설치

```bash
pip install -r requirements.txt
```

### 5. 서버 실행

```bash
uvicorn app.main:app --reload
```
