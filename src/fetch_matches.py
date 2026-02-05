"""
LoL戦績ダッシュボード - 試合データ取得モジュール

Riot Games APIから試合データを取得し、内部形式に変換してJSONに保存します。
"""

import os
import json
import time
import requests
from datetime import datetime
from typing import Optional

from utils import (
    BASE_URLS,
    ENDPOINTS,
    RiotAPIError,
    RateLimitError,
    DataNotFoundError
)


class RiotAPIClient:
    """Riot Games APIクライアント"""

    def __init__(self, api_key: str, region: str = "jp1"):
        """
        初期化

        Args:
            api_key: Riot API Key
            region: リージョン（デフォルト: jp1）
        """
        self.api_key = api_key
        self.region = region
        self.platform_base_url = BASE_URLS.get(region)

        # Match API用のリージョナルエンドポイント
        # jp1, kr -> asia
        # na1, br1, la1, la2 -> americas
        # euw1, eun1, tr1, ru -> europe
        regional_mapping = {
            "jp1": "asia",
            "kr": "asia",
            "na1": "americas",
            "br1": "americas",
            "la1": "americas",
            "la2": "americas",
            "euw1": "europe",
            "eun1": "europe",
            "tr1": "europe",
            "ru": "europe",
            "oc1": "sea",
        }
        regional_endpoint = regional_mapping.get(region, "asia")
        self.regional_base_url = BASE_URLS.get(regional_endpoint)

    def _request(self, url: str, params: Optional[dict] = None) -> dict:
        """
        HTTP GETリクエストの共通処理

        Args:
            url: リクエストURL
            params: クエリパラメータ

        Returns:
            JSONレスポンス

        Raises:
            RateLimitError: 429エラー時
            DataNotFoundError: 404エラー時
            RiotAPIError: その他のAPIエラー
        """
        headers = {
            "X-Riot-Token": self.api_key
        }

        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                response = requests.get(url, headers=headers, params=params, timeout=10)

                # 429 Rate Limit Exceeded
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 120))
                    print(f"Rate limit hit. Waiting {retry_after}s...")
                    time.sleep(retry_after)
                    continue

                # 404 Not Found
                if response.status_code == 404:
                    print(f"Data not found: {url}")
                    raise DataNotFoundError(f"Data not found: {url}")

                # 5xx Server Error
                if 500 <= response.status_code < 600:
                    retry_count += 1
                    print(f"Server error: {response.status_code}. Retry {retry_count}/{max_retries}")
                    if retry_count < max_retries:
                        time.sleep(5)
                        continue
                    else:
                        raise RiotAPIError(f"Server error after {max_retries} retries: {response.status_code}")

                # その他の4xxエラー
                if 400 <= response.status_code < 500:
                    raise RiotAPIError(f"Client error: {response.status_code} - {response.text}")

                # 成功
                response.raise_for_status()

                # レート制限対策
                time.sleep(1.2)

                return response.json()

            except requests.exceptions.RequestException as e:
                retry_count += 1
                print(f"Request exception: {e}. Retry {retry_count}/{max_retries}")
                if retry_count < max_retries:
                    time.sleep(5)
                    continue
                else:
                    raise RiotAPIError(f"Request failed after {max_retries} retries: {e}")

        raise RiotAPIError("Unexpected error in _request")

    def get_summoner(self, summoner_name: str) -> dict:
        """
        サマナー情報を取得

        Args:
            summoner_name: サマナー名

        Returns:
            サマナー情報 {id, accountId, puuid, name, summonerLevel, ...}

        Raises:
            RiotAPIError: 取得失敗時
        """
        endpoint = ENDPOINTS["summoner_by_name"].format(summonerName=summoner_name)
        url = self.platform_base_url + endpoint
        return self._request(url)

    def get_match_ids(self, puuid: str, start: int = 0, count: int = 100) -> list[str]:
        """
        試合IDリストを取得

        Args:
            puuid: プレイヤーのPUUID
            start: オフセット（0始まり）
            count: 取得件数（最大100）

        Returns:
            試合IDの配列（新しい順）

        Raises:
            RateLimitError: レート制限時
        """
        endpoint = ENDPOINTS["match_ids"].format(puuid=puuid)
        url = self.regional_base_url + endpoint
        params = {
            "start": start,
            "count": count
        }
        return self._request(url, params)

    def get_match_detail(self, match_id: str) -> dict:
        """
        試合詳細を取得

        Args:
            match_id: 試合ID

        Returns:
            Riot APIレスポンス

        Raises:
            RiotAPIError: 取得失敗時
        """
        endpoint = ENDPOINTS["match_detail"].format(matchId=match_id)
        url = self.regional_base_url + endpoint
        return self._request(url)

    def get_all_match_ids(self, puuid: str) -> list[str]:
        """
        全試合IDを取得（ページネーション処理）

        Args:
            puuid: プレイヤーのPUUID

        Returns:
            全試合IDリスト（新しい順）
        """
        all_ids = []
        start = 0
        count = 100

        while True:
            batch = self.get_match_ids(puuid, start, count)

            if not batch:
                break

            all_ids.extend(batch)

            if len(batch) < count:
                break

            start += count

        return all_ids


