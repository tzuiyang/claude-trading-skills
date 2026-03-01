---
layout: default
title: FinViz Screener
grand_parent: 日本語
parent: スキルガイド
nav_order: 1
lang_peer: /en/skills/finviz-screener/
permalink: /ja/skills/finviz-screener/
---

# FinViz Screener
{: .no_toc }

自然言語でFinVizのスクリーニング条件を構築し、Chromeで結果を表示するスキルです。
{: .fs-6 .fw-300 }

<span class="badge badge-free">API不要</span> <span class="badge badge-optional">FINVIZ Elite任意</span>

<details open markdown="block">
  <summary>目次</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. 概要

FinViz Screenerは、日本語または英語の自然言語による指示をFinVizのフィルターコードに変換し、スクリーニングURLを構築してChromeで開くスキルです。

**主な特徴:**
- 日本語・英語どちらの自然言語でも条件指定が可能
- 500以上のFinVizフィルターコードに対応（ファンダメンタル、テクニカル、記述的フィルター）
- FINVIZ Elite の自動検出（`$FINVIZ_API_KEY` 環境変数から判定）
- Chrome優先のブラウザ起動（OS別のフォールバック対応）
- URLインジェクション防止のための厳格なフィルター検証

**解決する問題:**
- FinVizの複雑なフィルターコードを覚える必要がなくなります
- 「高配当で成長している小型株」のような条件を、正しいフィルターの組み合わせに即座に変換します
- Eliteユーザーは自動的にリアルタイムデータのスクリーナーURLが生成されます

---

## 2. 前提条件

| 項目 | 要否 | 説明 |
|------|------|------|
| Python 3.7+ | 必須 | スクリプト実行用 |
| FINVIZ Elite APIキー | 任意 | 設定するとEliteスクリーナー（リアルタイムデータ）を使用 |
| Chromeブラウザ | 推奨 | 未インストール時はデフォルトブラウザで代替 |

追加のPythonパッケージのインストールは不要です（標準ライブラリのみ使用）。

> FINVIZ Eliteは `$FINVIZ_API_KEY` 環境変数が設定されている場合に自動検出されます。未設定時はパブリック（無料）スクリーナーにフォールバックします。
{: .tip }

---

## 3. クイックスタート

Claudeに自然言語で条件を伝えるだけで使えます：

```
高配当で割安な大型株を探して
```

Claudeが以下の流れで処理します：
1. 条件をフィルターコードに変換（`cap_large,fa_div_o3,fa_pe_u20,fa_pb_u2`）
2. フィルター一覧を確認用に表示
3. 確認後、URLを構築してChromeで開く

---

## 4. 仕組み

### ワークフロー

```
ユーザーの自然言語 → フィルター変換 → フィルター確認 → URL構築 → Chrome起動
```

**Step 1: フィルターリファレンスの読み込み**
- `references/finviz_screener_filters.md` に定義された500以上のフィルターコードを参照

**Step 2: 自然言語の解釈**
- 日本語/英語のキーワードをFinVizフィルターコードにマッピング
- 範囲指定（「配当3-8%」）は `{from}to{to}` 構文（例: `fa_div_3to8`）に変換

**Step 3: フィルター確認**
- 選択されたフィルターを表形式で表示し、ユーザーに確認を求める

**Step 4: スクリプト実行**
- `scripts/open_finviz_screener.py` でURL構築とChromeオープン
- `$FINVIZ_API_KEY` が設定されていれば `elite.finviz.com`、なければ `finviz.com` のURLを生成

**Step 5: 結果レポート**
- 構築されたURL、使用モード（Elite/Public）、適用フィルターのサマリー、次のステップの提案

### URL構造

```
https://finviz.com/screener.ashx?v={view}&f={filters}&o={order}
```

- `v` : ビュータイプ（overview=111, valuation=121, financial=161, technical=171 等）
- `f` : カンマ区切りのフィルターコード
- `o` : ソート順（`-marketcap` で時価総額降順など）

