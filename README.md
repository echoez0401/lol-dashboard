# LoL戦績ダッシュボード

League of Legendsの個人戦績を可視化する静的Webダッシュボードです。Riot Games APIから試合データを取得し、GitHub Pagesで公開できます。

![Dashboard Preview](docs/assets/placeholder.png)

## 特徴

- **完全無料**: GitHub Pages + GitHub Actionsで運用コスト$0
- **自動更新**: GitHub Actionsで定期的にデータを取得・更新
- **静的サイト**: サーバー不要、高速表示
- **ダークテーマ**: 目に優しいミニマルデザイン
- **レスポンシブ対応**: PC・タブレットで快適に閲覧

## 機能一覧

### チャンピオン統計
- チャンピオン別の試合数・勝率・KDA
- 平均与ダメージ・被ダメージの表示
- カラムクリックでソート可能

### 試合履歴
- 直近20試合の詳細表示
- 勝敗・使用チャンピオン・KDA
- 試合時間・ゲームモード

### フィルタリング
- **期間フィルター**:
  - 全期間
  - 最近7日/30日
  - 今週/先週
  - パッチ別（最新5パッチ）
- **モードフィルター**:
  - 全モード
  - ランクソロ/デュオ
  - ランクフレックス
  - ノーマル・ARAM・その他

### 試合詳細
- 試合カードクリックでモーダル表示
- 全10人のプレイヤー情報
- チーム別表示（青/赤）
- アイテム・ルーン情報

## セットアップ手順

### 1. リポジトリの準備

#### Forkする場合
1. このリポジトリの右上「Fork」ボタンをクリック
2. 自分のGitHubアカウントにFork

#### Cloneする場合
```bash
git clone https://github.com/yourusername/lol-dashboard.git
cd lol-dashboard
```

### 2. Riot API Key取得

