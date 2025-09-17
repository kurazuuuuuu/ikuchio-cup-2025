# ikuchio-cup-2025
## アイデア：２４時間でさようなら

- 24時間に一度、日付が変わると同時に訪れる永遠かもしれないお別れ  
- あなたは毎日この世界中のどこの誰かわからない相手と出会うことができる。しかし、与えられたコミュニケーションの手段は一つだけ  
- 人と人が直接会話することはできず、システム（AI）を介してのみ対話を試みることができる  
- その日あった出来事やふとしたことを書いておけばめちゃめちゃ話広げてくれてかつ個人に関わる内容は隠しつつ相手に送ってくれる

- 24時間の範囲内でしかできない交換日記みたいな感じ？

## UI/UX デザイン

### レトロターミナル風インターフェース
- **DotGothic16フォント** - 日本語対応のドット風フォント
- **CRTモニター効果** - ビンテージコンピューター風の視覚効果
  - スキャンライン（走査線）
  - ビネット効果（画面周辺の暗化）
  - フリッカー（ちらつき）
  - マウスカーソル周辺のノイズ効果
- **Linux風ブート画面** - システム起動時のローディング演出
- **ターミナル配色** - 緑色テキスト on 黒背景
- **タイプライター効果** - 文字が一文字ずつ表示されるアニメーション

### PWA対応
- **ホーム画面追加** - スマートフォンでアプリのようにインストール可能
- **スタンドアロン表示** - ブラウザUIを隠してネイティブアプリ風に動作
- **オフライン対応** - 基本的なキャッシュ機能
- **レスポンシブデザイン** - モバイル・タブレット・デスクトップ対応

### 操作性
- **キーボードショートカット**
  - `Cmd+Enter` / `Ctrl+Enter`: メッセージ送信
  - `Enter`: 改行
- **誤操作防止** - UI要素のテキスト選択を無効化
- **パフォーマンス最適化** - GPU加速とアニメーション最適化

- GCPの無料クレジットが大量に余ってるからいろんなサービス行使してみたい  
  - Vertex AI、 Firestoreとか？  
  - Compute Engineも使っても良さそう（コスパは知らん🤔）  
- フロントエンドは割と適当でも大丈夫そう  
  - バックエンドの処理がメイン

## 深堀り

- 0:00にランダムなユーザーとルームを生成する

## 技術スタック

- **フロントエンド**：
  - Vue.js 3 (TypeScript)
  - Vite (ビルドツール)
  - PWA (Progressive Web App)
  - Firebase Authentication (匿名認証)
  - レトロターミナル風UI (CRT効果、タイプライター、スキャンライン)

- **バックエンド**：  
  - FastAPI (Python)
  - WebSocket (リアルタイム通信)
  - uvicorn (ASGIサーバー)

- **データベース**：  
  - Google Cloud Firestore (NoSQL)

- **AI**：
  - Google Cloud Vertex AI Gemini 2.5 Pro (メッセージ処理・匿名化)

- **インフラ**：
  - Google Cloud GKE (Kubernetesコンテナオーケストレーション)
  - Google Cloud DNS (ドメイン管理)
  - Google Cloud Secret Manager (API Key管理)
  - Google Cloud Build (CI/CD)
  - Docker (コンテナ化)
  - Kubernetes (Pod管理、自動スケーリング、ロードバランシング)
  - GitHub (ソースコード管理)

## 開発環境

### 前提条件
- Node.js 22+
- Python 3.11+
- UV (Pythonパッケージ管理)
- gcloud CLI
- Docker (オプション)

### フロントエンド開発
```bash
cd frontend/ikuchio-cup-2025
npm install
npm run dev  # http://localhost:5173
```

### バックエンド開発
```bash
cd backend/ikuchio-cup-2025
uv sync
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Firebase設定
1. Firebase Console で匿名認証を有効化
2. プロジェクト設定からFirebase設定を取得
3. `frontend/ikuchio-cup-2025/src/firebase/config.ts` を更新

### Google Cloud設定
```bash
# gcloud CLI認証
gcloud auth login
gcloud config set project ikuchio-cup-2025

# Secret Manager設定
echo "YOUR_GEMINI_API_KEY" | gcloud secrets create google-vertexai-api-key --data-file=-
```

### GKE セットアップ
```bash
# GKEクラスター作成
./setup-gke.sh

# DNS設定
./setup-dns.sh

# 手動でKubernetesマニフェストを適用
kubectl apply -f k8s/
```

### デプロイ
```bash
# 自動デプロイ（GitHub push時）
git push origin main

