import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Filament Flow - ניהול פילמנטים",
    page_icon="🧵",
    layout="wide",
)

st.markdown(
    """
<style>
    .main > div {direction: rtl;}
    .stMetric, h1, h2, h3, p, label {text-align: right !important;}
    .stForm {border: 1px solid #e2e8f0; border-radius: 14px; padding: 12px;}
    .status-ok {color: #047857; font-weight: 600;}
    .status-low {color: #b45309; font-weight: 600;}
    .status-critical {color: #b91c1c; font-weight: 700;}
</style>
""",
    unsafe_allow_html=True,
)

DATA_FILE = Path("data/filaments.json")
LOW_STOCK_GRAMS = 250
CRITICAL_STOCK_GRAMS = 100


@dataclass
class Filament:
    id: str
    name: str
    material: str
    color: str
    brand: str
    spool_weight_g: int
    remaining_g: int
    nozzle_temp_c: str
    bed_temp_c: str
    location: str
    notes: str
    updated_at: str


@dataclass
class UsageLog:
    filament_id: str
    project_name: str
    grams_used: int
    print_hours: float
    created_at: str


def ensure_data_file() -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text(
            json.dumps({"filaments": [], "usage_logs": []}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def load_data() -> Dict[str, List[Dict]]:
    ensure_data_file()
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def save_data(data: Dict[str, List[Dict]]) -> None:
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def status_label(remaining_g: int) -> str:
    if remaining_g <= CRITICAL_STOCK_GRAMS:
        return "🔴 קריטי"
    if remaining_g <= LOW_STOCK_GRAMS:
        return "🟠 נמוך"
    return "🟢 תקין"


def status_class(remaining_g: int) -> str:
    if remaining_g <= CRITICAL_STOCK_GRAMS:
        return "status-critical"
    if remaining_g <= LOW_STOCK_GRAMS:
        return "status-low"
    return "status-ok"


def filaments_df(data: Dict[str, List[Dict]]) -> pd.DataFrame:
    rows = []
    for filament in data["filaments"]:
        used_percent = 100 - (filament["remaining_g"] / filament["spool_weight_g"] * 100)
        rows.append(
            {
                "מזהה": filament["id"],
                "שם": filament["name"],
                "חומר": filament["material"],
                "צבע": filament["color"],
                "מותג": filament["brand"],
                "נשאר (גרם)": filament["remaining_g"],
                "משקל סליל (גרם)": filament["spool_weight_g"],
                "% שימוש": round(used_percent, 1),
                "סטטוס": status_label(filament["remaining_g"]),
                "מיקום": filament["location"],
                "עודכן": filament["updated_at"],
            }
        )
    return pd.DataFrame(rows)


def usage_df(data: Dict[str, List[Dict]]) -> pd.DataFrame:
    name_map = {f["id"]: f["name"] for f in data["filaments"]}
    rows = []
    for log in data["usage_logs"]:
        rows.append(
            {
                "תאריך": log["created_at"],
                "פרויקט": log["project_name"],
                "פילמנט": name_map.get(log["filament_id"], log["filament_id"]),
                "צריכה (גרם)": log["grams_used"],
                "שעות הדפסה": log["print_hours"],
            }
        )
    return pd.DataFrame(rows)


def add_filament(data: Dict[str, List[Dict]], filament: Filament) -> None:
    data["filaments"].append(asdict(filament))
    save_data(data)


def log_usage(data: Dict[str, List[Dict]], usage: UsageLog) -> None:
    target = next((f for f in data["filaments"] if f["id"] == usage.filament_id), None)
    if not target:
        raise ValueError("פילמנט לא נמצא")
    if usage.grams_used > target["remaining_g"]:
        raise ValueError("אין מספיק פילמנט לרישום הצריכה הזו")
    target["remaining_g"] -= usage.grams_used
    target["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    data["usage_logs"].append(asdict(usage))
    save_data(data)


def dashboard(data: Dict[str, List[Dict]]) -> None:
    st.subheader("סקירה מהירה")
    total_spools = len(data["filaments"])
    total_remaining = sum(f["remaining_g"] for f in data["filaments"])
    low_stock = [f for f in data["filaments"] if f["remaining_g"] <= LOW_STOCK_GRAMS]
    usage_today = sum(
        log["grams_used"]
        for log in data["usage_logs"]
        if log["created_at"].startswith(date.today().isoformat())
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("סלילים במלאי", total_spools)
    c2.metric("סה״כ פילמנט זמין", f"{total_remaining:,} גרם")
    c3.metric("מלאי נמוך/קריטי", len(low_stock))
    c4.metric("צריכה היום", f"{usage_today} גרם")

    if low_stock:
        st.warning("⚠️ יש לך פילמנטים שדורשים חידוש מלאי")
        for item in low_stock:
            css = status_class(item["remaining_g"])
            st.markdown(
                f"<div class='{css}'>• {item['name']} ({item['material']} {item['color']}) - נשאר {item['remaining_g']} גרם</div>",
                unsafe_allow_html=True,
            )


def main() -> None:
    st.title("🧵 Filament Flow")
    st.caption("מערכת נוחה וקלה לניהול מלאי פילמנטים עם חוויית משתמש נקייה וברורה")

    data = load_data()

    tabs = st.tabs(["📊 דשבורד", "➕ הוספת סליל", "🛠️ רישום שימוש", "📦 ניהול מלאי", "📈 אנליטיקה"])

    with tabs[0]:
        dashboard(data)

    with tabs[1]:
        st.subheader("הוספת פילמנט חדש")
        with st.form("add_filament_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("שם מזהה לסליל", placeholder="לדוגמה: PLA לבן - מדפסת ראשית")
                material = st.selectbox("חומר", ["PLA", "PETG", "ABS", "TPU", "ASA", "Nylon", "אחר"])
                color = st.text_input("צבע", placeholder="לבן")
                brand = st.text_input("מותג", placeholder="eSUN / Prusament / Sunlu")
                spool_weight_g = st.number_input("משקל סליל מלא (גרם)", min_value=250, max_value=5000, value=1000, step=50)
            with c2:
                remaining_g = st.number_input("כמות נוכחית (גרם)", min_value=0, max_value=5000, value=1000, step=10)
                nozzle_temp = st.text_input("טמפרטורת נחיר מומלצת", placeholder="200-220°C")
                bed_temp = st.text_input("טמפרטורת מיטה מומלצת", placeholder="55-65°C")
                location = st.text_input("מיקום אחסון", placeholder="ארון A - קופסה 2")
                notes = st.text_area("הערות", placeholder="רגיש ללחות, מומלץ לייבש לפני הדפסות ארוכות")

            submitted = st.form_submit_button("שמור פילמנט")

        if submitted:
            if not name.strip():
                st.error("צריך להזין שם לסליל")
            elif remaining_g > spool_weight_g:
                st.error("הכמות הנוכחית לא יכולה להיות גדולה ממשקל הסליל")
            else:
                filament = Filament(
                    id=f"F-{int(datetime.now().timestamp())}",
                    name=name.strip(),
                    material=material,
                    color=color.strip() or "לא צוין",
                    brand=brand.strip() or "לא צוין",
                    spool_weight_g=int(spool_weight_g),
                    remaining_g=int(remaining_g),
                    nozzle_temp_c=nozzle_temp.strip() or "לא צוין",
                    bed_temp_c=bed_temp.strip() or "לא צוין",
                    location=location.strip() or "לא צוין",
                    notes=notes.strip(),
                    updated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
                )
                add_filament(data, filament)
                st.success("הפילמנט נוסף בהצלחה ✅")

    with tabs[2]:
        st.subheader("רישום צריכת חומר מהדפסה")
        if not data["filaments"]:
            st.info("אין עדיין פילמנטים במערכת. הוסיפו סליל קודם.")
        else:
            options = {
                f"{f['name']} | נשאר: {f['remaining_g']} גרם": f["id"] for f in data["filaments"]
            }
            with st.form("usage_form", clear_on_submit=True):
                selected_label = st.selectbox("בחר פילמנט", list(options.keys()))
                project_name = st.text_input("שם פרויקט", placeholder="Bracket v2")
                grams_used = st.number_input("כמה גרם השתמשת?", min_value=1, max_value=2000, value=30)
                print_hours = st.number_input("משך הדפסה (שעות)", min_value=0.1, max_value=100.0, value=2.5, step=0.1)
                usage_submitted = st.form_submit_button("רשום שימוש")

            if usage_submitted:
                try:
                    usage = UsageLog(
                        filament_id=options[selected_label],
                        project_name=project_name.strip() or "פרויקט ללא שם",
                        grams_used=int(grams_used),
                        print_hours=float(print_hours),
                        created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
                    )
                    log_usage(data, usage)
                    st.success("השימוש נשמר והמלאי עודכן ✅")
                except ValueError as err:
                    st.error(str(err))

    with tabs[3]:
        st.subheader("מבט מלאי")
        df = filaments_df(data)
        if df.empty:
            st.info("עדיין אין נתוני מלאי")
        else:
            st.dataframe(df, use_container_width=True)

            st.markdown("#### מחיקת סליל")
            ids = {f"{f['name']} ({f['id']})": f["id"] for f in data["filaments"]}
            selected = st.selectbox("בחר סליל למחיקה", list(ids.keys()))
            if st.button("מחק סליל", type="secondary"):
                data["filaments"] = [f for f in data["filaments"] if f["id"] != ids[selected]]
                data["usage_logs"] = [u for u in data["usage_logs"] if u["filament_id"] != ids[selected]]
                save_data(data)
                st.success("הסליל והיסטוריית השימוש שלו נמחקו")

    with tabs[4]:
        st.subheader("אנליטיקה ותובנות")
        usage = usage_df(data)
        if usage.empty:
            st.info("אין עדיין נתוני שימוש")
        else:
            st.dataframe(usage.sort_values("תאריך", ascending=False), use_container_width=True)

            by_filament = (
                usage.groupby("פילמנט", as_index=False)["צריכה (גרם)"]
                .sum()
                .sort_values("צריכה (גרם)", ascending=False)
            )
            st.bar_chart(by_filament, x="פילמנט", y="צריכה (גרם)")

            total_usage = int(usage["צריכה (גרם)"].sum())
            avg_hours = round(float(usage["שעות הדפסה"].mean()), 2)
            st.markdown(f"**סה״כ חומר שנצרך:** {total_usage} גרם")
            st.markdown(f"**ממוצע שעות להדפסה:** {avg_hours}")


if __name__ == "__main__":
    main()
