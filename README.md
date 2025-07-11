# 🏝️ 제주도 여행 챗봇

Ollama의 Gemma 모델과 Upstage 임베딩, ChromaDB를 활용한 제주도 여행 추천 챗봇입니다.
Streamlit을 통해 프롬프트 엔지니어링과 대화형 인터페이스를 제공합니다.

## ✨ 주요 기능

- **대화 메모리**: 이전 대화 내용을 기억하여 맥락있는 대화 제공
- **대화 기록 저장**: 대화를 파일로 저장하고 불러오기 가능
- **프롬프트 엔지니어링**: 웹 인터페이스에서 실시간 프롬프트 수정
- **RAG 시스템**: ChromaDB와 Upstage 임베딩을 활용한 정보 검색
- **다양한 모델 지원**: Ollama의 여러 모델 선택 가능
- **실시간 데이터 관리**: 제주도 음식, 숙소, 관광지, 행사 정보 활용

## 📋 요구사항

- Python 3.8+
- Ollama 서버 실행 중
- Upstage API Key

## 🚀 설치 방법

### 1. 저장소 복제
```bash
git clone <repository-url>
cd 오르다
```

### 2. 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정
프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
UPSTAGE_API_KEY=your_upstage_api_key_here
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b
```

### 4. Ollama 설치 및 모델 다운로드
```bash
# Ollama 설치 (macOS)
brew install ollama

# Ollama 서버 실행
ollama serve

# 다른 터미널에서 모델 다운로드
ollama pull gemma3:4b
```

### 5. 제주도 데이터 준비
`data/` 폴더에 다음 JSON 파일들을 배치하세요:
- `visitjeju_food.json` - 음식점 정보
- `visitjeju_hotel.json` - 숙소 정보
- `visitjeju_tour.json` - 관광지 정보
- `visitjeju_event.json` - 행사 정보

## 🎯 사용 방법

### 1. 데이터 로딩
```bash
python data_loader.py
```

### 2. Streamlit 앱 실행
```bash
streamlit run app.py
```

### 3. 웹 브라우저에서 접속
기본적으로 `http://localhost:8501`에서 접속 가능합니다.

### 4. 채팅 시작
1. **설정 탭**에서 시스템 상태 확인
2. **사이드바**에서 ChromaDB 상태 확인
3. **채팅 탭**에서 대화 시작!

### 5. 프롬프트 엔지니어링
- **프롬프트 편집 탭**에서 시스템 프롬프트 수정
- 실시간으로 챗봇 답변 스타일 변경 가능
- 저장하면 즉시 반영됩니다

## 📁 프로젝트 구조

```
오르다/
├── app.py                    # Streamlit 메인 애플리케이션
├── chatbot.py               # 챗봇 로직
├── conversation_manager.py   # 대화 기록 관리
├── chroma_setup.py          # ChromaDB 설정 및 초기화 (레거시)
├── data_loader.py           # 데이터 로딩 스크립트
├── prompt.txt               # 시스템 프롬프트
├── requirements.txt         # 패키지 의존성
├── README.md               # 프로젝트 설명서
├── .env                    # 환경 변수 (직접 생성)
├── conversations/          # 대화 기록 저장 폴더 (자동 생성)
└── data/                   # 제주도 데이터 (직접 추가)
    ├── visitjeju_food.json
    ├── visitjeju_hotel.json
    ├── visitjeju_tour.json
    └── visitjeju_event.json
```

## 🔧 주요 컴포넌트

### 1. `app.py` - Streamlit 메인 애플리케이션
- 웹 인터페이스 제공
- 대화형 채팅 인터페이스
- 프롬프트 편집 기능
- 시스템 상태 모니터링

### 2. `chatbot.py` - 챗봇 로직
- Ollama API 연동
- 대화 메모리 관리
- RAG 시스템 통합
- 프롬프트 동적 로딩

### 3. `conversation_manager.py` - 대화 기록 관리
- JSON 파일 기반 대화 저장/불러오기
- 자동 저장 및 복원 기능
- 대화 기록 내보내기
- Streamlit UI 통합

### 4. `data_loader.py` - 데이터 로딩 스크립트
- 제주도 JSON 데이터 로딩
- ChromaDB 초기화 및 임베딩 생성
- 검색 기능 테스트

### 5. `prompt.txt` - 시스템 프롬프트
- 챗봇 페르소나 정의
- 답변 스타일 설정
- 실시간 편집 가능

## 🎨 기능 상세

### 대화 메모리
- 세션 기반 대화 히스토리 저장
- 최근 3개 대화 컨텍스트 활용
- 대화 초기화 기능

### 대화 기록 저장
- **자동 저장**: 대화할 때마다 자동으로 임시 저장
- **수동 저장**: 원하는 대화를 영구 저장
- **대화 불러오기**: 저장된 대화 기록 복원
- **파일 내보내기**: 텍스트 파일로 다운로드
- **기록 관리**: 저장된 대화 목록 관리 및 삭제

### 프롬프트 엔지니어링
- 웹 인터페이스에서 실시간 편집
- 파일 기반 프롬프트 관리
- 기본 프롬프트 복원 기능

### RAG 시스템
- Upstage 임베딩으로 의미 검색
- ChromaDB 벡터 저장소
- 관련도 기반 정보 제공

## 🛠️ 트러블슈팅

### Ollama 연결 오류
```bash
# Ollama 서버 실행 확인
ollama serve

# 모델 다운로드 확인
ollama list
```

### ChromaDB 초기화 실패
- Upstage API Key 확인
- 네트워크 연결 상태 확인
- 데이터 파일 존재 여부 확인

### 데이터 로딩 실패
- JSON 파일 형식 확인
- 파일 경로 확인 (`data/` 폴더 내)
- 파일 읽기 권한 확인

## 🤝 기여하기

1. Fork 프로젝트
2. Feature 브랜치 생성 (`git checkout -b feature/AmazingFeature`)
3. 변경사항 커밋 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치 Push (`git push origin feature/AmazingFeature`)
5. Pull Request 생성


**제주도 여행이 더욱 즐거워지길 바랍니다! 🏝️**
