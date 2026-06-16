"""
L3 低关注度追踪器 — 瓶颈标的关注度量化工具
用于跟踪关键词搜索热度变化，量化五因子中的 L3（低关注度）维度。

用法：
  python l3_tracker.py           # 手动运行一次，输出当前快照
  python l3_tracker.py --weekly  # 写入weekly CSV记录

依赖：pip install requests beautifulsoup4
"""

import json
import time
import csv
import os
from datetime import datetime
from urllib.parse import quote

try:
    import requests
except ImportError:
    print("请先安装 requests: pip install requests")
    exit(1)

# ═══════════════ 配置 ═══════════════
KEYWORDS = {
    "MPO光纤":       {"group": "光互联",   "baidu": "MPO光纤连接器",    "xueqiu": "MPO 光纤"},
    "HVLP铜箔":      {"group": "铜箔",     "baidu": "HVLP铜箔",        "xueqiu": "HVLP 铜箔"},
    "氧化镝":        {"group": "MLCC材料", "baidu": "氧化镝 MLCC",     "xueqiu": "氧化镝"},
    "太辰光":        {"group": "标的",     "baidu": "太辰光 MPO",      "xueqiu": "$太辰光"},
    "德福科技":      {"group": "标的",     "baidu": "德福科技 HVLP",    "xueqiu": "$德福科技"},
    "MLCC离型膜":    {"group": "MLCC材料", "baidu": "MLCC离型膜 赛伍",  "xueqiu": "MLCC 离型膜"},
}

CSV_PATH = os.path.join(os.path.dirname(__file__), "l3_tracker_log.csv")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def baidu_search_count(keyword):
    """获取百度搜索结果数（粗略替代百度指数）"""
    try:
        url = f"https://www.baidu.com/s?wd={quote(keyword)}"
        r = requests.get(url, headers=HEADERS, timeout=8)
        # 从返回的HTML中提取"百度为您找到相关结果约xxx个"
        if "找到相关结果" in r.text or "条结果" in r.text:
            import re
            match = re.search(r'找到相关结果[约]?([\d,]+)个', r.text)
            if match:
                return int(match.group(1).replace(',', ''))
        # 降级方案：用文本长度作为替代指标
        return len(r.text)
    except Exception as e:
        return -1


def xueqiu_post_count(keyword):
    """获取雪球讨论帖数量"""
    try:
        url = f"https://xueqiu.com/query/v1/search/web/search.json?q={quote(keyword)}&count=1"
        r = requests.get(url, headers={**HEADERS, "Referer": "https://xueqiu.com"}, timeout=8)
        data = r.json()
        return data.get("count", -1)
    except:
        try:
            # 降级: 用网页版
            url = f"https://xueqiu.com/k?q={quote(keyword)}"
            r = requests.get(url, headers=HEADERS, timeout=8)
            return len(r.text) // 1000  # 粗略估计
        except:
            return -1


def guba_post_count(stock_code):
    """获取东方财富股吧帖子数"""
    try:
        url = f"https://guba.eastmoney.com/list,{stock_code}.html"
        r = requests.get(url, headers=HEADERS, timeout=8)
        import re
        # 找总帖子数
        match = re.search(r'全部.*?(\d+).*?篇', r.text)
        if match:
            return int(match.group(1))
        return -1
    except:
        return -1


def calc_l3_score(count, baseline=100000):
    """
    将搜索量映射到 L3 分数 (0-5)
    越低 = 关注度越低 = L3越好（越没人关注）
    """
    if count < 0:
        return -1  # 数据获取失败
    ratio = max(0, min(1, count / baseline))
    score = 5 - int(ratio * 5)
    return max(1, score)


