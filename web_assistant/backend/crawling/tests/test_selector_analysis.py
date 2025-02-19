"""Tests for the selector pattern analysis utility."""
from django.test import TestCase
from ..utils.selector_analysis import SelectorPattern

# CRITICAL: These tests verify pattern recognition functionality
# TODO(future): Add more complex HTML test cases
# CHECK(periodic): Review pattern detection accuracy

class TestSelectorPattern(TestCase):
    """Test cases for the SelectorPattern class."""

    def setUp(self):
        """Set up test data."""
        self.test_html = """
        <div class="container">
            <div class="item item-1" data-testid="test1">
                <h2>Item 1</h2>
                <p class="description">Description 1</p>
            </div>
            <div class="item item-2" data-testid="test2">
                <h2>Item 2</h2>
                <p class="description">Description 2</p>
            </div>
            <div class="item item-3" data-testid="test3">
                <h2>Item 3</h2>
                <p class="description">Description 3</p>
            </div>
        </div>
        """
        self.pattern = SelectorPattern(self.test_html)

    def test_analyze_element(self):
        """Test element attribute analysis."""
        soup = self.pattern.soup
        element = soup.find('div', class_='item-1')
        
        attributes = self.pattern.analyze_element(element)
        
        self.assertEqual(attributes['tag'], 'div')
        self.assertIn('item', attributes['classes'])
        self.assertIn('item-1', attributes['classes'])
        self.assertEqual(attributes['attributes']['data-testid'], 'test1')

    def test_generate_selector_with_id(self):
        """Test selector generation for element with ID."""
        html = '<div id="test-id" class="test-class">Test</div>'
        test_pattern = SelectorPattern(html)
        element = test_pattern.soup.find('div')
        
        selector = test_pattern.generate_selector(element)
        
        self.assertEqual(selector, '#test-id')

    def test_generate_selector_with_classes(self):
        """Test selector generation for element with classes."""
        soup = self.pattern.soup
        element = soup.find('div', class_='item')
        
        selector = self.pattern.generate_selector(element)
        
        self.assertTrue(selector.startswith('div.item'))

    def test_generate_selector_with_data_attribute(self):
        """Test selector generation with data attributes."""
        soup = self.pattern.soup
        element = soup.find('div', attrs={'data-testid': 'test1'})
        
        selector = self.pattern.generate_selector(element)
        
        self.assertIn('data-testid', selector)

    def test_find_common_patterns(self):
        """Test finding common patterns among elements."""
        soup = self.pattern.soup
        elements = soup.find_all('div', class_='item')
        
        patterns = self.pattern.find_common_patterns(elements)
        
        self.assertTrue(any('item' in pattern for pattern in patterns))

    def test_suggest_selectors(self):
        """Test selector suggestions for an element."""
        soup = self.pattern.soup
        element = soup.find('div', class_='item-1')
        
        suggestions = self.pattern.suggest_selectors(element)
        
        self.assertTrue(len(suggestions) > 0)
        self.assertIn('selector', suggestions[0])
        self.assertIn('type', suggestions[0])
        self.assertIn('description', suggestions[0])

    def test_analyze_page_structure(self):
        """Test page structure analysis."""
        analysis = self.pattern.analyze_page_structure()
        
        self.assertIn('elements', analysis)
        self.assertIn('patterns', analysis)
        self.assertIn('recommendations', analysis)
        self.assertTrue(analysis['elements']['div'] >= 4)  # Container + 3 items

    def test_calculate_confidence(self):
        """Test confidence score calculation."""
        patterns = [
            'div.item',
            'div[data-testid]',
            '#unique-id'
        ]
        
        confidence = self.pattern._calculate_confidence(patterns)
        
        self.assertGreater(confidence, 0)
        self.assertLessEqual(confidence, 1)

    def test_empty_html(self):
        """Test handling of empty HTML."""
        test_pattern = SelectorPattern('')
        analysis = test_pattern.analyze_page_structure()
        
        self.assertEqual(analysis['elements']['div'], 0)
        self.assertEqual(len(analysis['patterns']), 0)
        self.assertEqual(len(analysis['recommendations']), 0)

    def test_complex_selectors(self):
        """Test handling of complex nested elements."""
        html = """
        <div class="wrapper">
            <section class="content">
                <article class="post" data-category="tech">
                    <h1 class="title">Post 1</h1>
                    <div class="meta">
                        <span class="date">2024-02-17</span>
                        <span class="author">Author 1</span>
                    </div>
                </article>
                <article class="post" data-category="news">
                    <h1 class="title">Post 2</h1>
                    <div class="meta">
                        <span class="date">2024-02-17</span>
                        <span class="author">Author 2</span>
                    </div>
                </article>
            </section>
        </div>
        """
        test_pattern = SelectorPattern(html)
        
        # Test article pattern detection
        articles = test_pattern.soup.find_all('article')
        patterns = test_pattern.find_common_patterns(articles)
        self.assertTrue(any('post' in p for p in patterns))
        
        # Test nested element suggestions
        meta_div = test_pattern.soup.find('div', class_='meta')
        suggestions = test_pattern.suggest_selectors(meta_div)
        self.assertTrue(any('meta' in s['selector'] for s in suggestions))

    def test_similar_elements_with_variations(self):
        """Test pattern detection with element variations."""
        html = """
        <ul class="list">
            <li class="item active">Item 1</li>
            <li class="item">Item 2</li>
            <li class="item featured">Item 3</li>
            <li class="item active featured">Item 4</li>
        </ul>
        """
        test_pattern = SelectorPattern(html)
        
        items = test_pattern.soup.find_all('li')
        patterns = test_pattern.find_common_patterns(items)
        
        # Should detect 'item' as common class despite variations
        self.assertTrue(any('item' in p for p in patterns))
        
        # Test suggestions for varied elements
        featured_item = test_pattern.soup.find('li', class_='featured')
        suggestions = test_pattern.suggest_selectors(featured_item)
        
        # Should have both specific and general selectors
        self.assertTrue(any('featured' in s['selector'] for s in suggestions))
        self.assertTrue(any('item' in s['selector'] for s in suggestions))

    def test_attribute_pattern_detection(self):
        """Test detection of patterns in element attributes."""
        html = """
        <div class="container">
            <input type="text" data-field="name" class="input" />
            <input type="email" data-field="email" class="input" />
            <input type="tel" data-field="phone" class="input" />
        </div>
        """
        test_pattern = SelectorPattern(html)
        
        inputs = test_pattern.soup.find_all('input')
        patterns = test_pattern.find_common_patterns(inputs)
        
        # Should detect common attributes and classes
        self.assertTrue(any('data-field' in p for p in patterns))
        self.assertTrue(any('input' in p for p in patterns))
        
        # Test confidence scoring
        confidence = test_pattern._calculate_confidence(patterns)
        self.assertGreater(confidence, 0.5)  # High confidence due to consistent patterns
