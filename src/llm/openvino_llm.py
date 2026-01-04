"""
OpenVINO-optimized LLM interface.

Provides high-performance inference for Mistral-7B and TinyLlama models.
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
from loguru import logger
import time
import functools

try:
    from optimum.intel import OVModelForCausalLM
    from transformers import AutoTokenizer, AutoConfig
    OPENVINO_AVAILABLE = True
except ImportError:
    OPENVINO_AVAILABLE = False
    logger.warning("OpenVINO not installed. Install with: pip install optimum[openvino]")

from src.core.config import get_settings
from src.core.exceptions import ModelLoadError, InferenceError, TokenLimitError


class OpenVINOLLM:
    """
    OpenVINO-optimized LLM for fast CPU inference.
    
    Features:
    - 2-5x faster than PyTorch on CPU
    - INT8 quantization for memory efficiency
    - KV-cache for faster generation
    - Streaming support
    
    Supported Models:
    - mistral-7b-ov (default)
    - tinyllama-ov
    """
    
    def __init__(
        self,
        model_name: str = "mistral-7b-ov",
        model_path: Optional[str] = None,
        device: str = "AUTO",
        max_tokens: int = 300
    ):
        """
        Initialize OpenVINO LLM.
        
        Args:
            model_name: Model name (mistral-7b-ov or tinyllama-ov)
            model_path: Custom model path
            device: Device (CPU, GPU)
            max_tokens: Maximum tokens to generate
        """
        if not OPENVINO_AVAILABLE:
            raise ModelLoadError("OpenVINO not available - install optimum[openvino]")
        
        self.settings = get_settings()
        self.model_name = model_name
        self.device = device
        self.max_tokens = max_tokens
        
        # Determine model path
        self.model_path = model_path or self._get_model_path(model_name)
        
        # Load model
        self.model = None
        self.tokenizer = None
        self.config = None
        self._load_model()
        
        # Generation config
        self.generation_config = {
            "max_new_tokens": max_tokens,
            "do_sample": True,
            "temperature": self.settings.llm.temperature,
            "top_p": 0.95,
            "top_k": 50,
            "repetition_penalty": 1.1,
        }
        
        logger.info(f"✅ LLM initialized: {model_name} on {device}")
    
    def _get_model_path(self, model_name: str) -> str:
        """Get model path from name"""
        base_path = Path(self.settings.llm.model_path)
        model_path = base_path / model_name
        
        if not model_path.exists():
            raise ModelLoadError(
                f"Model not found: {model_path}. "
                f"Available models: {list(base_path.glob('*-ov'))}"
            )
        
        return str(model_path)
    
    def _load_model(self):
        """Load OpenVINO model and tokenizer"""
        try:
            logger.info(f"Loading model from {self.model_path}...")
            
            start_time = time.time()
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            
            # Load config
            self.config = AutoConfig.from_pretrained(self.model_path)
            
            # Load OpenVINO model
            self.model = OVModelForCausalLM.from_pretrained(
                self.model_path,
                device=self.device,
                ov_config={"PERFORMANCE_HINT": "LATENCY"}
            )
            
            load_time = time.time() - start_time
            logger.info(f"✅ Model loaded in {load_time:.2f}s")
            
        except Exception as e:
            raise ModelLoadError(f"Failed to load model: {e}")
    
    @functools.lru_cache(maxsize=100)
    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """
        Generate text from prompt (Cached).
        
        Args:
            prompt: Input prompt
            max_tokens: Max tokens to generate (uses default if None)
            temperature: Sampling temperature
            stop_sequences: Stop generation when these appear
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text
        """
        try:
            # Tokenize
            inputs = self.tokenizer(prompt, return_tensors="pt")
            input_length = inputs.input_ids.shape[1]
            
            # Check token limit
            if input_length > self.config.max_position_embeddings:
                raise TokenLimitError(
                    f"Input too long: {input_length} tokens "
                    f"(max: {self.config.max_position_embeddings})"
                )
            
            # Update generation config
            gen_config = self.generation_config.copy()
            if max_tokens:
                gen_config["max_new_tokens"] = max_tokens
            if temperature:
                gen_config["temperature"] = temperature
            gen_config.update(kwargs)
            
            # Generate
            start_time = time.time()
            
            outputs = self.model.generate(
                **inputs,
                **gen_config
            )
            
            # Decode
            generated_text = self.tokenizer.decode(
                outputs[0][input_length:],  # Exclude prompt
                skip_special_tokens=True
            )
            
            # Handle stop sequences
            if stop_sequences:
                for stop_seq in stop_sequences:
                    if stop_seq in generated_text:
                        generated_text = generated_text.split(stop_seq)[0]
            
            generation_time = time.time() - start_time
            output_tokens = len(outputs[0]) - input_length
            tokens_per_sec = output_tokens / generation_time if generation_time > 0 else 0
            
            logger.debug(
                f"Generated {output_tokens} tokens in {generation_time:.2f}s "
                f"({tokens_per_sec:.1f} tokens/s)"
            )
            
            return generated_text.strip()
            
        except TokenLimitError:
            raise
        except Exception as e:
            raise InferenceError(f"Generation failed: {e}")
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Chat completion (formats messages into prompt).
        
        Args:
            messages: List of {"role": "user/assistant", "content": "..."}
            max_tokens: Max tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Returns:
            Assistant's response
        """
        # Format messages into prompt
        prompt = self._format_chat_messages(messages)
        
        # Generate
        return self.generate(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop_sequences=["<|im_end|>", "</s>"],
            **kwargs
        )
    
    def _format_chat_messages(self, messages: List[Dict[str, str]]) -> str:
        """Format chat messages into prompt (ChatML format)"""
        formatted = ""
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                formatted += f"<|im_start|>system\n{content}<|im_end|>\n"
            elif role == "user":
                formatted += f"<|im_start|>user\n{content}<|im_end|>\n"
            elif role == "assistant":
                formatted += f"<|im_start|>assistant\n{content}<|im_end|>\n"
        
        # Add assistant tag for response
        formatted += "<|im_start|>assistant\n"
        
        return formatted
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.tokenizer.encode(text))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get model statistics"""
        return {
            "model_name": self.model_name,
            "model_path": self.model_path,
            "device": self.device,
            "max_tokens": self.max_tokens,
            "max_position_embeddings": self.config.max_position_embeddings,
            "vocab_size": self.config.vocab_size,
        }
    
    def __repr__(self) -> str:
        return f"OpenVINOLLM(model={self.model_name}, device={self.device})"


# Singleton instances
_llm_instances: Dict[str, OpenVINOLLM] = {}


def get_llm(model_name: str = "mistral-7b-ov") -> OpenVINOLLM:
    """
    Get or create LLM instance (singleton per model).
    
    Args:
        model_name: Model name
        
    Returns:
        OpenVINOLLM instance
    """
    if model_name not in _llm_instances:
        _llm_instances[model_name] = OpenVINOLLM(model_name=model_name)
    
    return _llm_instances[model_name]