def snapshot():
    """运行一次全量快照"""
    results = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    print(f"\n{'='*60}")
    print(f"L3 关注度快照 — {now}")
    print(f"{'='*60}")
    print(f"{'关键词':<16} {'百度结果':>10} {'雪球帖子':>10} {'L3分数':>8} {'评级':>8}")
    print("-"*58)

    for name, kw in KEYWORDS.items():
        bd = baidu_search_count(kw["baidu"])
        time.sleep(0.8)  # 礼貌延迟
        xq = xueqiu_post_count(kw["xueqiu"])
        time.sleep(0.5)
        
        # 综合评分: 百度权重0.4 + 雪球权重0.6
        bd_score = calc_l3_score(bd, 5000000) if bd > 0 else -1
        xq_score = calc_l3_score(xq, 500) if xq > 0 else -1
        
        if bd_score < 0 and xq_score < 0:
            combo = -1
            rating = "ERR"
        else:
            valid_scores = [s for s in [bd_score, xq_score] if s >= 0]
            combo = round(sum(valid_scores) / len(valid_scores), 1)
            if combo >= 4.5: rating = "★★★★★"
            elif combo >= 3.5: rating = "★★★★"
            elif combo >= 2.5: rating = "★★★"
            elif combo >= 1.5: rating = "★★"
            else: rating = "★"
        
        print(f"{name:<16} {str(bd):>10} {str(xq):>10} {str(combo):>8} {rating:>8}")
        
        results.append({
            "timestamp": now,
            "keyword": name,
            "group": kw["group"],
            "baidu_count": bd,
            "xueqiu_posts": xq,
            "l3_score": combo,
            "rating": rating,
        })
    
    # 按L3排序（越低越好，说明越没人关注）
    results.sort(key=lambda x: x['l3_score'] if x['l3_score'] > 0 else 0, reverse=True)
    
    print(f"\n📊 L3 最低关注度 TOP3（最被忽视的瓶颈）：")
    for r in results[:3]:
        print(f"  {r['keyword']} ({r['group']}): L3={r['l3_score']} {r['rating']}")
    
    # 如果有历史数据，自动对比上周变化
    if os.path.exists(CSV_PATH):
        try:
            from collections import defaultdict
            hist = defaultdict(list)
            with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    hist[row['关键词']].append((row['日期'], float(row['L3分数']) if row['L3分数'] != '-1' else None))
            
            print(f"\n📈 环比变化（vs 上次记录）：")
            for r in results:
                kw_data = hist.get(r['keyword'], [])
                if len(kw_data) >= 1:
                    prev = kw_data[-1][1]
                    if prev is not None and r['l3_score'] > 0:
                        delta = r['l3_score'] - prev
                        if delta > 0.5:
                            arrow = "↘ 降温 (L3改善)"
                        elif delta < -0.5:
                            arrow = "↗ 升温 (L3恶化)"
                        else:
                            arrow = "→ 平稳"
                        print(f"  {r['keyword']:<16} L3 {prev:.1f} → {r['l3_score']:.1f}  {arrow}")
        except:
            pass
    
    return results


def weekly_log():
    """写入CSV每周记录"""
    results = snapshot()
    today = datetime.now().strftime("%Y-%m-%d")
    
    file_exists = os.path.exists(CSV_PATH)
    
    with open(CSV_PATH, 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["日期", "关键词", "分组", "百度结果数", "雪球帖子数", "L3分数", "评级"])
        for r in results:
            writer.writerow([today, r['keyword'], r['group'], r['baidu_count'], r['xueqiu_posts'], r['l3_score'], r['rating']])
    
    print(f"\n✅ 数据已追加到 {CSV_PATH}")
    print(f"   累计记录 {sum(1 for _ in open(CSV_PATH)) - 1} 行")


def read_history():
    """读取历史记录并显示趋势分析"""
    if not os.path.exists(CSV_PATH):
        print("⚠️ 暂无历史数据，请先运行 --weekly 创建记录")
        return
    
    from collections import defaultdict
    history = defaultdict(list)
    
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            history[row['关键词']].append({
                'date': row['日期'],
                'l3': float(row['L3分数']) if row['L3分数'] != '-1' else None,
            })
    
    all_dates = sorted(set(e['date'] for entries in history.values() for e in entries))
    
    print(f"\n{'='*72}")
    print(f"L3 趋势分析 — 数据范围: {all_dates[0]} ~ {all_dates[-1]} (共 {len(all_dates)} 周)")
    print(f"{'='*72}")
    print(f"{'关键词':<16} {'L3起点':>6} {'L3当前':>6} {'变化':>6} {'速度':>8} {'状态':>16}")
    print("-"*72)
    
    alerts = []
    
    for kw, entries in history.items():
        scores = [e['l3'] for e in entries if e['l3'] is not None]
        if len(scores) < 2:
            continue
        
        first_score = scores[0]
        last_score = scores[-1]
        delta = last_score - first_score  # 正=关注度下降(L3改善), 负=关注度上升(L3恶化)
        
        # 变化速度: 每周L3变化
        weeks = len(scores)
        velocity = abs(delta) / max(weeks - 1, 1) if delta != 0 else 0
        
        if delta > 0.5:
            trend = "↘ 关注度下降"
            status = "✅ L3改善中"
        elif delta < -0.5:
            trend = "↗ 关注度急升"
            status = "⚠️ L3恶化"
            if velocity >= 0.3:
                status = "🔴 关注度暴增！"
        elif delta < 0:
            trend = "↗ 微升"
            status = "📊 保持观察"
        else:
            trend = "→ 平稳"
            status = "⚪ 无变化"
        
        # 检测L3拐点: 前几周L3高(没人关注) → 最近1-2周L3突然下降
        if len(scores) >= 3:
            recent_two = scores[-2:]
            earlier = scores[:-2]
            avg_earlier = sum(earlier) / len(earlier)
            avg_recent = sum(recent_two) / len(recent_two)
            if avg_earlier >= 3.5 and avg_recent <= 2.5:
                status = "🟡 拐点！从低关注度进入关注度上升期"
                alerts.append((kw, avg_earlier, avg_recent))
        
        print(f"{kw:<16} {first_score:>5.1f} {last_score:>5.1f} {delta:>+5.1f} {velocity:>7.2f}/周 {status:<16}")
    
    if alerts:
        print(f"\n🟡 L3 拐点检测（从极低关注度→开始被讨论）：")
        for kw, old, new in alerts:
            print(f"  {kw}: L3 {old:.1f} → {new:.1f} | 信息扩散前夜——从无人关注到开始讨论的拐点窗口")


