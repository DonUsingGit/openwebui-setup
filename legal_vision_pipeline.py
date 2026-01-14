"""
title: Legal Vision (llava + deepseek-r1)
author: Don Strickland
version: 1.0
license: MIT
description: Two-stage pipeline - llava:13b interprets images, deepseek-r1:8b does legal reasoning
requirements: requests
"""

import requests
import base64
import json
from typing import List, Generator
from pydantic import BaseModel, Field


class Pipeline:
    """Legal Vision pipeline - uses llava for images, deepseek-r1 for reasoning."""

    class Valves(BaseModel):
        OLLAMA_HOST: str = Field(
            default="http://host.docker.internal:11434",
            description="Ollama API endpoint"
        )
        VISION_MODEL: str = Field(
            default="llava:13b",
            description="Model for image interpretation"
        )
        REASONING_MODEL: str = Field(
            default="deepseek-r1:8b",
            description="Model for legal reasoning"
        )
        TEMPERATURE: float = Field(
            default=0.3,
            description="Lower temperature for more focused legal analysis"
        )

    def __init__(self):
        self.name = "Legal Vision (llava + deepseek-r1)"
        self.valves = self.Valves()

    def _has_images(self, messages: List[dict]) -> tuple:
        """Check if any message contains images. Returns (has_image, images_list, text_content)."""
        images = []
        text_parts = []
        
        for msg in messages:
            content = msg.get("content", "")
            
            # Handle string content
            if isinstance(content, str):
                text_parts.append(content)
                continue
            
            # Handle list content (may contain images)
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            text_parts.append(item.get("text", ""))
                        elif item.get("type") == "image_url":
                            url = item.get("image_url", {}).get("url", "")
                            if url.startswith("data:image"):
                                # Extract base64 data
                                try:
                                    base64_data = url.split(",")[1]
                                    images.append(base64_data)
                                except IndexError:
                                    pass
                    elif isinstance(item, str):
                        text_parts.append(item)
        
        return (len(images) > 0, images, " ".join(text_parts))

    def _call_ollama(self, model: str, prompt: str, images: List[str] = None, stream: bool = True) -> Generator[str, None, None]:
        """Call Ollama API with optional images."""
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": self.valves.TEMPERATURE
            }
        }
        
        if images:
            payload["images"] = images
        
        try:
            response = requests.post(
                f"{self.valves.OLLAMA_HOST}/api/generate",
                json=payload,
                stream=stream,
                timeout=300
            )
            response.raise_for_status()
            
            if stream:
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                        except json.JSONDecodeError:
                            continue
            else:
                data = response.json()
                yield data.get("response", "")
                
        except Exception as e:
            yield f"Error calling {model}: {str(e)}"

    def _call_ollama_sync(self, model: str, prompt: str, images: List[str] = None) -> str:
        """Call Ollama API synchronously (non-streaming) for image interpretation."""
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.valves.TEMPERATURE
            }
        }
        
        if images:
            payload["images"] = images
        
        try:
            response = requests.post(
                f"{self.valves.OLLAMA_HOST}/api/generate",
                json=payload,
                timeout=300
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
                
        except Exception as e:
            return f"Error calling {model}: {str(e)}"

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: List[dict],
        body: dict
    ) -> Generator[str, None, None]:
        """Process input - route through llava if images present, then deepseek-r1 for reasoning."""
        
        # Check for images in the conversation
        has_images, images, text_content = self._has_images(messages)
        
        if has_images:
            # Stage 1: Use llava to interpret the image(s)
            yield "🔍 *Analyzing image with llava:13b...*\n\n"
            
            vision_prompt = f"""Describe this image in detail. If it contains text (like a legal question, 
exam problem, or document), transcribe ALL the text exactly as written. Include any multiple choice 
options if present.

User's question: {user_message if user_message else text_content}"""
            
            image_description = self._call_ollama_sync(
                self.valves.VISION_MODEL,
                vision_prompt,
                images
            )
            
            yield f"**Image Analysis:**\n{image_description}\n\n---\n\n"
            yield "⚖️ *Processing with deepseek-r1:8b for legal reasoning...*\n\n"
            
            # Stage 2: Use deepseek-r1 for legal reasoning
            reasoning_prompt = f"""You are a legal reasoning assistant helping with Texas bar exam preparation.

Based on this image content:
{image_description}

User's question: {user_message if user_message else "Analyze this and provide legal reasoning."}

Provide thorough legal analysis. If this is a multiple choice question:
1. Identify the legal issue(s)
2. State the applicable rule(s) of law
3. Apply the rule to the facts
4. Explain why each answer choice is correct or incorrect
5. State the best answer with confidence"""

            for chunk in self._call_ollama(self.valves.REASONING_MODEL, reasoning_prompt):
                yield chunk
        else:
            # No images - direct to deepseek-r1 for text-based legal reasoning
            reasoning_prompt = f"""You are a legal reasoning assistant helping with Texas bar exam preparation.

Question: {user_message}

Provide thorough legal analysis. If this is a legal question:
1. Identify the legal issue(s)
2. State the applicable rule(s) of law  
3. Apply the rule to the facts
4. Reach a conclusion"""

            for chunk in self._call_ollama(self.valves.REASONING_MODEL, reasoning_prompt):
                yield chunk
