import streamlit as st
import pandas as pd
import sqlalchemy
import os
from dotenv import load_dotenv
import re
from urllib.parse import quote_plus
import time
import requests
import json

# -------------------------------------------------------
# Load environment variables
# -------------------------------------------------------
load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")

DB_SERVER    = os.getenv("DB_SERVER", "localhost")
DB_PORT      = os.getenv("DB_PORT", "1434")
DB_USER      = os.getenv("DB_USER", "sa")
DB_PASSWORD  = os.getenv("DB_PASSWORD", "YourStrong@Passw0rd")
DB_NAME      = os.getenv("DB_NAME", "BusinessDB")

# -------------------------------------------------------
# Client Configuration
# -------------------------------------------------------
client_config = {
    "base_url": OLLAMA_BASE_URL,
    "model": OLLAMA_MODEL
}

# -------------------------------------------------------
# Database Engine
# -------------------------------------------------------
@st.cache_resource(show_spinner=False)
def get_db_engine(server, port, user, password, db):
    try:
        pwd_encoded = quote_plus(password)
        driver = "ODBC+Driver+18+for+SQL+Server"
        conn_str = (
            f"mssql+pyodbc://{user}:{pwd_encoded}@{server},{port}/{db}"
            f"?driver={driver}&TrustServerCertificate=yes&Encrypt=no"
        )
        engine = sqlalchemy.create_engine(conn_str, fast_executemany=True)
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text("SELECT 1"))
        return engine, None
    except Exception as e:
        return None, str(e)

engine, db_error = get_db_engine(DB_SERVER, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)

# -------------------------------------------------------
# Schema Retrieval
# -------------------------------------------------------
@st.cache_data(show_spinner=False)
def get_database_schema(_engine):
    if _engine is None:
        return "Không thể kết nối database."
    schema = ""
    try:
        tables = pd.read_sql(
            "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'",
            _engine
        )
        for _, row in tables.iterrows():
            tbl = row["TABLE_NAME"]
            schema += f"Table: {tbl}\nColumns:\n"
            cols = pd.read_sql(
                f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='{tbl}'",
                _engine
            )
            for _, col in cols.iterrows():
                schema += f"  - {col['COLUMN_NAME']} ({col['DATA_TYPE']})\n"
            schema += "\n"
        return schema
    except Exception as e:
        return f"Lỗi đọc schema: {e}"

db_schema = get_database_schema(engine)

