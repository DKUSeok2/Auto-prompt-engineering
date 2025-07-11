import os
import ollama
from typing import List, Dict, Optional

class JejuTravelChatbot:
    def __init__(self, model_name: str = "gemma3:4b"):
        """
        제주도 여행 챗봇 초기화
        
        Args:
            model_name: Ollama 모델 이름 (기본값: gemma3:4b)
        """
        self.model_name = model_name
        self.conversation_history = []
        
        # ChromaDB 연결 (이미 로딩된 데이터베이스 사용)
        try:
            self.client, self.collection = self.connect_to_existing_db()
            print("✅ ChromaDB 연결 완료")
        except Exception as e:
            print(f"❌ ChromaDB 연결 실패: {e}")
            print("💡 data_loader.py를 먼저 실행해서 데이터를 로딩하세요.")
            self.client = None
            self.collection = None
    
    def connect_to_existing_db(self):
        """
        이미 로딩된 ChromaDB에 연결
        
        Returns:
            client, collection: ChromaDB 클라이언트와 컬렉션
        """
        import chromadb
        from chromadb.utils.embedding_functions import EmbeddingFunction
        from langchain_upstage import UpstageEmbeddings
        from dotenv import load_dotenv
        
        # 환경 변수 로딩
        load_dotenv()
        api_key = os.getenv("UPSTAGE_API_KEY")
        if not api_key:
            raise ValueError("UPSTAGE_API_KEY가 설정되어 있지 않습니다.")
        
        # Upstage 임베딩 모델 설정
        passage_embedder = UpstageEmbeddings(model="solar-embedding-1-large-passage")
        
        # EmbeddingFunction 래퍼 정의
        class UpstageEmbeddingFunction(EmbeddingFunction):
            def __init__(self, embedder):
                self.embedder = embedder

            def __call__(self, input):
                try:
                    # input이 리스트가 아닌 경우 리스트로 변환
                    if isinstance(input, str):
                        input = [input]
                    return [self.embedder.embed_query(text) for text in input]
                except Exception as e:
                    raise RuntimeError(f"임베딩 생성 중 오류 발생: {e}")
        
        # ChromaDB 클라이언트 연결
        if not os.path.exists("./chroma_db"):
            raise FileNotFoundError("ChromaDB 데이터베이스가 없습니다. data_loader.py를 먼저 실행하세요.")
        
        client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=chromadb.Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # 컬렉션 가져오기
        collection = client.get_collection(
            name="visitjeju",
            embedding_function=UpstageEmbeddingFunction(passage_embedder)
        )
        
        return client, collection
    
    def load_prompt(self, prompt_file: str = "prompt.txt") -> str:
        """
        프롬프트 파일 로드
        
        Args:
            prompt_file: 프롬프트 파일 경로
            
        Returns:
            프롬프트 내용
        """
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return "당신은 제주도 여행 전문가입니다. 사용자에게 유용한 여행 정보를 제공해주세요."
    
    def search_relevant_info(self, query: str, n_results: int = 3) -> List[Dict]:
        """
        사용자 쿼리에 관련된 정보 검색
        
        Args:
            query: 사용자 질문
            n_results: 검색 결과 개수
            
        Returns:
            검색 결과 리스트
        """
        if not self.collection:
            return []
        
        try:
            # 쿼리 임베딩 생성
            from langchain_upstage import UpstageEmbeddings
            from dotenv import load_dotenv
            
            load_dotenv()
            query_embedder = UpstageEmbeddings(model="solar-embedding-1-large-query")
            query_embedding = query_embedder.embed_query(query)
            
            # 검색 실행
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            # 검색 결과 정리
            relevant_info = []
            if results and 'metadatas' in results:
                for i, metadata in enumerate(results['metadatas'][0]):
                    info = {
                        'name': metadata.get('이름', metadata.get('title', '제목 없음')),
                        'category': metadata.get('category', '카테고리 없음'),
                        'address': metadata.get('주소', metadata.get('roadaddress', '주소 없음')),
                        'phone': metadata.get('전화번호', '전화번호 없음'),
                        'tags': metadata.get('태그', metadata.get('alltag', '태그 없음')),
                        'description': metadata.get('소개', metadata.get('introduction', '설명 없음')),
                        'distance': results.get('distances', [[]])[0][i] if results.get('distances') else 0
                    }
                    relevant_info.append(info)
            
            return relevant_info
        except Exception as e:
            print(f"❌ 검색 중 오류 발생: {e}")
            return []
    
    def format_context(self, relevant_info: List[Dict]) -> str:
        """
        검색된 정보를 컨텍스트로 포맷팅
        
        Args:
            relevant_info: 검색 결과 리스트
            
        Returns:
            포맷팅된 컨텍스트 문자열
        """
        if not relevant_info:
            return "관련 정보를 찾을 수 없습니다."
        
        context = "=== 제주도 관련 정보 ===\n\n"
        
        for i, info in enumerate(relevant_info, 1):
            context += f"{i}. {info['name']} ({info['category']})\n"
            context += f"   📍 주소: {info['address']}\n"
            if info['phone'] != '전화번호 없음':
                context += f"   📞 전화번호: {info['phone']}\n"
            context += f"   🏷 태그: {info['tags']}\n"
            context += f"   💬 설명: {info['description']}\n"
            context += f"   📊 관련도: {info['distance']:.3f}\n\n"
        
        return context
    
    def generate_response(self, user_input: str) -> str:
        """
        사용자 입력에 대한 응답 생성
        
        Args:
            user_input: 사용자 입력
            
        Returns:
            챗봇 응답
        """
        # 프롬프트 로드
        system_prompt = self.load_prompt()
        
        # 관련 정보 검색
        relevant_info = self.search_relevant_info(user_input)
        context = self.format_context(relevant_info)
        
        # 대화 히스토리 포함
        conversation_context = ""
        if self.conversation_history:
            conversation_context = "\n=== 이전 대화 ===\n"
            for i, (user_msg, bot_msg) in enumerate(self.conversation_history[-3:], 1):  # 최근 3개 대화만
                conversation_context += f"사용자 {i}: {user_msg}\n"
                conversation_context += f"챗봇 {i}: {bot_msg}\n\n"
        
        # 최종 프롬프트 구성
        full_prompt = f"""
{system_prompt}

{context}

{conversation_context}

현재 사용자 질문: {user_input}

위의 정보를 바탕으로 사용자에게 도움이 되는 답변을 해주세요.
"""
        
        try:
            # Ollama API 호출
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {
                        'role': 'system',
                        'content': system_prompt
                    },
                    {
                        'role': 'user', 
                        'content': f"{context}\n\n{conversation_context}\n\n사용자 질문: {user_input}"
                    }
                ]
            )
            
            bot_response = response['message']['content']
            
            # 대화 히스토리에 추가
            self.conversation_history.append((user_input, bot_response))
            
            return bot_response
            
        except Exception as e:
            return f"죄송합니다. 응답 생성 중 오류가 발생했습니다: {e}"
    
    def clear_history(self):
        """대화 히스토리 초기화"""
        self.conversation_history = []
        print("✅ 대화 히스토리가 초기화되었습니다.")
    
    def get_conversation_history(self) -> List[tuple]:
        """대화 히스토리 반환"""
        return self.conversation_history
    
    def set_model(self, model_name: str):
        """모델 변경"""
        self.model_name = model_name
        print(f"✅ 모델이 {model_name}으로 변경되었습니다.")

# 테스트 코드
if __name__ == "__main__":
    # 챗봇 초기화
    chatbot = JejuTravelChatbot()
    
    print("🏝️ 제주도 여행 챗봇에 오신 것을 환영합니다!")
    print("종료하려면 'quit' 또는 'exit'를 입력하세요.")
    print("대화 히스토리를 초기화하려면 'clear'를 입력하세요.")
    print("-" * 50)
    
    while True:
        user_input = input("\n사용자: ")
        
        if user_input.lower() in ['quit', 'exit']:
            print("👋 안녕히 가세요!")
            break
        elif user_input.lower() == 'clear':
            chatbot.clear_history()
            continue
        elif user_input.strip() == '':
            continue
        
        print("🤖 답변 생성 중...")
        response = chatbot.generate_response(user_input)
        print(f"\n챗봇: {response}")
        print("-" * 50) 