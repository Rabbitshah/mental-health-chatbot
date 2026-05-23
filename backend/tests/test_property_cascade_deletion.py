"""
Property-Based Tests for Database Cascade Deletion and Message Retrieval Ordering

This module contains property tests that validate:
- Property 7: Message Retrieval Ordering
- Requirement 3.4: Messages are retrieved in correct chronological order
- Requirement 3.6: Cascade deletion of sessions and messages when user is deleted
"""
import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant, initialize
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from models import User, ChatSession, ChatMessage
import time


# Strategy for generating valid message text
message_text_strategy = st.text(min_size=1, max_size=500).filter(lambda x: x.strip())

# Strategy for generating sender types
sender_strategy = st.sampled_from(["user", "ai"])

# Strategy for generating number of messages
message_count_strategy = st.integers(min_value=1, max_value=50)


class TestMessageRetrievalOrdering:
    """
    Property 7: Message Retrieval Ordering
    
    PROPERTY: When messages are retrieved for a chat session, they MUST be ordered
    by created_at timestamp in ascending order (oldest first).
    
    This validates Requirement 3.4: "WHEN a User requests a Chat_Session, THEN THE
    Backend SHALL retrieve all Messages ordered by creation timestamp"
    """
    
    @given(
        message_count=message_count_strategy,
        messages_data=st.lists(
            st.tuples(message_text_strategy, sender_strategy),
            min_size=1,
            max_size=50
        )
    )
    @settings(
        max_examples=15,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_messages_ordered_by_creation_time(
        self,
        test_db: Session,
        sample_user: User,
        message_count: int,
        messages_data: list
    ):
        """
        Property: Messages retrieved from a session are always ordered by created_at ascending.
        
        Given: A chat session with N messages created at different times
        When: Messages are retrieved from the database
        Then: Messages MUST be ordered by created_at in ascending order
        """
        # Limit to the specified message count
        messages_data = messages_data[:message_count]
        assume(len(messages_data) > 0)
        
        # Create a new session for this test run
        session = ChatSession(
            user_id=sample_user.id,
            title=f"Test Session {message_count}",
            tag="General"
        )
        test_db.add(session)
        test_db.flush()
        
        # Create messages with incrementing timestamps
        created_messages = []
        base_time = datetime.now(timezone.utc).replace(tzinfo=None)
        
        for i, (text, sender) in enumerate(messages_data):
            # Add small time increments to ensure distinct timestamps
            message = ChatMessage(
                session_id=session.id,
                sender=sender,
                text=text,
                created_at=base_time + timedelta(seconds=i)
            )
            test_db.add(message)
            created_messages.append(message)
        
        test_db.commit()
        
        # Retrieve messages ordered by created_at
        retrieved_messages = (
            test_db.query(ChatMessage)
            .filter(ChatMessage.session_id == session.id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )
        
        # Property assertion: Messages must be in chronological order
        assert len(retrieved_messages) == len(messages_data), \
            "Retrieved message count must match created message count"
        
        for i in range(len(retrieved_messages) - 1):
            current_time = retrieved_messages[i].created_at
            next_time = retrieved_messages[i + 1].created_at
            
            assert current_time <= next_time, \
                f"Messages not in chronological order: message {i} created at {current_time}, " \
                f"message {i+1} created at {next_time}"
        
        # Verify the order matches insertion order
        for i, message in enumerate(retrieved_messages):
            assert message.text == messages_data[i][0], \
                f"Message order mismatch at position {i}"
            assert message.sender == messages_data[i][1], \
                f"Sender mismatch at position {i}"
        
        # Clean up for next hypothesis run
        test_db.delete(session)
        test_db.commit()
    
    @given(
        session_count=st.integers(min_value=1, max_value=5),
        messages_per_session=st.integers(min_value=2, max_value=10)
    )
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_messages_ordered_within_each_session(
        self,
        test_db: Session,
        sample_user: User,
        session_count: int,
        messages_per_session: int
    ):
        """
        Property: Message ordering is maintained independently for each session.
        
        Given: Multiple chat sessions each with multiple messages
        When: Messages are retrieved for each session
        Then: Each session's messages MUST be ordered by created_at independently
        """
        sessions_data = []
        base_time = datetime.now(timezone.utc).replace(tzinfo=None)
        
        # Create multiple sessions with messages
        for session_idx in range(session_count):
            session = ChatSession(
                user_id=sample_user.id,
                title=f"Session {session_idx}",
                tag="General"
            )
            test_db.add(session)
            test_db.flush()
            
            session_messages = []
            for msg_idx in range(messages_per_session):
                # Use session_idx in time calculation to interleave timestamps across sessions
                timestamp = base_time + timedelta(
                    seconds=session_idx * messages_per_session + msg_idx
                )
                message = ChatMessage(
                    session_id=session.id,
                    sender="user" if msg_idx % 2 == 0 else "ai",
                    text=f"Session {session_idx} Message {msg_idx}",
                    created_at=timestamp
                )
                test_db.add(message)
                session_messages.append((msg_idx, timestamp))
            
            sessions_data.append((session.id, session_messages))
        
        test_db.commit()
        
        # Verify ordering for each session independently
        for session_id, expected_messages in sessions_data:
            retrieved_messages = (
                test_db.query(ChatMessage)
                .filter(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.created_at.asc())
                .all()
            )
            
            assert len(retrieved_messages) == len(expected_messages), \
                f"Session {session_id} message count mismatch"
            
            # Verify chronological order
            for i in range(len(retrieved_messages) - 1):
                assert retrieved_messages[i].created_at <= retrieved_messages[i + 1].created_at, \
                    f"Session {session_id} messages not in chronological order"
            
            # Verify messages match expected order
            for i, (expected_idx, expected_time) in enumerate(expected_messages):
                assert retrieved_messages[i].created_at == expected_time, \
                    f"Session {session_id} message {i} timestamp mismatch"


class TestCascadeDeletion:
    """
    Property Tests for Cascade Deletion
    
    Validates Requirement 3.6: "WHEN a User is deleted, THEN THE Database SHALL
    cascade delete all associated Chat_Sessions and Messages"
    """
    
    @given(
        session_count=st.integers(min_value=1, max_value=10),
        messages_per_session=st.integers(min_value=1, max_value=20)
    )
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_cascade_delete_user_removes_sessions_and_messages(
        self,
        test_db: Session,
        session_count: int,
        messages_per_session: int
    ):
        """
        Property: Deleting a user cascades to delete all sessions and messages.
        
        Given: A user with N sessions, each with M messages
        When: The user is deleted
        Then: All sessions and messages MUST be deleted from the database
        """
        # Create user with unique identifiers
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        user = User(
            email=f"cascade_test_{unique_id}@example.com",
            name="Cascade Test User",
            username=f"cascade_user_{unique_id}",
            password="hashed_password"
        )
        test_db.add(user)
        test_db.flush()
        
        session_ids = []
        message_ids = []
        
        # Create sessions and messages
        for session_idx in range(session_count):
            session = ChatSession(
                user_id=user.id,
                title=f"Session {session_idx}",
                tag="General"
            )
            test_db.add(session)
            test_db.flush()
            session_ids.append(session.id)
            
            for msg_idx in range(messages_per_session):
                message = ChatMessage(
                    session_id=session.id,
                    sender="user" if msg_idx % 2 == 0 else "ai",
                    text=f"Message {msg_idx}"
                )
                test_db.add(message)
                test_db.flush()
                message_ids.append(message.id)
        
        test_db.commit()
        
        # Verify data exists before deletion
        assert test_db.query(User).filter(User.id == user.id).count() == 1
        assert test_db.query(ChatSession).filter(
            ChatSession.user_id == user.id
        ).count() == session_count
        assert test_db.query(ChatMessage).filter(
            ChatMessage.session_id.in_(session_ids)
        ).count() == session_count * messages_per_session
        
        # Delete user (load with noload for non-existent relationships)
        from sqlalchemy.orm import noload
        user_obj = test_db.query(User).options(
            noload(User.crisis_events),
            noload(User.notifications)
        ).filter(User.id == user.id).first()
        test_db.delete(user_obj)
        test_db.commit()
        
        # Property assertion: All related data must be deleted
        assert test_db.query(User).filter(User.id == user.id).count() == 0, \
            "User should be deleted"
        
        assert test_db.query(ChatSession).filter(
            ChatSession.id.in_(session_ids)
        ).count() == 0, \
            "All sessions should be cascade deleted"
        
        assert test_db.query(ChatMessage).filter(
            ChatMessage.id.in_(message_ids)
        ).count() == 0, \
            "All messages should be cascade deleted"
    
    @given(
        messages_in_session=st.integers(min_value=1, max_value=30)
    )
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_cascade_delete_session_removes_messages(
        self,
        test_db: Session,
        sample_user: User,
        messages_in_session: int
    ):
        """
        Property: Deleting a session cascades to delete all its messages.
        
        Given: A session with N messages
        When: The session is deleted
        Then: All messages in that session MUST be deleted
        """
        # Create session
        session = ChatSession(
            user_id=sample_user.id,
            title="Test Session for Cascade",
            tag="General"
        )
        test_db.add(session)
        test_db.flush()
        
        message_ids = []
        
        # Create messages
        for i in range(messages_in_session):
            message = ChatMessage(
                session_id=session.id,
                sender="user" if i % 2 == 0 else "ai",
                text=f"Message {i}"
            )
            test_db.add(message)
            test_db.flush()
            message_ids.append(message.id)
        
        test_db.commit()
        
        # Verify messages exist
        assert test_db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).count() == messages_in_session
        
        # Delete session
        test_db.delete(session)
        test_db.commit()
        
        # Property assertion: All messages must be deleted
        assert test_db.query(ChatSession).filter(
            ChatSession.id == session.id
        ).count() == 0, \
            "Session should be deleted"
        
        assert test_db.query(ChatMessage).filter(
            ChatMessage.id.in_(message_ids)
        ).count() == 0, \
            "All messages should be cascade deleted"
    
    @given(
        user_count=st.integers(min_value=2, max_value=5),
        sessions_per_user=st.integers(min_value=1, max_value=3)
    )
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_cascade_delete_preserves_other_users_data(
        self,
        test_db: Session,
        user_count: int,
        sessions_per_user: int
    ):
        """
        Property: Cascade deletion only affects the deleted user's data.
        
        Given: Multiple users each with their own sessions and messages
        When: One user is deleted
        Then: Only that user's data is deleted; other users' data remains intact
        """
        users_data = []
        
        # Create multiple users with sessions
        for user_idx in range(user_count):
            import uuid
            unique_id = str(uuid.uuid4())[:8]
            user = User(
                email=f"user{user_idx}_{unique_id}@example.com",
                name=f"User {user_idx}",
                username=f"user{user_idx}_{unique_id}",
                password="hashed_password"
            )
            test_db.add(user)
            test_db.flush()
            
            session_ids = []
            for session_idx in range(sessions_per_user):
                session = ChatSession(
                    user_id=user.id,
                    title=f"User {user_idx} Session {session_idx}",
                    tag="General"
                )
                test_db.add(session)
                test_db.flush()
                session_ids.append(session.id)
                
                # Add a message to each session
                message = ChatMessage(
                    session_id=session.id,
                    sender="user",
                    text=f"User {user_idx} Session {session_idx} Message"
                )
                test_db.add(message)
            
            users_data.append((user.id, session_ids))
        
        test_db.commit()
        
        # Delete the first user
        user_to_delete_id = users_data[0][0]
        deleted_session_ids = users_data[0][1]
        
        # Delete the first user (load with noload for non-existent relationships)
        from sqlalchemy.orm import noload
        user_to_delete = test_db.query(User).options(
            noload(User.crisis_events),
            noload(User.notifications)
        ).filter(User.id == user_to_delete_id).first()
        test_db.delete(user_to_delete)
        test_db.commit()
        
        # Property assertion: Deleted user's data is gone
        assert test_db.query(User).filter(User.id == user_to_delete_id).count() == 0
        assert test_db.query(ChatSession).filter(
            ChatSession.id.in_(deleted_session_ids)
        ).count() == 0
        
        # Property assertion: Other users' data remains intact
        for user_id, session_ids in users_data[1:]:
            assert test_db.query(User).filter(User.id == user_id).count() == 1, \
                f"User {user_id} should still exist"
            
            assert test_db.query(ChatSession).filter(
                ChatSession.id.in_(session_ids)
            ).count() == len(session_ids), \
                f"User {user_id} sessions should still exist"
            
            for session_id in session_ids:
                assert test_db.query(ChatMessage).filter(
                    ChatMessage.session_id == session_id
                ).count() == 1, \
                    f"Messages for session {session_id} should still exist"
