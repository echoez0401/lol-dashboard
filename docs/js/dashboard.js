// ================================================
// LoL戦績ダッシュボード - JavaScript
// ================================================

// ================================================
// 定数定義
// ================================================
const QUEUE_NAMES = {
    420: 'ランクソロ/デュオ',
    440: 'ランクフレックス',
    400: 'ノーマル(ドラフト)',
    430: 'ノーマル(ブラインド)',
    450: 'ARAM',
    1700: 'Arena',
    1900: 'URF'
};

// ================================================
// グローバル変数
// ================================================
let currentStats = [];
let currentMatches = [];
let currentSort = {
    column: 'games',
    ascending: false
};

// ================================================
// 初期化処理
// ================================================
document.addEventListener('DOMContentLoaded', () => {
    // イベントリスナー登録
    document.getElementById('period-filter').addEventListener('change', applyFilters);
    document.getElementById('mode-filter').addEventListener('change', applyFilters);

    // ソート可能なヘッダーにイベントリスナー設定
    const sortableHeaders = document.querySelectorAll('.sortable');
    sortableHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const column = header.getAttribute('data-sort');
            sortTable(column);
        });
    });

    // 初期データ表示
    currentStats = calculateStats(ALL_MATCHES, 'all', 'all');
    currentMatches = ALL_MATCHES.slice(0, 20);
    renderChampionTable(currentStats);
    renderMatchList(currentMatches);
});

// ================================================
// フィルター処理
// ================================================

/**
 * フィルター適用
 * 期間・モードの選択に応じてデータを再計算・再描画
 */
function applyFilters() {
    const period = document.getElementById('period-filter').value;
    const mode = document.getElementById('mode-filter').value;

    // フィルタリング実行
    const filteredMatches = filterMatches(ALL_MATCHES, period, mode);

    // 統計再計算
    currentStats = calculateStats(filteredMatches, period, mode);
    currentMatches = filteredMatches.slice(0, 20);

    // 再描画
    renderChampionTable(currentStats);
    renderMatchList(currentMatches);
}

/**
 * 試合データフィルタリング
 * @param {Array} matches - 試合データ配列
 * @param {string} period - 期間フィルター
 * @param {string} mode - モードフィルター
 * @returns {Array} フィルタ後の試合データ
 */
function filterMatches(matches, period, mode) {
    let filtered = [...matches];

    // 期間フィルター適用
    if (period !== 'all') {
        const now = new Date();

        if (period.startsWith('patch_')) {
            // パッチフィルター
            const patchVersion = period.replace('patch_', '');
            filtered = filtered.filter(match => match.gameVersion.startsWith(patchVersion));
        } else if (period === 'this_week') {
            // 今週（月曜0時以降）
            const monday = new Date(now);
            monday.setDate(now.getDate() - now.getDay() + 1); // 今週の月曜日
            monday.setHours(0, 0, 0, 0);
            filtered = filtered.filter(match => match.gameCreation >= monday.getTime());
        } else if (period === 'last_week') {
            // 先週（先週月曜〜今週月曜）
            const thisMonday = new Date(now);
            thisMonday.setDate(now.getDate() - now.getDay() + 1);
            thisMonday.setHours(0, 0, 0, 0);

            const lastMonday = new Date(thisMonday);
            lastMonday.setDate(thisMonday.getDate() - 7);

            filtered = filtered.filter(match =>
                match.gameCreation >= lastMonday.getTime() &&
                match.gameCreation < thisMonday.getTime()
            );
        } else if (period === 'last_30_days') {
            // 最近30日
            const thirtyDaysAgo = new Date(now);
            thirtyDaysAgo.setDate(now.getDate() - 30);
            filtered = filtered.filter(match => match.gameCreation >= thirtyDaysAgo.getTime());
        } else if (period === 'last_7_days') {
            // 最近7日
            const sevenDaysAgo = new Date(now);
            sevenDaysAgo.setDate(now.getDate() - 7);
            filtered = filtered.filter(match => match.gameCreation >= sevenDaysAgo.getTime());
        }
    }

    // モードフィルター適用
    if (mode !== 'all') {
        const queueId = parseInt(mode, 10);
        filtered = filtered.filter(match => match.queueId === queueId);
    }

    return filtered;
}

