import boto3
import json

class AIService:
    def __init__(self, region_name="us-east-1"):
        self.client = boto3.client("bedrock-runtime", region_name=region_name)
        self.embedding_model = "amazon.titan-embed-text-v2:0"
        self.llm_model = "anthropic.claude-3-haiku-20240307-v1:0"
    def _invoke_model(self, model_id: str, payload: dict) -> dict:
        try:
            request = json.dumps(payload)
            response = self.client.invoke_model(modelId=model_id, body=request)
            return json.loads(response["body"].read())
        except Exception as e:
            print(f"Error invoking model {model_id}: {e}")
            return {}
    
    def generate_embedding(self, text: str) -> list[float]:
        payload = {"inputText": text}
        response = self._invoke_model(self.embedding_model, payload)
        return response.get("embedding", [])
    
    def generate_text(self, prompt: str, max_tokens: int = 1000) -> str:
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        response = self._invoke_model(self.llm_model, payload)
        
        if "content" in response:
            return response["content"][0]["text"]
        return ""
