"""Test suite for multi-agent system"""
import pytest
from src.main import MultiAgentSystem
from src.models.schemas import UserAttributes


@pytest.fixture
def system():
    """Create system instance for testing"""
    return MultiAgentSystem()


def test_user_creation(system):
    """Test user creation"""
    user_id = "test_user_1"
    user = system.create_or_get_user(user_id, {
        "preferences": {"communication_style": "casual"},
        "demographics": {"age_group": "25-35"}
    })
    
    assert user.user_id == user_id
    assert isinstance(user, UserAttributes)


def test_conversation_creation(system):
    """Test conversation creation"""
    user_id = "test_user_2"
    system.create_or_get_user(user_id)
    
    conversation_id = system.create_conversation(user_id)
    assert conversation_id is not None
    assert len(conversation_id) > 0


def test_message_processing(system):
    """Test message processing through agents"""
    user_id = "test_user_3"
    system.create_or_get_user(user_id)
    conversation_id = system.create_conversation(user_id)
    
    response = system.process_message(
        user_id=user_id,
        conversation_id=conversation_id,
        user_input="運動を始めたいのですが、何から始めればいいですか?"
    )
    
    assert response is not None
    assert len(response) > 0
    
    # Cleanup
    system.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