/**
 * チャンピオン統計計算
 * @param {Array} matches - 試合データ配列
 * @param {string} period - 期間フィルター
 * @param {string} mode - モードフィルター
 * @returns {Array} チャンピオン統計配列
 */
function calculateStats(matches, period, mode) {
    // フィルタリング
    const filteredMatches = filterMatches(matches, period, mode);

    // チャンピオンごとに集計
    const statsMap = {};

    filteredMatches.forEach(match => {
        const championName = match.myData.championName;

        if (!statsMap[championName]) {
            statsMap[championName] = {
                championName: championName,
                games: 0,
                wins: 0,
                losses: 0,
                totalKills: 0,
                totalDeaths: 0,
                totalAssists: 0,
                totalDamageDealt: 0,
                totalDamageTaken: 0
            };
        }

        const stat = statsMap[championName];
        stat.games += 1;
        if (match.myData.win) {
            stat.wins += 1;
        } else {
            stat.losses += 1;
        }
        stat.totalKills += match.myData.kills;
        stat.totalDeaths += match.myData.deaths;
        stat.totalAssists += match.myData.assists;
        stat.totalDamageDealt += match.myData.totalDamageDealtToChampions;
        stat.totalDamageTaken += match.myData.totalDamageTaken;
    });

    // 統計値計算
    const statsArray = Object.values(statsMap).map(stat => {
        const winRate = (stat.wins / stat.games * 100).toFixed(1);
        const avgKDA = calculateKDA(stat.totalKills, stat.totalDeaths, stat.totalAssists);
        const avgDamageDealt = Math.round(stat.totalDamageDealt / stat.games);
        const avgDamageTaken = Math.round(stat.totalDamageTaken / stat.games);

        return {
            championName: stat.championName,
            games: stat.games,
            wins: stat.wins,
            losses: stat.losses,
            winRate: parseFloat(winRate),
            avgKDA: avgKDA,
            avgDamageDealt: avgDamageDealt,
            avgDamageTaken: avgDamageTaken
        };
    });

    // 試合数でソート（降順）
    statsArray.sort((a, b) => b.games - a.games);

    return statsArray;
}

// ================================================
// テーブル操作
// ================================================

/**
 * テーブルソート
 * @param {string} column - ソート対象カラム
 */
function sortTable(column) {
    // 同じカラムなら昇順/降順トグル、別カラムなら降順に設定
    if (currentSort.column === column) {
        currentSort.ascending = !currentSort.ascending;
    } else {
        currentSort.column = column;
        currentSort.ascending = false;
    }

    // ソート実行
    currentStats.sort((a, b) => {
        let aVal = a[column];
        let bVal = b[column];

        // 文字列の場合は大文字小文字を無視
        if (typeof aVal === 'string') {
            aVal = aVal.toLowerCase();
            bVal = bVal.toLowerCase();
        }

        if (currentSort.ascending) {
            return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
        } else {
            return aVal < bVal ? 1 : aVal > bVal ? -1 : 0;
        }
    });

    // 再描画
    renderChampionTable(currentStats);
}

/**
 * チャンピオン統計テーブル描画
 * @param {Array} stats - チャンピオン統計配列
 */
