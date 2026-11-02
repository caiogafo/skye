"""Test data and sample datasets for Skye Prompts Support.

This module provides sample datasets for testing and demonstrating
the prompts support functionality, including:

- Named Entity Recognition (NER) examples
- Text classification examples  
- Question-answering examples
- Multimodal content examples
- Code generation examples

The data is provided in JSON format and can be loaded using the
utility functions in this module.
"""

import json
from pathlib import Path
from typing import Any, Dict, List


def load_test_data(filename: str) -> List[Dict[str, Any]]:
    """Load test data from a JSON file.
    
    Args:
        filename: Name of the JSON file (without extension)
        
    Returns:
        List of dictionaries containing the test data
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    data_dir = Path(__file__).parent
    file_path = data_dir / f"{filename}.json"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Test data file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_ner_examples() -> List[Dict[str, Any]]:
    """Load Named Entity Recognition examples."""
    return load_test_data("ner_examples")


def load_classification_examples() -> List[Dict[str, Any]]:
    """Load text classification examples."""
    return load_test_data("classification_examples")


def load_qa_examples() -> List[Dict[str, Any]]:
    """Load question-answering examples."""
    return load_test_data("qa_examples")


def load_multimodal_examples() -> List[Dict[str, Any]]:
    """Load multimodal content examples."""
    return load_test_data("multimodal_examples")


def load_code_examples() -> List[Dict[str, Any]]:
    """Load code generation examples."""
    return load_test_data("code_examples")


def get_sample_templates() -> Dict[str, str]:
    """Get paths to sample templates in the prompts module.
    
    Returns:
        Dictionary mapping template names to file paths
    """
    # Navigate to the prompts templates directory from test location
    templates_dir = Path(__file__).parent.parent.parent.parent / "src" / "skye" / "prompts" / "templates"
    
    templates = {}
    if templates_dir.exists():
        for template_file in templates_dir.glob("*.jinja"):
            template_name = template_file.stem
            templates[template_name] = str(template_file)
        
        # Also look for other template extensions
        for template_file in templates_dir.glob("*.txt"):
            template_name = template_file.stem
            if template_name not in templates:  # Don't override .jinja files
                templates[template_name] = str(template_file)
    
    return templates


# Convenience exports
__all__ = [
    "load_test_data",
    "load_ner_examples", 
    "load_classification_examples",
    "load_qa_examples",
    "load_multimodal_examples",
    "load_code_examples",
    "get_sample_templates",
]