---

## 5. 使用例

### 例1: グロースモメンタム株

**プロンプト:**
```
EPS成長率が25%以上、SMA50とSMA200の上にあるモメンタム株を見つけて
```

**Claudeの動作:**
- フィルター: `fa_epsqoq_o25,ta_sma50_pa,ta_sma200_pa`
- ビュー: Technical (v=171)
- グロースとモメンタムの両方の条件を満たす銘柄を一覧表示

**なぜ有用か:** 業績成長がテクニカルトレンドでも確認されている銘柄に絞り込めます。

---

### 例2: CANSLIM + Minervini + VCP 統合フィルタ

**プロンプト:**
```
CANSLIMとMinerviniの条件を組み合わせたスクリーニングをしたい。
EPS成長25%以上、52週高値に近い、出来高が増加傾向、SMA全部の上にある銘柄
```

**Claudeの動作:**
- フィルター: `fa_epsqoq_o25,ta_highlow52w_b0to10h,sh_relvol_o1.5,ta_sma20_pa,ta_sma50_pa,ta_sma200_pa`
- ビュー: Performance (v=141)
- CANSLIM の C条件 + Minervini の Trend Template に近い条件の統合

**なぜ有用か:** 複数の投資手法の核心条件を1つのスクリーナーに統合し、高品質な候補銘柄を絞り込めます。

---

### 例3: 高配当バリュー株

**プロンプト:**
```
配当利回り3-8%、PER 10-20倍、PBR 2倍以下、ROE 15%以上の高配当バリュー株を探して
```

**Claudeの動作:**
- フィルター: `fa_div_3to8,fa_pe_10to20,fa_pb_u2,fa_roe_o15`
- ビュー: Valuation (v=121)
- 範囲指定 `fa_div_3to8` で配当トラップ（超高利回り）を除外

**なぜ有用か:** 配当利回りに上限を設けることで、減配リスクの高い銘柄を除外しつつ安定した配当収入を目指せます。

---

### 例4: 売られ過ぎリバウンド候補

**プロンプト:**
```
RSI30以下の売られすぎ大型株で、52週安値付近にあるものを表示して
```

**Claudeの動作:**
- フィルター: `cap_large,ta_rsi_os30,ta_highlow52w_a0to5l`
- ビュー: Technical (v=171)
- 大型株に限定することで流動性リスクを軽減

**なぜ有用か:** 一時的に売られ過ぎた優良大型株の反発エントリー候補を発見できます。

---

### 例5: AIテーマ株

**プロンプト:**
```
AIテーマの銘柄で、直近パフォーマンスが良好なものを見せて
```

**Claudeの動作:**
- フィルター: `theme_artificialintelligence`
- ソート: `-perf13w`（13週パフォーマンス降順）
- ビュー: Performance (v=141)

**なぜ有用か:** FinVizのテーマフィルター機能を使い、特定の投資テーマに直接アクセスできます。

---

### 例6: 小型株ブレイクアウト候補

**プロンプト:**
```
小型株で、52週高値から5%以内、出来高が通常の1.5倍以上のブレイクアウト候補を探して
```

**Claudeの動作:**
- フィルター: `cap_small,ta_highlow52w_b0to5h,sh_relvol_o1.5`
- ビュー: Overview (v=111)
- ブレイクアウトの2大条件（新高値近辺 + 出来高増加）を組み合わせ

**なぜ有用か:** 小型株のブレイクアウトエントリーポイントを効率的に発見できます。

---

### 例7: 日本語入力の柔軟性

**プロンプト:**
```
テクノロジーセクターの半導体関連で、機関保有率60%以上、インサイダー買いがある銘柄
```

**Claudeの動作:**
- フィルター: `sec_technology,ind_semiconductors,sh_instown_o60,sh_insidertrans_verypos`
- ビュー: Ownership (v=131)
- 日本語キーワード「半導体」「機関保有率」「インサイダー買い」を正確にマッピング

