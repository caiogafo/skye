"""Test all prompt examples to see which ones work."""

import sys
import subprocess
from pathlib import Path

def test_example(example_file):
    """Test a single example file."""
    print(f"Testing {example_file}...")
    try:
        result = subprocess.run(
            [sys.executable, example_file],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            print(f"✓ {example_file} - SUCCESS")
            return True
        else:
            print(f"❌ {example_file} - FAILED")
            print(f"   Error: {result.stderr.strip()[:100]}...")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ {example_file} - TIMEOUT")
        return False
    except Exception as e:
        print(f"💥 {example_file} - EXCEPTION: {e}")
        return False

def main():
    """Test all example files."""
    print("Testing All Prompt Examples")
    print("=" * 40)
    
    examples_dir = Path(__file__).parent
    example_files = [
        "basic_usage.py",
        "few_shot_learning.py", 
        "message_roles.py",
        "message_roles_complete.py",
        "multimodal_content.py",
        "run_all_examples.py",
        "simple_template_demo.py",
        "template_showcase.py",
        "agent_templates_showcase.py",
        "working_agent_showcase.py",
        "simple_agent_test.py"
    ]
    
    working = []
    broken = []
    
    for example_file in example_files:
        example_path = examples_dir / example_file
        if example_path.exists():
            if test_example(example_path):
                working.append(example_file)
            else:
                broken.append(example_file)
        else:
            print(f"⚠️  {example_file} - NOT FOUND")
    
    print()
    print("=" * 40)
    print("SUMMARY")
    print("=" * 40)
    print(f"✓ Working examples ({len(working)}):")
    for example in working:
        print(f"  - {example}")
    
    print(f"\n❌ Broken examples ({len(broken)}):")
    for example in broken:
        print(f"  - {example}")
    
    print(f"\nTotal: {len(working)} working, {len(broken)} broken")

if __name__ == "__main__":
    main()