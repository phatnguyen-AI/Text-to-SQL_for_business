# SYSTEM DESIGN: TEXT-TO-SQL FOR BUSINESS (Production-Grade)

> **Role:** System Design Engineer | **Level:** Senior | **Version:** 1.0  
> **Date:** 2026-04-26 | **Status:** Approved for Phase 2

---

## 1. TỔNG QUAN HỆ THỐNG (System Overview)

### 1.1 Mục tiêu
Xây dựng hệ thống Text-to-SQL production-grade cho phép Business User truy vấn dữ liệu nội bộ bằng ngôn ngữ tự nhiên, đảm bảo **bảo mật tuyệt đối (Read-only)**, **độ chính xác ≥ 85%**, **latency < 3s**, và **chi phí vận hành tối thiểu**.

### 1.2 Constraints (Ràng buộc thiết kế)
| Constraint | Yêu cầu |
|---|---|
| **Security** | Read-only, RBAC, không lộ raw schema ra ngoài |
| **Cost** | Tối ưu cost/query, ưu tiên local/cached LLM |
| **Scalability** | Horizontal scale, stateless services |
| **Reliability** | Availability ≥ 99.5%, auto-retry, fallback |
| **Accuracy** | SQL correctness ≥ 85%, hallucination detection |

---

## 2. KIẾN TRÚC TỔNG THỂ (High-Level Architecture)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                │
│   [Web UI - Streamlit/React]    [API Client]    [Slack Bot (v2)]   │
└───────────────────────┬─────────────────────────────────────────────┘
                        │ HTTPS / WSS
┌───────────────────────▼─────────────────────────────────────────────┐
│                      API GATEWAY (FastAPI)                          │
│   Auth (JWT/SSO) │ Rate Limiting │ Request Logging │ CORS          │
└───────┬───────────────────────────────────┬─────────────────────────┘
        │                                   │
┌───────▼──────────┐              ┌─────────▼──────────┐
│  QUERY PIPELINE  │              │   ADMIN SERVICE    │
│  (Core Engine)   │              │  Schema Manager    │
│                  │              │  User Management   │
│ 1. NL Processor  │              │  Audit Logs        │
│ 2. Schema Retr.  │              └────────────────────┘
│ 3. SQL Generator │
│ 4. Validator     │
│ 5. Executor      │
│ 6. Explainer     │
└───────┬──────────┘
        │
┌───────▼──────────────────────────────────────────────┐
│                  INFRASTRUCTURE LAYER                 │
│                                                       │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │  LLM Layer  │  │  Cache Layer │  │  Data Layer │ │
│  │  (Ollama /  │  │  (Redis)     │  │  SQL Server │ │
│  │   Cloud LLM)│  │              │  │  (Read-only)│ │
│  └─────────────┘  └──────────────┘  └─────────────┘ │
│                                                       │
│  ┌─────────────────────────────────────────────────┐ │
│  │         OBSERVABILITY STACK                     │ │
│  │  Prometheus │ Grafana │ Loki │ Sentry           │ │
│  └─────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

---

## 3. CHI TIẾT CÁC COMPONENT

### 3.1 API Gateway
**Tech:** FastAPI + Nginx reverse proxy

**Trách nhiệm:**
- Xác thực JWT token (tích hợp SSO công ty)
- Rate limiting: 20 req/min/user (chống spam)
- Request/Response logging (traceID cho mỗi query)
- CORS policy

**Endpoints chính:**
```
POST /api/v1/query          # Main query endpoint
GET  /api/v1/history        # Lịch sử query của user
GET  /api/v1/schema/tables  # Xem schema (filtered by RBAC)
GET  /api/v1/health         # Health check
```

---

### 3.2 Query Pipeline (Core Engine)

Đây là trái tim của hệ thống. Pipeline gồm **6 bước tuần tự**:

```
[Input] → [1. NL Processor] → [2. Schema Retriever] → [3. SQL Generator]
       → [4. Validator] → [5. Executor] → [6. Explainer] → [Output]
```

#### Bước 1: NL Processor (Natural Language Processor)
- **Mục đích:** Làm sạch và chuẩn hóa câu hỏi đầu vào
- **Logic:**
  - Detect ngôn ngữ (VI/EN)
  - Glossary Mapping: "miền bắc" → `Region='Miền Bắc'`, "tháng này" → `MONTH(GETDATE())`
  - Phát hiện câu hỏi mơ hồ → yêu cầu làm rõ
  - Phát hiện intent nguy hiểm (DELETE, DROP trong câu hỏi tự nhiên)

