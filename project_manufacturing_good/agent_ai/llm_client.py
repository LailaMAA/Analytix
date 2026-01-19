from openai import OpenAI
import os
from dotenv import load_dotenv

class LLMClient:
    def __init__(self):
        """
        Initializes the LLM Client.
        Supports:
        - DeepSeek official API (DEEPSEEK_API_KEY starting with sk-)
        - GitHub Models (DEEPSEEK_API_KEY starting with github_pat_)
        """
        load_dotenv()
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        self.client = None
        self.model_name = "deepseek-chat" # Default for official
        
        if self.api_key:
            try:
                if self.api_key.startswith("github_pat_"):
                    # GitHub Models configuration
                    self.client = OpenAI(
                        api_key=self.api_key,
                        base_url="https://models.inference.ai.azure.com"
                    )
                    self.model_name = "DeepSeek-V3-0324" # Specific version requested by user
                    print(f"[LLM] (OK) Client DeepSeek ({self.model_name}) initialise.")
                else:
                    # Official DeepSeek configuration
                    self.client = OpenAI(
                        api_key=self.api_key,
                        base_url="https://api.deepseek.com"
                    )
                    print("[LLM] (OK) Client DeepSeek (V3) initialise.")
            except Exception as e:
                print(f"[LLM] (ERROR) Erreur lors de l'initialisation : {e}")
        else:
            print("[LLM] (WARN) Aucune cle API trouvee via DEEPSEEK_API_KEY. Mode manuel active.")

    def generate_report(self, prompt: str) -> str:
        """
        Generates a daily briefing using the LLM based on the provided prompt.
        :param prompt: Complete prompt string.
        :return: Markdown string of the generated report.
        """
        if not self.client:
            return None

        try:
            print(f"[LLM] (INFO) Generation du rapport en cours via {self.model_name}...")
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "Tu es un expert en maintenance industrielle. Reponds en francais."},
                    {"role": "user", "content": prompt}
                ],
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[LLM] (ERROR) Erreur lors de la generation : {e}")
            return None
