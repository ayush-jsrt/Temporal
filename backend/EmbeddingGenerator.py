import boto3
import json

class EmbeddingGenerator:
    def __init__(self, region_name="us-east-1", model_id="amazon.titan-embed-text-v2:0"):
        self.client = boto3.client("bedrock-runtime", region_name=region_name)
        self.model_id = model_id
    
    def generate_embedding(self, text: str) -> list[float]:
        try:
            native_request = {"inputText": text}
            request = json.dumps(native_request)
            response = self.client.invoke_model(modelId=self.model_id, body=request)
            model_response = json.loads(response["body"].read())
            return model_response["embedding"]
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return []
    
    def generate_card_embedding(self, card_title: str, card_content: str) -> list[float]:
        combined_text = f"Title: {card_title}\n\nContent: {card_content}"
        return self.generate_embedding(combined_text)