#### Bước 2: Schema Retriever
- **Mục đích:** Chỉ inject schema liên quan, KHÔNG dump toàn bộ DB schema
- **Logic (RAG-based Schema Retrieval):**
  - Embedding câu hỏi → similarity search với table/column embeddings
  - Chỉ lấy top-K tables liên quan (thường 2-4 bảng)
  - Inject Foreign Key relationships của các bảng được chọn
- **Lợi ích:** Giảm token cost 60-70%, tăng accuracy

#### Bước 3: SQL Generator (LLM)
- **Model ưu tiên:** `qwen2.5-coder:7b` (local Ollama) → Fallback: `gemini-flash` (cloud)
- **Prompt Engineering:**
  - System prompt cố định (T-SQL rules, forbidden keywords)
  - Few-shot examples (3-5 ví dụ sát schema thực)
  - Schema filtered từ Bước 2
  - Câu hỏi đã chuẩn hóa từ Bước 1
- **Output:** Raw SQL string

#### Bước 4: SQL Validator (Security Gate)
- **Layer 1 - Syntax Check:** Parse SQL AST, kiểm tra cú pháp hợp lệ
- **Layer 2 - Security Check:**
  - Whitelist: chỉ cho phép `SELECT`, `WITH` (CTE)
  - Blacklist: `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `EXEC`, `xp_cmdshell`
  - Chống SQL Injection pattern
- **Layer 3 - Schema Check:**
  - Xác nhận tất cả table/column trong query tồn tại trong schema
  - Phát hiện hallucinated column names
- **Kết quả:** PASS → tiếp tục | FAIL → trả về lỗi có hướng dẫn

#### Bước 5: SQL Executor
- **Connection Pool:** SQLAlchemy pool size=5, max_overflow=10
- **Timeout:** Query timeout = 30s (chống long-running query)
- **Row Limit:** Hard limit TOP 1000 rows (inject tự động nếu không có)
- **Read-only user:** DB user chỉ có quyền `SELECT` ở DB level
- **Error Handling:** Catch lỗi SQL → log → auto-retry với modified prompt

#### Bước 6: Explainer (LLM)
- **Mục đích:** Giải thích kết quả bằng tiếng Việt cho Business User
- **Input:** Câu hỏi gốc + SQL + top 5 rows kết quả
- **Output:** 2-3 câu giải thích business-friendly
- **Optimization:** Có thể dùng model nhỏ hơn (3b) vì task đơn giản hơn

---

### 3.3 Cache Layer (Redis)

**Chiến lược cache đa tầng:**

| Cache Key | TTL | Nội dung |
|---|---|---|
| `schema:{db_name}` | 1 giờ | Database schema đã format |
| `sql:{hash(question+schema)}` | 24 giờ | SQL đã generate cho câu hỏi giống nhau |
| `result:{hash(sql)}` | 15 phút | Kết quả query (dữ liệu thay đổi thường xuyên) |
| `embedding:{table_name}` | 7 ngày | Vector embedding của schema |

**Lợi ích:** Câu hỏi lặp lại không cần gọi LLM → cost ≈ $0, latency < 100ms

---

### 3.4 LLM Layer

**Chiến lược LLM (Cost-Optimized):**
```
Request → Check Cache (Redis)
           ├─ HIT → Return cached SQL (cost: $0)
           └─ MISS → Local Ollama (cost: $0, latency: 1-5s)
                      └─ FAIL (overload/timeout) → Cloud LLM Fallback
                                                    (Gemini Flash: ~$0.001/query)
```

**Model Selection theo complexity:**
| Query Type | Model |
|---|---|
| Simple (1 bảng) | `qwen2.5-coder:1.5b` (nhanh hơn) |
| Medium (2-3 bảng, JOIN) | `qwen2.5-coder:7b` |
| Complex (subquery, CTE) | `qwen2.5-coder:7b` + few-shot |
| Fallback | `gemini-1.5-flash` |

---

### 3.5 Database Layer

**Architecture:**
```
Application → Read Replica (SELECT queries)
           ↗
Primary DB ← Write operations (từ business systems khác)
           ↘
Read Replica 2 (scaling khi cần)
```

**Security:**
- Tạo dedicated DB user `text2sql_readonly` chỉ có `GRANT SELECT ON DATABASE`
- Connection qua TLS/SSL
- Không expose connection string ra UI
- Schema chỉ được expose qua Schema Retriever (filtered)

---

### 3.6 RBAC (Role-Based Access Control)

| Role | Quyền truy cập | Tables được phép |
|---|---|---|
| `viewer` | Xem dữ liệu tổng hợp | Orders (aggregated), Customers (no PII) |
| `analyst` | Xem chi tiết | Orders, Customers, Products |
| `marketing` | Xem dữ liệu marketing | MarketingCampaigns, Orders (aggregated) |
| `admin` | Full read access | Tất cả tables |

**Row-Level Security:** Filter thêm theo region/department nếu cần.

---

## 4. DATA FLOW CHI TIẾT

```
User: "Doanh thu tháng 3 theo miền là bao nhiêu?"
         │
         ▼
