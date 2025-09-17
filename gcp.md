# GCP サービス構成詳細

## プロジェクト概要
- **プロジェクト名**: ikuchio-cup-2025
- **リージョン**: asia-northeast1 (東京)
- **課金方式**: 従量課金 + 無料クレジット活用

## 使用中のGCPサービス

### 1. Google Kubernetes Engine (GKE) Autopilot
**用途**: コンテナオーケストレーション・自動スケーリング

**設定**:
- クラスター名: autopilot-cluster-1
- モード: Autopilot (フルマネージド)
- リージョン: asia-northeast1
- ノードプール: 自動管理
- 自動スケーリング: 1-100 Pod (バックエンド), 1-50 Pod (フロントエンド)

**料金**:
- Pod使用時間のみ課金
- 平常時: 月額 ¥1,000-3,000
- 高負荷時: 自動スケール (最大 ¥50,000/月)

**最適化機能**:
- HorizontalPodAutoscaler (CPU 50%, Memory 60%)
- Pod Disruption Budget (高可用性)
- Pod Anti-Affinity (分散配置)
- Network Policy (セキュリティ)
- Resource Quota (コスト制御)

### 2. Google Container Registry (GCR)
**用途**: Dockerイメージ保存・配信

**設定**:
- レジストリ: gcr.io/ikuchio-cup-2025
- イメージ:
  - ikuchio-backend:latest (FastAPI)
  - ikuchio-frontend:latest (Vue.js + Nginx)

**料金**:
- ストレージ: ¥26/GB/月
- ネットワーク: ¥12/GB (ダウンロード)
- 予想コスト: ¥100-500/月

### 3. Cloud Firestore
**用途**: NoSQLデータベース (ユーザー・ルーム・メッセージ)

**データ構造**:
```
users/{user_id}
  - firebase_uid: string
  - created_at: timestamp
  - room_id: string

rooms/{room_id}
  - id: string
  - created_at: timestamp
  - users: array

messages/{message_id}
  - room_id: string
  - original_sender_id: string
  - original_text: string
  - processed_text: string
  - created_at: timestamp
```

**料金**:
- 読み取り: ¥0.036/10万回
- 書き込み: ¥0.18/10万回
- ストレージ: ¥0.18/GB/月
- 予想コスト: ¥500-2,000/月

### 4. Vertex AI (Gemini 2.5 Pro)
**用途**: メッセージ処理・個人情報匿名化

**機能**:
- テキスト解析・匿名化
- 自然言語処理
- コンテキスト保持

**料金**:
- 入力: ¥0.00125/1Kトークン
- 出力: ¥0.005/1Kトークン
- 予想コスト: ¥1,000-5,000/月

### 5. Secret Manager
**用途**: API Key・機密情報管理

**保存データ**:
- google-vertexai-api-key: Vertex AI認証キー
- Firebase設定情報

**料金**:
- アクティブシークレット: ¥6/月/シークレット
- アクセス: ¥0.03/1万回
- 予想コスト: ¥50-100/月

### 6. Cloud Build
**用途**: CI/CD・自動デプロイ

**設定**:
- トリガー: GitHub push (main branch)
- ビルド: Docker イメージ作成
- デプロイ: GKE自動更新

**料金**:
- 無料枠: 120分/日
- 超過分: ¥0.003/分
- 予想コスト: ¥0-1,000/月

### 7. Cloud Logging
**用途**: ログ収集・監視 (Autopilot自動設定)

**機能**:
- アプリケーションログ
- システムログ
- エラー追跡

**料金**:
- 無料枠: 50GB/月
- 超過分: ¥0.50/GB
- 予想コスト: ¥0-500/月

### 8. Cloud Monitoring
**用途**: メトリクス監視 (Autopilot自動設定)

**監視項目**:
- CPU・メモリ使用率
- Pod数・レプリカ数
- レスポンス時間

**料金**:
- 無料枠: 150MB/月
- 超過分: ¥0.258/MB
- 予想コスト: ¥0-300/月

## 外部サービス連携

### Firebase Authentication
**用途**: 匿名認証・ユーザー管理

**設定**:
- 匿名認証有効
- Firebase Admin SDK (サーバーサイド)

**料金**: 無料 (匿名認証)

### Cloudflare
**用途**: DNS・CDN・DDoS保護・SSL

**設定**:
- ドメイン: krz-tech.net
- SSL: Full Strict
- プロキシ: 有効 (フロントエンド)

**料金**: 無料プラン

## 月額コスト予想

### 平常時 (低負荷)
- GKE Autopilot: ¥2,000
- Firestore: ¥500
- Vertex AI: ¥1,000
- その他: ¥500
- **合計: ¥4,000/月**

### 高負荷時
- GKE Autopilot: ¥20,000 (50Pod稼働)
- Firestore: ¥3,000
- Vertex AI: ¥8,000
- その他: ¥1,000
- **合計: ¥32,000/月**

## セキュリティ設定

### IAM・権限管理
- Workload Identity: GKE ↔ GCP サービス連携
- 最小権限の原則
- サービスアカウント分離

### ネットワークセキュリティ
- Network Policy: Pod間通信制御
- Private Cluster: 内部IP通信
- Firewall Rules: 必要ポートのみ開放

### データ保護
- Firestore Security Rules: 認証済みユーザーのみ
- Secret Manager: 暗号化保存
- SSL/TLS: 全通信暗号化

## 監視・運用

### 自動化機能
- Pod自動復旧 (Liveness Probe)
- 負荷分散 (Readiness Probe)
- スケーリング (HPA)
- セキュリティ更新 (Autopilot)

### アラート設定
- CPU使用率 > 80%
- メモリ使用率 > 90%
- エラー率 > 5%
- レスポンス時間 > 2秒

## 災害復旧・バックアップ

### データバックアップ
- Firestore: 自動バックアップ (Point-in-time recovery)
- Container Images: GCR冗長化
- 設定ファイル: GitHub管理

### 可用性設計
- Multi-Zone配置 (GKE Autopilot)
- Pod Disruption Budget
- Load Balancer冗長化
- DNS Failover (Cloudflare)

## 最適化ポイント

### コスト最適化
- Autopilot従量課金活用
- 最小リソース設定 (CPU 50m-100m)
- 自動スケールダウン (5分後)
- 無料枠最大活用

### パフォーマンス最適化
- 東京リージョン (低レイテンシ)
- CDN活用 (Cloudflare)
- WebSocket最適化
- Pod Anti-Affinity (分散)

### 運用最適化
- GitOps (GitHub → Cloud Build → GKE)
- Infrastructure as Code (Kubernetes YAML)
- 自動監視・アラート
- ログ集約・分析