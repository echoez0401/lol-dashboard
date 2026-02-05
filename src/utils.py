"""
LoL戦績ダッシュボード - ユーティリティモジュール

共通処理、定数定義、エラークラスを提供します。
"""

from datetime import datetime


# ========================================
# API関連定数
# ========================================

BASE_URLS = {
    "jp1": "https://jp1.api.riotgames.com",
    "kr": "https://kr.api.riotgames.com",
    "na1": "https://na1.api.riotgames.com",
    "euw1": "https://euw1.api.riotgames.com",
    "eun1": "https://eun1.api.riotgames.com",
    "br1": "https://br1.api.riotgames.com",
    "la1": "https://la1.api.riotgames.com",
    "la2": "https://la2.api.riotgames.com",
    "oc1": "https://oc1.api.riotgames.com",
    "tr1": "https://tr1.api.riotgames.com",
    "ru": "https://ru.api.riotgames.com",
    "asia": "https://asia.api.riotgames.com",  # Match API用
    "americas": "https://americas.api.riotgames.com",  # Match API用
    "europe": "https://europe.api.riotgames.com",  # Match API用
    "sea": "https://sea.api.riotgames.com",  # Match API用
}

ENDPOINTS = {
    "summoner_by_name": "/lol/summoner/v4/summoners/by-name/{summonerName}",
    "match_ids": "/lol/match/v5/matches/by-puuid/{puuid}/ids",
    "match_detail": "/lol/match/v5/matches/{matchId}",
}


# ========================================
# ゲームモード定数
# ========================================

QUEUE_NAMES = {
    420: "ランクソロ/デュオ",
    440: "ランクフレックス",
    400: "ノーマル（ドラフト）",
    430: "ノーマル（ブラインド）",
    450: "ARAM",
    1700: "Arena",
    1900: "URF",
}


# ========================================
# エラークラス
# ========================================

class RiotAPIError(Exception):
    """Riot API エラーの基底クラス"""
    pass


class RateLimitError(RiotAPIError):
    """429 Rate Limit Exceeded エラー専用"""
    pass


class DataNotFoundError(RiotAPIError):
    """404 Not Found エラー専用"""
    pass


# ========================================
# ユーティリティ関数
# ========================================

def format_duration(seconds: int) -> str:
    """
    秒を「MM分SS秒」形式に変換

    Args:
        seconds: 秒数

    Returns:
        フォーマットされた文字列（例: "30分30秒"）
    """
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    return f"{minutes}分{remaining_seconds:02d}秒"


def format_timestamp(timestamp_ms: int) -> str:
    """
    Unix timestamp (ms)を日本語日時文字列に変換

    Args:
        timestamp_ms: Unix timestamp (ミリ秒)

    Returns:
        フォーマットされた日時文字列（例: "2024-02-02 14:00"）
    """
    timestamp_s = timestamp_ms / 1000
    dt = datetime.fromtimestamp(timestamp_s)
    return dt.strftime("%Y-%m-%d %H:%M")


def get_queue_name(queue_id: int) -> str:
    """
    queueIdからゲームモード名を取得

    Args:
        queue_id: キューID

    Returns:
        ゲームモード名（未定義の場合は "その他 ({queue_id})"）
    """
    return QUEUE_NAMES.get(queue_id, f"その他 ({queue_id})")
