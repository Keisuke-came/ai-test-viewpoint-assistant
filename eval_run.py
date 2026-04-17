#!/usr/bin/env python3
"""評価実行 CLI。

使い方:
    # デフォルトケースで評価（キャッシュ利用）
    python eval_run.py

    # キャッシュを無視して再生成
    python eval_run.py --refresh

    # 結果を JSON ファイルに保存
    python eval_run.py --output-json results/eval_report.json

    # 結果を Markdown ファイルに保存
    python eval_run.py --output-md results/eval_report.md

    # 両方保存
    python eval_run.py --output-json results/eval.json --output-md results/eval.md

    # カスタムケースファイルを指定
    python eval_run.py --cases eval_cases/my_cases.json
"""
import argparse
import logging
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AI テスト観点生成の評価ツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="キャッシュを無視して LLM を再実行する",
    )
    parser.add_argument(
        "--output-json",
        metavar="PATH",
        help="評価結果を JSON ファイルに保存するパス",
    )
    parser.add_argument(
        "--output-md",
        metavar="PATH",
        help="評価結果を Markdown ファイルに保存するパス",
    )
    parser.add_argument(
        "--cases",
        metavar="PATH",
        default="eval_cases/default_cases.json",
        help="評価ケース JSON ファイルのパス（デフォルト: eval_cases/default_cases.json）",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="詳細ログを出力する",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    # 遅延 import（設定系の副作用を CLI 引数処理後に発生させる）
    from app.eval.case_loader import load_cases
    from app.eval.reporter import to_json, to_markdown
    from app.eval.runner import run_cases

    print(f"評価ケースを読み込み中: {args.cases}")
    try:
        cases = load_cases(Path(args.cases))
    except FileNotFoundError as e:
        print(f"エラー: {e}", file=sys.stderr)
        return 1

    cache_msg = "（--refresh: キャッシュ無効）" if args.refresh else "（キャッシュ利用）"
    print(f"評価を実行します {cache_msg}: {len(cases)} ケース")

    try:
        report = run_cases(cases, refresh=args.refresh)
    except EnvironmentError as e:
        print(f"設定エラー: {e}", file=sys.stderr)
        return 1

    # コンソール出力
    print()
    print(f"{'=' * 50}")
    print(f"  結果: {report.passed}/{report.total} PASS  ({report.failed} FAIL)")
    pass_rate = f"{report.passed / report.total * 100:.1f}%" if report.total > 0 else "N/A"
    print(f"  合格率: {pass_rate}")
    print(f"  処理時間: {report.total_duration_seconds}s")
    if report.total_tokens is not None:
        print(f"  総トークン数: {report.total_tokens:,}")
    print(f"{'=' * 50}")
    print()

    for r in report.results:
        status = "PASS" if r.passed else "FAIL"
        cache_str = "[cache]" if r.cache_hit else "[llm]  "
        print(f"  {status}  {cache_str}  {r.case_id}: {r.title}  ({r.viewpoint_count} 観点, {r.duration_seconds}s)")
        for failure in r.failures:
            print(f"        ✗ {failure}")

    # ファイル出力
    if args.output_json:
        out_path = Path(args.output_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(to_json(report), encoding="utf-8")
        print(f"\nJSON 保存: {out_path}")

    if args.output_md:
        out_path = Path(args.output_md)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(to_markdown(report), encoding="utf-8")
        print(f"Markdown 保存: {out_path}")

    return 0 if report.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
