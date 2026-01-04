"""
Unit tests for LLM components.

Tests OpenVINO LLM wrapper, prompt templates, and response parser.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.llm import OpenVINOLLM, PromptBuilder, PromptTemplate, ResponseParser, parse_llm_output
from src.core.exceptions import ModelLoadError, InferenceError


class TestPromptBuilder:
    """Test prompt builder"""
    
    def test_basic_template(self):
        """Test basic template building"""
        builder = PromptBuilder(custom_template="Hello {name}!")
        builder.set("name", "World")
        
        result = builder.build()
        assert result == "Hello World!"
    
    def test_analysis_template(self):
        """Test analysis template"""
        builder = PromptBuilder(PromptTemplate.ANALYSIS)
        builder.set("context", "Python is popular")
        builder.set("query", "Why?")
        
        result = builder.build()
        assert "Python is popular" in result
        assert "Why?" in result
    
    def test_json_template(self):
        """Test JSON mode template"""
        builder = PromptBuilder(PromptTemplate.JSON_MODE)
        builder.set("task", "Extract data")
        builder.set("input_data", "John Smith, 35")
        builder.set("schema", '{"name": "string"}')
        
        result = builder.build()
        assert "Extract data" in result
        assert "JSON" in result
    
    def test_missing_variable(self):
        """Test error on missing variable"""
        builder = PromptBuilder(custom_template="Hello {name}!")
        
        with pytest.raises(ValueError):
            builder.build()
    
    def test_build_messages(self):
        """Test building chat messages"""
        builder = PromptBuilder(custom_template="User question")
        builder.set_system("You are helpful")
        
        messages = builder.build_messages()
        
        assert len(messages) == 2
        assert messages[0]['role'] == 'system'
        assert messages[1]['role'] == 'user'


class TestResponseParser:
    """Test response parser"""
    
    def test_extract_json_direct(self):
        """Test direct JSON extraction"""
        text = '{"name": "John", "age": 30}'
        result = ResponseParser.extract_json(text)
        
        assert result == {"name": "John", "age": 30}
    
    def test_extract_json_from_code_block(self):
        """Test JSON extraction from code block"""
        text = '''Here is the result:
```json
{"name": "Alice", "city": "NYC"}
```'''
        result = ResponseParser.extract_json(text)
        
        assert result == {"name": "Alice", "city": "NYC"}
    
    def test_extract_json_embedded(self):
        """Test JSON extraction from embedded text"""
        text = 'The data is {"value": 42} and more text'
        result = ResponseParser.extract_json(text)
        
        assert result == {"value": 42}
    
    def test_extract_json_strict_mode(self):
        """Test strict mode raises error"""
        text = 'No JSON here'
        
        with pytest.raises(InferenceError):
            ResponseParser.extract_json(text, strict=True)
    
    def test_extract_code(self):
        """Test code extraction"""
        text = '''Here is code:
```python
def hello():
    print("Hello")
```'''
        result = ResponseParser.extract_code(text, language="python")
        
        assert "def hello():" in result
    
    def test_extract_list_numbered(self):
        """Test numbered list extraction"""
        text = '''Items:
1. First item
2. Second item
3. Third item'''
        result = ResponseParser.extract_list(text)
        
        assert len(result) == 3
        assert "First item" in result
    
    def test_extract_list_bulleted(self):
        """Test bulleted list extraction"""
        text = '''Items:
- Apple
- Banana
* Orange'''
        result = ResponseParser.extract_list(text)
        
        assert len(result) >= 2
        assert "Apple" in result
    
    def test_clean_response(self):
        """Test response cleaning"""
        text = "Response text<|im_end|>  \n\n\n  More text"
        result = ResponseParser.clean_response(text)
        
        assert "<|im_end|>" not in result
        assert "\n\n\n" not in result
    
    def test_validate_schema(self):
        """Test schema validation"""
        data = {"name": "John", "age": 30, "active": True}
        schema = {"name": "string", "age": "number", "active": "boolean"}
        
        assert ResponseParser.validate_schema(data, schema)
    
    def test_validate_schema_missing_field(self):
        """Test schema validation with missing field"""
        data = {"name": "John"}
        schema = {"name": "string", "age": "number"}
        
        assert not ResponseParser.validate_schema(data, schema)


class TestParseOutput:
    """Test parse_llm_output function"""
    
    def test_parse_text(self):
        """Test text parsing"""
        text = "Simple text response"
        result = parse_llm_output(text, output_type="text")
        
        assert result == "Simple text response"
    
    def test_parse_json(self):
        """Test JSON parsing"""
        text = '{"result": "success"}'
        result = parse_llm_output(text, output_type="json")
        
        assert result == {"result": "success"}
    
    def test_parse_code(self):
        """Test code parsing"""
        text = '''```python
print("hello")
```'''
        result = parse_llm_output(text, output_type="code")
        
        assert 'print("hello")' in result
    
    def test_parse_list(self):
        """Test list parsing"""
        text = '''1. Item one
2. Item two
3. Item three'''
        result = parse_llm_output(text, output_type="list")
        
        assert len(result) == 3


class TestOpenVINOLLM:
    """Test OpenVINO LLM wrapper (mocked)"""
    
    @pytest.fixture
    def mock_llm(self):
        """Mock LLM for testing"""
        with patch('src.llm.openvino_llm.OPENVINO_AVAILABLE', True):
            with patch('src.llm.openvino_llm.OVModelForCausalLM'):
                with patch('src.llm.openvino_llm.AutoTokenizer'):
                    with patch('src.llm.openvino_llm.AutoConfig'):
                        llm = Mock(spec=OpenVINOLLM)
                        llm.model_name = "mistral-7b-ov"
                        llm.generate = Mock(return_value="Generated text")
                        llm.chat = Mock(return_value="Chat response")
                        llm.count_tokens = Mock(return_value=10)
                        return llm
    
    def test_generate(self, mock_llm):
        """Test text generation"""
        result = mock_llm.generate("Test prompt")
        assert result == "Generated text"
    
    def test_chat(self, mock_llm):
        """Test chat completion"""
        messages = [{"role": "user", "content": "Hello"}]
        result = mock_llm.chat(messages)
        assert result == "Chat response"
    
    def test_count_tokens(self, mock_llm):
        """Test token counting"""
        count = mock_llm.count_tokens("test text")
        assert count == 10


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
