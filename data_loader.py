import os
import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv
import chromadb
from chromadb.utils.embedding_functions import EmbeddingFunction
from langchain_upstage import UpstageEmbeddings

# 1. 환경 변수 로딩
load_dotenv()
api_key = os.getenv("UPSTAGE_API_KEY")
if not api_key:
    raise ValueError("UPSTAGE_API_KEY가 설정되어 있지 않습니다. .env 파일을 확인해주세요.")

print("🔑 API Key 확인 완료")

# 2. Upstage 임베딩 모델 설정
try:
    print("⚡ Upstage 임베딩 모델 로딩 중...")
    query_embedder = UpstageEmbeddings(model="solar-embedding-1-large-query")
    passage_embedder = UpstageEmbeddings(model="solar-embedding-1-large-passage")
    print("✅ Upstage 임베딩 모델 로딩 완료")
except Exception as e:
    raise RuntimeError(f"Upstage 임베딩 로드 중 오류 발생: {e}")

# 3. ChromaDB에 사용할 EmbeddingFunction 래퍼 정의
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

# 4. ChromaDB 초기화
print("🗄️ ChromaDB 초기화 중...")
try:
    # 기존 데이터베이스 삭제 (새로 시작)
    import shutil
    if os.path.exists("./chroma_db"):
        shutil.rmtree("./chroma_db")
    
    client = chromadb.PersistentClient(
        path="./chroma_db",
        settings=chromadb.Settings(
            anonymized_telemetry=False,
            allow_reset=True
        )
    )
    collection = client.get_or_create_collection(
        name="visitjeju",
        embedding_function=UpstageEmbeddingFunction(passage_embedder)
    )
    print("✅ ChromaDB 초기화 완료")
except Exception as e:
    print(f"❌ ChromaDB 초기화 실패: {e}")
    raise

# 5. 파일-카테고리 매핑
category_map = {
    "data/visitjeju_food.json": "음식",
    "data/visitjeju_hotel.json": "숙소",
    "data/visitjeju_tour.json": "관광지",
    "data/visitjeju_event.json": "행사"
}

print("📂 데이터 파일 확인 중...")
for filename in category_map.keys():
    if os.path.exists(filename):
        print(f"✅ {filename} 파일 존재")
    else:
        print(f"⚠️ {filename} 파일 없음")

# 6. 파일 순회하며 임베딩 및 저장
total_processed = 0

for filename, category in category_map.items():
    if not os.path.exists(filename):
        print(f"⏭️ {filename} 파일이 없어 건너뜀")
        continue
        
    try:
        df = pd.read_json(filename)
        print(f"📊 {filename}: {len(df)}개 데이터 로드")
    except Exception as e:
        print(f"❌ {filename} 로딩 실패: {e}")
        continue

    ids, documents, metadatas = [], [], []

    for i, row in tqdm(df.iterrows(), total=df.shape[0], desc=f"📂 {filename} 처리 중"):
        try:
            metadata = row.to_dict()

            # 카테고리별 document 구성
            if category == "음식":
                content = (
                    f"카테고리: 음식 "
                    f"이름: {row.get('이름', '')} "
                    f"주소: {row.get('주소', '')} "
                    f"소개: {row.get('소개', '')} "
                    f"태그: {row.get('태그', '')} "
                )
            elif category == "숙소":
                content = (
                    f"카테고리: 숙소 "
                    f"이름: {row.get('이름', '')} "
                    f"주소: {row.get('주소', '')} "
                    f"전화번호: {row.get('전화번호', '')} "
                    f"소개: {row.get('소개', '')}"
                    f"태그: {row.get('태그', '')} "
                )
            elif category == "관광지":
                content = (
                    f"카테고리: 관광지 "
                    f"이름: {row.get('이름', '')} "
                    f"주소: {row.get('주소', '')} "
                    f"전화번호: {row.get('전화번호', '')} "
                    f"소개: {row.get('소개', '')}"
                    f"태그: {row.get('태그', '')} "
                )
            elif category == "행사":
                content = (
                    f"카테고리: 행사 "
                    f"이름: {row.get('title', '')} "
                    f"주소: {row.get('roadaddress', '')} "
                    f"태그: {row.get('alltag', '')} "
                    f"소개: {row.get('introduction', '')}"
                )
            else:
                content = "카테고리 정보 없음"

            ids.append(f"{category}_{i}")
            documents.append(content)
            metadatas.append({**metadata, "category": category, **{key: value if value is not None else '' for key, value in metadata.items()}})
        except Exception as e:
            print(f"{i}번째 행 처리 중 오류: {e}")
            continue

    # 배치 단위로 저장
    batch_size = 100
    for batch_start in range(0, len(ids), batch_size):
        batch_end = batch_start + batch_size
        try:
            collection.add(
                ids=ids[batch_start:batch_end],
                documents=documents[batch_start:batch_end],
                metadatas=metadatas[batch_start:batch_end]
            )
            print(f"✅ {filename} → {batch_start}~{batch_end}번 저장 완료")
        except Exception as e:
            print(f"❌ {filename} → {batch_start}~{batch_end} 저장 실패: {e}")

    total_processed += len(ids)
    print(f"📊 {filename} 처리 완료: {len(ids)}개 데이터")

print(f"\n🎉 전체 데이터 로딩 완료! 총 {total_processed}개 데이터 처리")

# 7. 예시 쿼리 테스트
print("\n🧪 검색 기능 테스트 중...")
query_text = "제주 감성 카페 추천해줘"
try:
    query_embedding = query_embedder.embed_query(query_text)
    print(f"✅ 쿼리 임베딩 생성 완료: '{query_text}'")
except Exception as e:
    raise RuntimeError(f"쿼리 임베딩 생성 중 오류 발생: {e}")

# 8. 검색 실행
try:
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )
    print("✅ 검색 실행 완료")
except Exception as e:
    raise RuntimeError(f"ChromaDB 검색 중 오류 발생: {e}")

# 9. 결과 출력
print(f"\n🔍 '{query_text}' 검색 결과:")
print("=" * 60)
for i, metadata in enumerate(results.get('metadatas', [[]])[0]):
    print(f"[{i+1}] {metadata.get('이름', metadata.get('title', '제목 없음'))} ({metadata.get('category', '카테고리 없음')})")
    print(f"📍 주소: {metadata.get('주소', metadata.get('roadaddress', '없음'))}")
    print(f"📞 전화번호: {metadata.get('전화번호', '없음')}")
    print(f"🏷 태그: {metadata.get('태그', metadata.get('alltag', '없음'))}")
    print(f"💬 설명: {metadata.get('소개', metadata.get('introduction', '없음'))}")
    print("-" * 50)

# 10. 유사도 거리 출력
print("\n📏 유사도 거리:")
for i, (metadata, distance) in enumerate(zip(results.get('metadatas', [[]])[0], results.get('distances', [[]])[0])):
    name = metadata.get('이름', metadata.get('title', '제목 없음'))
    print(f"[{i+1}] {name} (유사도 거리: {distance:.4f})")

print("\n🎯 데이터 로더 실행 완료!")
print("이제 Streamlit 앱에서 ChromaDB를 사용할 수 있습니다.")
print("실행 명령어: streamlit run app.py") 