**なぜ有用か:** FinVizのフィルターコードを知らなくても、日本語の投資用語だけで高度なスクリーニングが実行できます。

---

### 例8: プログラマティック使用（`--url-only`）

**CLI コマンド:**
```bash
python3 skills/finviz-screener/scripts/open_finviz_screener.py \
  --filters "cap_mega,fa_div_o3,fa_pe_u15,ta_sma200_pa" \
  --view valuation \
  --url-only
```

**出力:**
```
https://finviz.com/screener.ashx?v=121&f=cap_mega,fa_div_o3,fa_pe_u15,ta_sma200_pa
```

**なぜ有用か:** `--url-only` オプションを使えば、ブラウザを開かずにURLだけを取得できます。スクリプトやSlack連携、定期実行での利用に便利です。

---

## 6. 出力の読み方

FinViz Screenerの結果は、FinVizのウェブサイト上で表示されます。

### ビュータイプの選び方

| ビュー | コード | 用途 |
|--------|--------|------|
| Overview | v=111 | 銘柄の概要確認（セクター、時価総額、P/E等） |
| Valuation | v=121 | バリュエーション比較（P/E、P/B、PEG、P/S等） |
| Ownership | v=131 | 機関投資家保有率、インサイダー取引 |
| Performance | v=141 | 期間別リターン（1W、1M、3M、6M、1Y） |
| Custom | v=152 | ユーザー定義カラム |
| Financial | v=161 | 財務指標（ROE、ROA、マージン、負債比率等） |
| Technical | v=171 | テクニカル指標（RSI、SMA、ベータ、ATR等） |

### 結果の確認ポイント

1. **銘柄数の確認** - 条件が厳しすぎて0件の場合は条件を緩和
2. **ソート順の活用** - カラムヘッダーをクリックしてソート切替
3. **ビューの切替** - 目的に応じてタブを切り替えて多角的に確認

---

## 7. Tips & ベストプラクティス

### フィルターの組み合わせ方

- **最大5-7フィルター**を目安にしてください。多すぎると結果が0件になりがちです
- **ファンダメンタル + テクニカル** の組み合わせが最も実用的です
- **範囲指定** (`fa_div_3to8`) を活用して極端な値を除外しましょう

### レシピの活用

以下のようなプリセットレシピが特に人気です：

| レシピ名 | フィルター例 |
|----------|-------------|
| Minervini Trend Template | `ta_sma20_pa,ta_sma50_pa,ta_sma200_pa,ta_highlow52w_b0to25h` |
| 配当貴族候補 | `fa_div_o2,fa_div_u8,fa_roe_o15,fa_debteq_u1,cap_large` |
| モメンタム突破 | `ta_highlow52w_b0to5h,sh_relvol_o2,ta_sma50_pa` |
| ディープバリュー | `fa_pb_u1,fa_pe_u10,fa_div_o3` |

### Elite vs Public の違い

| 項目 | Public | Elite |
|------|--------|-------|
| データ更新頻度 | 15分遅延 | リアルタイム |
| URL | finviz.com | elite.finviz.com |
| 料金 | 無料 | $39.99/月 |
| 検出方法 | `$FINVIZ_API_KEY` 未設定 | `$FINVIZ_API_KEY` 設定済み |

---

## 8. 他スキルとの連携

### FinViz → CANSLIM Screener

FinVizでグロース条件の粗い絞り込みを行い、CANSLIM Screenerで7コンポーネントの深い分析を実施：

```
1. FinViz: fa_epsqoq_o25,ta_sma200_pa で候補リスト取得
2. CANSLIM: リスト銘柄を --universe で渡して詳細スコアリング
```

### FinViz → VCP Screener

FinVizでStage 2のトレンドテンプレート条件を満たす銘柄をプレスクリーニング：

