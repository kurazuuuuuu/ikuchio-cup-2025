# ikuchio-cup-2025
## アイデア：２４時間でさようなら

- 24時間に一度、日付が変わると同時に訪れる永遠かもしれないお別れ  
- あなたは毎日この世界中のどこの誰かわからない相手と出会うことができる。しかし、与えられたコミュニケーションの手段は一つだけ  
- 人と人が直接会話することはできず、システム（AI）を介してのみ対話を試みることができる  
- その日あった出来事やふとしたことを書いておけばめちゃめちゃ話広げてくれてかつ個人に関わる内容は隠しつつ相手に送ってくれる

- 24時間の範囲内でしかできない交換日記みたいな感じ？

- GCPの無料クレジットが大量に余ってるからいろんなサービス行使してみたい  
  - Vertex AI、 Firestoreとか？  
  - Compute Engineも使っても良さそう（コスパは知らん🤔）  
- フロントエンドは割と適当でも大丈夫そう  
  - バックエンドの処理がメイン

## 深堀り

- 0:00にランダムなユーザーとルームを生成する

## 技術スタック

- フロント：
  - Vue.js (JavaScript)
- バックエンド：  
  - API：  
    - FastAPI (Python)  
  - DB：  
    - FireStore (NoSQL)  
  - AI：  
    - Vertex AI Studio (Gemini 2.5 Pro)
- デプロイ：
  - Docker
    - GCP or homelab
  - Cloudflare Tunnel

## 開発環境
### Frontend
```bash
cd ikuchio-cup-2025
npm install
npm run dev
```
### Backend (Python)
- UV(Pythonのパッケージ管理ツール)が入っていないなら
  - Standalone: https://docs.astral.sh/uv/getting-started/installation/#standalone-installer
  - Homebrew: `brew install uv`
```bash
# Pythonパッケージ
cd backend/ikuchio-cup-2025
uv sync
```

### Backend (Google Cloud)
- gcloud CLIのインストール
  - URL：https://cloud.google.com/sdk/docs/install?hl=ja#installation_instructions
    - 1. デバイスに応じたパッケージをダウンロード
    - 2. 解凍する→`tar -xf google-cloud-〇〇.tar.gz`
    - 3. インストールする→`cd google-cloud-sdk && ./install.sh`
    - 4. なんか色々あるから進める
- gcloud CLIの初期化
  - `gcloud init`
  - また色々出てくるからログインする（GCPのプロジェクトにアクセスできるアカウント）

## いろいろメモ
### エンドポイント
```markdown
POST `/api/users`  - ユーザー登録
  - Body {"device_id": "DEVICE_ID"} // ユーザーのデバイスID、ログイン時に使用する
GET `/api/users` - ユーザー情報取得、たぶんそんなに使わない？
  - Query {"device_id": "DEVICE_ID"}
POST `/api/room/{ROOM_ID}` - メッセージ送信
  - Body {"original_text": "送信したいメッセージ"} // 送信後AIで処理し"processed_text"として保管
GET `/api/room/{ROOM_ID}` - ルームのメッセージ履歴取得
```

### スキーマ
### USER
```json
user: {
  device_id: "{DEVICE_ID}" // ユーザーのデバイスID、ログイン時に使用する
  created_at: {TIMEDATE}, // ユーザーの作成日時
  room_id: "room_{UUID}" // その日参加しているルームUUID
}
```

### ROOM
```json
room: {
  id: "room_{UUID}", // UUID4で生成
  created_at: {TIMEDATE}, // ルームが作成された日時
  users: [ // ルームに参加しているユーザーのUUID
    "user_{DEVICE_ID}", "user_{DEVICE_ID}"
  ]
}
```

### TURN
```json
turn: {
  id: "turn_{UUID}", // ターンごとのID
  room_id: "room_{UUID}", // どのルームでのやりとりか
  original_sender_id: "user_{DEVICE_ID}", // 元のメッセージを書いたユーザーID
  original_text: "String", // ユーザーが書いた元のメッセージ
  processed_text: "String", // AIが広げて匿名化した後のメッセージ
  created_at: {TIMEDATE}, // ユーザーが書いた日時
  processed_at: {TIMEDATE} // AIが処理を完了した日時
}
```
### AI_RESPONSE
```json
ai_response: {
  processed_text: "String"
}
```