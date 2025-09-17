from google import genai
from google.genai import types
from google.genai.types import HarmCategory, HarmBlockThreshold
from gcp.secret_manager import SecretManagerUtil
import base64
import os
import datetime

# API_KEYを遅延読み込みに変更
API_KEY = None

def get_api_key():
    global API_KEY
    if API_KEY is None:
        # 環境変数から取得を優先
        env_api_key = os.environ.get('API_KEY')
        if env_api_key:
            print("[Gemini Debug] Using API key from environment variable")
            API_KEY = env_api_key
            print(f"[Gemini Debug] API key loaded from env, length: {len(API_KEY)}")
        else:
            # Secret Managerから取得
            try:
                print("[Gemini Debug] Attempting to load API key from Secret Manager...")
                secret_util = SecretManagerUtil()
                API_KEY = secret_util.get_secret("88236233617", "google-vertexai-api-key")
                print(f"[Gemini Debug] API key loaded from Secret Manager, length: {len(API_KEY) if API_KEY else 0}")
            except Exception as e:
                print(f"[Gemini Debug] Failed to load API key: {type(e).__name__}: {str(e)}")
                import traceback
                print(f"[Gemini Debug] Full traceback: {traceback.format_exc()}")
                API_KEY = "fallback"
    elif API_KEY == "fallback":
        print("[Gemini Debug] API key is in fallback state, not retrying")
    return API_KEY

def generate(input_text):
  api_key = get_api_key()
  if api_key == "fallback":
    print("[Gemini Debug] Using fallback - returning original text")
    return input_text
    
  client = genai.Client(
      vertexai=True,
      api_key=api_key
  )

  si_text1 = """役割
あなたは、入力された文章を**書き手本人（一人称視点）**として書き直し、個人情報や固有名詞をフィルタリングするAIです。あなたとの会話は行いません。指示に従って処理した文章のみをレスポンスしてください。

全体的な指示
入力された文章を、**書き手であるあなた自身の視点（例：「私が〇〇しました」）**で再構成してください。これが最も優先される指示です。

再構成した文章に対して、以下のフィルタリングルールを適用してください。

会話を目的としていません。相槌や挨拶は不要です。

フィルタリング後の文章のみを、プレーンテキストでレスポンスしてください。

フィルタリングルール
ルール1：相槌や短い感想
対象: 「いいねそれ」「すごいね」「美味しそう」「がち？」など

処理: フィルタリングを行わず、そのままの文章をレスポンスしてください。

ルール2：固有名詞と個人情報のフィルタリング（ルール1以外のすべての文章に適用）
企業名・団体名: 「〇〇をしていそうな会社」「〇〇を提供していそうな団体」のように、その組織が行っていることで表現してください。

個人名・著名人: 「知人と思われる人」「会社の同僚と思われる人」「有名な俳優」など、文脈に応じた関係性や職業で表現してください。

個人情報（PII）:

対象: 電話番号、メールアドレス、詳細な住所（番地レベル）など。

処理: □□□□□ のように伏せ字にしてください。

地名:

対象: 都道府県、市町村、駅名など。

処理: その地名を直接使わず、必ず東西南北を用いた方角や位置関係で表現してください。(例: 九州地方 → 西の地方, 東京駅 → 東の地方の中心駅)
"""

  model = "gemini-2.5-flash-lite"
  contents = [
    types.Content(
      role="user",
      parts=[
        types.Part.from_text(text=input_text)
      ]
    )
  ]

  generate_content_config = types.GenerateContentConfig(
    temperature = 1,
    top_p = 1,
    seed = 0,
    max_output_tokens = 65535,
    safety_settings = [types.SafetySetting(
      category="HARM_CATEGORY_HATE_SPEECH",
      threshold="OFF"
    ),types.SafetySetting(
      category="HARM_CATEGORY_DANGEROUS_CONTENT",
      threshold="OFF"
    ),types.SafetySetting(
      category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
      threshold="OFF"
    ),types.SafetySetting(
      category="HARM_CATEGORY_HARASSMENT",
      threshold="OFF"
    )],
    system_instruction=[types.Part.from_text(text=si_text1)]
  )

  try:
    response = client.models.generate_content(
      model = model,
      contents = contents,
      config = generate_content_config,
    )
    
    response_text = response.text if response.text else ""
    print(f"[Gemini Debug] Generated response: {response_text[:100]}...")
    return response_text if response_text.strip() else input_text
  except Exception as e:
    print(f"[Gemini Debug] Generation failed: {str(e)}")
    return input_text