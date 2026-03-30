import streamlit as st
from google import genai
from google.genai import types
import json
import os
import re
import pandas as pd

st.set_page_config(page_title="EGOGRAM EVIDENCE ANALYZER", layout="wide")

st.title("🔬 エゴグラム妥当性検証ツール")
st.caption("文章から15カテゴリ（P/M/Z）の判定根拠を抽出し、エビデンス化します。")

# --- API設定 ---
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# --- 入力エリア ---
col_info_1, col_info_2 = st.columns(2)
with col_info_1: gender = st.selectbox("性別", ["男性", "女性", "その他"])
with col_info_2: age = st.selectbox("年齢", ["10代", "20代", "30代", "40代", "50代", "60代", "70代以上"])
input_text = st.text_area("分析対象の文章を入力してください", height=200)

if st.button("🔍 エビデンス抽出実行"):
    if not input_text:
        st.warning("文章を入力してください。")
    else:
        with st.spinner("AIが深層心理のベクトルと語彙を照合中..."):
            # 検証用の詳細プロンプト
            prompt = f"""
            属性: {age}、{gender}。対象文章: '{input_text}'
            エゴグラムの5つの自我状態(CP,NP,A,FC,AC)について、P(建設的/光)、M(破壊的/影)、Z(不活性/無)の15項目を分析せよ。
            
            各項目について、以下の3点を必ず出力すること：
            1. スコア (0-10)
            2. 根拠となった具体的な単語またはフレーズ (evidence)
            3. その語彙がなぜそのカテゴリに該当すると判断したかの論理的理由 (reason)

            回答は必ず以下の構造のJSON形式のみで行うこと。
            {{
              "analysis": {{
                "CP": {{
                  "P": {{"score": 0, "evidence": "...", "reason": "..."}},
                  "M": {{"score": 0, "evidence": "...", "reason": "..."}},
                  "Z": {{"score": 0, "evidence": "...", "reason": "..."}}
                }},
                "NP": {{ ...同様に15項目分... }},
                ...
              }}
            }}
            """

            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash", 
                    contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json")
                )
                res_data = json.loads(response.text)
                
                # --- 結果の表示 ---
                st.subheader("📋 分析エビデンス一覧表")
                
                rows = []
                for ego, categories in res_data["analysis"].items():
                    for cat_type, details in categories.items():
                        rows.append({
                            "自我状態": ego,
                            "タイプ": "P (光)" if cat_type == "P" else "M (影)" if cat_type == "M" else "Z (無)",
                            "スコア": details["score"],
                            "採用された単語・フレーズ": details["evidence"],
                            "判定の論理的根拠": details["reason"]
                        })
                
                df = pd.DataFrame(rows)
                st.table(df) # 画面表示は元のままの項目
                
                # CSV出力用には「分析対象文章」を先頭に追加
                df_csv = df.copy()
                df_csv.insert(0, "分析対象文章", input_text)
                
                # CSVダウンロード機能（エビデンス蓄積用）
                csv = df_csv.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 結果をCSVとしてダウンロード",
                    data=csv,
                    file_name="egogram_evidence.csv",
                    mime="text/csv",
                )

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

st.divider()
st.info("※このツールは研究用です。トークン消費量は通常版より多くなりますが、15カテゴリの判定プロセスを可視化できます。")