# ═══════════════ L3纯度判断：真L3 vs 伪L3（炒过回落）═══════════
def purity_check(keyword, price_history=None):
    """
    判断当前低关注度是真L3（从未被炒过）还是伪L3（炒过回落）。

    参数:
        keyword: 关键词/标的名称
        price_history: dict with keys
            '12m_peak_pct' — 12月内最高涨幅%
            '12m_search_peak' — 12月内搜索量峰值倍数
            '12m_shareholder_change' — 12月内股东户数变化%

    返回: dict with purity score and verdict
    """
    print(f"\n{'='*60}")
    print(f"L3纯度检测 — {keyword}")
    print(f"{'='*60}")

    true_score = 0
    false_score = 0

    if price_history:
        # 维度1: 股价尖峰
        peak_pct = price_history.get('12m_peak_pct', 0)
        if peak_pct < 50:
            print(f"  股价: 12月最高涨幅{peak_pct}% → +1 真L3(无尖峰)")
            true_score += 1
        elif peak_pct > 100:
            print(f"  股价: 12月最高涨幅{peak_pct}% → +1 伪L3(有过>100%尖峰)")
            false_score += 1

        # 维度2: 搜索峰值
        search_peak = price_history.get('12m_search_peak', 0)
        if search_peak > 0:
            if search_peak < 3:
                print(f"  搜索: 12月最高{search_peak}x → +1 真L3(无>3x峰值)")
                true_score += 1
            elif search_peak > 5:
                print(f"  搜索: 12月最高{search_peak}x → +1 伪L3(有过>5x峰值)")
                false_score += 1

        # 维度3: 股东户数
        sh_chg = price_history.get('12m_shareholder_change', 0)
        if sh_chg:
            if sh_chg < 50:
                print(f"  股东: 12月+{sh_chg}% → +1 真L3(无>50%暴增)")
                true_score += 1
            else:
                print(f"  股东: 12月+{sh_chg}% → +1 伪L3(有过>50%暴增)")
                false_score += 1
    else:
        print("  ⚠️ 无价格历史数据，跳过纯度检测")

    total = true_score + false_score
    if total == 0:
        purity = 0.5
        verdict = "⚠️ 数据不足"
    else:
        purity = true_score / total
        if purity > 0.66:
            verdict = "✅ 高纯度真L3 — 可信任"
        elif purity > 0.33:
            verdict = "🟡 中等纯度 — 需人工判断"
        else:
            verdict = "🔴 低纯度伪L3 — 炒过回落，不可信"

    print(f"  纯度: {purity:.0%} ({true_score}真/{false_score}伪) → {verdict}")
    return {"purity": purity, "true_score": true_score, "false_score": false_score, "verdict": verdict}


