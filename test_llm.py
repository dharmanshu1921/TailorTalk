from llm import process_message
from langchain_core.messages import HumanMessage

def test_llm_processing():
    print("\nTesting valid scheduling request:")
    conversation = [
        HumanMessage(content="Schedule a meeting tomorrow at 2pm for 1 hour")
    ]
    _, response = process_message(conversation)
    print(f"Response: {response}")
    
    print("\nTesting calendar query:")
    conversation = [
        HumanMessage(content="What's on my calendar tomorrow?")
    ]
    _, response = process_message(conversation)
    print(f"Response: {response}")
    
    print("\nTesting empty input:")
    conversation = [HumanMessage(content="")]
    _, response = process_message(conversation)
    print(f"Response: {response}")

if __name__ == "__main__":
    test_llm_processing()