# -------------------------------------------------------
# Text-to-SQL  (dùng Ollama)
# -------------------------------------------------------
@st.cache_data(show_spinner=False)
def generate_sql(question: str, schema: str, client_cfg: dict) -> str:
    prompt = f"""You are a senior T-SQL engineer specializing in Microsoft SQL Server.

Your task is to translate a natural language business question into a syntactically correct and executable T-SQL SELECT query.

Follow these rules strictly:

Use TOP (n) instead of LIMIT.
Only reference tables and columns explicitly defined in the provided database schema.
Do not use any table or column that is not present in the schema.
Ensure all selected columns come from tables that are properly joined.
Use appropriate JOIN conditions based only on defined relationships in the schema.
Do not assume implicit relationships. Specifically, there is no direct relationship between Orders and Products.
Prefer clear and efficient queries suitable for business reporting (e.g., use aggregation, grouping, filtering where appropriate).
If the question is ambiguous, choose the most reasonable business interpretation without inventing new fields.
Do not include INSERT, UPDATE, DELETE, or DDL statements.
Output requirements:
Return only the final SQL query.
Do not include explanations, comments, or markdown formatting.
Database Schema:
{schema}

Question: {question}"""
    
    url = f"{client_cfg['base_url'].rstrip('/')}/api/generate"
    payload = {
        "model": client_cfg["model"],
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=120)
        if response.status_code == 500:
            return f"ERROR: Ollama báo lỗi 500 (Internal Server Error). Nguyên nhân thường do thiếu RAM/VRAM để chạy model {client_cfg['model']}. Vui lòng đóng bớt ứng dụng (còn khoảng 1GB RAM trống) hoặc dùng model nhỏ hơn (vd: 1.5b, 3b)."
        response.raise_for_status()
        raw = response.json().get("response", "").strip()
        # Strip possible markdown code fences
        raw = re.sub(r"^```(?:sql)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)
        return raw.strip()
    except requests.exceptions.Timeout:
        return f"ERROR: Ollama phản hồi quá chậm (Timeout > 120s). Có thể máy đang thiếu RAM và phải tải model chậm."
    except Exception as e:
        return f"ERROR: Lỗi kết nối Ollama: {e}"

# -------------------------------------------------------
# SQL Validator (Security – Read-Only)
# -------------------------------------------------------
FORBIDDEN = {"INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "EXEC", "GRANT", "MERGE"}

def validate_sql(sql: str):
    upper = sql.upper()
    if not (upper.lstrip().startswith("SELECT") or upper.lstrip().startswith("WITH")):
        return False, "Query phải bắt đầu bằng SELECT hoặc WITH (CTE)."
    for kw in FORBIDDEN:
        if re.search(rf"\b{kw}\b", upper):
            return False, f"Từ khóa bị cấm: '{kw}'. Hệ thống chỉ cho phép đọc (Read-Only)."
    return True, "OK"

# -------------------------------------------------------
# Result Explanation  (dùng Ollama)
# -------------------------------------------------------
@st.cache_data(show_spinner=False)
def explain_result(question: str, sql: str, df_head: pd.DataFrame, client_cfg: dict) -> str:
    prompt = f"""Bạn là Business Analyst. Hãy giải thích ngắn gọn (2-3 câu) kết quả dữ liệu dưới đây cho người dùng Business bằng tiếng Việt.
KHÔNG cần giải thích SQL.

Câu hỏi gốc: {question}
SQL đã thực thi: {sql}
Kết quả (tối đa 5 dòng):
{df_head.to_markdown(index=False)}"""
    
    url = f"{client_cfg['base_url'].rstrip('/')}/api/generate"
    payload = {
        "model": client_cfg["model"],
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=120)
        if response.status_code == 500:
            return f"Lỗi 500 từ Ollama. Hệ thống có thể đang quá tải hoặc thiếu RAM/VRAM khi chạy model {client_cfg['model']}."
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.exceptions.Timeout:
        return f"Lỗi: Ollama phản hồi quá chậm (Timeout > 120s). Có thể máy thiếu RAM."
    except Exception as e:
        return f"Lỗi gọi API giải thích: {e}"

# -------------------------------------------------------
# STREAMLIT UI
# -------------------------------------------------------
st.set_page_config(page_title="Text-to-SQL for Business", layout="wide")

st.title("Trợ lý Truy vấn Dữ liệu Doanh nghiệp")
st.markdown("*Chuyển đổi câu hỏi thường ngày thành dữ liệu thực tế bằng AI (Text-to-SQL) — Demo System*")

# --- Sidebar ---
with st.sidebar:
    st.header("Cấu hình Ollama (Local AI)")

    ollama_url = st.text_input("Ollama Base URL", value=OLLAMA_BASE_URL)
    ollama_model = st.text_input("Model Name", value=OLLAMA_MODEL)
    
    client_config["base_url"] = ollama_url
    client_config["model"] = ollama_model
    st.success(f"✅ Đang sử dụng {ollama_model} qua {ollama_url}")

    st.divider()

    # DB Status
    st.subheader("Kết nối Database")
    if engine:
        st.success(f"✅ Đã kết nối: {DB_NAME} @ {DB_SERVER}:{DB_PORT}")
    else:
        st.error(f"❌ Không thể kết nối DB.\nLỗi: {db_error}")

    st.divider()

    st.subheader("Cấu trúc Database (Schema)")
    with st.expander("Xem Schema"):
        st.text(db_schema)

    st.divider()
    st.markdown("**Ví dụ câu hỏi:**")
    st.markdown("- *Tổng doanh thu theo trạng thái đơn hàng?*")
    st.markdown("- *Danh sách khách hàng ở Miền Bắc?*")
    st.markdown("- *Top 2 chiến dịch marketing có ngân sách cao nhất?*")

# --- Main ---
user_question = st.text_input(
    "Nhập câu hỏi nghiệp vụ:",
    placeholder="VD: Tổng doanh thu của đơn hàng có trạng thái Hoàn thành?"
)

if st.button("Truy xuất dữ liệu", type="primary"):
    if not user_question.strip():
        st.warning("Vui lòng nhập câu hỏi trước khi tiếp tục.")
    elif not client_config["base_url"] or not client_config["model"]:
        st.error("Vui lòng cấu hình Ollama URL và Model ở thanh bên trái.")
    elif not engine:
        st.error(f"Không có kết nối Database. Kiểm tra Docker SQL Server.\nLỗi: {db_error}")
    else:
        with st.status("Đang xử lý...", expanded=True) as status:

            # Step 1 – Generate SQL
            status.update(label="Bước 1/4: AI đang phân tích câu hỏi và tạo SQL...")
            sql_query = generate_sql(user_question, db_schema, client_config)

            if sql_query.startswith("ERROR:"):
                status.update(label="Thất bại tại bước tạo SQL.", state="error")
                st.error(sql_query)
                st.stop()

            st.markdown("**Câu lệnh SQL được tạo ra:**")
            st.code(sql_query, language="sql")

            # Step 2 – Validate
            status.update(label="Bước 2/4: Kiểm tra bảo mật (Validation)...")
            is_safe, msg = validate_sql(sql_query)
            if not is_safe:
                status.update(label="Truy vấn không an toàn.", state="error")
                st.error(f"Bị từ chối: {msg}")
                st.stop()
            st.success("✅ Đã vượt qua kiểm tra bảo mật (Read-only).")

            # Step 3 – Execute
            status.update(label="Bước 3/4: Đang thực thi trên Database...")
            try:
                df = pd.read_sql(sql_query, engine)
            except Exception as e:
                status.update(label="Lỗi thực thi SQL.", state="error")
                st.error(f"Lỗi khi chạy SQL: {e}")
                st.stop()

            if df.empty:
                status.update(label="Hoàn tất — không có dữ liệu trả về.", state="complete")
                st.info("Không tìm thấy dữ liệu nào phù hợp với câu hỏi.")
                st.stop()

            # Bỏ sleep 3 giây vì gọi Local AI không bị giới hạn Rate Limit như API web
            # Step 4 – Explain
            status.update(label="Bước 4/4: AI đang phân tích kết quả...")
            explanation = explain_result(user_question, sql_query, df.head(5), client_config)
            status.update(label="✅ Hoàn tất quy trình Text-to-SQL!", state="complete")

        # Display
        st.divider()
        st.subheader("Kết quả Dữ liệu")
        st.dataframe(df, use_container_width=True)

        st.subheader("Phân tích & Giải thích (Bởi AI)")
        st.info(explanation)