function renderChampionTable(stats) {
    const tbody = document.getElementById('champion-table-body');

    if (stats.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">データがありません</td></tr>';
        return;
    }

    const rows = stats.map(stat => {
        const championImgUrl = `https://ddragon.leagueoflegends.com/cdn/${DDRAGON_VERSION}/img/champion/${stat.championName}.png`;
        const winRateClass = stat.winRate >= 50 ? 'win-rate' : 'loss-rate';

        return `
            <tr>
                <td class="champion-cell">
                    <img
                        src="${championImgUrl}"
                        alt="${stat.championName}"
                        onerror="this.src='assets/placeholder.png'"
                        class="champion-img"
                    >
                    <span>${stat.championName}</span>
                </td>
                <td>${stat.games}</td>
                <td>
                    <span class="${winRateClass}">
                        ${stat.winRate}%
                    </span>
                    <span class="win-loss-text">(${stat.wins}W-${stat.losses}L)</span>
                </td>
                <td>${stat.avgKDA}</td>
                <td>${formatNumber(stat.avgDamageDealt)}</td>
                <td>${formatNumber(stat.avgDamageTaken)}</td>
            </tr>
        `;
    }).join('');

    tbody.innerHTML = rows;
}

/**
 * 試合履歴リスト描画
 * @param {Array} matches - 試合データ配列
 */
function renderMatchList(matches) {
    const matchList = document.getElementById('match-list');

    if (matches.length === 0) {
        matchList.innerHTML = '<p class="text-center">データがありません</p>';
        return;
    }

    const cards = matches.map(match => {
        const resultClass = match.myData.win ? 'victory' : 'defeat';
        const resultText = match.myData.win ? '勝利' : '敗北';
        const championImgUrl = `https://ddragon.leagueoflegends.com/cdn/${DDRAGON_VERSION}/img/champion/${match.myData.championName}.png`;
        const kda = calculateKDA(match.myData.kills, match.myData.deaths, match.myData.assists);
        const queueName = getQueueName(match.queueId);
        const minutes = Math.floor(match.gameDuration / 60);
        const seconds = match.gameDuration % 60;

        return `
            <div class="match-card ${resultClass}"
                 data-match-id="${match.matchId}"
                 onclick="showMatchDetail('${match.matchId}')">
                <div class="match-result">
                    <span class="result-badge">
                        ${resultText}
                    </span>
                </div>
                <div class="match-champion">
                    <img
                        src="${championImgUrl}"
                        alt="${match.myData.championName}"
                        onerror="this.src='assets/placeholder.png'"
                        class="champion-img-small"
                    >
                </div>
                <div class="match-kda">
                    <span class="kda-score">
                        ${match.myData.kills}/${match.myData.deaths}/${match.myData.assists}
                    </span>
                    <span class="kda-ratio">
                        (${kda} KDA)
                    </span>
                </div>
                <div class="match-info">
                    <div class="match-mode">${queueName}</div>
                    <div class="match-duration">
                        ${minutes}分${seconds}秒
                    </div>
                </div>
            </div>
        `;
    }).join('');

    matchList.innerHTML = cards;
}

// ================================================
// モーダル操作
// ================================================

/**
 * 試合詳細モーダル表示
 * @param {string} matchId - 試合ID
 */
function showMatchDetail(matchId) {
    // 試合データ検索
    const match = ALL_MATCHES.find(m => m.matchId === matchId);
    if (!match) {
        console.error('Match not found:', matchId);
        return;
    }

    // チームに分割
    const blueTeam = match.allPlayers.filter(p => p.teamId === 100);
    const redTeam = match.allPlayers.filter(p => p.teamId === 200);

    // モーダルコンテンツ生成
    const queueName = getQueueName(match.queueId);
    const minutes = Math.floor(match.gameDuration / 60);
    const seconds = match.gameDuration % 60;
    const gameDate = new Date(match.gameCreation).toLocaleString('ja-JP');

    const modalContent = `
        <h3>試合詳細</h3>
        <p><strong>ゲームモード:</strong> ${queueName}</p>
        <p><strong>試合時間:</strong> ${minutes}分${seconds}秒</p>
        <p><strong>日時:</strong> ${gameDate}</p>

        <div class="team-header blue-team">青チーム</div>
        ${renderTeamTable(blueTeam)}

        <div class="team-header red-team">赤チーム</div>
        ${renderTeamTable(redTeam)}
    `;

    document.getElementById('match-detail-content').innerHTML = modalContent;
    document.getElementById('match-detail-modal').style.display = 'block';
}

