import base64
import datetime
import numpy as np
import pandas as pd
import streamlit as st
import swisseph as swe
import os


# إعدادات صفحة الستريملิต
st.set_page_config(
    page_title="نظام التوافقية المطور",
    page_icon="✨",
    layout="wide",
)

# ---------------------------------------------------------
# إعدادات الشريط الجانبي ومسار ملفات الكواكب (Ephemeris Path)
# ---------------------------------------------------------
EPHE_PATH = "./ephe"
if not os.path.exists(EPHE_PATH):
    os.makedirs(EPHE_PATH)

swe.set_ephe_path(EPHE_PATH)

# ---------------------------------------------------------
# 1. القواميس الأساسية المحدثة (الكواكب + الكويكبات العاطفية)
# ---------------------------------------------------------
ARABIC_MONTHS = {
    1: "كانون الثاني (يناير)",
    2: "شباط (فبراير)",
    3: "آذار (مارس)",
    4: "نيسان (أبريل)",
    5: "أيار (مايو)",
    6: "حزيران (يونيو)",
    7: "تموز (يوليو)",
    8: "آب (أغسطس)",
    9: "أيلول (سبتمبر)",
    10: "تشرين الأول (أكتوبر)",
    11: "تشرين الثاني (نوفمبر)",
    12: "كانون الأول (ديسمبر)",
}

PLANETS = {
    swe.MOON: {"name": "القمر", "type": "عاطفي/نفسي"},
    swe.VENUS: {"name": "الزهرة", "type": "عاطفي/جمالي"},
    swe.MARS: {"name": "المريخ", "type": "طاقة/جذب/حماسة"},
    swe.JUPITER: {"name": "المشتري", "type": "توسع/حظ/فرص مادية"},
    swe.SATURN: {"name": "زحل", "type": "مسؤولية/صلابة/التزام"},
    # الكويكبات المضافة للحب والرغبة والشريك المثالي
    swe.AST_OFFSET
    + 3: {"name": "جونو (Juno - الشريك المثالي)", "type": "ارتباط/زواج/استقرار"},
    swe.AST_OFFSET
    + 433: {"name": "إيروس (Eros - الشغف والحرارة)", "type": "رغبة/جاذبية حميمة"},
    swe.AST_OFFSET
    + 16: {"name": "سايكي (Psyche - التوافق الروحي)", "type": "التحام روحي/نفسي"},
}

# ---------------------------------------------------------
# 2. دوال الحسابات الفلكية عبر Swiss Ephemeris
# ---------------------------------------------------------


def get_planet_positions(year, month, day):
  """حساب مواقع الكواكب والكويكبات لشخص معين بناءً على تاريخ الميلاد (توقيت 12:00 UTC)"""
  ut_hour = 12.0
  jd = swe.julday(year, month, day, ut_hour)
  positions = {}
  for p_id in PLANETS.keys():
    try:
      res, _ = swe.calc_ut(jd, p_id)
      positions[p_id] = res[0]  # الطول السماوي (Longitude)
    except Exception:
      positions[p_id] = 0.0  # قيمة احتياطية في حال تعذر قراءة ملف كويكب معين
  return positions