1. [Riot Developer Portal](https://developer.riotgames.com/)にアクセス
2. Riotアカウントでログイン
3. 「REGISTER PRODUCT」をクリック
4. **Personal API Key**をコピー
   - 注意: 24時間で失効します
   - Production API Keyの申請も可能（長期運用の場合）

### 3. GitHub Secrets設定

1. リポジトリの「Settings」タブを開く
2. 左メニューから「Secrets and variables」→「Actions」を選択
3. 「New repository secret」をクリック

#### 必要なSecrets

**RIOT_API_KEY**
- Name: `RIOT_API_KEY`
- Value: Riot Developer Portalで取得したAPI Key
- 例: `RGAPI-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

**SUMMONER_NAME**
- Name: `SUMMONER_NAME`
- Value: 自分のサマナー名
- 例: `Hide on bush`（Faker選手のサマナー名）

### 4. GitHub Pages有効化

1. リポジトリの「Settings」タブを開く
2. 左メニューから「Pages」を選択
3. **Source**を「GitHub Actions」に変更
4. 「Save」をクリック

### 5. GitHub Actions実行

#### 初回実行
1. リポジトリの「Actions」タブを開く
2. 左メニューから「Update Dashboard」を選択
3. 右上の「Run workflow」ボタンをクリック
4. 「Run workflow」を再度クリックして実行開始

#### 実行状況の確認
- 黄色のアイコン: 実行中
- 緑のチェックマーク: 成功
- 赤のバツマーク: 失敗（ログで原因を確認）

#### 定期実行の設定（オプション）
`.github/workflows/update.yml`に以下を追加すると自動更新されます：

```yaml
on:
  workflow_dispatch:  # 手動実行
  schedule:
    - cron: '0 */6 * * *'  # 6時間ごとに実行
```

### 6. ダッシュボードにアクセス

GitHub Actionsの実行が成功したら、以下のURLでアクセスできます：

```
https://yourusername.github.io/lol-dashboard/
```

## 使い方

### データ更新

GitHub Actionsを手動実行することで、最新の試合データを取得できます：

1. Actionsタブ → Update Dashboard
2. Run workflow → Run workflow

### フィルター操作

#### 期間フィルター
- プルダウンメニューから期間を選択
- 統計とマッチ履歴が自動更新されます

#### モードフィルター
- ランクソロのみ、ARAMのみなどで絞り込み可能

### 試合詳細表示

1. 試合履歴カードをクリック
2. モーダルで詳細情報を表示
3. ×ボタンまたはモーダル外クリックで閉じる

## プロジェクト構造

```
lol-dashboard/
├── .github/
│   └── workflows/
│       └── update.yml          # GitHub Actions設定
├── data/
│   └── matches.json            # 試合データ（自動生成）
├── docs/                       # GitHub Pages公開ディレクトリ
│   ├── css/
│   │   └── style.css          # スタイルシート
│   ├── js/
│   │   └── dashboard.js       # フロントエンドロジック
│   ├── assets/
│   │   └── placeholder.png    # フォールバック画像
│   └── index.html             # メインHTML（自動生成）
├── src/
│   ├── __init__.py
│   ├── utils.py               # 共通ユーティリティ
│   ├── fetch_matches.py       # Riot APIデータ取得
│   ├── calculate_stats.py    # 統計計算
│   └── generate_html.py       # HTML生成
├── templates/
│   ├── base.html              # ベーステンプレート
│   ├── index.html             # メインテンプレート
│   └── components/            # コンポーネント
│       ├── champion_table.html
│       ├── match_history.html
│       └── match_detail_modal.html
├── config.json                # 設定ファイル
├── requirements.txt           # Python依存パッケージ
├── .gitignore
└── README.md
```

## トラブルシューティング

### GitHub Actionsが失敗する

#### エラー: "401 Unauthorized"
- **原因**: API Keyが無効または期限切れ
- **対処**: Riot Developer Portalで新しいAPI Keyを取得し、GitHub Secretsを更新

#### エラー: "403 Forbidden"
- **原因**: API Keyの権限不足
- **対処**: Production API Keyの申請を検討

#### エラー: "404 Not Found"
- **原因**: サマナー名が正しくない、または別リージョン
- **対処**:
  1. サマナー名のスペルを確認
  2. config.jsonのregionを確認（jp1, kr, na1など）

#### エラー: "429 Too Many Requests"
- **原因**: APIレート制限に到達
- **対処**: 自動的にRetry-Afterヘッダーに従って待機します（コード内で実装済み）

### GitHub Pagesが表示されない

#### ページが404エラー
1. Settings → Pagesで「GitHub Actions」が選択されているか確認
2. Actionsタブで「pages-build-deployment」が成功しているか確認
3. 数分待ってからリロード

#### CSSが適用されない
- ブラウザのキャッシュをクリア（Ctrl+Shift+R / Cmd+Shift+R）

### データが更新されない

1. Actionsタブで最新の実行ログを確認
2. Step 5 (Fetch match data)が成功しているか確認
3. Step 7 (Commit and push)で変更がコミットされているか確認

### チャンピオン画像が表示されない

- Data Dragon CDNの接続を確認
- ブラウザのコンソール（F12）でエラーを確認
- プレースホルダー画像が表示される場合は正常動作

## カスタマイズ

### 表示件数の変更

`src/generate_html.py`の以下の行を編集：

```python
recent_matches = get_recent_matches(matches, count=20)  # 20を変更
```

### デザインの変更

`docs/css/style.css`でカラーやレイアウトをカスタマイズ：

```css
:root {
    --bg-primary: #0a0e27;     /* 背景色 */
    --accent-blue: #5383e8;    /* アクセントカラー */
    /* ... */
}
```

### 対応リージョンの追加

`src/utils.py`の`BASE_URLS`に追加：

```python
BASE_URLS = {
    "jp1": "https://jp1.api.riotgames.com",
    "kr": "https://kr.api.riotgames.com",
    "na1": "https://na1.api.riotgames.com",
    # 他のリージョンを追加...
}
```

## 技術スタック

### バックエンド
- Python 3.11
- Riot Games API
- Jinja2 (テンプレートエンジン)

### フロントエンド
- HTML5 / CSS3
- Vanilla JavaScript
- Data Dragon CDN

### インフラ
- GitHub Actions (CI/CD)
- GitHub Pages (ホスティング)

## ライセンス

MIT License

Copyright (c) 2026 LoL Dashboard Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## 免責事項

このプロジェクトはRiot Gamesが承認しておらず、Riot Gamesまたは League of Legendsの製作・管理に正式に関与した者の見解や意見を反映するものではありません。League of LegendsおよびRiot GamesはRiot Games, Inc.の商標または登録商標です。

## 貢献

プルリクエストやIssueの報告を歓迎します！

### 開発環境のセットアップ

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/lol-dashboard.git
cd lol-dashboard

# 仮想環境を作成
python -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate

# 依存パッケージをインストール
pip install -r requirements.txt

# 環境変数を設定
export RIOT_API_KEY="your_api_key"
export SUMMONER_NAME="your_summoner_name"

# データ取得とHTML生成
python src/fetch_matches.py
python src/generate_html.py

# ローカルでプレビュー
cd docs
python -m http.server 8000
# ブラウザで http://localhost:8000 にアクセス
```

## 参考リンク

- [Riot Developer Portal](https://developer.riotgames.com/)
- [Riot Games API Documentation](https://developer.riotgames.com/apis)
- [Data Dragon Documentation](https://developer.riotgames.com/docs/lol#data-dragon)
- [GitHub Actions Documentation](https://docs.github.com/actions)
- [GitHub Pages Documentation](https://docs.github.com/pages)

---

**楽しいLoLライフを！** 🎮✨