[API Gateway] → Xác thực JWT → Rate check → tạo traceID: abc-123
         │
         ▼
[NL Processor]
  - Detect: tiếng Việt
  - Glossary: "tháng 3" → MONTH(OrderDate)=3, "theo miền" → GROUP BY Region
  - Intent: aggregation query, JOIN cần thiết
         │
         ▼
[Schema Retriever]
  - Embed câu hỏi → similarity search
  - Kết quả: Orders (Revenue, OrderDate), Customers (Region)
  - Inject FK: Orders.CustomerID → Customers.CustomerID
         │
         ▼
[SQL Generator - Ollama qwen2.5-coder:7b]
  Prompt → Response:
  SELECT c.Region, SUM(o.TotalAmount) AS Revenue
  FROM Orders o
  JOIN Customers c ON o.CustomerID = c.CustomerID
  WHERE MONTH(o.OrderDate) = 3
  GROUP BY c.Region
  ORDER BY Revenue DESC
         │
         ▼
[Validator]
  ✅ Starts with SELECT
  ✅ No forbidden keywords
  ✅ Tables exist: Orders ✓, Customers ✓
  ✅ Columns exist: Region ✓, TotalAmount ✓, OrderDate ✓
         │
         ▼
[Executor]
  - Execute trên Read Replica
  - Trả về DataFrame: [{Miền Bắc: 26M}, {Miền Nam: 40M}, ...]
         │
         ▼
[Explainer]
  → "Trong tháng 3/2024, Miền Nam có doanh thu cao nhất với 40 triệu đồng,
     tiếp theo là Miền Bắc với 26 triệu. Tổng doanh thu toàn quốc đạt 73.5 triệu đồng."
         │
         ▼
[Response] → Cache result → Log to Audit → Return to User
  Latency tổng: ~2.5s (first query) | ~0.1s (cached)
```

---

## 5. DEPLOYMENT ARCHITECTURE

### 5.1 Phase 1 (PoC - Hiện tại → Production nhỏ)

```
┌──────────────────────────────────┐
│         Single Server            │
│  (16GB RAM, 8 CPU, GPU optional) │
│                                  │
│  ┌──────────┐  ┌──────────────┐  │
│  │ Streamlit│  │ FastAPI      │  │
│  │ UI       │  │ (port 8000)  │  │
│  └──────────┘  └──────────────┘  │
│  ┌──────────┐  ┌──────────────┐  │
│  │ Ollama   │  │ Redis        │  │
│  │ (port    │  │ (port 6379)  │  │
│  │  11434)  │  └──────────────┘  │
│  └──────────┘                    │
│  ┌──────────────────────────────┐ │
│  │ SQL Server (Docker)          │ │
│  │ (port 1434)                  │ │
│  └──────────────────────────────┘ │
└──────────────────────────────────┘
```

**Docker Compose services:**
- `api`: FastAPI query pipeline
- `ui`: Streamlit frontend
- `ollama`: Local LLM server
- `redis`: Cache
- `sqlserver`: Database (dev/demo)

### 5.2 Phase 2 (Production - Scale)

```
                    [Load Balancer - Nginx]
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         [API Pod 1]  [API Pod 2]  [API Pod 3]   ← Kubernetes HPA
              │
    ┌─────────┼──────────┐
    ▼         ▼          ▼
[Ollama   [Redis     [SQL Server
 Cluster]  Cluster]   Read Replicas]
```

---

## 6. RELIABILITY & ERROR HANDLING

### 6.1 Chiến lược Retry
```python
# Auto-retry với exponential backoff
Attempt 1: Generate SQL → Fail (hallucinated column)
           │
           ▼ (retry với error feedback trong prompt)
Attempt 2: "Column 'revenue' không tồn tại. Dùng 'TotalAmount'. Thử lại."
           │
           ▼
Attempt 3: Fallback sang Cloud LLM nếu local fail 2 lần
           │
           ▼
