#!/usr/bin/env python3
"""
Interactive Chat Interface for TTS Assistant
Text-based interface for testing and debugging the TTS assistant
"""

import sys
import time
import threading
from pathlib import Path

# Load environment variables before importing assistant
from dotenv import load_dotenv
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / '.env')

from tts_assistant import TTSAssistant

class InteractiveChat:
    """Interactive chat interface for testing the TTS assistant"""
    
    def __init__(self):
        self.assistant = TTSAssistant()
        self.running = True
        self.auto_commentary = False
        self.commentary_interval = 30  # seconds
        self.commentary_thread = None
    
    def start_auto_commentary(self):
        """Start automatic commentary in background thread"""
        if self.commentary_thread and self.commentary_thread.is_alive():
            return
        
        self.auto_commentary = True
        self.commentary_thread = threading.Thread(target=self._commentary_loop, daemon=True)
        self.commentary_thread.start()
        print(f"🤖 Auto-commentary started (every {self.commentary_interval}s)")
    
    def stop_auto_commentary(self):
        """Stop automatic commentary"""
        self.auto_commentary = False
        print("🤖 Auto-commentary stopped")
    
    def _commentary_loop(self):
        """Background loop for automatic commentary"""
        while self.running and self.auto_commentary:
            time.sleep(self.commentary_interval)
            
            if self.auto_commentary:  # Check again in case it was disabled
                commentary = self.assistant.provide_game_commentary()
                if commentary:
                    print(f"\n💬 [{self.assistant.personality.name}]: {commentary}")
                    print("You: ", end="", flush=True)
    
    def show_help(self):
        """Show available commands"""
        print("""
=== TTS Assistant Chat Commands ===
/help          - Show this help message
/personality   - Show current personality details
/reset         - Generate new personality (restart assistant)
/commentary    - Toggle automatic commentary on/off
/status        - Show assistant status and game data
/game          - Request game commentary
/logs          - View recent chat logs
/quit          - Exit the chat

Type anything else to chat with your assistant!
=======================================""")
    
    def show_personality(self):
        """Show current personality details"""
        p = self.assistant.personality
        print(f"""
=== Current Assistant ===
Name: {p.name}
Type: {p.personality_type}
Traits: {', '.join(p.traits)}
Backstory: {p.backstory}
Voice Style: {p.voice_style}
Response Style: {p.response_style}

Quirks:
""")
        for quirk in p.quirks:
            print(f"  - {quirk}")
        
        print(f"\nSample Catchphrases:")
        for phrase in p.catchphrases[:5]:
            print(f'  - "{phrase}"')
        print("=" * 30)
    
    def show_status(self):
        """Show assistant and game status"""
        print(f"\n=== Assistant Status ===")
        print(f"Name: {self.assistant.personality.name}")
        print(f"AI Client: {self.assistant.ai_client.__class__.__name__ if self.assistant.ai_client else 'None'}")
        print(f"AI Available: {self.assistant.ai_client is not None}")
        print(f"Game Data Loaded: {self.assistant.current_game_data is not None}")
        print(f"Conversation History: {len(self.assistant.conversation_history)} exchanges")
        print(f"Recent Changes: {len(self.assistant.notable_changes)} tracked")
        print(f"Auto Commentary: {'ON' if self.auto_commentary else 'OFF'}")
        print(f"Personality File: {self.assistant.personality_file}")
        print(f"Chat Log: {self.assistant.chat_log_file}")
        print(f"Prompt Log: {self.assistant.prompt_log_file}")
        
        if self.assistant.current_game_data:
            game_summary = self.assistant.get_game_context_summary()
            print(f"Game Context: {game_summary}")
        
        print("=" * 30)
    
    def request_game_commentary(self):
        """Request immediate game commentary"""
        print(f"🎮 Checking game state...")
        commentary = self.assistant.provide_game_commentary()
        
        if commentary:
            print(f"[{self.assistant.personality.name}]: {commentary}")
        else:
            print("No commentary available right now.")
    
    def show_recent_logs(self):
        """Show recent chat logs"""
        try:
            if self.assistant.chat_log_file.exists():
                with open(self.assistant.chat_log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Show last 50 lines
                recent_lines = lines[-50:] if len(lines) > 50 else lines
                print("\n=== Recent Chat Log (last 50 lines) ===")
                for line in recent_lines:
                    print(line.rstrip())
                print("=" * 40)
            else:
                print("No chat log file found yet.")
                
        except Exception as e:
            print(f"Error reading chat log: {e}")
    
    def run(self):
        """Run the interactive chat session"""
        print(f"=== TTS Assistant Interactive Chat ===")
        print(f"Connected to: {self.assistant.personality.name} ({self.assistant.personality.personality_type})")
        print(f'Backstory: {self.assistant.personality.backstory}')
        print(f'Sample phrase: "{self.assistant.personality.catchphrases[0]}"')
        print("\nType '/help' for commands or start chatting!")
        print("=" * 50)
        
        try:
            while self.running:
                try:
                    user_input = input("You: ").strip()
                    
                    if not user_input:
                        continue
                    
                    # Handle commands
                    if user_input.startswith('/'):
                        command = user_input.lower()
                        
                        if command == '/help':
                            self.show_help()
                        elif command == '/personality':
                            self.show_personality()
                        elif command == '/reset':
                            print("🔄 Generating new personality...")
                            self.assistant.reset_personality()
                            print(f"New assistant: {self.assistant.personality.name} ({self.assistant.personality.personality_type})")
                        elif command == '/commentary':
                            if self.auto_commentary:
                                self.stop_auto_commentary()
                            else:
                                self.start_auto_commentary()
                        elif command == '/status':
                            self.show_status()
                        elif command == '/game':
                            self.request_game_commentary()
                        elif command == '/logs':
                            self.show_recent_logs()
                        elif command == '/quit':
                            print(f"👋 [{self.assistant.personality.name}]: Auf Wiedersehen!")
                            self.running = False
                            break
                        else:
                            print(f"Unknown command: {user_input}")
                            print("Type '/help' for available commands")
                        
                        continue
                    
                    # Regular chat
                    print(f"🤔 [{self.assistant.personality.name}] is thinking...")
                    
                    start_time = time.time()
                    response = self.assistant.respond_to_user(user_input)
                    response_time = time.time() - start_time
                    
                    print(f"[{self.assistant.personality.name}]: {response}")
                    print(f"⏱️ Response time: {response_time:.1f}s")
                    
                except KeyboardInterrupt:
                    print(f"\n👋 [{self.assistant.personality.name}]: Goodbye!")
                    self.running = False
                    break
                except EOFError:
                    print(f"\n👋 [{self.assistant.personality.name}]: Farewell!")
                    self.running = False
                    break
        
        finally:
            self.running = False
            if self.auto_commentary:
                self.stop_auto_commentary()

def main():
    """Main entry point"""
    print("Loading TTS Assistant...")
    
    try:
        chat = InteractiveChat()
        chat.run()
    except Exception as e:
        print(f"Error starting chat: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()