def process_match_data(raw_match: dict, puuid: str) -> dict:
    """
    Riot APIレスポンスを内部形式に変換

    Args:
        raw_match: Riot APIの生データ
        puuid: 自分のPUUID

    Returns:
        Match型のdict
    """
    info = raw_match["info"]
    participants = info["participants"]

    # 自分のデータを検索
    my_participant = None
    for p in participants:
        if p["puuid"] == puuid:
            my_participant = p
            break

    if not my_participant:
        raise ValueError(f"PUUID {puuid} not found in match participants")

    # アイテム購入履歴を抽出
    # Riot APIのタイムラインデータが必要だが、基本的な試合データには含まれていない
    # ここでは最終ビルド（item0-6）のみを記録
    items = []
    for i in range(7):
        item_id = my_participant.get(f"item{i}", 0)
        if item_id > 0:
            items.append({
                "itemId": item_id,
                "timestamp": 0  # タイムラインデータがないため0
            })

    # ルーン情報を抽出
    perks = my_participant.get("perks", {})
    styles = perks.get("styles", [])

    primary_runes = []
    secondary_runes = []
    stat_runes = []

    if len(styles) >= 1:
        # メインパス（キーストーン含む4つ）
        primary_selections = styles[0].get("selections", [])
        primary_runes = [s["perk"] for s in primary_selections[:4]]
        # 4つに満たない場合は0で埋める
        while len(primary_runes) < 4:
            primary_runes.append(0)

    if len(styles) >= 2:
        # サブパス（2つ）
        secondary_selections = styles[1].get("selections", [])
        secondary_runes = [s["perk"] for s in secondary_selections[:2]]
        # 2つに満たない場合は0で埋める
        while len(secondary_runes) < 2:
            secondary_runes.append(0)

    # ステータスルーン（3つ）
    stat_perks = perks.get("statPerks", {})
    stat_runes = [
        stat_perks.get("defense", 0),
        stat_perks.get("flex", 0),
        stat_perks.get("offense", 0)
    ]

    # 自分のデータ
    my_data = {
        "championName": my_participant["championName"],
        "kills": my_participant["kills"],
        "deaths": my_participant["deaths"],
        "assists": my_participant["assists"],
        "totalDamageDealtToChampions": my_participant["totalDamageDealtToChampions"],
        "totalDamageTaken": my_participant["totalDamageTaken"],
        "win": my_participant["win"],
        "items": items,
        "runes": {
            "primary": primary_runes,
            "secondary": secondary_runes,
            "stats": stat_runes
        }
    }

    # 全プレイヤーのデータ
    all_players = []
    for p in participants:
        # 各プレイヤーのルーン情報
        p_perks = p.get("perks", {})
        p_styles = p_perks.get("styles", [])

        p_primary = []
        p_secondary = []
        p_stats = []

        if len(p_styles) >= 1:
            p_primary_selections = p_styles[0].get("selections", [])
            p_primary = [s["perk"] for s in p_primary_selections[:4]]
            while len(p_primary) < 4:
                p_primary.append(0)

        if len(p_styles) >= 2:
            p_secondary_selections = p_styles[1].get("selections", [])
            p_secondary = [s["perk"] for s in p_secondary_selections[:2]]
            while len(p_secondary) < 2:
                p_secondary.append(0)

        p_stat_perks = p_perks.get("statPerks", {})
        p_stats = [
            p_stat_perks.get("defense", 0),
            p_stat_perks.get("flex", 0),
            p_stat_perks.get("offense", 0)
        ]

        # アイテム（最終ビルド）
        p_items = []
        for i in range(7):
            item_id = p.get(f"item{i}", 0)
            if item_id > 0:
                p_items.append(item_id)

        player_data = {
            "summonerName": p["summonerName"],
            "teamId": p["teamId"],
            "championName": p["championName"],
            "kills": p["kills"],
            "deaths": p["deaths"],
            "assists": p["assists"],
            "totalDamageDealtToChampions": p["totalDamageDealtToChampions"],
            "totalDamageTaken": p["totalDamageTaken"],
            "tier": p.get("tier"),
            "rank": p.get("rank"),
            "items": p_items,
            "runes": {
                "primary": p_primary,
                "secondary": p_secondary,
                "stats": p_stats
            }
        }
        all_players.append(player_data)

    # Match型に整形
    match_data = {
        "matchId": raw_match["metadata"]["matchId"],
        "gameCreation": info["gameCreation"],
        "queueId": info["queueId"],
        "gameDuration": info["gameDuration"],
        "gameVersion": info["gameVersion"],
        "myData": my_data,
        "allPlayers": all_players
    }

    return match_data


