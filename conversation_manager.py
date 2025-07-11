import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import streamlit as st

class ConversationManager:
    def __init__(self, save_dir: str = "conversations"):
        """
        대화 기록 관리자 초기화
        
        Args:
            save_dir: 대화 기록을 저장할 디렉토리
        """
        self.save_dir = save_dir
        self.ensure_save_directory()
    
    def ensure_save_directory(self):
        """저장 디렉토리가 없으면 생성"""
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
    
    def save_conversation(self, conversation_history: List[tuple], filename: Optional[str] = None) -> str:
        """
        대화 기록을 JSON 파일로 저장
        
        Args:
            conversation_history: (user_input, bot_response) 튜플의 리스트
            filename: 저장할 파일명 (None이면 자동 생성)
            
        Returns:
            저장된 파일 경로
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_{timestamp}.json"
        
        filepath = os.path.join(self.save_dir, filename)
        
        # 대화 기록을 저장 가능한 형태로 변환
        conversation_data = {
            "timestamp": datetime.now().isoformat(),
            "total_messages": len(conversation_history),
            "conversations": [
                {
                    "user": user_msg,
                    "assistant": bot_msg,
                    "order": i + 1
                }
                for i, (user_msg, bot_msg) in enumerate(conversation_history)
            ]
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, ensure_ascii=False, indent=2)
            return filepath
        except Exception as e:
            raise RuntimeError(f"대화 기록 저장 실패: {e}")
    
    def load_conversation(self, filename: str) -> List[tuple]:
        """
        JSON 파일에서 대화 기록을 불러오기
        
        Args:
            filename: 불러올 파일명
            
        Returns:
            (user_input, bot_response) 튜플의 리스트
        """
        filepath = os.path.join(self.save_dir, filename)
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"대화 기록 파일을 찾을 수 없습니다: {filename}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                conversation_data = json.load(f)
            
            # 대화 기록을 원래 형태로 변환
            conversation_history = [
                (conv["user"], conv["assistant"])
                for conv in sorted(conversation_data["conversations"], key=lambda x: x["order"])
            ]
            
            return conversation_history
        except Exception as e:
            raise RuntimeError(f"대화 기록 불러오기 실패: {e}")
    
    def get_saved_conversations(self) -> List[Dict]:
        """
        저장된 대화 기록 목록 가져오기
        
        Returns:
            파일 정보 리스트 [{"filename": str, "timestamp": str, "message_count": int}]
        """
        conversations = []
        
        if not os.path.exists(self.save_dir):
            return conversations
        
        for filename in os.listdir(self.save_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.save_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    conversations.append({
                        "filename": filename,
                        "timestamp": data.get("timestamp", "Unknown"),
                        "message_count": data.get("total_messages", 0),
                        "date": self._format_timestamp(data.get("timestamp", ""))
                    })
                except Exception:
                    continue
        
        # 타임스탬프로 정렬 (최신순)
        conversations.sort(key=lambda x: x["timestamp"], reverse=True)
        return conversations
    
    def delete_conversation(self, filename: str) -> bool:
        """
        대화 기록 파일 삭제
        
        Args:
            filename: 삭제할 파일명
            
        Returns:
            삭제 성공 여부
        """
        filepath = os.path.join(self.save_dir, filename)
        
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False
        except Exception:
            return False
    
    def export_conversation_text(self, conversation_history: List[tuple]) -> str:
        """
        대화 기록을 텍스트 형태로 변환 (다운로드용)
        
        Args:
            conversation_history: 대화 기록
            
        Returns:
            텍스트 형태의 대화 기록
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text_content = f"제주도 여행 챗봇 대화 기록\n"
        text_content += f"저장 시간: {timestamp}\n"
        text_content += "=" * 50 + "\n\n"
        
        for i, (user_msg, bot_msg) in enumerate(conversation_history, 1):
            text_content += f"[{i}] 사용자: {user_msg}\n"
            text_content += f"[{i}] 챗봇: {bot_msg}\n"
            text_content += "-" * 30 + "\n\n"
        
        return text_content
    
    def auto_save_conversation(self, conversation_history: List[tuple]):
        """
        대화 기록 자동 저장 (임시 파일)
        
        Args:
            conversation_history: 현재 대화 기록
        """
        if conversation_history:
            try:
                self.save_conversation(conversation_history, "auto_save.json")
            except Exception:
                pass  # 자동 저장 실패 시 무시
    
    def load_auto_save(self) -> Optional[List[tuple]]:
        """
        자동 저장된 대화 기록 불러오기
        
        Returns:
            자동 저장된 대화 기록 또는 None
        """
        try:
            return self.load_conversation("auto_save.json")
        except Exception:
            return None
    
    def _format_timestamp(self, timestamp_str: str) -> str:
        """타임스탬프를 읽기 쉬운 형태로 변환"""
        try:
            if timestamp_str:
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                return dt.strftime("%Y-%m-%d %H:%M")
            return "Unknown"
        except Exception:
            return "Unknown"

