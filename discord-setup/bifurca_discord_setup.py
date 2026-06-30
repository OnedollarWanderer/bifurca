"""
BIFURCA公式Discord 初期構成 v1.1 自動構築スクリプト
====================================================

前提:
  1. Discord Developer Portal でBotを作成し、トークンを取得していること
  2. そのBotを対象サーバーに Administrator 権限で招待済みであること
  3. pip install requests

使い方:
  export DISCORD_BOT_TOKEN="あなたのボットトークン"
  python bifurca_discord_setup.py            # DRY_RUN（実行せず内容確認のみ）
  python bifurca_discord_setup.py --apply     # 実際に構築する

設計方針:
  - カテゴリ/チャンネル/ロール/権限/シード投稿をすべて1つのCONFIGに宣言し、
    汎用エンジン(create_*関数)が解釈して実行する「データ駆動」構成。
  - チャンネルごとの権限は「見える/見えない」「書ける/書けない」の2軸だけで指定し、
    それ以外の細かい権限(リアクション・埋め込み等)はDiscordのデフォルトに委ねる。
"""

import os
import sys
import time
import requests

# ----------------------------------------------------------------------------
# 設定
# ----------------------------------------------------------------------------

GUILD_ID = "1520963619062415503"  # ご提示のURLから抽出したギルドID
API_BASE = "https://discord.com/api/v10"

BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
APPLY = "--apply" in sys.argv  # 指定しない限りDRY_RUN(実行せず内容を表示するだけ)

if not BOT_TOKEN and APPLY:
    print("環境変数 DISCORD_BOT_TOKEN が設定されていません。")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bot {BOT_TOKEN}",
    "Content-Type": "application/json",
}

# Discord permission bit (必要最小限のみ定義)
PERM = {
    "ADMINISTRATOR": 1 << 3,
    "MANAGE_CHANNELS": 1 << 4,
    "MANAGE_MESSAGES": 1 << 13,
    "VIEW_CHANNEL": 1 << 10,
    "SEND_MESSAGES": 1 << 11,
    "READ_MESSAGE_HISTORY": 1 << 16,
    "CONNECT": 1 << 20,
    "SPEAK": 1 << 21,
    "CREATE_PUBLIC_THREADS": 1 << 35,
    "SEND_MESSAGES_IN_THREADS": 1 << 38,
    "MODERATE_MEMBERS": 1 << 40,
    "KICK_MEMBERS": 1 << 1,
}

WRITE_BITS = (
    PERM["SEND_MESSAGES"]
    | PERM["CREATE_PUBLIC_THREADS"]
    | PERM["SEND_MESSAGES_IN_THREADS"]
)

# ----------------------------------------------------------------------------
# ロール定義
# ----------------------------------------------------------------------------

ROLES = [
    # name, color(int), base_permissions
    {"name": "管理者", "color": 0xE6B400, "permissions": PERM["ADMINISTRATOR"], "hoist": True},
    {"name": "モデレーター", "color": 0xE05050, "permissions": PERM["MANAGE_MESSAGES"] | PERM["MODERATE_MEMBERS"] | PERM["KICK_MEMBERS"], "hoist": True},
    {"name": "古記録研究者", "color": 0x9B7FD4, "permissions": 0, "hoist": True},
    {"name": "創作者", "color": 0x53C68C, "permissions": 0, "hoist": True},
    {"name": "旅人", "color": 0x99AAB5, "permissions": 0, "hoist": False},
]

# ----------------------------------------------------------------------------
# パーミッションテンプレート（カテゴリ単位のデフォルト方針）
#   "view"/"send": True=許可 / False=明示的に拒否 / None=指定しない(継承)
# ----------------------------------------------------------------------------

def perm_set(view=None, send=None):
    return {"view": view, "send": send}

PERM_INFO = {
    "everyone": perm_set(view=True, send=False),
    "旅人": perm_set(view=True, send=False),
    "モデレーター": perm_set(view=True, send=True),
}
PERM_COMMUNITY = {
    "everyone": perm_set(view=False),
    "旅人": perm_set(view=True, send=True),
    "モデレーター": perm_set(view=True, send=True),
}
PERM_CREATION_RULES = {
    "everyone": perm_set(view=False),
    "旅人": perm_set(view=True, send=False),
    "モデレーター": perm_set(view=True, send=True),
}
PERM_ADMIN = {
    "everyone": perm_set(view=False),
    "旅人": perm_set(view=False),
    "モデレーター": perm_set(view=True, send=True),
}
PERM_ADMIN_SECRET = {  # 商標・法務: モデレーターも見せない
    "everyone": perm_set(view=False),
    "旅人": perm_set(view=False),
    "モデレーター": perm_set(view=False),
}
PERM_GALLERY_INFO = {
    "everyone": perm_set(view=True, send=False),
    "旅人": perm_set(view=True, send=False),
    "モデレーター": perm_set(view=True, send=True),
}
PERM_VOICE = {
    "everyone": perm_set(view=False),
    "旅人": perm_set(view=True),
    "モデレーター": perm_set(view=True),
}