def fetch_new_matches(puuid: str, api_key: str, last_update: Optional[str] = None) -> list[dict]:
    """
    新規試合データを取得

    Args:
        puuid: プレイヤーのPUUID
        api_key: Riot API Key
        last_update: 前回更新日時（ISO 8601形式）。Noneなら全件取得

    Returns:
        Match型のリスト
    """
    client = RiotAPIClient(api_key)

    # 試合IDリスト取得
    if last_update is None:
        # 初回は全件取得
        print("Fetching all match IDs...")
        match_ids = client.get_all_match_ids(puuid)
    else:
        # 差分取得
        print(f"Fetching matches since {last_update}...")
        last_update_timestamp = int(datetime.fromisoformat(last_update.replace('Z', '+00:00')).timestamp() * 1000)

        match_ids = []
        start = 0
        count = 100

        while True:
            batch = client.get_match_ids(puuid, start, count)

            if not batch:
                break

            # バッチの最初の試合の日時をチェック
            first_match = client.get_match_detail(batch[0])
            first_match_time = first_match["info"]["gameCreation"]

            if first_match_time < last_update_timestamp:
                # このバッチより前の試合は不要
                # バッチ内で該当する試合のみ追加
                for match_id in batch:
                    match_detail = client.get_match_detail(match_id)
                    if match_detail["info"]["gameCreation"] >= last_update_timestamp:
                        match_ids.append(match_id)
                    else:
                        break
                break

            match_ids.extend(batch)

            if len(batch) < count:
                break

            start += count

    print(f"Found {len(match_ids)} matches to fetch")

    # 各試合の詳細を取得して変換
    matches = []
    for i, match_id in enumerate(match_ids, 1):
        try:
            print(f"Fetching match {i}/{len(match_ids)}: {match_id}")
            raw_match = client.get_match_detail(match_id)
            match_data = process_match_data(raw_match, puuid)
            matches.append(match_data)
        except DataNotFoundError:
            print(f"Skipping match {match_id} (not found)")
            continue
        except KeyError as e:
            print(f"Warning: Missing field in match {match_id}: {e}")
            continue
        except Exception as e:
            print(f"Error processing match {match_id}: {e}")
            continue

    return matches


def main():
    """データ取得のエントリーポイント"""
    # 環境変数から取得
    api_key = os.getenv("RIOT_API_KEY")
    summoner_name = os.getenv("SUMMONER_NAME")

    if not api_key:
        raise ValueError("RIOT_API_KEY environment variable is required")
    if not summoner_name:
        raise ValueError("SUMMONER_NAME environment variable is required")

    # config.json読み込み（リージョン情報など）
    config_path = "config.json"
    config = {}
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

    region = config.get("region", "jp1")

    # サマナー情報取得
    print(f"Fetching summoner info for: {summoner_name}")
    client = RiotAPIClient(api_key, region)
    summoner = client.get_summoner(summoner_name)
    puuid = summoner["puuid"]

    print(f"PUUID: {puuid}")

    # 既存データの読み込み
    matches_path = "data/matches.json"
    existing_data = {
        "last_update": None,
        "summoner": {
            "name": summoner["name"],
            "puuid": puuid,
            "region": region
        },
        "matches": []
    }

    if os.path.exists(matches_path):
        print("Loading existing matches...")
        with open(matches_path, "r", encoding="utf-8") as f:
            existing_data = json.load(f)

    last_update = existing_data.get("last_update")
    existing_matches = existing_data.get("matches", [])

    # 新規データ取得
    new_matches = fetch_new_matches(puuid, api_key, last_update)

    print(f"Fetched {len(new_matches)} new matches")

    # マージ
    all_matches = existing_matches + new_matches

    # 重複排除（matchIdでユニーク化）
    unique_matches = {}
    for match in all_matches:
        match_id = match["matchId"]
        unique_matches[match_id] = match

    # gameCreationでソート（降順）
    sorted_matches = sorted(
        unique_matches.values(),
        key=lambda m: m["gameCreation"],
        reverse=True
    )

    print(f"Total unique matches: {len(sorted_matches)}")

    # 保存
    output_data = {
        "last_update": datetime.now().isoformat(),
        "summoner": {
            "name": summoner["name"],
            "puuid": puuid,
            "region": region
        },
        "matches": sorted_matches
    }

    os.makedirs("data", exist_ok=True)
    with open(matches_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"Saved to {matches_path}")


if __name__ == "__main__":
    main()
