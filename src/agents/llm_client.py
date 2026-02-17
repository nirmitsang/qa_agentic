# src/agents/llm_client.py
"""
Unified LLM client supporting both AWS Bedrock and Google Gemini.
Dispatches based on settings.llm_provider.
"""

import json
import time
import logging
from dataclasses import dataclass
from typing import Optional

import boto3
from botocore.exceptions import ClientError

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from src.config.settings import settings


logger = logging.getLogger(__name__)


# ============================================================================
# RESPONSE DATACLASS
# ============================================================================

@dataclass
class LLMResponse:
    """Unified response from any LLM provider."""
    content: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    trace_name: str
    model_id: str
    latency_ms: int


# ============================================================================
# TOKEN BUDGETS (per-node)
# ============================================================================

TOKEN_BUDGETS = {
    "qa_interaction": 4096,
    "requirements_spec_gen": 8192,
    "judge_requirements": 4096,
    "strategy": 8192,
    "judge_strategy": 4096,
    "test_case_generation": 8192,
    "judge_test_cases": 4096,
    "code_structure_planning": 8192,
    "judge_code_plan": 4096,
    "scripting": 8192,
    "judge_code": 4096,
}

# Max continuation calls when output is truncated (stop_reason == "max_tokens")
MAX_CONTINUATIONS = 3


# ============================================================================
# BEDROCK IMPLEMENTATION
# ============================================================================

def _call_bedrock(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
    temperature: float,
) -> LLMResponse:
    """
    Call AWS Bedrock with Claude 3.5 Sonnet (EU cross-region inference).
    
    Includes automatic continuation: if the response is truncated
    (stop_reason == "max_tokens"), sends follow-up calls to get the
    rest of the output and stitches results together.
    """
    start_time = time.time()
    
    try:
        client = boto3.client(
            "bedrock-runtime",
            region_name=settings.aws_default_region,
            aws_access_key_id=settings.aws_access_key_id or None,
            aws_secret_access_key=settings.aws_secret_access_key or None,
        )
        
        # --- Initial call ---
        messages = [
            {
                "role": "user",
                "content": [{"type": "text", "text": user_prompt}]
            }
        ]
        
        native_request = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_prompt,
            "messages": messages,
        }
        
        response = client.invoke_model(
            modelId=settings.bedrock_model_id,
            body=json.dumps(native_request)
        )
        
        model_response = json.loads(response["body"].read())
        content_text = model_response["content"][0]["text"]
        stop_reason = model_response.get("stop_reason", "end_turn")
        
        # Accumulate usage across continuations
        usage = model_response.get("usage", {})
        total_input_tokens = usage.get("input_tokens", 0)
        total_output_tokens = usage.get("output_tokens", 0)
        
        # --- Continuation loop ---
        continuation_count = 0
        while stop_reason == "max_tokens" and continuation_count < MAX_CONTINUATIONS:
            continuation_count += 1
            logger.info(
                f"Response truncated (stop_reason=max_tokens). "
                f"Sending continuation {continuation_count}/{MAX_CONTINUATIONS}..."
            )
            
            # Build continuation messages: original user prompt + assistant partial + user "continue"
            continuation_messages = [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": user_prompt}]
                },
                {
                    "role": "assistant",
                    "content": [{"type": "text", "text": content_text}]
                },
                {
                    "role": "user",
                    "content": [{"type": "text", "text": "Continue from where you left off. Do not repeat any content already generated. Pick up exactly where you stopped."}]
                },
            ]
            
            continuation_request = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": system_prompt,
                "messages": continuation_messages,
            }
            
            cont_response = client.invoke_model(
                modelId=settings.bedrock_model_id,
                body=json.dumps(continuation_request)
            )
            
            cont_model_response = json.loads(cont_response["body"].read())
            continuation_text = cont_model_response["content"][0]["text"]
            stop_reason = cont_model_response.get("stop_reason", "end_turn")
            
            # Accumulate
            content_text += continuation_text
            cont_usage = cont_model_response.get("usage", {})
            total_input_tokens += cont_usage.get("input_tokens", 0)
            total_output_tokens += cont_usage.get("output_tokens", 0)
        
        if continuation_count > 0:
            logger.info(
                f"Continuation complete. {continuation_count} follow-up call(s). "
                f"Total output: {len(content_text)} chars."
            )
        
        # Calculate cost (approximate Claude 3.5 Sonnet pricing)
        # Input: $3/1M tokens, Output: $15/1M tokens
        cost_usd = (total_input_tokens / 1_000_000 * 3.0) + (total_output_tokens / 1_000_000 * 15.0)
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return LLMResponse(
            content=content_text,
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            cost_usd=cost_usd,
            trace_name="",  # Set by caller
            model_id=settings.bedrock_model_id,
            latency_ms=latency_ms,
        )
        
    except ClientError as e:
        raise RuntimeError(f"LLM call failed (Bedrock): {e}") from e
    except Exception as e:
        raise RuntimeError(f"LLM call failed (Bedrock): {e}") from e


# ============================================================================
# GEMINI IMPLEMENTATION
# ============================================================================