# ----------------------------------------------------------------------------
# 世界観アーカイブ フォーラムのタグとシード投稿
# ----------------------------------------------------------------------------

LORE_TAGS = ["世界史", "用語辞典", "ヴァルン", "タラッサ", "ヴェルカ", "サハール",
             "コルダ", "カルナ", "リンガ", "ンガ・ソル", "未解明の謎"]

LORE_SEEDS = {
    "世界史": ("世界史の読み方", "プレート分岐から現代まで。Ⅰ〜Ⅵ部の年表とンガ・ソルの証言断片についてはこちらで。\nhttps://bifurca.wandereronedollar.workers.dev/worldhistory/index.html"),
    "用語辞典": ("用語辞典について話す場所", "地理から疫学史まで全十一部。気になる項目のリンクを貼って語り合ってください。\nhttps://bifurca.wandereronedollar.workers.dev/dict/index.html"),
    "ヴァルン": ("ヴァルン人スレッド", "ノルド東洋大陸の農耕官僚国家。失政パターンは「情報の上方歪曲」。三層粥・歳簿経などの設定はこちらで。"),
    "タラッサ": ("タラッサ人スレッド", "赤道東洋大陸の海洋民族。失政パターンは「公共財の過小投資」。漂い干物・初波の儀礼などはこちらで。"),
    "ヴェルカ": ("ヴェルカ人スレッド", "ノルド西洋大陸の半遊牧民族。失政パターンは「決定不能トラップ」。長鍋・夜語りなどはこちらで。"),
    "サハール": ("サハール人スレッド", "赤道西洋大陸の隊商文化民族。客人歓待と氏族連合の分断（ビザンチン将軍問題）についてはこちらで。"),
    "コルダ": ("コルダ人スレッド", "南西洋大陸の牧畜都市国家連合。「負けても屈服しない」誇りの文化。賓客の大角などはこちらで。"),
    "カルナ": ("カルナ人スレッド", "南東洋大陸の入植者の子孫。赤土の約束・先住民問題についてはこちらで。"),
    "リンガ": ("リンガ人スレッド", "グランドリッジ峠帯の山岳民族。峠管理家系・戦略的あいまい性についてはこちらで。"),
    "ンガ・ソル": ("ンガ・ソル目撃談", "正体不明・解明禁止がコア設定です。気配や目撃譚は自由に。断定的な正体描写は対象外とさせてください。"),
    "未解明の謎": ("未解明の謎を考察するスレッド", "古西語・原宗教仮説・未解明の数「三」など、辞典上でも仮説扱いの要素についての考察はこちらで。"),
}

CREATION_TAGS = ["ファンアート", "小説・SS", "キャラクター", "町と村", "拡張設定提案"]

CREATION_SEEDS = {
    "ファンアート": ("ファンアート投稿スレッド", "サブテーマは食卓／旅人／掟／証人。#ビフルカ タグでのSNS投稿もこちらで共有してください。"),
    "小説・SS": ("小説・SS投稿スレッド", "日常レベルの物語を歓迎します。「峠を初めて越えたリンガ人の若者の日記」のような掌編もぜひ。"),
}

# ----------------------------------------------------------------------------
# カテゴリ／チャンネル全体構成
# ----------------------------------------------------------------------------

