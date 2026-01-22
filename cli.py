#!/usr/bin/env python3
"""CLI interface for the Multi-Agent System"""
import sys
import argparse
from typing import Optional
import json

from src.main import MultiAgentSystem
from src.utils.config import settings


def print_banner():
    """Print application banner"""
    print("""
╔══════════════════════════════════════════════════════════╗
║   Multi-Agent System with Azure OpenAI & Neo4j           ║
║   Powered by LangChain & LangGraph                       ║
╚══════════════════════════════════════════════════════════╝
""")


def interactive_mode(system: MultiAgentSystem, user_id: str):
    """Run interactive chat mode"""
    print(f"\nInteractive Mode - User ID: {user_id}")
    print("Type 'exit' or 'quit' to end the session")
    print("Type 'new' to start a new conversation")
    print("Type 'update' to update user attributes")
    print("-" * 60)
    
    conversation_id = system.create_conversation(user_id)
    print(f"Conversation ID: {conversation_id}\n")
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit']:
                print("\nThank you for using the Multi-Agent System!")
                break
            
            if user_input.lower() == 'new':
                conversation_id = system.create_conversation(user_id)
                print(f"\n✓ New conversation started: {conversation_id}\n")
                continue
            
            if user_input.lower() == 'update':
                print("\nEnter user attributes as JSON:")
                print("Example: {\"preferences\": {\"communication_style\": \"formal\"}, \"demographics\": {\"age_group\": \"30-40\"}}")
                attrs_input = input("Attributes: ").strip()
                try:
                    attrs = json.loads(attrs_input)
                    system.update_user_attributes(user_id, attrs)
                    print("\n✓ User attributes updated\n")
                except json.JSONDecodeError:
                    print("\n✗ Invalid JSON format\n")
                continue
            
            # Process message
            print("\n[Processing through multi-agent system...]")
            response = system.process_message(user_id, conversation_id, user_input)
            
            print(f"\nAssistant: {response}")
            print("-" * 60)
            
        except KeyboardInterrupt:
            print("\n\nSession interrupted.")
            break
        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()


def single_message_mode(system: MultiAgentSystem, user_id: str, message: str):
    """Process a single message"""
    conversation_id = system.create_conversation(user_id)
    print(f"\nConversation ID: {conversation_id}")
    print(f"User: {message}")
    print("\n[Processing through multi-agent system...]\n")
    
    response = system.process_message(user_id, conversation_id, message)
    print(f"Assistant: {response}\n")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Multi-Agent System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python cli.py --user user123

  # Single message
  python cli.py --user user123 --message "健康的な食事について教えてください"

  # Set user attributes
  python cli.py --user user123 --update-attrs '{"demographics": {"age": 35}}'
        """
    )
    
    parser.add_argument(
        "--user",
        type=str,
        default="default_user",
        help="User ID (default: default_user)"
    )
    
    parser.add_argument(
        "--message",
        type=str,
        help="Single message to process (instead of interactive mode)"
    )
    
    parser.add_argument(
        "--update-attrs",
        type=str,
        help="Update user attributes (JSON format)"
    )
    
    parser.add_argument(
        "--conversation",
        type=str,
        help="Existing conversation ID to continue"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    print_banner()
    
    # Initialize system
    print("Initializing Multi-Agent System...")
    print(f"Azure OpenAI Endpoint: {settings.azure_openai_endpoint.split('/')[2]}")
    print(f"Neo4j URI: {settings.neo4j_uri}")
    print()
    
    try:
        system = MultiAgentSystem()
        
        # Update user attributes if provided
        if args.update_attrs:
            try:
                attrs = json.loads(args.update_attrs)
                system.update_user_attributes(args.user, attrs)
                print(f"✓ Updated attributes for user {args.user}\n")
            except json.JSONDecodeError:
                print("✗ Invalid JSON format for attributes\n")
                return 1
        
        # Process based on mode
        if args.message:
            single_message_mode(system, args.user, args.message)
        else:
            interactive_mode(system, args.user)
        
        # Cleanup
        system.close()
        return 0
        
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        return 0
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
