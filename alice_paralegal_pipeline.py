"""
title: Alice Paralegal
author: Don Strickland
version: 1.0
license: MIT
description: Fully local pipeline - Tesseract OCR reads images, deepseek-r1:8b does legal reasoning
requirements: pytesseract, Pillow
"""

import io
import base64
import json
import requests
from typing import List, Generator
from pydantic import BaseModel, Field

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


class Pipeline:
    """Alice Paralegal - fully local vision + reasoning pipeline."""

    class Valves(BaseModel):
        OLLAMA_HOST: str = Field(
            default="http://host.docker.internal:11434",
            description="Ollama API endpoint"
        )
        REASONING_MODEL: str = Field(
            default="deepseek-r1:8b",
            description="Local model for legal reasoning"
        )
        TEMPERATURE: float = Field(
            default=0.3,
            description="Lower temperature for focused legal analysis"
        )

    def __init__(self):
        self.name = "Alice Paralegal"
        self.valves = self.Valves()

    def _extract_images(self, messages: List[dict]) -> tuple:
        """Extract images and text from messages. Returns (images_bytes_list, text_content)."""
        images = []
        text_parts = []
        
        for msg in messages:
            content = msg.get("content", "")
            
            if isinstance(content, str):
                text_parts.append(content)
                continue
            
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            text_parts.append(item.get("text", ""))
                        elif item.get("type") == "image_url":
                            url = item.get("image_url", {}).get("url", "")
                            if url.startswith("data:image"):
                                try:
                                    base64_data = url.split(",", 1)[1]
                                    image_bytes = base64.b64decode(base64_data)
                                    images.append(image_bytes)
                                except (IndexError, ValueError):
                                    pass
                    elif isinstance(item, str):
                        text_parts.append(item)
        
        return (images, " ".join(text_parts))

    def _ocr_image(self, image_bytes: bytes) -> str:
        """Use Tesseract to extract text from image."""
        if not TESSERACT_AVAILABLE:
            return "Error: pytesseract not installed"
        
        try:
            image = Image.open(io.BytesIO(image_bytes))
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            return f"Error reading image: {str(e)}"

    def _call_ollama_stream(self, prompt: str) -> Generator[str, None, None]:
        """Call Ollama API for local reasoning with streaming."""
        
        try:
            response = requests.post(
                f"{self.valves.OLLAMA_HOST}/api/generate",
                json={
                    "model": self.valves.REASONING_MODEL,
                    "prompt": prompt,
                    "stream": True,
                    "options": {"temperature": self.valves.TEMPERATURE}
                },
                stream=True,
                timeout=300
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            yield f"Error calling {self.valves.REASONING_MODEL}: {str(e)}"

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: List[dict],
        body: dict
    ) -> Generator[str, None, None]:
        """Process input - use Tesseract for images, local model for reasoning."""
        
        images, text_content = self._extract_images(messages)
        
        if images:
            yield "👁️ *Alice Paralegal reading image with Tesseract OCR...*\n\n"
            
            # OCR all images
            all_text = []
            for i, img_bytes in enumerate(images):
                ocr_text = self._ocr_image(img_bytes)
                all_text.append(ocr_text)
            
            combined_ocr = "\n\n".join(all_text)
            
            yield f"**Extracted Text:**\n```\n{combined_ocr}\n```\n\n---\n\n"
            yield "⚖️ *Analyzing with deepseek-r1:8b...*\n\n"
            
            # Send to reasoning model
            reasoning_prompt = f"""You are a legal reasoning assistant for Texas bar exam preparation.

Here is the question extracted from the image:
{combined_ocr}

User asks: {user_message if user_message else "What is the correct answer?"}

Provide thorough legal analysis:
1. Identify the legal issue(s) being tested
2. State the applicable rule(s) of law
3. Apply the rule to these specific facts
4. Analyze each answer choice - explain why it is correct or incorrect
5. State the best answer with confidence"""

            for chunk in self._call_ollama_stream(reasoning_prompt):
                yield chunk
        else:
            # No images - direct legal reasoning
            reasoning_prompt = f"""You are a legal reasoning assistant for Texas bar exam preparation.

Question: {user_message}

Provide thorough legal analysis:
1. Identify the legal issue(s)
2. State the applicable rule(s) of law  
3. Apply the rule to the facts
4. Reach a conclusion"""

            for chunk in self._call_ollama_stream(reasoning_prompt):
                yield chunk
