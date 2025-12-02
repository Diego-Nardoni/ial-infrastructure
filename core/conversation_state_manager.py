"""
Enterprise-Grade Conversation State Manager
Manages multi-turn conversations with proper state transitions
"""

import json
import time
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, asdict

class ConversationState(Enum):
    INITIAL = "initial"
    AWAITING_CLARIFICATION = "awaiting_clarification"
    PROCESSING_ANSWERS = "processing_answers"
    READY_TO_GENERATE = "ready_to_generate"
    COMPLETED = "completed"
    ERROR = "error"

@dataclass
class ClarificationQuestion:
    key: str
    question: str
    options: List[str]
    context: str
    answered: bool = False
    answer: Optional[str] = None

@dataclass
class ConversationSession:
    session_id: str
    user_id: str
    state: ConversationState
    original_request: str
    service_type: str
    questions: List[ClarificationQuestion]
    answers: Dict[str, str]
    created_at: float
    updated_at: float
    
    def to_dict(self) -> Dict:
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'state': self.state.value,
            'original_request': self.original_request,
            'service_type': self.service_type,
            'questions': [asdict(q) for q in self.questions],
            'answers': self.answers,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

class ConversationStateManager:
    """Enterprise conversation state management with DynamoDB persistence"""
    
    def __init__(self):
        self.sessions: Dict[str, ConversationSession] = {}
        self.current_session_id: Optional[str] = None
        
        # Initialize DynamoDB for persistence
        try:
            import boto3
            self.dynamodb = boto3.resource('dynamodb')
            self.table = self.dynamodb.Table('ial-state')
            print("✅ Conversation State Manager initialized with DynamoDB")
        except Exception as e:
            print(f"⚠️ DynamoDB not available for state persistence: {e}")
            self.dynamodb = None
            self.table = None
    
    def start_conversation(self, user_id: str, original_request: str, service_type: str) -> str:
        """Start new conversation session"""
        session_id = f"conv-{int(time.time())}-{hash(original_request) % 10000}"
        
        session = ConversationSession(
            session_id=session_id,
            user_id=user_id,
            state=ConversationState.INITIAL,
            original_request=original_request,
            service_type=service_type,
            questions=[],
            answers={},
            created_at=time.time(),
            updated_at=time.time()
        )
        
        self.sessions[session_id] = session
        self.current_session_id = session_id
        self._persist_session(session)
        
        print(f"🔄 Started conversation session: {session_id}")
        return session_id
    
    def add_clarification_questions(self, session_id: str, questions: List[Dict]) -> bool:
        """Add clarification questions to session"""
        if session_id not in self.sessions:
            return False
            
        session = self.sessions[session_id]
        session.questions = []
        
        for q in questions:
            question = ClarificationQuestion(
                key=q.get('key', ''),
                question=q.get('question', ''),
                options=q.get('options', []),
                context=q.get('context', '')
            )
            session.questions.append(question)
        
        session.state = ConversationState.AWAITING_CLARIFICATION
        session.updated_at = time.time()
        self._persist_session(session)
        
        print(f"📝 Added {len(questions)} questions to session {session_id}")
        return True
    
    def process_user_response(self, user_input: str) -> Dict[str, Any]:
        """Process user response in context of current conversation"""
        if not self.current_session_id or self.current_session_id not in self.sessions:
            return {'status': 'no_active_session'}
        
        session = self.sessions[self.current_session_id]
        
        if session.state == ConversationState.AWAITING_CLARIFICATION:
            return self._process_clarification_answer(session, user_input)
        elif session.state == ConversationState.INITIAL:
            return {'status': 'needs_clarification'}
        else:
            return {'status': 'invalid_state', 'current_state': session.state.value}
    
    def _process_clarification_answer(self, session: ConversationSession, user_input: str) -> Dict[str, Any]:
        """Process answer to clarification questions"""
        # Find next unanswered question
        next_question = None
        for q in session.questions:
            if not q.answered:
                next_question = q
                break
        
        if not next_question:
            # All questions answered
            session.state = ConversationState.READY_TO_GENERATE
            session.updated_at = time.time()
            self._persist_session(session)
            return {
                'status': 'ready_to_generate',
                'answers': session.answers,
                'original_request': session.original_request
            }
        
        # Process current answer
        answer = self._parse_user_answer(user_input, next_question)
        next_question.answered = True
        next_question.answer = answer
        session.answers[next_question.key] = answer
        session.updated_at = time.time()
        
        # Check if more questions remain
        remaining_questions = [q for q in session.questions if not q.answered]
        
        if remaining_questions:
            # More questions to ask
            next_q = remaining_questions[0]
            self._persist_session(session)
            return {
                'status': 'needs_more_clarification',
                'next_question': {
                    'question': next_q.question,
                    'options': next_q.options,
                    'context': next_q.context
                },
                'progress': f"{len(session.questions) - len(remaining_questions)}/{len(session.questions)}"
            }
        else:
            # All questions answered
            session.state = ConversationState.READY_TO_GENERATE
            self._persist_session(session)
            return {
                'status': 'ready_to_generate',
                'answers': session.answers,
                'original_request': session.original_request
            }
    
    def _parse_user_answer(self, user_input: str, question: ClarificationQuestion) -> str:
        """Parse user answer intelligently"""
        user_input = user_input.strip()
        
        # If it's a number, map to option
        if user_input.isdigit():
            option_index = int(user_input) - 1
            if 0 <= option_index < len(question.options):
                return question.options[option_index]
        
        # If it's text and matches an option partially
        for option in question.options:
            if user_input.lower() in option.lower() or option.lower() in user_input.lower():
                return option
        
        # Return as-is for custom answers (like workload names)
        return user_input
    
    def get_current_session(self) -> Optional[ConversationSession]:
        """Get current active session"""
        if self.current_session_id and self.current_session_id in self.sessions:
            return self.sessions[self.current_session_id]
        return None
    
    def _persist_session(self, session: ConversationSession):
        """Persist session to DynamoDB"""
        if not self.table:
            return
            
        try:
            self.table.put_item(
                Item={
                    'system_id': f'conversation-{session.session_id}',
                    'component': 'conversation_state',
                    'data': json.dumps(session.to_dict()),
                    'ttl': int(time.time()) + 3600  # 1 hour TTL
                }
            )
        except Exception as e:
            print(f"⚠️ Failed to persist session: {e}")
    
    def cleanup_old_sessions(self):
        """Cleanup sessions older than 1 hour"""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if current_time - session.updated_at > 3600:  # 1 hour
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
            print(f"🧹 Cleaned up expired session: {session_id}")