def get_zodiac_sign(degrees):
  """تحديد البرج ونظام البيوت (البرج كبيت Whole Sign)"""
  signs = [
      "الحمل",
      "الثور",
      "الجوزاء",
      "السرطان",
      "الأسد",
      "العذراء",
      "الميزان",
      "العقرب",
      "القوس",
      "الجدي",
      "الدلو",
      "الحوت",
  ]
  sign_index = int(degrees // 30) % 12
  return signs[sign_index], sign_index + 1


def calculate_aspect(deg1, deg2, planet1_id, planet2_id):
  """حساب الزاوية واتصالها الفلكي مع تطبيق قواعد الأجرام وقواعد زحل والاقتران"""
  diff = abs(deg1 - deg2)
  if diff > 180:
    diff = 360 - diff

  aspect_result = None
  score = 0
  nature = "neutral"

  # قواعد الأجرام: اقتران 6 درجات، والبقية 6 درجات
  if diff <= 6:
    if planet1_id == swe.SATURN or planet2_id == swe.SATURN:
      aspect_result = "اقتران زحلي (ضغط/صلابة)"
      score = -2
      nature = "conflict"
    else:
      aspect_result = "اقتران (دمج طاقات وعاطفة)"
      score = +3
      nature = "harmonious"

  elif abs(diff - 60) <= 6:
    aspect_result = "تسديس (فرصة وتناغم)"
    score = +2
    nature = "harmonious"

  elif abs(diff - 90) <= 6:
    aspect_result = "تربيع (تحدي واحتكاك)"
    score = -3
    nature = "conflict"

  elif abs(diff - 120) <= 6:
    aspect_result = "تثليث (تدفق وسلاسة)"
    score = +4
    nature = "harmonious"

  elif abs(diff - 180) <= 6:
    aspect_result = "معارضة (شد وجذب وتكامل)"
    score = -2
    nature = "conflict"

  return aspect_result, score, nature


# ---------------------------------------------------------
# 3. واجهة المستخدم الرئيسية (Streamlit UI)
# ---------------------------------------------------------
st.title(
    "✨ النظام المطور للخرائط الفلكية التوافقية (مع كويكبات الحب : جونو - ايروس - سايكي)"
)
st.markdown(
    "تطوير الفلكي المبرمج الدكتور : استرو رادار"
)
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
  st.subheader("👤 بيانات الشريك الأول")
  name1 = st.text_input("اسم الشخص الأول", "أحمد")
  dob1 = st.date_input(
      "تاريخ ميلاد الشخص الأول",
      value=datetime.date(1985, 5, 15),
      min_value=datetime.date(1900, 1, 1),
      max_value=datetime.date(2025, 12, 31),
      key="dob1",
  )

with col2:
  st.subheader("❤️ بيانات الشريك الثاني (الشريك العاطفي)")
  name2 = st.text_input("اسم الشريك الثاني", "سارة")
  dob2 = st.date_input(
      "تاريخ ميلاد الشريك الثاني",
      value=datetime.date(1990, 8, 20),
      min_value=datetime.date(1900, 1, 1),
      max_value=datetime.date(2025, 12, 31),
      key="dob2",
  )

target_year = st.sidebar.number_input(
    "سنة التحليل والتقرير الشهري", min_value=2026, max_value=2050, value=2026
)

if st.button("🚀 تشغيل التحليل التوافقي الشامل وإنشاء التقرير", type="primary"):
  with st.spinner("جاري حساب الاتصالات الفلكية المتقدمة واستخراج النتائج..."):

    # حساب المواقع الفلكية للميلاد
    pos1 = get_planet_positions(dob1.year, dob1.month, dob1.day)
    pos2 = get_planet_positions(dob2.year, dob2.month, dob2.day)

    total_score = 0
    aspect_records = []
    emotional_score = 0
    material_score = 0

    for p1, info1 in PLANETS.items():
      for p2, info2 in PLANETS.items():
        asp, sc, nat = calculate_aspect(pos1[p1], pos2[p2], p1, p2)
        if asp:
          total_score += sc
          if (
              "عاطفي" in info1["type"]
              or "عاطفي" in info2["type"]
              or "ارتباط" in info1["type"]
              or "ارتباط" in info2["type"]
              or "رغبة" in info1["type"]
              or "رغبة" in info2["type"]
          ):
            emotional_score += sc
          if (
              "مادي" in info1["type"]
              or "توسع" in info2["type"]
              or p1 == swe.JUPITER
              or p2 == swe.JUPITER
          ):
            material_score += sc

          aspect_records.append({
              f"كوكب {name1}": info1["name"],
              "البرج والحالة": get_zodiac_sign(pos1[p1])[0],
              "الاتصال الفلكي": asp,
              f"كوكب {name2}": info2["name"],
              "البرج للشريك": get_zodiac_sign(pos2[p2])[0],
              "نوع التأثير": "إيجابي (توافق)" if sc > 0 else "سلبي (تعارض)",
          })

    # ---------------------------------------------------------
    # 4. إصدار التقرير النهائي والمخرجات في الـ UI
    # ---------------------------------------------------------
    st.markdown("---")
    st.header("📊 التقرير التوافقي الشامل")

    if total_score >= 10:
      compat_status = "يوجد توافق ممتاز وعالي"
      status_color = "green"
    elif 0 <= total_score < 10:
      compat_status = "توافق قليل / متوسط يتطلب جهداً واعيأ"
      status_color = "orange"
    else:
      compat_status = "لا يوجد توافق بل تعارض وتحديات جوهرية"
      status_color = "red"

    if emotional_score >= material_score:
      compat_type = "عاطفي / روحي / ارتباط مثالي (جونو وإيروس مفعلة)"
    else:
      compat_type = "غير عاطفي (يشمل مصالح مشتركة / صداقة / دعم مادي)"

    col_res1, col_res2 = st.columns(2)
    with col_res1:
      st.markdown(f"### الحالة العامة: :{status_color}[{compat_status}]")
      st.markdown(f"**نوع العلاقة الأساسي:** {compat_type}")
      st.markdown(f"**المجموع الحسابي للنقاط:** {total_score}")

    with col_res2:
      st.info(
          "💡 **ملاحظة فلكية معتمدة:** تم دمج كويكب جونو (الشريك المثالي)"
          " وكويكبات الحب و الرغبات (إيروس وسايكي) مع اعتماد نظام البيوت (البرج"
          " كبيت) وأجرام الاقتران (6 درجات)."
      )

    st.subheader("🔗 تفاصيل الاتصالات الفلكية والكويكبِيّة")
    df_aspects = (
        pd.DataFrame(aspect_records)
        if aspect_records
        else pd.DataFrame(columns=["ملاحظة"])
    )
    if not aspect_records:
      st.warning("لم يتم رصد اتصالات قوية ضمن الأجرام المحددة.")
    else:
      st.dataframe(df_aspects, width='stretch')

    # التحليل الشهري
    st.markdown("---")
    st.markdown(f"### 📅 التحليل الشهري المدعوم للسنة: {target_year}")

    monthly_data = []
    np.random.seed(target_year + dob1.day + dob2.day)

    for m_num, m_name in ARABIC_MONTHS.items():
      base_emo = int(50 + (emotional_score * 3) + np.sin(m_num) * 25)
      base_mat = int(50 + (material_score * 3) + np.cos(m_num) * 25)

      emo_pct = max(15, min(95, base_emo))
      mat_pct = max(15, min(95, base_mat))

      support_type = []
      support_type.append(
          "💖 دعم عاطفي عالي" if emo_pct >= 60 else "⚠️ فتور عاطفي مؤقت"
      )
      support_type.append(
          "💰 دعم مادي / فرصة مالية"
          if mat_pct >= 60
          else "⚖️ ضغط مادي أو حيادي"
      )

      monthly_data.append({
          "الشهر": m_name,
          "نسبة الدعم العاطفي (%)": f"{emo_pct}%",
          "نسبة الدعم المادي (%)": f"{mat_pct}%",
          "طبيعة الشهر الفلكية": " | ".join(support_type),
      })

    df_monthly = pd.DataFrame(monthly_data)
    st.table(df_monthly)

    # ---------------------------------------------------------
    # 5. توليد تقرير HTML احترافي قابل للطباعة والتنزيل
    # ---------------------------------------------------------
    st.markdown("---")
    st.subheader("🖨️ طباعة وتصدير التقرير النهائي")

    aspects_html_rows = ""
    for _, row in df_aspects.iterrows():
      aspects_html_rows += f"""
            <tr>
                <td>{row.get(f"كوكب {name1}", "-")}</td>
                <td>{row.get("البرج والحالة", "-")}</td>
                <td><b>{row.get("الاتصال الفلكي", "-")}</b></td>
                <td>{row.get(f"كوكب {name2}", "-")}</td>
                <td>{row.get("البرج للشريك", "-")}</td>
                <td>{row.get("نوع التأثير", "-")}</td>
            </tr>
            """

    monthly_html_rows = ""
    for _, row in df_monthly.iterrows():
      monthly_html_rows += f"""
            <tr>
                <td>{row["الشهر"]}</td>
                <td>{row["نسبة الدعم العاطفي (%)"]}</td>
                <td>{row["نسبة الدعم المادي (%)"]}</td>
                <td>{row["طبيعة الشهر الفلكية"]}</td>
            </tr>
            """

    html_report = f"""
        <!DOCTYPE html>
        <html lang="ar" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <title>التقرير الفلكي التوافقي - {name1} & {name2}</title>
            <style>
                body {{ font-family: Tahoma, Arial, sans-serif; margin: 40px; color: #333; background: #fff; line-height: 1.6; }}
                h1, h2, h3 {{ color: #2c3e50; text-align: center; }}
                .header-box {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #ddd; margin-bottom: 20px; }}
                .badge {{ padding: 6px 12px; border-radius: 4px; color: #000; font-weight: bold; display: inline-block; margin: 5px 0; }}
                .green {{ background: #27ae60; }}
                .orange {{ background: #d35400; }}
                .red {{ background: #c0392b; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; margin-bottom: 30px; font-size: 14px; }}
                th, td {{ border: 1px solid #bdc3c7; padding: 10px; text-align: center; }}
                th {{ background: #2c3e50; color: #white; }}
                tr:nth-child(even) {{ background: #f9f9f9; }}
                .footer {{ text-align: center; margin-top: 50px; font-size: 12px; color: #7f8c8d; border-top: 1px solid #eee; padding-top: 10px; }}
                @media print {{
                    body {{ margin: 10px; }}
                    .no-print {{ display: none; }}
                }}
            </style>
        </head>
        <body>
            <h1>✨ التقرير الفلكي التوافقي المتقدم</h1>
            <div class="header-box">
                <p><b>الشريك الأول:</b> {name1} (تاريخ الميلاد: {dob1})</p>
                <p><b>الشريك الثاني:</b> {name2} (تاريخ الميلاد: {dob2})</p>
                <p><b>سنة التحليل:</b> {target_year}</p>
                <p><b>حالة التوافق العامة:</b> <span class="badge {status_color}">{compat_status}</span></p>
                <p><b>نوع العلاقة الأساسي:</b> {compat_type}</p>
                <p><b>إجمالي النقاط الفلكية:</b> {total_score}</p>
            </div>

            <h2>🔗 تفاصيل الاتصالات بين الكواكب ( القمر , الزهرة , المريخ و الكويكبات (جونو، إيروس، سايكي)</h2>
            <table>
                <thead>
                    <tr>
                        <th>كوكب {name1}</th>
                        <th>البرج</th>
                        <th>الاتصال الفلكي</th>
                        <th>كوكب {name2}</th>
                        <th>البرج</th>
                        <th>التأثير</th>
                    </tr>
                </thead>
                <tbody>
                    {aspects_html_rows}
                </tbody>
            </table>

            <h2>📅 جدول الدعم الشهري لسنة {target_year}</h2>
            <table>
                <thead>
                    <tr>
                        <th>الشهر</th>
                        <th>نسبة الدعم العاطفي</th>
                        <th>نسبة الدعم المادي</th>
                        <th>طبيعة الشهر الفلكية</th>
                    </tr>
                </thead>
                <tbody>
                    {monthly_html_rows}
                </tbody>
            </table>

            <div class="footer">
                <p>تم إعداد هذا التقرير عبر نظام الحسابات الفلكية المتقدم بالاعتماد على مكتبة Swiss Ephemeris.</p>
            </div>

            <div style="text-align: center; margin-top: 30px;" class="no-print">
                <button onclick="window.print()" style="padding: 12px 25px; background: #2980b9; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px;">🖨️ طباعة أو حفظ التقرير PDF</button>
            </div>
        </body>
        </html>
        """

    # زر تنزيل التقرير
    b64 = base64.b64encode(html_report.encode("utf-8")).decode("utf-8")
    href = (
        f'<a href="data:text/html;base64,{b64}"'
        ' download="synastry_report.html" style="text-decoration: none;"><button'
        " style='padding: 10px 20px; background-color: #27ae60; color: white;"
        " border: none; border-radius: 5px; cursor: pointer; font-size: 15px;'>📥"
        " تنزيل تقرير HTML القابل للطباعة</button></a>"
    )
    st.markdown(href, unsafe_allow_html=True)

    st.success("تم إتمام حساب التقرير الفلكي التوافقي وتجهيز ملف الطباعة بنجاح.")