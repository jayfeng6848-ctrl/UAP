# STEP 1-B / B0 — UUIDv7 Implementation Strategy

Status: **DESIGN PREPARATION — 不创建任何表 / 不执行任何 DDL**
来源：STEP 1-A Round 2 P1-02 实测结论（25 项断言全过）+ Round 3 冻结设计
配套：[CORE_DOMAIN_MODEL.md §9](./CORE_DOMAIN_MODEL.md)、[STEP1A_ARCHITECTURE_REVIEW.md §P1-02](./STEP1A_ARCHITECTURE_REVIEW.md)

> 本文档只**确认与固化**已冻结方案，不重新设计。

---

## 1. RFC 9562 Bit Layout（已实证，勿改）

```
  byte 0  byte 1  byte 2  byte 3  byte 4  byte 5  | byte 6  | byte 7  | byte 8  |  byte 9-15
+--------+--------+--------+--------+--------+--------+---------+---------+---------+------------
  unix_ts_ms (48 bits, big-endian)                  |ver=0111| rand_a  |var=10xxxx|  rand_b (62)
```

| 字段 | 字节偏移 | 位 | 值 |
|---|---|---|---|
| `unix_ts_ms` | [0:6] | 0–47 | `int64(ms)` 的低 6 字节（大端），PG 中取 `substring(int8send(ms) FROM 3 FOR 6)` |
| `ver` | byte 6 | 48–51 | `0111` = 7 |
| `rand_a` | byte 6–7 | 52–63 | 12 bits 随机 |
| `var` | byte 8 | 64–65 | `10` |
| `rand_b` | byte 8–15 | 66–127 | 62 bits 随机 |

> 注意：PG 中写版本/variant 必须用 **`set_byte`（byte 偏移）**，不要用 `set_bit`（bit 偏移）——Round 2 P1-02 已修正。

---

## 2. Application Generator（Python，主路径）

```python
import os, time, uuid

def uap_uuid_v7_py() -> uuid.UUID:
    ms = int(time.time() * 1000)
    b = bytearray(os.urandom(16))
    b[0:6] = ms.to_bytes(6, "big")      # 48-bit BE timestamp
    b[6] = (b[6] & 0x0F) | 0x70         # version 7 (upper 4 bits of byte 6)
    b[8] = (b[8] & 0x3F) | 0x80         # variant 10 (upper 2 bits of byte 8)
    return uuid.UUID(bytes=bytes(b))
```

- 用于：应用层所有新行 PK / FK / event_id / 幂等键（批量预生成、跨库一致、无 DB 往返）
- **并发安全**：单进程内 62bit 随机 + 毫秒前缀；同毫秒高并发时仍靠随机位，极端冲突由 PK 唯一约束兜底（应用层 `UniqueViolation` 重试一次）

---

## 3. Database Fallback（PG plpgsql，运维/回填/触发器）

```sql
CREATE FUNCTION uap_uuid_v7() RETURNS uuid
LANGUAGE plpgsql VOLATILE PARALLEL SAFE AS $$
DECLARE
  g    uuid := gen_random_uuid();          -- PG 13+ 内置，无需 pgcrypto 扩展
  ms   bigint := (extract(epoch FROM clock_timestamp()) * 1000)::bigint;
  ts   bytea := substring(int8send(ms) FROM 3 FOR 6);   -- int8 BE 的低 6 字节
  bytes bytea := uuid_send(g);
  out  bytea;
BEGIN
  out := overlay(bytes PLACING ts FROM 1 FOR 6);
  out := set_byte(out, 6, (get_byte(out, 6) & 15) | 112);  -- 0x70
  out := set_byte(out, 8, (get_byte(out, 8) & 63) | 128);  -- 0x80
  RETURN encode(out, 'hex')::uuid;
END;
$$;
```

- `clock_timestamp()`（非 `now()`）保证函数内每调用取真实时钟
- `gen_random_uuid()`：PostgreSQL 13+ 内置（`pgcrypto` 不再是必要依赖，PG 12 之前才需要）→ 与冻结决策"不引 pgcrypto"一致