CATEGORIES = [
    {
        "name": "📜 INFORMATION",
        "perms": PERM_INFO,
        "channels": [
            {"name": "ようこそ", "type": "text", "seed":
                "ようこそ、BIFURCA公式Discordへ。\n\n"
                "ここはオリジナル世界観『BIFURCA』のファン・創作者・考察好きのためのコミュニティです。\n"
                "初めての方は ①#ルール ②#世界観ガイド ③#自己紹介 の順がおすすめです。\n\n"
                "公式サイト：https://bifurca.wandereronedollar.workers.dev/"},
            {"name": "ルール", "type": "text", "seed":
                "【サーバー規約】\n"
                "誹謗中傷・差別・スパムは禁止です。\n\n"
                "【ライセンス】創作物はCC BY-SA 4.0（出典表示＋継承）で公開してください。商用利用可。\n\n"
                "【コア設定について】グランドリッジの存在・規模、七民族の名称と基本文化、"
                "ンガ・ソルの正体不明性は変更できません。新しい設定を正史にしたい場合は"
                "🗨️創作フォーラムの「拡張設定提案」タグから提案してください。"
                "ンガ・ソルの正体を断定する投稿のみ禁止です。"},
            {"name": "お知らせ", "type": "text", "seed":
                "運営からのお知らせをここに投稿します。サーバー開設しました。"},
            {"name": "世界観ガイド", "type": "text", "seed":
                "【BIFURCAとは？】\n"
                "・文明分岐をテーマにしたオリジナル世界\n"
                "・七つの民族・宗教・国家が存在\n"
                "・魔法よりも歴史と文化を重視\n"
                "・正体不明の観測者「ンガ・ソル」が全民族の伝承に登場\n\n"
                "【初心者向けの読む順番】\n"
                "①世界史Ⅰ〜Ⅵ → ②用語辞典 → ③会話ログ\n\n"
                "公式サイト：https://bifurca.wandereronedollar.workers.dev/"},
        ],
    },
    {
        "name": "💬 COMMUNITY",
        "perms": PERM_COMMUNITY,
        "channels": [
            {"name": "雑談", "type": "text", "seed": "なんでも自由にどうぞ。ビフルカ関連でも雑談でも構いません。"},
            {"name": "質問・考察", "type": "text", "seed": "設定についての質問・考察はこちらに。「これって辞典のどこに書いてある？」レベルも歓迎です。"},
            {"name": "感想", "type": "text", "seed": "他の人の創作物への感想・応援コメントはこちらに。"},
            {"name": "自己紹介", "type": "text", "seed": "ハンドル名・好きな民族や地域・やりたい創作を一言ずつどうぞ。「地図を眺めていただけ」でもOKです。"},
        ],
    },
    {
        "name": "🏛 LORE",
        "perms": PERM_COMMUNITY,
        "channels": [
            {"name": "世界観アーカイブ", "type": "forum", "tags": LORE_TAGS, "seeds": LORE_SEEDS},
        ],
    },
    {
        "name": "🎨 CREATION",
        "perms": PERM_COMMUNITY,
        "channels": [
            {"name": "創作ルール", "type": "text", "perms": PERM_CREATION_RULES, "seed":
                "Layer1コア設定／Layer2公認拡張設定／Layer3ファン創作の三層構造です。\n"
                "Layer3（町・村・キャラクター・日常の物語）は完全自由。\n"
                "正史採用を目指す提案は🗨️創作フォーラムの「拡張設定提案」タグへ。"},
            {"name": "創作", "type": "forum", "tags": CREATION_TAGS, "seeds": CREATION_SEEDS},
            {"name": "制作進捗", "type": "text", "seed":
                "運営・公認創作者の制作進捗を共有する場所です。キャラクター設定の修正、画像生成、サイト更新などをここで。"},
        ],
    },
    {
        "name": "🎉 GALLERY",
        "perms": PERM_COMMUNITY,
        "channels": [
            {"name": "キャンペーン概要", "type": "text", "perms": PERM_GALLERY_INFO, "seed":
                "ファンアートキャンペーン「ビフルカを描け」\n"
                "サブテーマ：食卓／旅人／掟／証人。Twitter/Xまたはpixivに #ビフルカ タグで投稿してください。\n"
                "https://bifurca.wandereronedollar.workers.dev/gallery/index.html"},
            {"name": "投稿報告", "type": "text", "seed": "#ビフルカ タグで投稿したらリンクをここに貼ってください。"},
        ],
    },
    {
        "name": "🔒 ADMIN",
        "perms": PERM_ADMIN,
        "channels": [
            {"name": "運営メモ", "type": "text", "seed": "日常的な運営連絡用。"},
            {"name": "モデレーター", "type": "text", "seed": "通報対応・警告等の記録用。"},
            {"name": "商標・法務", "type": "text", "perms": PERM_ADMIN_SECRET, "seed":
                "商標出願戦略・区分の段階出願計画など機密情報専用。運営以外には共有しないこと。"},
        ],
    },
    {
        "name": "🔊 VOICE",
        "perms": PERM_VOICE,
        "channels": [
            {"name": "雑談ボイス", "type": "voice"},
        ],
    },
]

# ----------------------------------------------------------------------------
# API ヘルパー
# ----------------------------------------------------------------------------

def api(method, path, json=None, retries=3):
    if not APPLY:
        print(f"[DRY RUN] {method} {path}  body={json}")
        return {"id": "dryrun-id", "name": (json or {}).get("name", "")}
    url = f"{API_BASE}{path}"
    for attempt in range(retries):
        resp = requests.request(method, url, headers=HEADERS, json=json)
        if resp.status_code == 429:
            retry_after = resp.json().get("retry_after", 1)
            print(f"  rate limited, sleeping {retry_after}s")
            time.sleep(retry_after + 0.5)
            continue
        if resp.status_code >= 400:
            print(f"  ERROR {resp.status_code}: {resp.text}")
            resp.raise_for_status()
        time.sleep(0.4)  # 簡易レート制限対策
        return resp.json() if resp.text else {}
    raise RuntimeError(f"failed after {retries} retries: {method} {path}")


