#!/usr/bin/env python3
"""熊野古道DB（sources.csv / excerpts.csv）を検索するための簡易CLI。

使い方:
  python3 search.py list-sources
  python3 search.py search キーワード
  python3 search.py search --tag 中辺路
  python3 search.py compare 中辺路        # 同じタグ/キーワードを出典ごとに並べて比較
"""
import argparse
import csv
import pathlib
import sys

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent


def load_csv(name):
    path = BASE_DIR / name
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_sources():
    return {row["source_id"]: row for row in load_csv("sources.csv")}


def load_excerpts():
    return load_csv("excerpts.csv")


def matches(row, keyword, tag):
    if tag and tag not in (row.get("tags") or "").split("|"):
        return False
    if keyword:
        haystack = " ".join(
            row.get(field, "") for field in ("quote", "tags", "note", "location")
        )
        if keyword not in haystack:
            return False
    return True


def print_excerpt(row, sources):
    src = sources.get(row["source_id"], {})
    title = src.get("title", row["source_id"])
    author = src.get("author", "")
    print(f"[{row['excerpt_id']}] {title}（{author}） {row['location']}")
    print(f"  引用: {row['quote']}")
    if row.get("tags"):
        print(f"  タグ: {row['tags']}")
    if row.get("note"):
        print(f"  メモ: {row['note']}")
    print()


def cmd_list_sources(args):
    for row in load_csv("sources.csv"):
        print(f"{row['source_id']}: {row['title']} / {row['author']} ({row['format']})")


def cmd_search(args):
    sources = load_sources()
    hits = [
        row for row in load_excerpts() if matches(row, args.keyword, args.tag)
    ]
    if not hits:
        print("該当する抜粋が見つかりませんでした。")
        return
    for row in hits:
        print_excerpt(row, sources)
    print(f"-- {len(hits)} 件 --")


def cmd_compare(args):
    sources = load_sources()
    hits = [row for row in load_excerpts() if matches(row, args.term, args.term)]
    if not hits:
        print("比較対象の抜粋が見つかりませんでした。")
        return
    grouped = {}
    for row in hits:
        grouped.setdefault(row["source_id"], []).append(row)
    for source_id, rows in grouped.items():
        src = sources.get(source_id, {})
        print(f"=== {src.get('title', source_id)}（{src.get('author', '')}） ===")
        for row in rows:
            print(f"  ・{row['location']}: {row['quote']}")
        print()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list-sources", help="登録済みの出典一覧を表示").set_defaults(func=cmd_list_sources)

    p_search = sub.add_parser("search", help="キーワード/タグで抜粋を検索")
    p_search.add_argument("keyword", nargs="?", default=None, help="引用・タグ・メモに含まれる語句")
    p_search.add_argument("--tag", default=None, help="タグで絞り込む（完全一致）")
    p_search.set_defaults(func=cmd_search)

    p_compare = sub.add_parser("compare", help="同じ語句/タグの抜粋を出典ごとに並べて比較")
    p_compare.add_argument("term", help="比較したいキーワードまたはタグ")
    p_compare.set_defaults(func=cmd_compare)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