---

## 4. DEFAULT 策略（明确回答"DEFAULT 到底用什么"）

| 场景 | 用哪个 | 理由 |
|---|---|---|
| **应用层 ORM 插入** | **Python `uap_uuid_v7_py()`** | 主路径：批量预生成、跨库一致、可审计（应用负责发号） |
| **DB 列 DEFAULT（兜底）** | `DEFAULT uap_uuid_v7()` | migration/回填/手工 INSERT 不显式给 id 时可用；避免 NULL |
| **域扩展表（1:1 resources）** | **不使用 DB 生成** —— 域表 `id` 必须 = `resources.id` | 由仓储层先插 registry 再插域表，同一个应用生成的 UUIDv7 |

**结论**：**PK 列声明 `DEFAULT uap_uuid_v7()` 仅为兜底**；正常路径全部由应用显式提供 UUIDv7。所有 `id uuid PRIMARY KEY DEFAULT uap_uuid_v7()` 统一写法。

---

## 5. 已验证测试矩阵（Round 2 探针已跑；B1 落地为 pytest）

| # | 断言 | 应用生成器 | DB 兜底 |
|---|---|---|---|
| 1 | version == 7（byte 6 高 4 位） | ✅ 10000/10000 | ✅ 10000/10000 |
| 2 | variant == 10xx（byte 8 高 2 位） | ✅ | ✅ |
| 3 | timestamp 反推 == 生成时刻（误差 < 1ms） | ✅ | ✅ |
| 4 | RFC 9562 严格字节布局（逐字节） | ✅ | ✅ |
| 5 | 10,000+ 唯一 | ✅ | ✅ |
| 6 | 同毫秒批量唯一（20000 同 ms 零冲突） | ✅ | ✅ |
| 7 | 时间顺序性质（单调性） | ✅ | — |
| 8 | PK 唯一约束兜底（INSERT 10000 无冲突） | — | ✅ |
| 9 | 应用 + DB 跨实现零碰撞 | ✅ | ✅ |

B1 pytest 落点：`tests/unit/core/test_uuid_v7.py` + `tests/integration/test_uuid_v7_db.py`（12 项，见 REVIEW 附录 A）。

---

## 6. 非 UUIDv7 的标识（不透明 ID）

| 用途 | 类型 | 说明 |
|---|---|---|
| 邀请码 / 分享链接 / 重置 token | **UUIDv4 或独立随机串** | 隐藏创建时间、防枚举时间窗 |
| `public_id`（对外暴露的资源 ID，需要隐藏时间） | UUIDv4 | 需要时才加列；不默认全表加 |
| 分区表 PK | `(id uuidv7, occurred_at)` | events / audit_logs / ai_request_logs |

**禁止**：用 UUIDv7 直接作为对外不透明标识（泄露创建时间）。

---

## 7. 未来 PG 内置 `uuidv7()`

- PostgreSQL 18+ 内置 `uuidv7()`。B1（PG 16 环境）不依赖它
- 若未来升级 PG 18+：检测 `pg_proc WHERE proname='uuidv7'` 存在则把 `uap_uuid_v7()` 函数体重定向为别名；无行为差异，应用层零改动

---

## 8. 风险与边界

| 项 | 说明 | 级别 |
|---|---|---|
| 时间回拨（NTP 校时倒退） | 应用层时钟倒退可能导致新 UUID 小于旧 UUID（索引尾部写入退化为随机插入） | P3：应用层加 `max(now, last+1)` 序列防护可解；DB 兜底用 `clock_timestamp()` 同样受系统时钟影响 |
| 同毫秒极端冲突 | 62bit 随机 + PK 唯一兜底，冲突概率可忽略 | P3 |
| 时钟精度 | `int(time.time()*1000)` 毫秒截断；UUID 内时间粒度=ms | 符合设计（`timestamptz(3)` 对齐） |