/**
 * チームテーブル描画
 * @param {Array} players - プレイヤー配列
 * @returns {string} テーブルHTML
 */
function renderTeamTable(players) {
    const rows = players.map(player => {
        const championImgUrl = `https://ddragon.leagueoflegends.com/cdn/${DDRAGON_VERSION}/img/champion/${player.championName}.png`;
        const kda = calculateKDA(player.kills, player.deaths, player.assists);
        const rank = player.tier && player.rank ? `${player.tier} ${player.rank}` : 'Unranked';

        // アイテム画像生成
        const itemsHtml = player.items.map(itemId => {
            if (itemId === 0) return '<span style="width: 32px; display: inline-block;"></span>';
            return `<img src="https://ddragon.leagueoflegends.com/cdn/${DDRAGON_VERSION}/img/item/${itemId}.png"
                         alt="Item ${itemId}"
                         style="width: 32px; height: 32px; margin-right: 4px;"
                         onerror="this.style.display='none'">`;
        }).join('');

        // ルーン画像（キーストーンのみ）
        const keystoneId = player.runes.primary[0];
        const runeHtml = `<img src="https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/perk-images/styles/${keystoneId}/${keystoneId}.png"
                               alt="Rune ${keystoneId}"
                               style="width: 32px; height: 32px;"
                               onerror="this.style.display='none'">`;

        return `
            <tr>
                <td>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <img src="${championImgUrl}"
                             alt="${player.championName}"
                             onerror="this.src='assets/placeholder.png'"
                             style="width: 32px; height: 32px; border-radius: 50%;">
                        <span>${player.summonerName}</span>
                    </div>
                </td>
                <td>${player.kills}/${player.deaths}/${player.assists}</td>
                <td>${kda}</td>
                <td>${rank}</td>
                <td>${formatNumber(player.totalDamageDealtToChampions)}</td>
                <td>${formatNumber(player.totalDamageTaken)}</td>
                <td>${itemsHtml}</td>
                <td>${runeHtml}</td>
            </tr>
        `;
    }).join('');

    return `
        <table class="team-table">
            <thead>
                <tr>
                    <th>サマナー</th>
                    <th>K/D/A</th>
                    <th>KDA</th>
                    <th>ランク</th>
                    <th>与ダメ</th>
                    <th>被ダメ</th>
                    <th>アイテム</th>
                    <th>ルーン</th>
                </tr>
            </thead>
            <tbody>
                ${rows}
            </tbody>
        </table>
    `;
}

/**
 * モーダルを閉じる
 */
function closeMatchDetail() {
    document.getElementById('match-detail-modal').style.display = 'none';
}

// モーダル外クリックで閉じる
window.onclick = function(event) {
    const modal = document.getElementById('match-detail-modal');
    if (event.target === modal) {
        closeMatchDetail();
    }
};

// ================================================
// ヘルパー関数
// ================================================

/**
 * キューIDからゲームモード名取得
 * @param {number} queueId - キューID
 * @returns {string} ゲームモード名
 */
function getQueueName(queueId) {
    return QUEUE_NAMES[queueId] || `その他 (${queueId})`;
}

/**
 * 数値を3桁区切りフォーマット
 * @param {number} num - 数値
 * @returns {string} フォーマット済み文字列
 */
function formatNumber(num) {
    return num.toLocaleString('ja-JP');
}

/**
 * KDA計算
 * @param {number} kills - キル数
 * @param {number} deaths - デス数
 * @param {number} assists - アシスト数
 * @returns {number} KDA比率（小数点2桁）
 */
function calculateKDA(kills, deaths, assists) {
    const kda = (kills + assists) / (deaths || 1);
    return parseFloat(kda.toFixed(2));
}
