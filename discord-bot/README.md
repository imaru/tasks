# Discord 定期投稿 Bot

指定した Discord スレッドに、cron で定期的にメッセージを投稿するスクリプト。
投稿のたびに前回の投稿を削除するので、スレッドに常に最新の1件だけが残る。

## ファイル構成

```
discord-bot/
├── post_discord.py     # 投稿スクリプト本体
├── threads.txt         # 投稿先スレッドIDのリスト
├── .env                # Bot Token・メッセージ・プロキシ設定（git管理外）
├── .env.example        # .env のテンプレート
├── last_messages.json  # 前回の投稿IDを記録（自動生成）
└── post.log            # 実行ログ（自動生成）
```

## セットアップ

### 1. Discord Bot の準備

1. [Discord Developer Portal](https://discord.com/developers/applications) でアプリを作成
2. Bot を追加して Token をコピー
3. 以下の OAuth2 URL でサーバーに招待（`YOUR_APP_ID` を置き換える）
   ```
   https://discord.com/oauth2/authorize?client_id=YOUR_APP_ID&permissions=2048&scope=bot
   ```
4. 投稿先スレッドの**親チャンネル**に Bot を個別権限で追加
   - View Channel
   - Send Messages in Threads
   - Manage Threads（アーカイブ済みスレッドへの投稿に必要）

> **注意:** ロールへの一括権限付与ではなく、チャンネルごとの個別権限設定が必要。
> Admin 権限はチャンネル個別の拒否設定を無視するため動くが、セキュリティリスクがあるので避ける。

### 2. スレッドID の取得

Discord の設定 → 詳細設定 → **開発者モード** をON にして、スレッドを右クリック → 「IDをコピー」。

### 3. 設定ファイルの作成

```bash
cp .env.example .env
```

`.env` を編集：

```env
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_MESSAGE=投稿するメッセージ

# プロキシ環境下の場合のみ設定
HTTP_PROXY=http://proxy.example.com:8080
HTTPS_PROXY=http://proxy.example.com:8080
```

`threads.txt` にスレッドIDを追記（`#` でコメント可）：

```
# サーバーAのスレッド
1234567890123456789

# サーバーBのスレッド
9876543210987654321
```

### 4. 依存パッケージのインストール

```bash
pip3 install requests python-dotenv
```

Python 3.10 以上が必要（`str | None` 型ヒントを使用）。

### 5. 動作確認

```bash
python3 post_discord.py
```

### 6. cron に登録

```bash
crontab -e
```

例（毎日9時に実行）：

```
0 9 * * * python3 /path/to/discord-bot/post_discord.py
```

## 動作仕様

- `threads.txt` の全スレッドに同一メッセージを投稿
- 投稿成功後、前回の投稿（`last_messages.json` に記録）を削除
- 投稿失敗時は前回の投稿を削除しない（メッセージが消えるだけの事故を防ぐ）
- 実行結果は `post.log` に記録

## トラブルシューティング

| エラー | 原因 | 対処 |
|--------|------|------|
| `403 Missing Access` | Bot がチャンネル権限を持っていない | 親チャンネルに Bot を個別権限で追加 |
| `TypeError: unsupported operand type(s) for \|` | Python が 3.9 以下 | Python 3.10 以上にアップグレード |
| プロキシ越えができない | cron が環境変数を引き継がない | `.env` に `HTTP_PROXY`/`HTTPS_PROXY` を設定 |
