"""Utilities for analyzing and generating element selectors."""
from typing import List, Dict, Optional, Tuple
import re
from bs4 import BeautifulSoup
from collections import Counter

# CRITICAL: These functions analyze HTML structure for selector generation
# TODO(future): Add machine learning-based pattern recognition
# CHECK(periodic): Review selector accuracy

class SelectorPattern:
    """Class for analyzing and generating element selectors."""
    
    def __init__(self, html: str):
        """Initialize with HTML content."""
        self.soup = BeautifulSoup(html, 'html.parser')
        self.common_patterns: Dict[str, List[str]] = {}
    
    def analyze_element(self, element) -> Dict[str, str]:
        """Analyze an element and return its attributes."""
        attributes = {
            'tag': element.name,
            'id': element.get('id', ''),
            'classes': ' '.join(element.get('class', [])),
            'attributes': {
                k: v for k, v in element.attrs.items()
                if k not in ['class', 'id', 'style']
            }
        }
        return attributes
    
    def generate_selector(self, element, unique: bool = True) -> str:
        """Generate a CSS selector for an element."""
        selectors = []
        
        # Try ID
        if element.get('id'):
            return f"#{element['id']}"
        
        # Try classes
        classes = element.get('class', [])
        if classes:
            class_selector = '.'.join(classes)
            selectors.append(f"{element.name}.{class_selector}")
        
        # Try data attributes
        for attr, value in element.attrs.items():
            if attr.startswith('data-'):
                selectors.append(f"{element.name}[{attr}='{value}']")
        
        # Try position-based selector if needed
        if not selectors or not unique:
            parent = element.parent
            if parent:
                siblings = parent.find_all(element.name, recursive=False)
                if len(siblings) > 1:
                    index = siblings.index(element) + 1
                    selectors.append(f"{element.name}:nth-child({index})")
        
        return selectors[0] if selectors else element.name
    
    def find_common_patterns(self, elements: List) -> List[str]:
        """Find common patterns among similar elements."""
        patterns = []
        
        if not elements:
            return patterns
        
        # Analyze common attributes
        attributes = [self.analyze_element(el) for el in elements]
        
        # Check for common classes
        class_patterns = Counter()
        for attr in attributes:
            classes = attr['classes'].split()
            for cls in classes:
                class_patterns[cls] += 1
        
        common_classes = [
            cls for cls, count in class_patterns.items()
            if count >= len(elements) * 0.8  # 80% threshold
        ]
        
        if common_classes:
            patterns.append(
                f"{attributes[0]['tag']}.{'.'.join(sorted(common_classes))}"
            )
        
        # Check for common data attributes
        data_attrs = Counter()
        for attr in attributes:
            for k, v in attr['attributes'].items():
                if k.startswith('data-'):
                    data_attrs[k] += 1
        
        common_data_attrs = [
            attr for attr, count in data_attrs.items()
            if count >= len(elements) * 0.8
        ]
        
        if common_data_attrs:
            patterns.append(
                f"{attributes[0]['tag']}[{common_data_attrs[0]}]"
            )
        
        return patterns
    
    def suggest_selectors(self, sample_element) -> List[Dict[str, str]]:
        """Suggest multiple selector options for an element."""
        suggestions = []
        
        # Basic selector
        basic_selector = self.generate_selector(sample_element, unique=False)
        suggestions.append({
            'selector': basic_selector,
            'type': 'basic',
            'description': 'Simple element selector'
        })
        
        # Unique selector
        unique_selector = self.generate_selector(sample_element, unique=True)
        suggestions.append({
            'selector': unique_selector,
            'type': 'unique',
            'description': 'Unique element selector'
        })
        
        # Find similar elements
        similar_elements = self.soup.find_all(sample_element.name)
        if len(similar_elements) > 1:
            patterns = self.find_common_patterns(similar_elements)
            for pattern in patterns:
                suggestions.append({
                    'selector': pattern,
                    'type': 'pattern',
                    'description': 'Pattern-based selector for similar elements'
                })
        
        return suggestions
    
    def analyze_page_structure(self) -> Dict[str, any]:
        """Analyze the overall page structure."""
        analysis = {
            'elements': {
                tag: len(self.soup.find_all(tag))
                for tag in ['div', 'p', 'a', 'img', 'span', 'ul', 'li']
            },
            'patterns': {},
            'recommendations': []
        }
        
        # Analyze common patterns
        for tag in analysis['elements']:
            elements = self.soup.find_all(tag)
            if elements:
                patterns = self.find_common_patterns(elements)
                if patterns:
                    analysis['patterns'][tag] = patterns
        
        # Generate recommendations
        if analysis['patterns']:
            for tag, patterns in analysis['patterns'].items():
                analysis['recommendations'].append({
                    'element_type': tag,
                    'suggested_selectors': patterns,
                    'confidence': self._calculate_confidence(patterns)
                })
        
        return analysis
    
    def _calculate_confidence(self, patterns: List[str]) -> float:
        """Calculate confidence score for pattern suggestions."""
        if not patterns:
            return 0.0
        
        # Base confidence on pattern specificity and consistency
        confidence = 0.0
        
        for pattern in patterns:
            # More specific selectors get higher confidence
            if '#' in pattern:
                confidence += 1.0
            elif '[data-' in pattern:
                confidence += 0.8
            elif '.' in pattern:
                confidence += 0.6
            else:
                confidence += 0.3
            
            # Adjust for potential uniqueness
            elements = self.soup.select(pattern)
            if elements:
                uniqueness = 1.0 / len(elements)
                confidence += uniqueness
        
        return min(confidence / len(patterns), 1.0)