# Streamlit과 통합하는 헬퍼 함수들
def create_conversation_sidebar(conversation_manager: ConversationManager):
    """
    Streamlit 사이드바에 대화 기록 관리 UI 생성
    
    Args:
        conversation_manager: ConversationManager 인스턴스
    """
    st.sidebar.subheader("💾 대화 기록 관리")
    
    # 현재 대화 저장
    if st.sidebar.button("💾 현재 대화 저장"):
        if 'messages' in st.session_state and st.session_state.messages:
            # Streamlit 메시지를 튜플 형태로 변환
            conversation_history = []
            for i in range(0, len(st.session_state.messages), 2):
                if i + 1 < len(st.session_state.messages):
                    user_msg = st.session_state.messages[i]['content']
                    bot_msg = st.session_state.messages[i + 1]['content']
                    conversation_history.append((user_msg, bot_msg))
            
            try:
                filepath = conversation_manager.save_conversation(conversation_history)
                filename = os.path.basename(filepath)
                st.sidebar.success(f"✅ 대화 저장 완료: {filename}")
            except Exception as e:
                st.sidebar.error(f"❌ 저장 실패: {e}")
        else:
            st.sidebar.warning("저장할 대화가 없습니다.")
    
    # 저장된 대화 목록
    saved_conversations = conversation_manager.get_saved_conversations()
    
    if saved_conversations:
        st.sidebar.subheader("📋 저장된 대화 목록")
        
        for conv in saved_conversations[:5]:  # 최근 5개만 표시
            with st.sidebar.expander(f"📝 {conv['date']} ({conv['message_count']}개 메시지)"):
                col1, col2 = st.sidebar.columns(2)
                
                with col1:
                    if st.button("📥 불러오기", key=f"load_{conv['filename']}"):
                        try:
                            conversation_history = conversation_manager.load_conversation(conv['filename'])
                            
                            # Streamlit 메시지 형태로 변환
                            st.session_state.messages = []
                            for user_msg, bot_msg in conversation_history:
                                st.session_state.messages.append({"role": "user", "content": user_msg})
                                st.session_state.messages.append({"role": "assistant", "content": bot_msg})
                            
                            st.sidebar.success("✅ 대화 불러오기 완료!")
                            st.experimental_rerun()
                        except Exception as e:
                            st.sidebar.error(f"❌ 불러오기 실패: {e}")
                
                with col2:
                    if st.button("🗑️ 삭제", key=f"delete_{conv['filename']}"):
                        if conversation_manager.delete_conversation(conv['filename']):
                            st.sidebar.success("✅ 삭제 완료!")
                            st.experimental_rerun()
                        else:
                            st.sidebar.error("❌ 삭제 실패!")
    
    # 대화 기록 내보내기
    if st.sidebar.button("📤 대화 기록 내보내기"):
        if 'messages' in st.session_state and st.session_state.messages:
            # Streamlit 메시지를 튜플 형태로 변환
            conversation_history = []
            for i in range(0, len(st.session_state.messages), 2):
                if i + 1 < len(st.session_state.messages):
                    user_msg = st.session_state.messages[i]['content']
                    bot_msg = st.session_state.messages[i + 1]['content']
                    conversation_history.append((user_msg, bot_msg))
            
            text_content = conversation_manager.export_conversation_text(conversation_history)
            
            st.sidebar.download_button(
                label="📥 텍스트 파일 다운로드",
                data=text_content,
                file_name=f"jeju_travel_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
        else:
            st.sidebar.warning("내보낼 대화가 없습니다.")

def auto_save_session(conversation_manager: ConversationManager):
    """
    현재 세션의 대화를 자동 저장
    
    Args:
        conversation_manager: ConversationManager 인스턴스
    """
    if 'messages' in st.session_state and st.session_state.messages:
        # Streamlit 메시지를 튜플 형태로 변환
        conversation_history = []
        for i in range(0, len(st.session_state.messages), 2):
            if i + 1 < len(st.session_state.messages):
                user_msg = st.session_state.messages[i]['content']
                bot_msg = st.session_state.messages[i + 1]['content']
                conversation_history.append((user_msg, bot_msg))
        
        conversation_manager.auto_save_conversation(conversation_history) 