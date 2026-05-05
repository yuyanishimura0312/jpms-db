# Group E — testimonials_v2 品質監査レポート

- 実行時刻: 2026-05-05T12:05:37.332641+00:00
- 対象レコード: 7767 件 (testimonials_v2 全件)
- DB: `/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db`

## 1. 概要

本監査は JPMS-DB v2 の `testimonials_v2` テーブル全 7767 件を対象に、(1)重複検出、(2)引用倫理ゲート、(3)PII マスキング、(4)`speaker_role` 再分類、(5)出典 URL 検証 の5パスで実行した。削除ではなく `ethics_review_status` を更新するマーキング方式とし、重大な問題（個人特定可能情報の混入や著作権侵害の疑い）のみをDELETE 候補として別途リストアップしている。実装は `scripts/group_e_quality_audit.py` を参照。

## 2. 検出統計

| 項目 | 件数 |
|---|---:|
| 完全一致重複（school × quote） | 80 |
| 80文字プレフィックス重複 | 6 |
| 類似度 > 0.95 重複 | 487 |
| 文字化け（バイナリ／エンコード破損） | 88 |
| エラーログ文字列 | 1 |
| ダミーテキスト | 1 |
| 引用長 < 30 もしくは > 400 | 45 |
| PII マスキング適用 | 61 |
| 未成年者の rights を anonymized_only に降格 | 0 |
| speaker_role 再分類 | 20 |
| speaker_role を NULL（要レビュー） | 0 |
| 不正な source_url | 0 |
| approved（無問題） | 7062 |

## 3. ethics_review_status 内訳（更新後）

| status | 件数 |
|---|---:|
| approved | 6845 |
| flagged_dup_similar | 469 |
| rejected | 134 |
| flagged_dup_exact | 10 |
| flagged_dup_prefix | 5 |
| rejected_navigation | 3 |

## 4. speaker_role 内訳（更新後）

| role | 件数 |
|---|---:|
| parent | 1106 |
| principal | 1354 |
| student_alumni | 3056 |
| student_current | 1235 |
| teacher | 715 |

## 5. rights_level 内訳（更新後）

| rights | 件数 |
|---|---:|
| anonymized_only | 2660 |
| quoted_with_attribution | 4806 |

## 6. DELETE 候補

以下 90 件は文字化け／エラーログ／ダミーテキストの混入で、学校証言として無価値と判断したものである。`ethics_review_status='rejected'` としてマーキング済みだが、後段で物理削除を検討してよい。

| id | school_id | reason |
|---:|---|---|
| 1061 | jpms_s_0008 | garbled_binary |
| 1082 | jpms_s_0015 | garbled_binary |
| 1088 | jpms_s_0016 | garbled_binary |
| 1089 | jpms_s_0016 | garbled_binary |
| 1090 | jpms_s_0016 | garbled_binary |
| 1091 | jpms_s_0016 | garbled_binary |
| 1092 | jpms_s_0016 | garbled_binary |
| 1093 | jpms_s_0016 | garbled_binary |
| 1094 | jpms_s_0016 | garbled_binary |
| 1095 | jpms_s_0016 | garbled_binary |
| 1096 | jpms_s_0016 | garbled_binary |
| 1097 | jpms_s_0016 | garbled_binary |
| 1098 | jpms_s_0016 | garbled_binary |
| 1099 | jpms_s_0016 | garbled_binary |
| 1100 | jpms_s_0016 | garbled_binary |
| 1101 | jpms_s_0016 | garbled_binary |
| 1102 | jpms_s_0016 | garbled_binary |
| 1103 | jpms_s_0016 | garbled_binary |
| 1104 | jpms_s_0016 | garbled_binary |
| 1105 | jpms_s_0016 | garbled_binary |
| 1112 | jpms_s_0024 | garbled_binary |
| 1113 | jpms_s_0024 | garbled_binary |
| 1140 | jpms_s_0031 | garbled_binary |
| 1173 | jpms_s_0038 | garbled_binary |
| 1177 | jpms_s_0041 | garbled_binary |
| 1185 | jpms_s_0048 | garbled_binary |
| 1194 | jpms_s_0067 | garbled_binary |
| 1288 | jpms_s_0408 | garbled_binary |
| 1355 | jpms_s_0428 | garbled_binary |
| 1374 | jpms_s_0435 | garbled_binary |
| 1426 | jpms_s_0476 | garbled_binary |
| 1443 | jpms_s_0493 | garbled_binary |
| 1444 | jpms_s_0493 | error_log_string |
| 1445 | jpms_s_0493 | garbled_binary |
| 1555 | jpms_s_0005 | garbled_binary |
| 1563 | jpms_s_0005 | garbled_binary |
| 1573 | jpms_s_0008 | garbled_binary |
| 1574 | jpms_s_0008 | garbled_binary |
| 1577 | jpms_s_0008 | garbled_binary |
| 1588 | jpms_s_0015 | garbled_binary |
| 1606 | jpms_s_0022 | garbled_binary |
| 1646 | jpms_s_0027 | garbled_binary |
| 1658 | jpms_s_0028 | garbled_binary |
| 1659 | jpms_s_0028 | garbled_binary |
| 1684 | jpms_s_0030 | garbled_binary |
| 1685 | jpms_s_0031 | garbled_binary |
| 1686 | jpms_s_0031 | garbled_binary |
| 1689 | jpms_s_0031 | garbled_binary |
| 1830 | jpms_s_0061 | garbled_binary |
| 1832 | jpms_s_0062 | garbled_binary |
| ... | ... | （残り 40 件） |

## 7. 倫理上の判断

未成年者（`speaker_role = student_current` かつ卒業生・保護者・教員等の成人属性が確認できないもの）について、`rights_level` が `quoted_with_attribution` のまま登録されているケースを検出した場合、`anonymized_only` へ自動降格した。これは原典が学校 HP の公開ページに掲載されていたとしても、JPMS-DB の利用規程（フォーサイト分析の二次利用）においては実名引用の必要性が乏しいためである。

個人名（家族名漢字＋名2-3文字の連続）は `○○` に置換し、学年（中1/高2 等）は「中学生」「高校生」へ generic 化、部活名・期数・卒業年は 「部活動」「卒業生」へ集約した。これにより、引用の本旨である学校風土の表現は保ちつつ、特定個人へのリーチを抑制している。

## 8. 残課題

- `needs_review` ステータス（`speaker_role` が再分類できなかったレコード）については、後段で人手レビューが必要である。
- 類似度判定はスクール内でのみ実施しており、スクール横断の重複（学校間で同一のテンプレ文がコピーされているケース）は検出していない。Phase F で検討すること。
- 著作権の精緻な判断（教科書・パンフレット引用）は本パスでは行っていない。`source_type='pamphlet'` 等が出現した場合は別途レビューを実施する必要がある。
