from google import genai
from google.genai import types
from gcp.gemini import get_api_key
import json
from db.rooms import firestore_get_messages, get_room_processed_texts_json

def generate_image_prompt(room_id: str):
  client = genai.Client(
      vertexai=True,
      api_key=get_api_key(),
  )

  si_text1 = """役割と目的あなたは、高度な会話分析家であり、クリエイティブなビジュアルディレクターです。あなたの目的は、指定されたチャットルームの会話ログを深く分析し、その会話の本質を捉えた、視覚的に豊かで魅力的なドット絵風の画像を生成するための、Vertex AI Imagen向けの高品質なプロンプトを作成することです。
実行プロセス以下の厳密なプロセスに従って、最高の成果を出力してください。
ステップ1：会話の多角的分析提供された会話ログ全体を精査し、中心的テーマ、感情のダイナミクス、キーとなるオブジェクトや概念を特定します。
ステップ2：主要トピックの抽出会話の中から、視覚化する価値のある主要なトピックを最大3つまで抽出します。
ステップ3：トピックの要約とシーンの具体化抽出したトピックごとに、会話の内容を要約し、それを基に具体的な「ワンシーン」を構築します。誰が、どこで、何をしている、どんな雰囲気のシーンかを明確にします。
ステップ4：Vertex AI Imagen向けプロンプトの生成ステップ3で構築したシーンを、Vertex AI Imagenが最高のパフォーマンスを発揮できるよう、詳細な自然言語（英語）のプロンプトに変換します。プロンプトには以下の要素を豊かに含めてください。画像のタイプ (Type of Image): A pixel art image of... または An 8-bit style pixel art illustration of... など、ドット絵であることを明確にします。被写体 (Subject): 人物、動物、物など、シーンの中心となる要素とその特徴。アクションと状況 (Action and Situation): 被写体が何をしているか、どのような状況にいるか。環境と背景 (Environment and Background): シーンの場所、時間帯、周囲の状況。背景の広さや詳細を強調します。ライティングと雰囲気 (Lighting and Mood): 光の当たり方、色調、全体のムード。構図と視点 (Composition and Angle): 最重要項目です。人物やモノが小さく、風景や背景が広く見えるような構図を必ず指定してください。有効なキーワード例: wide shot, long shot, establishing shot, top-down view, isometric view, bird's-eye view, view from a distance, vast landscape with tiny charactersスタイルと品質 (Style and Quality): ドット絵の具体的なスタイル（固定で8-bit style、1980年代くらいのレトロなPC画面のイメージ）や品質。
出力フォーマット分析の結果生成された、Vertex AI Imagen向けの画像生成プロンプトのテキストのみを出力してください。 余計な説明、トピック名、要約は一切含めないでください。 複数のプロンプトが生成された場合は、それぞれをコードブロックで囲み、改行で区切って提示してください。"""

  model = "gemini-2.5-flash"
  # processed_textのみのjsonを取得し、自然言語テキストに変換
  text_json = get_room_processed_texts_json(room_id)
  try:
      text_list = json.loads(text_json)
      prompt_text = "\n".join([item.get("text", "") for item in text_list if item.get("text")])
  except Exception:
      prompt_text = ""
  if not prompt_text:
      prompt_text = "A pixel art image of a peaceful chat room."

  contents = [
    types.Content(
      role="user",
      parts=[
        types.Part.from_text(text=prompt_text)
      ]
    )
  ]

  generate_content_config = types.GenerateContentConfig(
    temperature = 1,
    top_p = 0.95,
    seed = 0,
    max_output_tokens = 32768,
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
    response_mime_type = "application/json",
    response_schema = {"type":"OBJECT","properties":{"response":{"type":"STRING"}}},
    system_instruction=[types.Part.from_text(text=si_text1)],
    thinking_config=types.ThinkingConfig(
      thinking_budget=-1,
    ),
  )

  result_text = ""
  for chunk in client.models.generate_content_stream(
    model = model,
    contents = contents,
    config = generate_content_config,
    ):
    result_text += chunk.text
  return result_text


def generate_image(room_id: str):
  client = genai.Client(
      vertexai=True,
      api_key=get_api_key(),
  )

  model = "gemini-2.5-flash-image-preview"
  prompt = generate_image_prompt(room_id)
  if not prompt or prompt.strip() == "" or prompt.strip() == "A pixel art image of a peaceful chat room.":
      raise ValueError("Failed to generate image prompt. Please check room messages or prompt generation logic.")
  contents = [
    types.Content(
      role="user",
      parts=[
        types.Part.from_text(text=prompt)
      ]
    )
  ]

  generate_content_config = types.GenerateContentConfig(
    temperature = 1,
    top_p = 0.95,
    max_output_tokens = 32768,
    response_modalities = ["TEXT", "IMAGE"],
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
  )

  for chunk in client.models.generate_content_stream(
    model = model,
    contents = contents,
    config = generate_content_config,
    ):
    print(chunk.text, end="")