import openai
import json
import os
import time
from typing import Dict, Any, Optional

class LLMClient:
    def __init__(
        self,
        model_name: str,
        base_url: str, 
        api_key: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: int = 5
    ):
        self.model_name = model_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        os.environ["OPENAI_API_KEY"] = api_key
            
        try:
            openai.api_key = api_key
            self.client = openai.OpenAI(base_url=base_url)
            print(f"LLMClient initialized for model '{self.model_name}' at endpoint '{base_url}'")
        except Exception as e:
            print(f"Error initializing OpenAI client with base_url '{base_url}': {e}")
            raise
        
    def call(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful assistant.",
        temperature: float = 0.5,
        max_tokens: int = 2048,
        expect_json: bool = False
    ) -> Optional[Any]:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    
        api_params = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if expect_json:
            api_params["response_format"] = {"type": "json_object"}

        for attempt in range(self.max_retries):
            try:
                print(f"--- Calling LLM (Attempt {attempt + 1}/{self.max_retries}) ---")
             
                completion = self.client.chat.completions.create(**api_params)
                
                content = completion.choices[0].message.content

                if expect_json:
                    content = content.strip()
                    if content.startswith('```json'):
                        content = content[7:]  
                    if content.endswith('```'):
                        content = content[:-3] 
                    parsed_json = json.loads(content)
                    print("--- LLM call successful (JSON) ---")
                    return parsed_json
                else:
                    print("--- LLM call successful (Text) ---")
                    return content

            except openai.APIError as e:
                print(f"OpenAI API Error on attempt {attempt + 1}: {e}")
            except json.JSONDecodeError as e:
                print(f"JSON Decode Error on attempt {attempt + 1}: LLM did not return valid JSON. Response: {content}")
            except Exception as e:
                print(f"An unexpected error occurred on attempt {attempt + 1}: {e}")

            if attempt < self.max_retries - 1:
                print(f"Retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
        
        print("--- LLM call failed after all retries. ---")
        return None