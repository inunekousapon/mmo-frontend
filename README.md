## Frontend Client

- デスクトップ動作:

```bash
uv run python main.py
```

- Web ビルドをプレビューする場合（ローカル HTTP サーバー 8000 番）:

```bash
uv run pygbag --port 8000 .
```

- フロントエンドからは `ws://localhost:8080` へ WebSocket で接続し、キー入力状態のみを送信します（位置計算はバックエンドが担当）。

