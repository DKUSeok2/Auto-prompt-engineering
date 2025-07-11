import streamlit as st
import os
import time
from chatbot import JejuTravelChatbot
from conversation_manager import ConversationManager, create_conversation_sidebar, auto_save_session

# 페이지 설정
st.set_page_config(
    page_title="제주도 여행 챗봇",
    page_icon="🏝️",
    layout="wide"
)

# 사이드바 설정
st.sidebar.title("🏝️ 제주도 여행 챗봇")
st.sidebar.markdown("---")

# 세션 상태 초기화
if 'chatbot' not in st.session_state:
    st.session_state.chatbot = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'db_initialized' not in st.session_state:
    st.session_state.db_initialized = False
if 'conversation_manager' not in st.session_state:
    st.session_state.conversation_manager = ConversationManager()

# 자동 저장된 대화 불러오기 (페이지 로드 시 한 번만)
if 'auto_loaded' not in st.session_state:
    st.session_state.auto_loaded = True
    auto_saved = st.session_state.conversation_manager.load_auto_save()
    if auto_saved and not st.session_state.messages:
        for user_msg, bot_msg in auto_saved:
            st.session_state.messages.append({"role": "user", "content": user_msg})
            st.session_state.messages.append({"role": "assistant", "content": bot_msg})

# 사이드바: 모델 설정
st.sidebar.subheader("🤖 모델 설정")
model_name = st.sidebar.selectbox(
    "Ollama 모델 선택",
    ["gemma3:4b", "gemma:2b", "gemma:7b", "llama2", "llama2:7b", "mistral", "codellama"],
    index=0
)

# 사이드바: 데이터베이스 설정
st.sidebar.subheader("📊 데이터베이스 설정")

# ChromaDB 상태 확인
if os.path.exists("./chroma_db"):
    st.sidebar.success("✅ ChromaDB 데이터베이스 존재")
    st.session_state.db_initialized = True
else:
    st.sidebar.warning("⚠️ ChromaDB 데이터베이스 없음")
    st.sidebar.info("💡 터미널에서 다음 명령어를 실행하세요:")
    st.sidebar.code("python data_loader.py", language="bash")
    st.session_state.db_initialized = False

