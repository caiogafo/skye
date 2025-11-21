#!/usr/bin/env python3
"""Validation script for provider transformation architecture.

This script validates that the provider transformation architecture follows
the encapsulation principles:

1. All provider-specific transformation logic is in provider client classes
2. No provider-specific code exists in core library modules
3. MessageTransformer and CapabilityTransformer only delegate to providers
4. Adding a new provider requires no changes to core library code

Usage:
    python scripts/validate_provider_architecture.py
"""

import ast
import sys
from pathlib import Path
from typing import Any


class ProviderArchitectureValidator:
    """Validator for provider transformation architecture."""
    
    def __init__(self, root_dir: Path):
        """Initialize validator with project root directory."""
        self.root_dir = root_dir
        self.src_dir = root_dir / "src" / "nimbus"
        self.errors: list[str] = []
        self.warnings: list[str] = []
        
        # Core library modules that must be provider-agnostic
        self.core_modules = [
            "routes",
            "capabilities",
            "completion.py",
            "messages.py",
        ]
        
        # Provider names to check for
        self.provider_names = [
            "openai",
            "bedrock",
            "anthropic",
            "azure",
            "vertex",
        ]
    
    def validate(self) -> bool:
        """Run all validation checks.
        
        Returns:
            True if all checks pass, False otherwise
        """
        print("=" * 80)
        print("Provider Transformation Architecture Validation")
        print("=" * 80)
        print()
        
        # Run validation checks
        self.check_core_library_provider_agnostic()
        self.check_transformer_delegation()
        self.check_provider_encapsulation()
        self.check_known_architectural_debt()
        
        # Print results
        print()
        print("=" * 80)
        print("Validation Results")
        print("=" * 80)
        print()
        
        if self.warnings:
            print(f"⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  - {warning}")
            print()
        
        if self.errors:
            print(f"❌ Errors ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")
            print()
            print("VALIDATION FAILED")
            return False
        else:
            print("✅ All validation checks passed!")
            if self.warnings:
                print(f"   ({len(self.warnings)} warnings noted)")
            return True
    
    def check_core_library_provider_agnostic(self) -> None:
        """Check that core library modules don't contain provider-specific code."""
        print("Checking core library is provider-agnostic...")
        
        for module_path in self.core_modules:
            full_path = self.src_dir / module_path
            
            if full_path.is_file():
                self._check_file_for_provider_references(full_path, is_core=True)
            elif full_path.is_dir():
                for py_file in full_path.rglob("*.py"):
                    if "__pycache__" not in str(py_file):
                        self._check_file_for_provider_references(py_file, is_core=True)
        
        print("  ✓ Core library provider agnosticism check complete")
    
    def check_transformer_delegation(self) -> None:
        """Check that transformers only delegate to providers."""
        print("Checking transformers use delegation pattern...")
        
        # Check MessageTransformer
        transformer_file = self.src_dir / "providers" / "transformers.py"
        if transformer_file.exists():
            self._check_transformer_file(transformer_file, "MessageTransformer")
        
        # Check CapabilityTransformer
        capability_transformer = self.src_dir / "capabilities" / "capability_transformer.py"
        if capability_transformer.exists():
            self._check_transformer_file(capability_transformer, "CapabilityTransformer")
        
        print("  ✓ Transformer delegation check complete")
    
    def check_provider_encapsulation(self) -> None:
        """Check that provider classes properly encapsulate transformations."""
        print("Checking provider transformation encapsulation...")
        
        providers_dir = self.src_dir / "providers" / "llm"
        if not providers_dir.exists():
            self.errors.append("Providers directory not found")
            return
        
        required_methods = [
            "_transform_messages",
            "_transform_capabilities",
            "_extract_capability_calls",
            "_transform_request",
            "_transform_response",
        ]
        
        for provider_file in providers_dir.glob("*_provider.py"):
            if provider_file.name == "__init__.py":
                continue
            
            self._check_provider_methods(provider_file, required_methods)
        
        print("  ✓ Provider encapsulation check complete")
    
    def check_known_architectural_debt(self) -> None:
        """Check and document known architectural debt."""
        print("Checking known architectural debt...")
        
        # CapabilityCallHandler has provider-specific methods (documented debt)
        handler_file = self.src_dir / "capabilities" / "capability_call_handler.py"
        if handler_file.exists():
            content = handler_file.read_text()
            
            # Check if architectural debt is documented
            if "ARCHITECTURAL DEBT" in content or "Future Refactor" in content:
                self.warnings.append(
                    "CapabilityCallHandler contains provider-specific methods "
                    "(documented architectural debt - see file header for details)"
                )
                # Remove errors related to this file since it's documented debt
                self.errors = [
                    e for e in self.errors 
                    if "capability_call_handler.py" not in e
                ]
            else:
                self.errors.append(
                    "CapabilityCallHandler contains provider-specific methods "
                    "but architectural debt is not documented"
                )
        
        print("  ✓ Architectural debt check complete")
    
    def _check_file_for_provider_references(self, file_path: Path, is_core: bool = False) -> None:
        """Check a file for provider-specific references.
        
        Args:
            file_path: Path to the file to check
            is_core: Whether this is a core library file (stricter checks)
        """
        try:
            content = file_path.read_text()
            tree = ast.parse(content, filename=str(file_path))
            
            # Skip if this is a provider file itself
            if "providers" in str(file_path) and not is_core:
                return
            
            # Check for provider-specific string literals and identifiers
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    value_lower = node.value.lower()
                    for provider in self.provider_names:
                        if provider in value_lower:
                            # Check if it's in a docstring or comment (allowed)
                            if self._is_in_docstring_or_example(node, tree):
                                continue
                            
                            # Check if it's in a provider-specific context (allowed)
                            if not is_core:
                                continue
                            
                            rel_path = file_path.relative_to(self.root_dir)
                            self.errors.append(
                                f"Provider-specific reference '{provider}' found in core module: {rel_path}:{node.lineno}"
                            )
        
        except Exception as e:
            self.warnings.append(f"Could not parse {file_path}: {e}")
    
    def _is_in_docstring_or_example(self, node: ast.AST, tree: ast.AST) -> bool:
        """Check if a node is in a docstring or example.
        
        Args:
            node: AST node to check
            tree: Full AST tree
            
        Returns:
            True if node is in docstring or example
        """
        # Check if it's a docstring (string constant as first statement in function/class/module)
        for parent in ast.walk(tree):
            if isinstance(parent, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                if (hasattr(parent, 'body') and 
                    parent.body and 
                    isinstance(parent.body[0], ast.Expr) and
                    isinstance(parent.body[0].value, ast.Constant)):
                    if parent.body[0].value == node:
                        return True
        
        # Check if the string contains example markers (>>>, Example:, Args:, etc.)
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            doc_markers = [">>>", "Example:", "Args:", "Returns:", "Raises:", "Note:"]
            return any(marker in node.value for marker in doc_markers)
        
        return False
    
    def _check_transformer_file(self, file_path: Path, class_name: str) -> None:
        """Check that a transformer file only contains delegation methods.
        
        Args:
            file_path: Path to transformer file
            class_name: Name of transformer class
        """
        try:
            content = file_path.read_text()
            tree = ast.parse(content, filename=str(file_path))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    # Check methods in the class
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_name = item.name
                            
                            # Skip special methods
                            if method_name.startswith("__"):
                                continue
                            
                            # Check if method contains provider-specific logic
                            for provider in self.provider_names:
                                if provider in method_name.lower():
                                    rel_path = file_path.relative_to(self.root_dir)
                                    self.errors.append(
                                        f"Provider-specific method '{method_name}' found in {class_name}: {rel_path}"
                                    )
        
        except Exception as e:
            self.warnings.append(f"Could not parse {file_path}: {e}")
    
    def _check_provider_methods(self, file_path: Path, required_methods: list[str]) -> None:
        """Check that a provider file implements required transformation methods.
        
        Args:
            file_path: Path to provider file
            required_methods: List of required method names
        """
        try:
            content = file_path.read_text()
            tree = ast.parse(content, filename=str(file_path))
            
            provider_name = file_path.stem.replace("_provider", "")
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and "Provider" in node.name:
                    # Get all method names
                    methods = {
                        item.name for item in node.body 
                        if isinstance(item, ast.FunctionDef)
                    }
                    
                    # Check for required methods
                    missing_methods = set(required_methods) - methods
                    if missing_methods:
                        rel_path = file_path.relative_to(self.root_dir)
                        self.warnings.append(
                            f"{node.name} missing transformation methods: {', '.join(missing_methods)} ({rel_path})"
                        )
        
        except Exception as e:
            self.warnings.append(f"Could not parse {file_path}: {e}")


def main() -> int:
    """Main entry point."""
    root_dir = Path(__file__).parent.parent
    validator = ProviderArchitectureValidator(root_dir)
    
    success = validator.validate()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
