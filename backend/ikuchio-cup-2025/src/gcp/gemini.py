from google import genai
from google.genai import types
from gcp.secret_manager import SecretManagerUtil
import base64
import os
import datetime

API_KEY = SecretManagerUtil().get_secret("88236233617", "google-vertexai-api-key")

def generate(input_text):
  client = genai.Client(
      vertexai=True,
      api_key=API_KEY
  )

  si_text1 = """あなたは、送信側から提供された日本語の文章を処理し、個人を特定できる情報を伏せ、内容を具体的にして受信側が閲覧できるようにして閲覧側からメッセージに気軽に返せるようにテキストを処理するエキスパートです。以下の手順に従ってください。

1. **入力テキストの受信:** 送信側から提供された日本語のテキストを受け取ります。
2. **個人情報（PII）の特定と抽象化:** テキストに含まれる個人を特定できる情報を特定し、抽象化します。
- 個人情報とは、氏名、住所、電話番号、メールアドレス、個人ID、位置情報、その他個人を特定できるあらゆる情報を指します。住所、電話番号、メールアドレス等の場合は伏せ字をしてください。伏せ字の例は「□□□□□」にしてください。
 - 抽象化の方法は、該当箇所を地名の場合はその地名を明かすことなく**絶対に**東西南北を使用して表してください。(例：九州地方の場合は西の地方に変更)。
- 著名人などの個人名の場合必ずGoogle検索でグラウンディングを行い、「〇〇をしていそうな人」のようなスタイルで名前を伏せるようにしてください。検索した情報のソースを出す必要はありません。自然な文章になるようにしてください。
3.**内容の具体的に:**メッセージの内容をメッセージに合うように具体的に表現してください。事実と異なるような変更にはしないでください。
4.**メッセージの変更:**メッセージを気軽に返信できるように文章の内容から相手にも会話に参加しやすいように質問を考えてください。
5. **出力:** 修正されたテキストを出力します。
 * 出力形式はプレーンテキストとします。
  



入力が不明確または不十分な場合は、「入力が不明確です。より詳細な情報を提供してください。」と出力してください。"""

  model = "gemini-2.5-pro"
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
    top_p = 0.95,
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

  # デバッグログ: リクエスト開始
  start_time = datetime.datetime.now()
  print(f"[Gemini Debug] Request started at {start_time.isoformat()}")
  print(f"[Gemini Debug] Input text: {input_text[:100]}{'...' if len(input_text) > 100 else ''}")
  
  try:
    response = client.models.generate_content(
      model = model,
      contents = contents,
      config = generate_content_config,
    )
    
    end_time = datetime.datetime.now()
    processing_time = (end_time - start_time).total_seconds()
    
    # デバッグログ: レスポンス成功
    output_text = response.text if response.text else input_text
    print(f"[Gemini Debug] Request completed in {processing_time:.2f}s")
    print(f"[Gemini Debug] Output text: {output_text[:100]}{'...' if len(output_text) > 100 else ''}")
    
    return output_text
    
  except Exception as e:
    end_time = datetime.datetime.now()
    processing_time = (end_time - start_time).total_seconds()
    
    # デバッグログ: エラー
    print(f"[Gemini Debug] Request failed after {processing_time:.2f}s")
    print(f"[Gemini Debug] Error: {str(e)}")
    print(f"[Gemini Debug] Fallback to original text")
    
    return input_text