# 데이터 재로딩 버튼
if st.sidebar.button("🔄 데이터 재로딩"):
    with st.spinner("데이터 재로딩 중..."):
        try:
            import subprocess
            result = subprocess.run(["python", "data_loader.py"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                st.sidebar.success("✅ 데이터 재로딩 완료!")
                st.session_state.db_initialized = True
            else:
                st.sidebar.error(f"❌ 데이터 재로딩 실패: {result.stderr}")
        except Exception as e:
            st.sidebar.error(f"❌ 데이터 재로딩 실패: {e}")

# 데이터베이스 삭제 버튼
if st.sidebar.button("🗑️ 데이터베이스 삭제"):
    try:
        import shutil
        if os.path.exists("./chroma_db"):
            shutil.rmtree("./chroma_db")
        st.sidebar.success("✅ 데이터베이스 삭제 완료!")
        st.session_state.db_initialized = False
    except Exception as e:
        st.sidebar.error(f"❌ 데이터베이스 삭제 실패: {e}")

# 사이드바: 대화 히스토리 관리
st.sidebar.subheader("💬 대화 관리")
if st.sidebar.button("대화 히스토리 초기화"):
    st.session_state.messages = []
    if st.session_state.chatbot:
        st.session_state.chatbot.clear_history()
    st.sidebar.success("✅ 대화 히스토리 초기화 완료!")

# 대화 기록 관리 UI 추가
create_conversation_sidebar(st.session_state.conversation_manager)

# 메인 영역
st.title("🏝️ 제주도 여행 챗봇")
st.markdown("제주도 여행 계획을 도와드립니다! 원하는 정보를 물어보세요.")

# 탭 생성
tab1, tab2, tab3 = st.tabs(["💬 채팅", "✏️ 프롬프트 편집", "⚙️ 설정"])

with tab1:
    # 챗봇 초기화 (처음 실행 시 또는 모델 변경 시)
    if st.session_state.chatbot is None or st.session_state.chatbot.model_name != model_name:
        with st.spinner("챗봇 초기화 중..."):
            try:
                st.session_state.chatbot = JejuTravelChatbot(model_name)
                st.success(f"✅ 챗봇 초기화 완료! (모델: {model_name})")
            except Exception as e:
                st.error(f"❌ 챗봇 초기화 실패: {e}")
                st.stop()

    # 대화 히스토리 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 사용자 입력 처리
    if prompt := st.chat_input("제주도 여행에 대해 궁금한 것을 물어보세요!"):
        # 사용자 메시지 추가
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 챗봇 응답 생성
        with st.chat_message("assistant"):
            with st.spinner("답변 생성 중..."):
                response = st.session_state.chatbot.generate_response(prompt)
                st.markdown(response)
                
        # 챗봇 응답 저장
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # 자동 저장
        auto_save_session(st.session_state.conversation_manager)

with tab2:
    st.subheader("✏️ 프롬프트 편집")
    st.markdown("아래에서 프롬프트를 편집하고 저장하면 챗봇에 자동으로 반영됩니다.")
    
    # 현재 프롬프트 로드
    try:
        with open("prompt.txt", "r", encoding="utf-8") as f:
            current_prompt = f.read()
    except FileNotFoundError:
        current_prompt = "당신은 제주도 여행 전문가입니다. 사용자에게 유용한 여행 정보를 제공해주세요."
    
    # 프롬프트 편집기
    edited_prompt = st.text_area(
        "프롬프트 내용",
        value=current_prompt,
        height=400,
        help="프롬프트를 수정하고 저장 버튼을 클릭하세요."
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 프롬프트 저장"):
            try:
                with open("prompt.txt", "w", encoding="utf-8") as f:
                    f.write(edited_prompt)
                st.success("✅ 프롬프트가 저장되었습니다!")
            except Exception as e:
                st.error(f"❌ 프롬프트 저장 실패: {e}")
    
    with col2:
        if st.button("🔄 프롬프트 리셋"):
            default_prompt = """당신은 제주도 여행 전문가입니다. 제주도의 음식, 숙소, 관광지, 행사에 대한 정보를 바탕으로 사용자에게 맞춤형 여행 추천을 제공합니다.

**역할:**
- 제주도 여행 전문가
- 친근하고 도움이 되는 여행 가이드
- 사용자의 요구사항을 정확히 파악하여 맞춤형 추천 제공

**답변 스타일:**
- 친근하고 따뜻한 말투 사용
- 구체적이고 실용적인 정보 제공
- 이모지를 적절히 활용하여 시각적 효과 증대
- 사용자의 질문에 단계별로 체계적으로 답변

**제공 정보:**
- 음식: 제주도 특산품, 맛집, 카페 등
- 숙소: 호텔, 펜션, 게스트하우스 등 
- 관광지: 자연명소, 박물관, 테마파크 등
- 행사: 축제, 이벤트, 문화행사 등

**답변 형식:**
1. 사용자의 질문에 대한 간단한 인사
2. 추천 장소/음식/숙소 목록 (최대 3-5개)
3. 각 추천 항목에 대한 간단한 설명
4. 주소, 전화번호 등 실용적 정보
5. 추가 팁이나 주의사항

사용자의 질문을 잘 듣고 제주도에서의 즐거운 여행이 될 수 있도록 최선을 다해 도움을 드리겠습니다! 🏝️"""
            
            try:
                with open("prompt.txt", "w", encoding="utf-8") as f:
                    f.write(default_prompt)
                st.success("✅ 프롬프트가 기본값으로 리셋되었습니다!")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"❌ 프롬프트 리셋 실패: {e}")

with tab3:
    st.subheader("⚙️ 설정")
    
    # 환경 변수 설정 가이드
    st.markdown("### 🔑 환경 변수 설정")
    st.markdown("""
    `.env` 파일을 프로젝트 루트에 생성하고 다음 내용을 추가하세요:
    
    ```
    UPSTAGE_API_KEY=your_upstage_api_key_here
    OLLAMA_BASE_URL=http://localhost:11434
    OLLAMA_MODEL=gemma:2b
    ```
    """)
    
    # 시스템 상태 확인
    st.markdown("### 📊 시스템 상태")
    
    # Ollama 서버 상태 확인
    try:
        import ollama
        models = ollama.list()
        st.success(f"✅ Ollama 서버 연결 성공 (모델 {len(models['models'])}개)")
        
        # 사용 가능한 모델 목록
        if models['models']:
            st.markdown("**사용 가능한 모델:**")
            for model in models['models']:
                st.markdown(f"- {model['name']}")
    except Exception as e:
        st.error(f"❌ Ollama 서버 연결 실패: {e}")
        st.markdown("Ollama 서버가 실행되고 있는지 확인하세요: `ollama serve`")
    
    # ChromaDB 상태 확인
    if st.session_state.db_initialized:
        st.success("✅ ChromaDB 초기화 완료")
    else:
        st.warning("⚠️ ChromaDB가 초기화되지 않았습니다.")
    
    # 데이터 파일 존재 확인
    st.markdown("### 📁 데이터 파일 상태")
    data_files = [
        "data/visitjeju_food.json",
        "data/visitjeju_hotel.json", 
        "data/visitjeju_tour.json",
        "data/visitjeju_event.json"
    ]
    
    for file_path in data_files:
        if os.path.exists(file_path):
            st.success(f"✅ {file_path}")
        else:
            st.warning(f"⚠️ {file_path} - 파일이 존재하지 않습니다.")

# 푸터
st.markdown("---")
st.markdown("🏝️ **제주도 여행 챗봇** - Ollama + ChromaDB + Streamlit로 구현")
st.markdown("프롬프트를 수정하여 챗봇의 답변 스타일을 변경할 수 있습니다!") 