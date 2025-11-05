#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm_router import chat, embed

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 llm_cli.py <command> [args]")
        print("Commands:")
        print("  chat <message> - Send chat message")
        print("  embed <text> - Generate embedding")
        print("  test - Test all providers")
        return
    
    command = sys.argv[1]
    
    if command == "chat":
        if len(sys.argv) < 3:
            print("Usage: python3 llm_cli.py chat <message>")
            return
            
        message = " ".join(sys.argv[2:])
        print(f"🤖 Provider: {os.getenv('MODEL_PROVIDER', 'bedrock')}")
        print(f"💬 Message: {message}")
        
        response = chat(message)
        print(f"🎯 Response: {response}")
        
    elif command == "embed":
        if len(sys.argv) < 3:
            print("Usage: python3 llm_cli.py embed <text>")
            return
            
        text = " ".join(sys.argv[2:])
        print(f"📊 Provider: {os.getenv('MODEL_PROVIDER', 'bedrock')}")
        print(f"📝 Text: {text}")
        
        embedding = embed(text)
        print(f"🔢 Embedding: [{embedding[0]:.4f}, {embedding[1]:.4f}, ...] (dim: {len(embedding)})")
        
    elif command == "test":
        print("🧪 Testing all LLM providers...")
        
        providers = ["bedrock", "openai", "deepseek"]
        test_message = "Hello, how are you?"
        
        for provider in providers:
            print(f"\n🔄 Testing {provider}...")
            os.environ["MODEL_PROVIDER"] = provider
            
            try:
                response = chat(test_message)
                if response.startswith(f"{provider.title()} error:"):
                    print(f"❌ {provider}: {response}")
                else:
                    print(f"✅ {provider}: {response[:100]}...")
            except Exception as e:
                print(f"❌ {provider}: Exception - {e}")
        
        # Reset to default
        os.environ["MODEL_PROVIDER"] = "bedrock"
        
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
