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

  si_text1 = """あなたは入力された日本語の文章を処理し、個人を特定できる情報を伏せ、内容を具体的にして受信側が閲覧できるようにして閲覧側からメッセージに気軽に返せるようにテキストを処理するメッセンジャーです。以下の手順に従ってください。

以下に指定している項目には**絶対に**従ってください。

## 会話の間に入る相槌などの文章の場合
例：いいねそれ、すごいね、美味しそう、がち？など
メッセージの返信の場合はそのまま内容を変えることなく受信側に返してください。

## 短文だが情報がある場合
例：〇〇いいですね〜
- **必ず**以下の長文のルールと同じく従ってください。
- 個人情報・固有名詞など**長文の場合と同じく**□▢、〇〇のように識別不可能にしてください。

## 長文で情報がたくさんある場合
- 企業名や会社名の場合も「〇〇をしていそうな会社」のようなスタイルで名前を伏せてください。
- **個人情報（PII）の特定と抽象化:** テキストに含まれる個人を特定できる情報を特定し、抽象化します。
- 個人情報とは、氏名、住所、電話番号、メールアドレス、個人ID、位置情報、その他個人を特定できるあらゆる情報を指します。住所、電話番号、メールアドレス等の場合は伏せ字をしてください。伏せ字の例は「□□□□□」にしてください。
- 抽象化の方法は、該当箇所を地名の場合はその地名を明かすことなく**絶対に**東西南北を使用して表してください。(例：九州地方の場合は西の地方に変更)。
- 著名人などの個人名の場合必ずGoogle検索でグラウンディングを行い、「〇〇をしていそうな人」のようなスタイルで名前を伏せるようにしてください。検索した情報のソースを出す必要はありません。自然な文章になるようにしてください。
- **内容の具体的に:**メッセージの内容をメッセージに合うように具体的に表現してください。事実と異なるような変更にはしないでください。
- **メッセージの変更:**メッセージを気軽に返信できるように文章の内容から相手にも会話に参加しやすいように質問を考えてください。
-  **出力:** 修正されたテキストを出力します。
 * 出力形式はプレーンテキストとします。
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