# 手動デプロイ
gcloud builds submit --config cloudbuild.yaml .
```

### 現在のアクセスURL
- **フロントエンド**: http://35.187.202.58
- **バックエンド**: http://35.243.125.105:8000
- **DNS反映後**: https://ikuchio-cup-2025-vrcat.com

## 現在のインフラ構成

### GKEクラスター
- **クラスター名**: ikuchio-cluster
- **リージョン**: asia-northeast1
- **ノードタイプ**: e2-medium
- **ノード数**: 1-3 (自動スケーリング)

### Pod構成
- **Backend**: 1レプリカ (CPU: 100m-200m, Memory: 256Mi-512Mi)
- **Frontend**: 1レプリカ (CPU: 100m-200m, Memory: 128Mi-256Mi)
- **自動スケーリング**: CPU 70%でスケールアウト

### ネットワーク
- **静的IP**: 34.54.141.104
- **LoadBalancer IP**: 
  - Frontend: 35.187.202.58
  - Backend: 35.243.125.105
- **DNS**: ikuchio-cup-2025-vrcat.com (Google Cloud DNS)

### SSL証明書
- **Google管理SSL**: 自動発行・更新
- **ドメイン**: ikuchio-cup-2025-vrcat.com, api.ikuchio-cup-2025-vrcat.com

## 運用情報
### API エンドポイント

#### 認証
- すべてのAPIはFirebase ID Tokenによる認証が必要
- `Authorization: Bearer <firebase_id_token>` ヘッダーを付与

#### エンドポイント一覧
```
POST /api/users
  - ユーザー登録・取得
  - Body: {"firebase_uid": "string"}
  - Response: User object

GET /api/users?firebase_uid={uid}
  - ユーザー情報取得
  - Response: User object

POST /api/room/{room_id}
  - メッセージ送信
  - Body: {"original_text": "string", "sender_id": "string"}
  - Response: Message object (AI処理後)

GET /api/room/{room_id}
  - ルームのメッセージ履歴取得
  - Response: Message[] array

WS /ws/{room_id}
  - WebSocket接続（リアルタイム通信）
```

### データスキーマ

#### User (Firestore: users/{user_id})
```typescript
{
  firebase_uid: string;     // Firebase匿名認証UID
  created_at: Timestamp;    // ユーザー作成日時
  room_id: string | null;   // 参加中のルームID
}
```

#### Room (Firestore: rooms/{room_id})
```typescript
{
  id: string;              // room_{UUID}
  created_at: Timestamp;   // ルーム作成日時
  users: string[];         // 参加ユーザーのfirebase_uid配列
}
```

#### Message (Firestore: messages/{message_id})
```typescript
{
  id: string;                    // turn_{UUID}
  room_id: string;               // 所属ルームID
  original_sender_id: string;    // 送信者のfirebase_uid
  original_text: string;         // 元のメッセージ
  processed_text: string;        // AI処理後のメッセージ
  created_at: Timestamp;         // 送信日時
  processed_at: Timestamp;       // AI処理完了日時
}
```

## アーキテクチャ

```
[ユーザー] → [Google Cloud DNS] → [GKE Ingress] → [LoadBalancer]
                                            ↓
                                    [Frontend Pod] → [Firebase Auth]
                                            ↓
                                    [Backend Pod] → [Firestore]
                                            ↓
                                    [WebSocket] ← [Vertex AI Gemini]
```

### セキュリティ
- Firebase匿名認証による安全なユーザー識別
- Firebase Admin SDKによるサーバーサイド認証
- Vertex AI Geminiによる個人情報の自動匿名化
- Secret Managerによる機密情報管理
- Kubernetes RBACによるアクセス制御
- Workload IdentityによるGCPサービス連携

## モニタリング・トラブルシューティング

### ステータス確認
```bash
# Pod状態確認
kubectl get pods -n ikuchio-cup-2025

# サービス確認
kubectl get services -n ikuchio-cup-2025

# Ingress確認
kubectl get ingress -n ikuchio-cup-2025

# ログ確認
kubectl logs -f deployment/ikuchio-backend -n ikuchio-cup-2025
```

### トラブルシューティング
```bash
# Pod再起動
kubectl rollout restart deployment/ikuchio-backend -n ikuchio-cup-2025

# Secret再作成
kubectl delete secret google-vertexai-api-key -n ikuchio-cup-2025
API_KEY=$(gcloud secrets versions access latest --secret="google-vertexai-api-key")
kubectl create secret generic google-vertexai-api-key --from-literal=key="$API_KEY" -n ikuchio-cup-2025

# 強制Pod削除（スタック時）
kubectl delete pods -l app=ikuchio-backend -n ikuchio-cup-2025 --force --grace-period=0
```