def overwrite_for(role_id, view, send):
    allow, deny = 0, 0
    if view is True:
        allow |= PERM["VIEW_CHANNEL"]
    elif view is False:
        deny |= PERM["VIEW_CHANNEL"]
    if send is True:
        allow |= WRITE_BITS
    elif send is False:
        deny |= WRITE_BITS
    return {"id": str(role_id), "type": 0, "allow": str(allow), "deny": str(deny)}


def build_overwrites(perm_template, role_ids, everyone_id):
    overwrites = []
    for role_key, rule in perm_template.items():
        role_id = everyone_id if role_key == "everyone" else role_ids.get(role_key)
        if role_id is None:
            continue
        overwrites.append(overwrite_for(role_id, rule.get("view"), rule.get("send")))
    return overwrites


# ----------------------------------------------------------------------------
# メイン処理
# ----------------------------------------------------------------------------

def main():
    print(f"=== BIFURCA Discord構築 {'(本番実行)' if APPLY else '(DRY RUN・確認のみ)'} ===\n")

    everyone_id = GUILD_ID  # @everyone のロールIDはギルドIDと同一

    # 1. ロール作成
    role_ids = {}
    print("--- ロール作成 ---")
    for r in ROLES:
        res = api("POST", f"/guilds/{GUILD_ID}/roles", {
            "name": r["name"], "color": r["color"],
            "permissions": str(r["permissions"]), "hoist": r["hoist"],
        })
        role_ids[r["name"]] = res.get("id")
        print(f"  role created: {r['name']} -> {res.get('id')}")

    # 2. カテゴリ＋チャンネル作成
    print("\n--- カテゴリ／チャンネル作成 ---")
    for cat in CATEGORIES:
        cat_overwrites = build_overwrites(cat["perms"], role_ids, everyone_id)
        cat_res = api("POST", f"/guilds/{GUILD_ID}/channels", {
            "name": cat["name"], "type": 4, "permission_overwrites": cat_overwrites,
        })
        cat_id = cat_res.get("id")
        print(f"category: {cat['name']} -> {cat_id}")

        for ch in cat["channels"]:
            ch_perms = ch.get("perms", cat["perms"])
            ch_overwrites = build_overwrites(ch_perms, role_ids, everyone_id)

            if ch["type"] == "text":
                ch_res = api("POST", f"/guilds/{GUILD_ID}/channels", {
                    "name": ch["name"], "type": 0, "parent_id": cat_id,
                    "permission_overwrites": ch_overwrites,
                })
                print(f"  text channel: {ch['name']} -> {ch_res.get('id')}")
                if ch.get("seed") and ch_res.get("id") != "dryrun-id":
                    api("POST", f"/channels/{ch_res['id']}/messages", {"content": ch["seed"]})
                elif ch.get("seed"):
                    print(f"    [DRY RUN] seed message: {ch['seed'][:40]}...")

            elif ch["type"] == "voice":
                ch_res = api("POST", f"/guilds/{GUILD_ID}/channels", {
                    "name": ch["name"], "type": 2, "parent_id": cat_id,
                    "permission_overwrites": ch_overwrites,
                })
                print(f"  voice channel: {ch['name']} -> {ch_res.get('id')}")

            elif ch["type"] == "forum":
                available_tags = [{"name": t} for t in ch["tags"]]
                ch_res = api("POST", f"/guilds/{GUILD_ID}/channels", {
                    "name": ch["name"], "type": 15, "parent_id": cat_id,
                    "permission_overwrites": ch_overwrites,
                    "available_tags": available_tags,
                })
                print(f"  forum channel: {ch['name']} -> {ch_res.get('id')}")

                tag_id_by_name = {}
                if ch_res.get("id") != "dryrun-id":
                    for t in ch_res.get("available_tags", []):
                        tag_id_by_name[t["name"]] = t["id"]

                seeds = ch.get("seeds", {})
                for tag_name, (title, content) in seeds.items():
                    applied = [tag_id_by_name[tag_name]] if tag_name in tag_id_by_name else []
                    if ch_res.get("id") == "dryrun-id":
                        print(f"    [DRY RUN] forum thread tag={tag_name} title={title}")
                        continue
                    api("POST", f"/channels/{ch_res['id']}/threads", {
                        "name": title,
                        "message": {"content": content},
                        "applied_tags": applied,
                    })
                    print(f"    seed thread created: {tag_name} / {title}")

    print("\n=== 完了 ===")
    if not APPLY:
        print("これはDRY RUNです。内容を確認後、`python bifurca_discord_setup.py --apply` で実行してください。")


if __name__ == "__main__":
    main()
