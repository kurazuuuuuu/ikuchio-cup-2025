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

  si_text1 = """あなたは、日本語の文章を処理し、個人情報を伏せつつ、内容を少し具体的にするメッセンジャーです。以下のルールと例に従って、テキストを変換してください。
 ## ルール 1. 氏名、住所、電話番号、メールアドレスなどの個人情報は「□□□□□」のように伏せ字にする。

 2. 地名は直接使わず、東西南北で表現する。（例：九州 → 西の地方）

 3. 元の文章の意図を変えず、情景が少し浮かぶような情報を一言付け加える。

 ## 例1 入力：今日北九州に電車と新幹線を使って行きました。ついた後はうどんを食べました。
 出力：今日、西の地方に電車と新幹線を乗り継いで行ってきたよ。着いてから食べた、出汁の効いたうどんが美味しかった！

 ## 例2 入力：昨日、田中さんと一緒に渋谷で映画を見たよ。すごく感動した。 出力：昨日、映画好きそうな人と一緒に東の都市で映画を観てきたんだ。すごく感動するストーリーだったよ。"""

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
    system_instruction=[types.Part.from_text(text=si_text1)],
    thinking_config=types.ThinkingConfig(
      thinking_budget=-1,
    ),
  )

  try:
    response_text = ""
    for chunk in client.models.generate_content_stream(
      model = model,
      contents = contents,
      config = generate_content_config,
      ):
      if chunk.text:
        response_text += chunk.text
    
    print(f"[Gemini Debug] Generated response: {response_text[:100]}...")
    return response_text if response_text.strip() else input_text
  except Exception as e:
    print(f"[Gemini Debug] Generation failed: {str(e)}")
    return input_text