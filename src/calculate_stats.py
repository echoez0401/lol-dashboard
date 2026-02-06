"""
LoL戦績ダッシュボード - 統計計算モジュール

試合データから統計を計算し、フィルタリング処理を提供します。
"""

from datetime import datetime, timedelta
from typing import Optional

from utils import get_queue_name


def calculate_champion_stats(matches: list[dict], period: str = "all", mode: str = "all") -> list[dict]:
    """
    チャンピオン別統計を計算

    Args:
        matches: Match型のリスト
        period: 期間フィルター（"all", "patch_X.Y", "this_week", "last_week", "last_30_days"）
        mode: モードフィルター（"all" or queueId文字列）

    Returns:
        ChampionStats型のリスト（試合数降順でソート）
    """
    # フィルタリング
    filtered_matches = filter_matches(matches, period, mode)

    if not filtered_matches:
        return []

    # チャンピオン名ごとに集計用dictを作成
    champion_aggregates = {}

    for match in filtered_matches:
        my_data = match["myData"]
        champion_name = my_data["championName"]

        if champion_name not in champion_aggregates:
            champion_aggregates[champion_name] = {
                "championName": champion_name,
                "games": 0,
                "wins": 0,
                "totalKills": 0,
                "totalDeaths": 0,
                "totalAssists": 0,
                "totalDamageDealt": 0,
                "totalDamageTaken": 0,
            }

        agg = champion_aggregates[champion_name]
        agg["games"] += 1

        if my_data["win"]:
            agg["wins"] += 1

        agg["totalKills"] += my_data["kills"]
        agg["totalDeaths"] += my_data["deaths"]
        agg["totalAssists"] += my_data["assists"]
        agg["totalDamageDealt"] += my_data["totalDamageDealtToChampions"]
        agg["totalDamageTaken"] += my_data["totalDamageTaken"]

    # 統計値計算
    champion_stats = []
    for champion_name, agg in champion_aggregates.items():
        games = agg["games"]
        wins = agg["wins"]
        losses = games - wins
        total_kills = agg["totalKills"]
        total_deaths = agg["totalDeaths"]
        total_assists = agg["totalAssists"]

        # 勝率
        win_rate = (wins / games * 100) if games > 0 else 0

        # 平均KDA比率（ゼロ除算回避）
        avg_kda = (total_kills + total_assists) / (total_deaths or 1)

        # 平均ダメージ
        avg_damage_dealt = agg["totalDamageDealt"] / games if games > 0 else 0
        avg_damage_taken = agg["totalDamageTaken"] / games if games > 0 else 0

        stat = {
            "championName": champion_name,
            "games": games,
            "wins": wins,
            "losses": losses,
            "winRate": round(win_rate, 1),
            "totalKills": total_kills,
            "totalDeaths": total_deaths,
            "totalAssists": total_assists,
            "avgKDA": round(avg_kda, 2),
            "avgDamageDealt": round(avg_damage_dealt),
            "avgDamageTaken": round(avg_damage_taken),
        }
        champion_stats.append(stat)

    # 試合数でソート（降順）
    champion_stats.sort(key=lambda s: s["games"], reverse=True)

    return champion_stats


def filter_matches(matches: list[dict], period: str = "all", mode: str = "all") -> list[dict]:
    """
    試合データをフィルタリング

    Args:
        matches: Match型のリスト
        period: 期間フィルター
        mode: モードフィルター

    Returns:
        フィルタ後のMatch型リスト
    """
    filtered = matches.copy()

    # 期間フィルター
    if period != "all":
        if period.startswith("patch_"):
            # パッチバージョンフィルター（例: "patch_14.3"）
            patch_version = period.replace("patch_", "")
            filtered = [
                m for m in filtered
                if m["gameVersion"].startswith(patch_version)
            ]
        elif period == "this_week":
            # 今週月曜0時以降
            now = datetime.now()
            monday = now - timedelta(days=now.weekday())
            monday_start = monday.replace(hour=0, minute=0, second=0, microsecond=0)
            threshold = int(monday_start.timestamp() * 1000)
            filtered = [
                m for m in filtered
                if m["gameCreation"] >= threshold
            ]
        elif period == "last_week":
            # 先週月曜0時〜今週月曜0時
            now = datetime.now()
            this_monday = now - timedelta(days=now.weekday())
            this_monday_start = this_monday.replace(hour=0, minute=0, second=0, microsecond=0)
            last_monday = this_monday_start - timedelta(days=7)
            start_threshold = int(last_monday.timestamp() * 1000)
            end_threshold = int(this_monday_start.timestamp() * 1000)
            filtered = [
                m for m in filtered
                if start_threshold <= m["gameCreation"] < end_threshold
            ]
        elif period == "last_30_days":
            # 30日前以降
            now = datetime.now()
            thirty_days_ago = now - timedelta(days=30)
            threshold = int(thirty_days_ago.timestamp() * 1000)
            filtered = [
                m for m in filtered
                if m["gameCreation"] >= threshold
            ]
        elif period == "last_7_days":
            # 7日前以降
            now = datetime.now()
            seven_days_ago = now - timedelta(days=7)
            threshold = int(seven_days_ago.timestamp() * 1000)
            filtered = [
                m for m in filtered
                if m["gameCreation"] >= threshold
            ]

    # モードフィルター
    if mode != "all":
        try:
            queue_id = int(mode)
            filtered = [
                m for m in filtered
                if m["queueId"] == queue_id
            ]
        except ValueError:
            # modeが数値でない場合はフィルタしない
            pass

    return filtered


def get_recent_matches(matches: list[dict], count: int = 20) -> list[dict]:
    """
    直近N試合を取得

    Args:
        matches: Match型のリスト
        count: 取得件数（デフォルト: 20）

    Returns:
        Match型のリスト（直近N件）
    """
    # gameCreationでソート（降順）
    sorted_matches = sorted(matches, key=lambda m: m["gameCreation"], reverse=True)

    # 先頭N件を返す
    return sorted_matches[:count]


def get_available_patches(matches: list[dict]) -> list[str]:
    """
    試合データに存在するパッチバージョンリストを取得

    Args:
        matches: Match型のリスト

    Returns:
        パッチバージョンのリスト（例: ["14.3", "14.2", ...]）最大5件
    """
    if not matches:
        return []

    # 全試合のgameVersionから"X.Y"部分を抽出
    patches = set()
    for match in matches:
        game_version = match.get("gameVersion", "")
        # gameVersionは "14.3.123.4567" のような形式
        # "X.Y" 部分を抽出
        parts = game_version.split(".")
        if len(parts) >= 2:
            patch = f"{parts[0]}.{parts[1]}"
            patches.add(patch)

    # ソート（降順）
    sorted_patches = sorted(patches, reverse=True)

    # 先頭5件を返す
    return sorted_patches[:5]


def get_available_modes(matches: list[dict]) -> list[dict]:
    """
    試合データに存在するゲームモードリストを取得

    Args:
        matches: Match型のリスト

    Returns:
        ゲームモードのリスト（例: [{"id": "420", "name": "ランクソロ/デュオ"}, ...]）
    """
    if not matches:
        return []

    # 全試合のqueueIdを収集
    queue_ids = set()
    for match in matches:
        queue_id = match.get("queueId")
        if queue_id is not None:
            queue_ids.add(queue_id)

    # ソート
    sorted_queue_ids = sorted(queue_ids)

    # {id: string, name: string}形式に変換
    modes = []
    for queue_id in sorted_queue_ids:
        mode = {
            "id": str(queue_id),
            "name": get_queue_name(queue_id)
        }
        modes.append(mode)

    return modes
