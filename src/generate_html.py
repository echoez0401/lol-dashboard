"""
LoL戦績ダッシュボード - HTML生成モジュール

統計データから静的HTMLを生成します。
"""

import os
import json
import requests
from jinja2 import Environment, FileSystemLoader

from calculate_stats import (
    calculate_champion_stats,
    get_recent_matches,
    get_available_patches,
    get_available_modes
)


def get_latest_ddragon_version() -> str:
    """
    Data Dragon最新バージョンを取得

    Returns:
        バージョン文字列（例: "14.3.1"）
        失敗時は "14.3.1" をフォールバック値として返す
    """
    try:
        response = requests.get(
            "https://ddragon.leagueoflegends.com/api/versions.json",
            timeout=10
        )
        response.raise_for_status()
        versions = response.json()

        if versions and len(versions) > 0:
            return versions[0]
    except Exception as e:
        print(f"Warning: Failed to fetch Data Dragon version: {e}")
        print("Using fallback version: 14.3.1")

    # フォールバック
    return "14.3.1"


def generate_dashboard() -> None:
    """
    ダッシュボードHTMLを生成

    処理フロー:
        1. data/matches.json読み込み
        2. 統計計算
        3. Jinja2テンプレート読み込み
        4. レンダリング
        5. docs/index.htmlに出力
    """
    # 1. data/matches.json読み込み
    matches_path = "data/matches.json"

    if not os.path.exists(matches_path):
        raise FileNotFoundError(f"{matches_path} not found. Please run fetch_matches.py first.")

    print(f"Loading {matches_path}...")
    with open(matches_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    summoner = data.get("summoner", {})
    last_update = data.get("last_update", "")
    matches = data.get("matches", [])

    print(f"Loaded {len(matches)} matches")

    if not matches:
        print("Warning: No matches found in data")
        matches = []

    # 2. 統計計算
    print("Calculating champion stats...")
    champion_stats = calculate_champion_stats(matches, "all", "all")

    print("Getting recent matches...")
    recent_matches = get_recent_matches(matches, 20)

    print("Getting available patches...")
    available_patches = get_available_patches(matches)

    print("Getting available modes...")
    available_modes = get_available_modes(matches)

    print("Fetching Data Dragon version...")
    ddragon_version = get_latest_ddragon_version()

    print(f"Using Data Dragon version: {ddragon_version}")

    # 3. Jinja2環境設定
    print("Setting up Jinja2 environment...")
    template_dir = "templates"

    if not os.path.exists(template_dir):
        raise FileNotFoundError(f"Templates directory '{template_dir}' not found")

    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=True  # セキュリティ対策: 自動エスケープ有効
    )

    # 4. テンプレート読み込み
    print("Loading index.html template...")
    try:
        template = env.get_template("index.html")
    except Exception as e:
        print(f"Error loading template: {e}")
        raise

    # 5. レンダリング
    print("Rendering template...")

    # 全試合データをJSON文字列に変換
    all_matches_json = json.dumps(matches, ensure_ascii=False)

    html_content = template.render(
        summoner=summoner,
        last_update=last_update,
        champion_stats=champion_stats,
        recent_matches=recent_matches,
        available_patches=available_patches,
        available_modes=available_modes,
        ddragon_version=ddragon_version,
        all_matches_json=all_matches_json
    )

    # 6. docs/index.htmlに出力
    output_dir = "docs"
    output_path = os.path.join(output_dir, "index.html")

    os.makedirs(output_dir, exist_ok=True)

    print(f"Writing to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Successfully generated {output_path}")
    print(f"  - Champions: {len(champion_stats)}")
    print(f"  - Recent matches: {len(recent_matches)}")
    print(f"  - Available patches: {len(available_patches)}")
    print(f"  - Available modes: {len(available_modes)}")


def main():
    """エントリーポイント"""
    try:
        generate_dashboard()
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