# ═══════════════ 爆炒判断：多维度量化 ═══════════
def bubble_check(name, price_data=None):
    """
    判断个股是否被爆炒。三个维度：价格动量、估值偏离、板块偏离。

    参数:
        price_data: dict with keys
            'chg_1m', 'chg_3m', 'chg_6m' — 各周期涨幅%
            'pe_current', 'pe_median_5y', 'pe_std_5y' — PE及历史分布
            'sector_chg_1m' — 板块同期涨幅%

    返回: dict with bubble level and verdict
    """
    if not price_data:
        return {"level": "无数据", "verdict": "⚠️ 需手动输入价格数据"}

    triggers = []
    chg_1m = price_data.get('chg_1m', 0)
    chg_3m = price_data.get('chg_3m', 0)
    chg_6m = price_data.get('chg_6m', 0)

    # 维度1: 价格动量
    if chg_1m > 100 or chg_3m > 200 or chg_6m > 300:
        triggers.append(f"🔴暴烈上涨: 1m{chg_1m}%/3m{chg_3m}%/6m{chg_6m}%")
    elif chg_1m > 50:
        triggers.append(f"🟠快速上涨: 1m{chg_1m}%")

    # 维度2: 估值偏离
    pe_now = price_data.get('pe_current', 0)
    pe_med = price_data.get('pe_median_5y', 0)
    pe_std = price_data.get('pe_std_5y', 0)
    if pe_now and pe_med and pe_std:
        dev = (pe_now - pe_med) / pe_std if pe_std > 0 else 0
        if dev > 3:
            triggers.append(f"🔴估值极端: PE{pe_now:.0f}超中位数{dev:.1f}σ")
        elif dev > 2:
            triggers.append(f"🟠估值偏高: PE{pe_now:.0f}超中位数{dev:.1f}σ")

    # 维度3: 板块偏离
    sector_chg = price_data.get('sector_chg_1m', 0)
    if chg_1m and sector_chg and sector_chg > 0:
        ratio = chg_1m / sector_chg
        if ratio > 3:
            triggers.append(f"🔴严重领涨: 涨幅{sector_chg}%的{ratio:.1f}倍")
        elif ratio > 2:
            triggers.append(f"🟠明显领涨: 涨幅{sector_chg}%的{ratio:.1f}倍")

    red = sum(1 for t in triggers if t.startswith("🔴"))
    orange = sum(1 for t in triggers if t.startswith("🟠"))

    if red >= 2:
        level = "🔴确认爆炒"
        verdict = "触发退出#2(估值透支)→减至底仓"
    elif red >= 1 or orange >= 2:
        level = "🟠疑似过热"
        verdict = "高度警惕，紧密跟踪"
    elif orange >= 1:
        level = "🟡温和上涨"
        verdict = "正常关注"
    else:
        level = "⚪正常"
        verdict = "无过热迹象"

    print(f"\n{'='*60}")
    print(f"爆炒检测 — {name}")
    print(f"{'='*60}")
    for t in triggers:
        print(f"  {t}")
    print(f"  综合: {level} → {verdict}")

    return {"level": level, "triggers": triggers, "verdict": verdict, "red": red, "orange": orange}


if __name__ == "__main__":
    import sys
    if "--weekly" in sys.argv:
        weekly_log()
    elif "--history" in sys.argv:
        read_history()
    elif "--baseline" in sys.argv:
        # 手动基线：让你自己给每个关键词的讨论热度打分(1-5)，作为L3主观参考
        print("\n📝 L3 主观基线校准（你感觉到的讨论热度）")
        print("   1=几乎没人讨论  2=偶有提及  3=中等讨论  4=讨论较多  5=铺天盖地\n")
        results = []
        today = datetime.now().strftime("%Y-%m-%d")
        for name, kw in KEYWORDS.items():
            while True:
                try:
                    heat = int(input(f"  {name} ({kw['group']}) 热度(1-5): "))
                    if 1 <= heat <= 5:
                        break
                except:
                    pass
                print("  请输入1-5的数字")
            l3 = 6 - heat  # 热度1→L3=5(极低关注), 热度5→L3=1(极高关注)
            results.append({"date": today, "keyword": name, "group": kw['group'], "subjective_heat": heat, "l3_subjective": l3})
        
        print(f"\n{'='*50}")
        print(f"主观L3基线 — {today}")
        print(f"{'='*50}")
        for r in sorted(results, key=lambda x: x['l3_subjective'], reverse=True):
            bar = "█" * r['subjective_heat']
            print(f"  {r['keyword']:<14} 热度{r['subjective_heat']} {bar} → L3={r['l3_subjective']}")
        print("\n💡 提示：每周运行 --baseline 记录你的主观感知，与 --weekly 的自动数据对照")
    else:
        snapshot()
        print("\n💡 提示：")
        print("  python l3_tracker.py --baseline → 手动记录你对讨论热度的主观感知")
        print("  python l3_tracker.py --weekly   → 自动抓取数据并写入CSV")
        print("  python l3_tracker.py --history  → 查看历史趋势+拐点检测")
        print("  建议：先用 --baseline 建立一个主观基线，然后每周 --weekly 自动+手动对照")
