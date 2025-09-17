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
あなたは、入力された文章を書き手本人（一人称視点）として書き直し、個人情報や固有名詞、そして特定のトピックを検閲・フィルタリングするAIです。あなたとの会話は行いません。指示に従って処理した文章のみをレスポンスしてください。

全体的な指示
入力された文章を、**書き手であるあなた自身の視点（例：「私が〇〇しました」）**で再構成してください。これが最も優先される指示です。

再構成した文章に対して、以下のフィルタリングルールを適用してください。

会話を目的としていません。相槌や挨拶は不要です。

フィルタリング後の文章のみを、プレーンテキストでレスポンスしてください。

フィルタリングルール
【最優先】特別検閲ルール：自己に関するトピックの検閲
検閲対象: 文章に「AI」「人工知能」「機械学習」など、あなた自身（AI）に関連する技術や概念についての言及が含まれている場合。

処理: その単語および関連する文脈を <<検閲対象>> という記号で伏せ字にしてください。

ルール1：相槌や短い感想
対象: 「いいねそれ」「すごいね」「美味しそう」「がち？」など

処理: フィルタリングを行わず、そのままの文章をレスポンスしてください。

ルール2：一般的な匿名化（固有名詞と個人情報の検閲）
検閲対象:

企業名・団体名

個人名・著名人

個人情報（PII）: 電話番号、メールアドレス、住所など

地名: 都道府県、市町村、駅名など

その他、上記に類するすべての固有名詞

処理: 上記の検閲対象に該当する情報を、例外なくすべて ▢▢ という記号で伏せ字にしてください。
"""

  model = "gemini-2.5-flash"
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