```
1. FinViz: ta_sma20_pa,ta_sma50_pa,ta_sma200_pa,ta_highlow52w_b0to25h
2. VCP: 候補銘柄のVCPパターン（ボラティリティ収縮）を詳細分析
```

### FinViz → Theme Detector

FinVizのテーマフィルターで個別銘柄を確認し、Theme Detectorでテーマ全体の強度を把握：

```
1. Theme Detector: テーマの Heat/Lifecycle/Confidence を確認
2. FinViz: theme_artificialintelligence 等でテーマ銘柄の個別確認
```

---

## 9. トラブルシューティング

### Chromeが開かない

**原因:** Chromeがインストールされていない、またはパスが通っていない

**対処:**
- macOS: `/Applications/Google Chrome.app` に Chrome が存在するか確認
- `--url-only` オプションでURLだけ取得し、手動でブラウザに貼り付け

### フィルターコードが無効と表示される

**原因:** フィルターコードの形式が正しくない

**対処:**
- フィルターコードは小文字の英数字、アンダースコア、ドット、ハイフンのみ使用可能
- `references/finviz_screener_filters.md` で正確なコードを確認

### 結果が0件

**原因:** フィルター条件が厳しすぎる

**対処:**
1. フィルター数を減らして段階的に追加
2. 範囲条件を広げる（例: `fa_pe_u10` → `fa_pe_u20`）
3. 時価総額フィルターを外して全銘柄で検索

---

## 10. リファレンス

### CLIオプション一覧

```bash
python3 scripts/open_finviz_screener.py [OPTIONS]
```

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `--filters` | カンマ区切りのフィルターコード（必須） | - |
| `--view` | ビュータイプ: overview, valuation, financial, technical, ownership, performance, custom | overview |
| `--order` | ソート順（例: `-marketcap`, `dividendyield`） | - |
| `--elite` | Elite モードを強制 | `$FINVIZ_API_KEY` から自動検出 |
| `--url-only` | URLを出力するだけでブラウザを開かない | false |

### よく使うフィルターコード

| カテゴリ | コード | 意味 |
|----------|--------|------|
| 時価総額 | `cap_small`, `cap_mid`, `cap_large`, `cap_mega` | 小型/中型/大型/超大型 |
| P/E | `fa_pe_u10`, `fa_pe_u20`, `fa_pe_profitable` | P/E 10倍未満/20倍未満/黒字 |
| 配当 | `fa_div_o3`, `fa_div_o5`, `fa_div_3to8` | 利回り3%超/5%超/3-8%範囲 |
| EPS成長 | `fa_epsqoq_o25`, `fa_epsqoq_o50` | 四半期EPS成長25%超/50%超 |
| RSI | `ta_rsi_os30`, `ta_rsi_ob70` | RSI 30以下/70以上 |
| SMA | `ta_sma50_pa`, `ta_sma200_pa` | SMA50上/SMA200上 |
| 52週 | `ta_highlow52w_b0to5h`, `ta_highlow52w_a0to5l` | 高値5%以内/安値5%以内 |
| セクター | `sec_technology`, `sec_healthcare`, `sec_energy` | テクノロジー/ヘルスケア/エネルギー |
| テーマ | `theme_artificialintelligence`, `theme_cybersecurity` | AI/サイバーセキュリティ |
| 出来高 | `sh_relvol_o1.5`, `sh_relvol_o2`, `sh_avgvol_o500` | 相対出来高1.5倍超/2倍超/平均50万超 |

### 関連ファイル

| ファイル | 説明 |
|----------|------|
| `skills/finviz-screener/SKILL.md` | スキル定義（ワークフロー） |
| `skills/finviz-screener/references/finviz_screener_filters.md` | 完全なフィルターコードリファレンス |
| `skills/finviz-screener/scripts/open_finviz_screener.py` | URL構築・ブラウザ起動スクリプト |
