# -*- coding: utf-8 -*-
"""One-off: assemble data/analysis_2026-09-01.json from the hand-made Sep 1 analysis.

Headline links are recovered by fuzzy title match against the fetched data so the
rendered page has working "click back to source" links, same as the real pipeline.
"""
import json
from pathlib import Path

DATA = Path(__file__).parent / "data"
event = json.loads((DATA / "event_2026-09-01.json").read_text(encoding="utf-8"))
top = json.loads((DATA / "top_2026-09-01.json").read_text(encoding="utf-8"))

ALL_ITEMS = []
for block in event["countries"].values():
    ALL_ITEMS.extend(block["items"])
for items in top.values():
    ALL_ITEMS.extend(items)


def link_for(fragment: str) -> str:
    frag = fragment[:60].lower()
    for it in ALL_ITEMS:
        if frag in it["title"].lower():
            return it["link"]
    return ""


def hl(source: str, original: str, zh: str) -> dict:
    return {"source": source, "original": original, "zh": zh, "link": link_for(original)}


analysis = {
    "date": "2026-09-01",
    "event": "美国与伊朗一个月以来首次互相打击：美军空袭拉腊克岛，伊朗导弹还击约旦、阿联酋美军基地",
    "event_title": "美伊一个月来首次互袭",
    "findings": [
        {
            "title": "谁没报：英国头版整版沉默",
            "body": "BBC 和《卫报》都发了稿，但英国当天头版前 20 条里没有一条关于美伊冲突——版面被新首相伯纳姆首次面对议会的本国政治完全挤占。「一个国家此刻在关心什么」，有时候比「它说了什么」信息量更大。",
        },
        {
            "title": "伤亡的沉默：120 条标题里只有巴西写了死亡人数",
            "body": "美国媒体在讨论新型水雷（NYT: \"U.S. Strikes May Have Targeted a New Type of Iranian Naval Mine\"）和打击力度，欧洲媒体在讨论升级风险，只有巴西 G1 的标题写着：美军首次使用的新型导弹「留下大范围破坏痕迹，数十人死亡」（\"deixou amplo rastro de destruição e dezenas de mortos\"）。离冲突利益越远的国家，越有余裕报道人的代价。",
        },
        {
            "title": "定性词的分层：互相打击、重新开战、点燃中东",
            "body": "英语媒体普遍用 \"trade strikes\"（互相打击）这种对等、克制的说法；德媒直接定性 \"führen wieder Krieg\"（重新开战，n-tv）、\"Eskalation\"（升级，Spiegel）；阿语媒体的措辞温度最高——\"تهدد بإشعال الشرق الأوسط\"（威胁点燃中东，Investing.com 阿语版）。战火离自己越近，用词越热。",
        },
        {
            "title": "英语圈是一个信息茧房",
            "body": "美、英、印三国的英语信息流里，12 条对齐报道有 9 条来自同一批英美通讯社——换了国家版，看到的还是 Reuters、CBS 和 Fox。真正的视角差异只出现在跨语言的时候：日本在算武器供应账（NHK：美军向日本等盟友补充武器或需数年），德国在盯网络战新战线，埃及在担心战火烧到自家。语言墙，而不是国界，才是信息茧房真正的墙。",
        },
    ],
    "quote_comparison": {
        "intro": "特朗普的原话 \"we're going to hit them hard\"（外加一个 \"smack\"）在各国标题里被这样处理：",
        "rows": [
            ["美国 · Reuters", "vows to hit Iran hard", "誓言狠狠打击——原话直引"],
            ["英国 · The Independent", "may still 'smack' Iran", "保留了最口语的 smack，加引号保持距离"],
            ["日本 · FNN", "「強烈な攻撃を行う」", "译成正式书面语，口语感被抹掉"],
            ["法国 · Libération", "menace de « frapper fort »", "「威胁重拳打击」——动词换成了 menacer（威胁）"],
            ["巴西 · Terra", "promete atingir 'duramente'", "「承诺狠狠打击」——promete（承诺）比 menace 温和"],
            ["俄罗斯 · Интерфакс", "пообещал ответные удары", "整句改写为「承诺回应性打击」，原话消失"],
            ["中国 · 财联社", "称将\u201c狠狠打击\u201d伊朗", "直引加引号，与美媒处理一致"],
        ],
    },
    "countries": {
        "US": {
            "name": "美国",
            "frame": "华盛顿视角的威慑叙事：报道围着特朗普的表态转，关心「打多重、打多久」，几乎不提对面的伤亡。",
            "unique": "只有美国媒体在讨论武器技术细节——《纽约时报》分析这次打击目标可能是一种新型伊朗水雷。",
            "headlines": [
                hl("Reuters", "Trump vows to hit Iran hard after first exchanges of fire in a month", "一个月来首次交火后，特朗普誓言狠狠打击伊朗"),
                hl("The Washington Post", "Trump says U.S. might ‘smack’ Iran but that fighting is likely to remain limited", "特朗普称美国可能「抽」伊朗一下，但战斗大概率维持有限规模"),
                hl("The New York Times", "U.S. Strikes May Have Targeted a New Type of Iranian Naval Mine", "美军打击目标可能是一种新型伊朗水雷"),
            ],
        },
        "UK": {
            "name": "英国",
            "frame": "有报道但没上头版：BBC 和《卫报》都发了稿，但当天头版前 20 条被新首相伯纳姆首次面对议会的本国政治完全挤占。",
            "unique": "BBC 的措辞全场最克制——「US and Iran trade strikes」，被动、对等、不带形容词。",
            "headlines": [
                hl("BBC", "US and Iran trade strikes after first known US attack in weeks", "数周来美国首次出手后，美伊互相打击"),
                hl("The Guardian", "First US military attacks on Iran in a month prompt retaliation", "美军一个月来首次攻击伊朗，招致报复"),
                hl("The Independent", "Trump says American military may still ‘smack’ Iran despite it being a ‘failed nation’", "特朗普：尽管伊朗是「失败国家」，美军仍可能「抽」它"),
            ],
        },
        "India": {
            "name": "印度",
            "frame": "信息流被英美通讯社整体接管：搜索结果 12 条里 9 条与英美版重合，本国声音只在头版以「战争阴影下的印度经济」形式出现。",
            "unique": "头版把战争当经济背景板——「伊朗战争之中，印度 GDP 意外增长 7.8%」，以及金价、油气调价的连锁报道。",
            "headlines": [
                hl("NDTV（头版）", "US-Iran War Live Updates: Iran Attacks US Bases in UAE, Jordan After New Strikes", "美伊战争直播：新一轮打击后，伊朗攻击阿联酋和约旦的美军基地"),
                hl("Nikkei Asia（头版）", "India's GDP records surprise growth of 7.8% amid Iran war", "伊朗战争之中，印度 GDP 意外增长 7.8%"),
                hl("Sky News", "Iran war latest: Tehran calls Trump AI video 'laughable'", "伊朗战争最新：德黑兰称特朗普的 AI 视频「可笑」"),
            ],
        },
        "Japan": {
            "name": "日本",
            "frame": "「这对日本安保意味着什么」：全部主流媒体都在算这场冲突对日美同盟、武器供应和冲绳基地的影响。",
            "unique": "NHK 独家角度：美军因伊朗作战消耗，向日本等盟友补充武器可能要花数年。冲绳时报则紧盯当地美军基地卷入风险。",
            "headlines": [
                hl("NHK", "“米軍 日本などへの兵器補充に数年か”イラン攻撃の影響 米紙", "美报：受打击伊朗影响，美军向日本等国补充武器或需数年"),
                hl("日本経済新聞", "トランプ氏、対イラン報復を宣言 米軍「戦闘長期化は困難」と温度差", "特朗普宣布对伊报复，美军却称「战斗难以长期化」——温差明显"),
                hl("沖縄タイムス", "【米のイラン攻撃】米の本音「交戦激化回避」 長期作戦困難と軍幹部", "美国的真心话是「避免战事升级」：军方高层称长期作战困难"),
            ],
        },
        "France": {
            "name": "法国",
            "frame": "外交官视角 + 解释性新闻传统：头条给了阿联酋的谴责声明，franceinfo 用「目前我们知道什么」的解释体拆解事件。",
            "unique": "《世界报》把海湾国家的反应放在了美伊双方之前——阿联酋称伊朗袭击是「危险升级」。l'Opinion 关注重开霍尔木兹航道。",
            "headlines": [
                hl("Le Monde", "les Emirats arabes unis qualifient l’attaque iranienne d’« escalade dangereuse »", "阿联酋称伊朗袭击是「危险升级」"),
                hl("franceinfo", "Premières frappes depuis un mois, île de Larak bombardée, riposte de Téhéran… Ce que l'on sait", "一个月来首次打击、拉腊克岛遭轰炸……目前我们知道什么"),
                hl("Libération", "premier échange de tirs entre les Etats-Unis et l’Iran en un mois, Trump menace de «frapper fort", "美伊一个月来首次交火，特朗普威胁「重拳打击」"),
            ],
        },
        "Germany": {
            "name": "德国",
            "frame": "用词全场最重：别国说「互相打击」，德媒直接定性「重新开战」（wieder Krieg）、「升级」（Eskalation）。",
            "unique": "两个独家角度：伊朗对美国水电和管道系统开辟「网络战新战线」（fr.de）；400 艘货船仍被困波斯湾（FAZ）。还在追问特朗普 AI 视频的真伪。",
            "headlines": [
                hl("n-tv", "Erste Attacken seit Wochen: USA und Iran führen auch militärisch wieder Krieg", "数周来首次攻击：美国和伊朗在军事上重新开战"),
                hl("fr.de", "Cyberangriffe auf Wasser, Strom und Pipelines: Iran eröffnet eine neue Front gegen die USA", "对水、电、管道的网络攻击：伊朗对美国开辟新战线"),
                hl("FAZ", "Bericht: 400 Schiffe stecken weiterhin im Persischen Golf fest", "报道：400 艘船仍被困在波斯湾"),
            ],
        },
        "Brazil": {
            "name": "巴西",
            "frame": "经济冲击优先：油价单日暴涨 6% 是财经大报的头条位，战争本身排在后面。",
            "unique": "十个国家里唯一在标题里报出死亡人数的：G1 称美军首次使用的新型导弹「留下大范围破坏痕迹，数十人死亡」。",
            "headlines": [
                hl("Folha de S.Paulo", "Petróleo dispara mais de 6% com retomada dos ataques entre EUA e Irã", "美伊重启攻击，油价暴涨超 6%"),
                hl("G1", "Novo míssil dos EUA utilizado pela 1ª vez contra o Irã deixou amplo rastro de destruição e dezenas de mortos", "美国首次对伊使用的新型导弹留下大范围破坏，数十人死亡"),
                hl("Brasil de Fato", "Guerra entre Irã e EUA cada vez mais deixa de ser bilateral, afirma jornalista especializada", "专家记者：美伊战争正越来越不再是双边冲突"),
            ],
        },
        "Russia": {
            "name": "俄罗斯",
            "frame": "意外地平实：信息流被 Meduza、BBC 俄语等流亡/外媒俄语频道主导，标题多为不带立场的「美伊互相打击」。",
            "unique": "官方系媒体的兴趣点在别处：Interfax 只转述特朗普表态（且把 smack 弱化为「回应性打击」），头版更关心「俄股市因美国消息大涨」。",
            "headlines": [
                hl("Meduza", "США и Иран обменялись ударами впервые за месяц", "美国和伊朗一个月来首次互相打击"),
                hl("Интерфакс", "Трамп пообещал, что США нанесут ответные удары по Ирану", "特朗普承诺美国将对伊朗实施回应性打击"),
                hl("ProFinance（头版）", "Рынок акций России подскочил на новостях из США", "俄罗斯股市因来自美国的消息大涨"),
            ],
        },
        "Egypt": {
            "name": "埃及（阿语区）",
            "frame": "切身危险框架，语言温度全场最高：「威胁重新点燃中东」「引燃战争」——战火就在自家区域。",
            "unique": "独有的复盘视角：Masrawy 发「无胜者的战争？四种解读看美伊谁赢谁输」，并引伊朗消息源称「回应将强上数十倍」。",
            "headlines": [
                hl("Investing.com عربية", "أمريكا وإيران تعودان إلى النار.. ضربات متبادلة تهدد بإشعال الشرق الأوسط", "美伊重回战火……互相打击威胁点燃中东"),
                hl("Masrawy", "حرب بلا منتصر؟ 4 قراءات تكشف الرابح والخاسر بين إيران وأمريكا", "无胜者的战争？四种解读揭示美伊之间谁赢谁输"),
                hl("BBC عربي", "جزيرة لارك: الإمارات تنفي تعرض قاعدة المنهاد الجوية لقصف إيراني", "拉腊克岛：阿联酋否认其空军基地遭伊朗轰炸"),
            ],
        },
        "China": {
            "name": "中国（中文版）",
            "frame": "财经媒体接管叙事：油价、比特币、港股反应排在战况前面；时政报道则强调「美军吃不消」的疲态。",
            "unique": "凤凰网的角度在别国未见：「时隔 1 个月再度袭击伊朗，美国军方却为何直呼吃不消？」——聚焦美军的不可持续。",
            "headlines": [
                hl("华尔街见闻", "一个多月来首次！美国空袭伊朗拉腊克岛，油价应声走高", ""),
                hl("凤凰网", "时隔1个月再度袭击伊朗，美国军方却为何直呼“吃不消”？", ""),
                hl("财联社", "美国驻约旦基地遭袭后 特朗普称将“狠狠打击”伊朗", ""),
            ],
        },
    },
    "limitation": "Google News 的「俄罗斯版」被流亡媒体主导、「中文版」含被屏蔽的外媒——各国家版反映的是该语言的公开互联网，不完全等于当地人实际看到的信息流；且本期分析基于标题层，未读全文。",
}

out = DATA / "analysis_2026-09-01.json"
out.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
linked = sum(1 for c in analysis["countries"].values() for h in c["headlines"] if h["link"])
total = sum(len(c["headlines"]) for c in analysis["countries"].values())
print(f"wrote {out} ({linked}/{total} headlines matched to source links)")
