import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 計算 eGFR
def calculate_egfr(age, creatinine, sex):
    if sex == '女性':
        k = 0.7
        a = -0.329
        gender_factor = 1.018
    else:
        k = 0.9
        a = -0.411
        gender_factor = 1
    egfr = 141 * min(creatinine / k, 1) ** a * max(creatinine / k, 1) ** -1.209 * 0.993 ** age * gender_factor
    return egfr

# 預估衰弱分數
def frailty_score(inputs):
    score = 0
    if inputs['grip_strength'] == '無力':
        score += 1
    if inputs['slow_walk'] == '是':
        score += 1
    if inputs['weight_loss'] == '是':
        score += 1
    if inputs['fatigue'] == '是':
        score += 1
    if inputs['activity_level'] == '低':
        score += 1
    return score

# 衰弱程度對應
def frailty_level(score):
    if score == 0:
        return "無衰弱"
    elif score <= 2:
        return "前衰弱"
    else:
        return "衰弱"

# 檢查是否為整數或半整數
def is_int_or_half(num):
    return (num * 2) == int(num * 2)

def main():
    st.set_page_config(page_title="整合性健康評估工具", page_icon="🩺")
    st.title("🩺 健康評估、生活習慣分析與衰弱預測")

    with st.form("health_form"):
        st.header("📋 基本資料")
        col1, col2 = st.columns(2)
        with col1:
            age = st.number_input("年齡 (歲)", 1, 120, 65)
            sex = st.selectbox("生理性別", ["女性", "男性"])
            height = st.number_input("身高 (公分)", 100.0, 250.0, 165.0)
        with col2:
            weight = st.number_input("體重 (公斤)", 30.0, 200.0, 70.0)
            creatinine = st.number_input("肌酐值 (mg/dL)", 0.1, 15.0, 1.0)
            sbp = st.number_input("收縮壓 SBP", 80, 250, 130)
            dbp = st.number_input("舒張壓 DBP", 40, 150, 85)

        st.header("🧠 衰弱量表（Fried Criteria）")
        grip_strength = st.radio("握力是否無力", ["有力", "無力"])
        slow_walk = st.radio("步行是否遲緩", ["否", "是"])
        weight_loss = st.radio("最近是否無故體重減輕", ["否", "是"])
        fatigue = st.radio("是否經常感到疲倦", ["否", "是"])
        activity_level = st.radio("日常活動量", ["正常", "低"])

        st.header("💬 生活習慣")
        drinking = st.selectbox("飲酒習慣", ["不喝", "偶爾", "經常"])
        smoking = st.selectbox("抽菸習慣", ["不抽", "已戒菸", "目前仍抽"])
        betel_nut = st.selectbox("是否嚼檳榔", ["否", "偶爾", "經常"])
        drug_use = st.selectbox("藥物濫用史", ["無", "過去有", "目前有"])
        stress = st.slider("自評壓力程度 (0 = 無壓力, 10 = 非常大壓力)", 0, 10, 4)

        sleep_hours = st.number_input(
            "平均每日睡眠時間 (小時) - 僅限整數或半整數",
            min_value=0.0,
            max_value=12.0,
            step=0.5,
            format="%.1f",
            help="請輸入整數或半整數 (例如 6, 6.5, 7, 7.5)"
        )

        submitted = st.form_submit_button("送出分析")

    if submitted:
        if not is_int_or_half(sleep_hours):
            st.error("睡眠時間輸入錯誤，請輸入整數或半整數（例如 6, 6.5, 7, 7.5）")
            return

        bmi = weight / (height / 100) ** 2
        egfr = calculate_egfr(age, creatinine, sex)
        score = frailty_score({
            'grip_strength': grip_strength,
            'slow_walk': slow_walk,
            'weight_loss': weight_loss,
            'fatigue': fatigue,
            'activity_level': activity_level,
        })
        frail_status = frailty_level(score)

        lifestyle_risk_score = (
            int(drinking != "不喝") +
            int(smoking == "目前仍抽") +
            int(betel_nut != "否") +
            int(drug_use == "目前有") +
            int(stress >= 7) +
            int(sleep_hours < 5 or sleep_hours > 10)
        )

        st.header("📊 分析結果")
        st.metric("eGFR (ml/min/1.73m²)", f"{egfr:.1f}")
        st.metric("BMI (kg/m²)", f"{bmi:.1f}")
        st.metric("衰弱評估", f"{frail_status}（分數：{score}）")
        st.metric("生活習慣風險分數", f"{lifestyle_risk_score} / 6")

        st.subheader("📉 健康狀態折線圖（與理想值比較）")
        ideal_values = {
            'BMI': 22,
            'SBP': 120,
            'DBP': 80,
            'eGFR': 90,
            '睡眠時間': 7.5,
            '衰弱指數': 0,
            '生活習慣指數': 1
        }

        actual_values = {
            'BMI': bmi,
            'SBP': sbp,
            'DBP': dbp,
            'eGFR': egfr,
            '睡眠時間': sleep_hours,
            '衰弱指數': score / 5,
            '生活習慣指數': 1 - lifestyle_risk_score / 6
        }

        df = pd.DataFrame({"項目": list(ideal_values.keys()), "理想值": list(ideal_values.values()), "實際值": list(actual_values.values())})
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.lineplot(data=df, x="項目", y="理想值", label="理想值", marker="o", linewidth=2, color="green")
        sns.lineplot(data=df, x="項目", y="實際值", label="實際值", marker="o", linewidth=2, color="blue")
        for i in range(len(df)):
            ax.text(i, df["實際值"][i], f'{df["實際值"][i]:.1f}', ha='center', va='bottom', fontsize=8)
        plt.title("健康指標折線圖")
        plt.xticks(rotation=45)
        plt.ylabel("指數")
        plt.tight_layout()
        st.pyplot(fig)

        st.subheader("📌 建議就醫科別")
        if egfr < 60:
            st.write("👉 建議就診：腎臟內科")
        if sbp >= 140 or dbp >= 90:
            st.write("👉 建議就診：心臟內科")
        if bmi >= 27 or bmi < 18.5:
            st.write("👉 建議就診：新陳代謝科或營養師諮詢")
        if frail_status == "衰弱":
            st.write("👉 建議就診：老年醫學科或復健科")
        if drug_use == "目前有":
            st.write("👉 建議就診：精神科或藥癮治療中心")
        if smoking == "目前仍抽" or betel_nut != "否":
            st.write("👉 建議就診：戒菸門診、口腔外科或耳鼻喉科")

        st.subheader("📚 衛教建議")
        if drinking != "不喝":
            st.info("💡 建議減少飲酒，過量飲酒可能導致肝臟疾病、高血壓、心律不整及多種癌症。")
        if smoking == "目前仍抽":
            st.info("💡 建議戒菸，吸菸會大幅增加肺癌、口腔癌、心血管疾病、中風及慢性阻塞性肺病的風險。")
        if betel_nut != "否":
            st.info("💡 嚼檳榔與口腔癌、牙周病及消化系統疾病高度相關，應考慮戒除。")
        if drug_use == "目前有":
            st.info("💡 藥物濫用可能引發神經、肝腎、心理及社會功能受損，建議尋求戒治資源如毒品危害防制中心。")
        if stress >= 7:
            st.info("💡 長期壓力會影響免疫系統、腸胃及心血管健康，建議透過冥想、運動、心理諮詢紓壓。")
        if sleep_hours < 5:
            st.info("💡 睡眠不足會影響記憶力、免疫力與代謝功能，建議每天至少睡 6 小時。")
        elif sleep_hours > 10:
            st.info("💡 睡眠過多與抑鬱症、代謝症候群有關，建議維持每日 6–9 小時的規律睡眠。")

        if bmi < 18.5:
            st.info("💡 體重過輕可能導致營養不良、免疫力下降與骨質疏鬆，建議補充營養與諮詢營養師。")
        elif bmi >= 24 and bmi < 27:
            st.info("💡 屬於體重過重範圍，建議增加活動量、調整飲食以控制體重。")
        elif bmi >= 27:
            st.info("💡 體重過高會增加代謝症候群、心血管疾病與糖尿病風險，建議進行體重控制與諮詢營養師。")

if __name__ == "__main__":
    main()