Fail sau 3 attempts → Return friendly error + suggest rephrasing
```

### 6.2 Confidence Scoring
Mỗi SQL được generate kèm confidence score:
- **HIGH (>0.8):** Execute ngay
- **MEDIUM (0.5-0.8):** Hiển thị SQL cho user xác nhận trước khi chạy
- **LOW (<0.5):** Yêu cầu user rephrasing, không execute

### 6.3 Circuit Breaker
- Ollama down → Auto-switch sang Cloud LLM (Gemini Flash)
- Cloud LLM down → Return error với queue cho retry sau
- DB down → Return cached results nếu có, else error

---

## 7. OBSERVABILITY

### 7.1 Metrics (Prometheus + Grafana)
| Metric | Alert Threshold |
|---|---|
| `query_latency_p95` | > 5s |
| `sql_accuracy_rate` | < 80% |
| `llm_error_rate` | > 10% |
| `cache_hit_rate` | < 50% |
| `db_connection_pool_usage` | > 80% |

### 7.2 Logging (Structured JSON - Loki)
Mỗi query log đầy đủ:
```json
{
  "traceId": "abc-123",
  "userId": "user@company.com",
  "question": "Doanh thu tháng 3...",
  "generatedSQL": "SELECT ...",
  "validationStatus": "PASS",
  "executionTimeMs": 245,
  "rowCount": 3,
  "llmModel": "qwen2.5-coder:7b",
  "cacheHit": false,
  "feedback": null
}
```

### 7.3 Continuous Improvement Loop
```
Query Log → Feedback Collection → Wrong SQL Analysis
         → Few-shot Examples Update → Glossary Update
         → Model Fine-tuning (Phase 3)
```

---

## 8. SECURITY CHECKLIST

- [x] Read-only DB user tại DB level
- [x] SQL Validator (AST parsing, blacklist keywords)
- [x] JWT Authentication tại API Gateway
- [x] RBAC - phân quyền theo role và table
- [x] Rate Limiting (chống abuse)
- [x] Schema không expose trực tiếp ra UI
- [x] Tất cả traffic HTTPS
- [x] Audit log mọi query với userId
- [x] Row limit injection (chống dump toàn bộ DB)
- [x] No raw connection string trong response

---

## 9. COST ESTIMATION

### 9.1 Infrastructure Cost (Monthly)
| Component | Phase 1 (Local) | Phase 2 (Cloud) |
|---|---|---|
| Server/VM | ~500k VNĐ (existing) | ~2-4M VNĐ/tháng |
| LLM (Local Ollama) | $0 | $0 |
| LLM Fallback (Gemini Flash) | ~$2-5/tháng | ~$10-20/tháng |
| Redis | $0 (Docker) | ~$500k VNĐ/tháng |
| **Total** | **~$2-5/tháng** | **~$50-100/tháng** |

### 9.2 Cost/Query
| Scenario | Cost |
|---|---|
| Cache HIT | $0.000 |
| Local LLM (Ollama) | $0.000 |
| Cloud LLM Fallback (Gemini Flash) | ~$0.001 |

**So sánh với ROI:** Tiết kiệm 40M VNĐ/tháng, chi phí vận hành < 2M VNĐ/tháng → **ROI > 20x**

---

## 10. PHASED ROADMAP

### Phase 1 - Production Ready (4-6 tuần)
- [ ] Refactor `app.py` thành FastAPI microservice
- [ ] Implement Redis caching
- [ ] SQL Validator nâng cấp (AST parsing)
- [ ] Schema Retriever (RAG-based)
- [ ] Glossary mapping (từ điển nghiệp vụ)
- [ ] Structured logging + Sentry error tracking
- [ ] Docker Compose production config
- [ ] Unit tests + Integration tests

### Phase 2 - Scale & Reliability (2-3 tháng)
- [ ] Kubernetes deployment
- [ ] Read Replica cho DB
- [ ] RBAC đầy đủ
- [ ] Prometheus + Grafana dashboard
- [ ] Confidence scoring
- [ ] Auto-retry với error feedback
- [ ] Slack Bot integration

### Phase 3 - Intelligence (3-6 tháng)
- [ ] Fine-tune model trên query logs
- [ ] Multi-database support
- [ ] Natural Language chart generation
- [ ] Scheduled report automation

---

## 11. TECH STACK SUMMARY

| Layer | Technology | Lý do chọn |
|---|---|---|
| **Frontend** | Streamlit → React (Phase 2) | Đơn giản, quen thuộc Business |
| **Backend API** | FastAPI | Async, performance cao, auto docs |
| **LLM (Local)** | Ollama + qwen2.5-coder:7b | Zero cost, privacy, offline |
| **LLM (Cloud)** | Google Gemini Flash | Rẻ nhất, fallback |
| **Database** | SQL Server (Docker) → Managed | Enterprise standard |
| **Cache** | Redis | Đơn giản, nhanh, TTL support |
| **Container** | Docker + Docker Compose → K8s | Portable, scalable |
| **Monitoring** | Prometheus + Grafana + Loki | Open source, full-stack |
| **CI/CD** | GitHub Actions | Free, tích hợp tốt |

---

*Document này là living document — cập nhật sau mỗi sprint review.*