def _call_gemini(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
    temperature: float,
) -> LLMResponse:
    """
    Call Google Gemini API.
    Uses pattern from PRD Section 6.4.
    """
    if genai is None:
        raise RuntimeError("google-generativeai package not installed")
    
    start_time = time.time()
    
    try:
        genai.configure(api_key=settings.gemini_api_key)
        
        model = genai.GenerativeModel(
            model_name=settings.gemini_model_id,
            system_instruction=system_prompt,
        )
        
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        
        response = model.generate_content(
            user_prompt,
            generation_config=generation_config,
        )
        
        content_text = response.text
        
        # Count tokens (approximate)
        # Gemini SDK provides count_tokens() but we'll estimate for simplicity
        input_tokens = model.count_tokens(system_prompt + user_prompt).total_tokens
        output_tokens = model.count_tokens(content_text).total_tokens
        
        # Cost estimate from PRD Section 6.4
        # Input: $0.00125/1K tokens, Output: $0.005/1K tokens
        cost_usd = (input_tokens / 1000 * 0.00125) + (output_tokens / 1000 * 0.005)
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return LLMResponse(
            content=content_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            trace_name="",  # Set by caller
            model_id=settings.gemini_model_id,
            latency_ms=latency_ms,
        )
        
    except Exception as e:
        raise RuntimeError(f"LLM call failed (Gemini): {e}") from e


# ============================================================================
# UNIFIED CALL_LLM DISPATCHER
# ============================================================================

def call_llm(
    system_prompt: str,
    user_prompt: str,
    trace_name: str,
    trace_id: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> LLMResponse:
    """
    Unified LLM client. Dispatches to Bedrock or Gemini based on settings.llm_provider.
    
    Args:
        system_prompt: System context for the LLM
        user_prompt: User message/task
        trace_name: Node name (used for token budget lookup and logging)
        trace_id: Optional trace ID for debugging
        temperature: Optional override (default 0.3)
        max_tokens: Optional override (uses TOKEN_BUDGETS[trace_name] by default)
    
    Returns:
        LLMResponse with content, usage stats, and metadata
        
    Raises:
        RuntimeError: If LLM call fails
    """
    # Set defaults
    if temperature is None:
        temperature = 0.3
    
    if max_tokens is None:
        max_tokens = TOKEN_BUDGETS.get(trace_name, 4096)
    
    logger.info(
        f"LLM call [{trace_name}] provider={settings.llm_provider} "
        f"max_tokens={max_tokens} temperature={temperature}"
    )
    
    # Dispatch to appropriate backend
    if settings.llm_provider == "bedrock":
        response = _call_bedrock(system_prompt, user_prompt, max_tokens, temperature)
    elif settings.llm_provider == "gemini":
        response = _call_gemini(system_prompt, user_prompt, max_tokens, temperature)
    else:
        raise RuntimeError(f"Unknown LLM provider: {settings.llm_provider}")
    
    # Set trace_name in response
    response.trace_name = trace_name
    
    logger.info(
        f"LLM response [{trace_name}] tokens_in={response.input_tokens} "
        f"tokens_out={response.output_tokens} latency={response.latency_ms}ms "
        f"cost=${response.cost_usd:.4f}"
    )
    
    return response


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def extract_json_from_response(text: str) -> dict:
    """
    Extract JSON from LLM response using robust parsing.
    """
    # Import locally to avoid potential circular/top-level issues if any
    import json
    import re
    
    text = text.strip()
    decoder = json.JSONDecoder()
    
    # helper to try parsing from a specific index
    def try_decode(s, start_idx):
        try:
             obj, end_idx = decoder.raw_decode(s, idx=start_idx)
             return obj
        except json.JSONDecodeError:
            return None

    # Strategy 1: Attempt to parse the whole string (stripped of fences)
    # This handles simple cases fast
    stripped = text
    if stripped.startswith("```json"):
        stripped = stripped[7:]
    elif stripped.startswith("```"):
        stripped = stripped[3:]
    if stripped.endswith("```"):
        stripped = stripped[:-3]
    stripped = stripped.strip()
    
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Scan for first '{' or '[' and try to decode from there
    # This correctly handles nested structures where regex fails
    for i, char in enumerate(text):
        if char in ('{', '['):
            obj = try_decode(text, i)
            if obj is not None:
                # If we found a list, wrap it if needed (though our prompt expects dict)
                if isinstance(obj, list):
                    return {"items": obj}
                return obj
    
    # Strategy 3: Best-effort repair using ast.literal_eval (handles single quotes, trailing commas)
    import ast
    try:
        # Find the first { ... } block
        brace_match = re.search(r"(\{.*\})", text, re.DOTALL)
        if brace_match:
            candidate = brace_match.group(1)
            # limited fixups
            candidate = candidate.replace("true", "True").replace("false", "False").replace("null", "None")
            return ast.literal_eval(candidate)
    except (ValueError, SyntaxError):
        pass

    raise ValueError(
        f"Could not extract valid JSON from LLM response. "
        f"Response starts with: {text[:200]}..."
    )


def verify_llm_connection() -> bool:
    """
    Verify that the configured LLM provider is accessible.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        response = call_llm(
            system_prompt="You are a helpful assistant.",
            user_prompt="Reply with exactly: OK",
            trace_name="health_check",
        )
        
        # Check that we got a non-empty response
        if response.content and len(response.content) > 0:
            logger.info(f"LLM connection verified: provider={settings.llm_provider}")
            return True
        else:
            logger.warning("LLM returned empty response")
            return False
            
    except Exception as e:
        logger.error(f"LLM connection failed: {e}")
        return False