"""Few-shot learning examples for Nimbus Prompts Support.

This script demonstrates the few-shot learning capabilities:
- Adding examples to templates
- Different example selection strategies (fixed, random, semantic)
- Custom example formatting templates
- Dynamic example selection based on input
"""

from nimbus.prompts import MockPromptBuilder


def basic_few_shot_example():
    """Demonstrate basic few-shot learning with fixed examples."""
    print("=== Basic Few-Shot Learning ===")
    
    builder = MockPromptBuilder()
    
    # Register a template for named entity recognition
    builder.register_template(
        name="ner",
        template="""Extract named entities from the following text.

Examples:
{examples}

Text: {text}
Entities:"""
    )
    
    # Add few-shot examples
    examples = [
        {
            "text": "Alice works at Google in Mountain View.",
            "entities": "PERSON: Alice, ORG: Google, LOC: Mountain View"
        },
        {
            "text": "Bob visited Paris last summer.",
            "entities": "PERSON: Bob, LOC: Paris, TIME: last summer"
        },
        {
            "text": "Microsoft was founded by Bill Gates.",
            "entities": "ORG: Microsoft, PERSON: Bill Gates"
        }
    ]
    
    builder.add_examples("ner", examples)
    
    # Render with new input
    messages = builder.render("ner", {
        "text": "Sarah joined Apple in Cupertino yesterday."
    })
    
    print(f"Few-shot NER prompt:\n{messages[0].content}")
    print()


def custom_example_template():
    """Demonstrate custom example formatting."""
    print("=== Custom Example Template ===")
    
    builder = MockPromptBuilder()
    
    # Register template for sentiment analysis
    builder.register_template(
        name="sentiment",
        template="""Classify the sentiment of the following text as positive, negative, or neutral.

{examples}

Text: "{text}"
Sentiment:"""
    )
    
    # Add examples with custom formatting template
    examples = [
        {
            "text": "I love this product!",
            "sentiment": "positive"
        },
        {
            "text": "This is terrible quality.",
            "sentiment": "negative"
        },
        {
            "text": "The weather is okay today.",
            "sentiment": "neutral"
        }
    ]
    
    # Custom example template
    example_template = 'Text: "{text}" → Sentiment: {sentiment}'
    
    builder.add_examples("sentiment", examples, example_template)
    
    # Render with new input
    messages = builder.render("sentiment", {
        "text": "The movie was absolutely fantastic!"
    })
    
    print(f"Sentiment analysis with custom formatting:\n{messages[0].content}")
    print()


def example_selection_strategies():
    """Demonstrate different example selection strategies."""
    print("=== Example Selection Strategies ===")
    
    builder = MockPromptBuilder()
    
    # Register template for text classification
    builder.register_template(
        name="classify",
        template="""Classify the following text into one of these categories: technology, sports, politics, entertainment.

Examples:
{examples}

Text: {text}
Category:"""
    )
    
    # Add many examples
    examples = [
        {"text": "New iPhone released with advanced AI features", "category": "technology"},
        {"text": "Local team wins championship game", "category": "sports"},
        {"text": "Election results announced yesterday", "category": "politics"},
        {"text": "Celebrity couple announces engagement", "category": "entertainment"},
        {"text": "Breakthrough in quantum computing achieved", "category": "technology"},
        {"text": "Olympic records broken in swimming", "category": "sports"},
        {"text": "New policy on healthcare proposed", "category": "politics"},
        {"text": "Movie wins multiple awards at festival", "category": "entertainment"},
    ]
    
    builder.add_examples("classify", examples)
    
    # Test different selection strategies
    strategies = ["fixed", "random", "semantic"]
    
    for strategy in strategies:
        print(f"--- {strategy.title()} Selection ---")
        
        builder.set_example_selector(
            "classify",
            selector_type=strategy,
            max_examples=3
        )
        
        messages = builder.render("classify", {
            "text": "Scientists develop new machine learning algorithm"
        })
        
        print(f"Selected examples with {strategy} strategy:")
        print(messages[0].content[:200] + "..." if len(messages[0].content) > 200 else messages[0].content)
        print()


def dynamic_example_selection():
    """Demonstrate dynamic example selection based on input similarity."""
    print("=== Dynamic Example Selection ===")
    
    builder = MockPromptBuilder()
    
    # Register template for code generation
    builder.register_template(
        name="code_gen",
        template="""Generate Python code for the given task.

Examples:
{examples}

Task: {task}
Code:"""
    )
    
    # Add programming examples
    examples = [
        {
            "task": "sort a list of numbers",
            "code": "numbers.sort()"
        },
        {
            "task": "read a file",
            "code": "with open('file.txt', 'r') as f:\n    content = f.read()"
        },
        {
            "task": "make HTTP request",
            "code": "import requests\nresponse = requests.get('https://api.example.com')"
        },
        {
            "task": "parse JSON data",
            "code": "import json\ndata = json.loads(json_string)"
        },
        {
            "task": "create a dictionary",
            "code": "my_dict = {'key': 'value'}"
        }
    ]
    
    builder.add_examples("code_gen", examples)
    
    # Configure semantic selection (mock implementation will use fixed selection)
    builder.set_example_selector(
        "code_gen",
        selector_type="semantic",
        max_examples=2,
        similarity_threshold=0.7
    )
    
    # Test with different inputs
    test_tasks = [
        "create a list",
        "send HTTP POST request",
        "write to a file"
    ]
    
    for task in test_tasks:
        print(f"Task: {task}")
        messages = builder.render("code_gen", {"task": task})
        
        # Extract just the examples part for brevity
        content = messages[0].content
        examples_start = content.find("Examples:")
        examples_end = content.find("Task:")
        if examples_start != -1 and examples_end != -1:
            examples_section = content[examples_start:examples_end].strip()
            print(f"Selected examples:\n{examples_section}")
        print()


def few_shot_with_metadata():
    """Demonstrate few-shot learning with example metadata."""
    print("=== Few-Shot with Metadata ===")
    
    builder = MockPromptBuilder()
    
    # Register template for question answering
    builder.register_template(
        name="qa",
        template="""Answer the question based on the given context.

Examples:
{examples}

Context: {context}
Question: {question}
Answer:"""
    )
    
    # Add examples with metadata
    examples = [
        {
            "context": "The capital of France is Paris. It has a population of over 2 million.",
            "question": "What is the capital of France?",
            "answer": "Paris",
            "difficulty": "easy",
            "domain": "geography"
        },
        {
            "context": "Photosynthesis is the process by which plants convert sunlight into energy.",
            "question": "How do plants make energy?",
            "answer": "Through photosynthesis, converting sunlight into energy",
            "difficulty": "medium",
            "domain": "biology"
        }
    ]
    
    # Custom example template that includes metadata
    example_template = """Context: {context}
Question: {question}
Answer: {answer}
(Domain: {domain}, Difficulty: {difficulty})"""
    
    builder.add_examples("qa", examples, example_template)
    
    # Render with new question
    messages = builder.render("qa", {
        "context": "Water boils at 100 degrees Celsius at sea level.",
        "question": "At what temperature does water boil?"
    })
    
    print(f"Q&A with metadata:\n{messages[0].content}")
    print()


def main():
    """Run all few-shot learning examples."""
    print("Nimbus Prompts Support - Few-Shot Learning Examples")
    print("=" * 55)
    
    basic_few_shot_example()
    custom_example_template()
    example_selection_strategies()
    dynamic_example_selection()
    few_shot_with_metadata()
    
    print("All few-shot learning examples completed successfully!")


if __name__ == "__main__":
    main()