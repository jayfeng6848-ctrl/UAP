# STEP 1-A Architecture Review — Round 2 & 3 Revision

Status: **READY FOR THIRD HUMAN AUDIT**
Created: 2026-09-07 · Phase: `STEP 1-A / DESIGN REVISION`
基线：`72ade9f` · `UAP-V0.1.0-INIT-DB-VALIDATED`

> **本文件记录第一轮审计的 4 个 P1/P2 问题（Round 2）与第二轮一致性审计的 3 个 P2 问题（Round 3），逐项含：原问题 / 修改前 / 修改后 / 理由 / 测试 / 最终状态。**
> **本阶段未创建任何表、未执行 Alembic、未改 Core 代码、未创建业务表。**

---

## 0. 总览

| ID | 等级 | 主题 | 状态 | 核心修改 |
|---|---|---|---|---|
| P1-01 | P1 | Tenant Role 无实际分配关系 | ✅ FIXED | `tenant_memberships.role_id`（方案 A） |
| P1-02 | P1 | UUIDv7 DB fallback bit layout | ✅ FIXED | 探针库实测，15+10 项断言全过 |
| P1-03 | P1 | Event SKIP LOCKED ≠ exactly-once | ✅ FIXED | at-least-once + CAS claim + lease reaper |
| P1/P2-04 | P1/P2 | Resource ACL subject 是裸多态 | ✅ FIXED | `acl_subject_types` 注册表 + trigger 验证 |
| P2-01 | P2 | Tenant Role 默认角色 scope 冲突 | ✅ FIXED (R3) | 默认 `tenant_member`（TENANT scope） |
| P2-02 | P2 | ACL `group` 引用不存在的 `groups` | ✅ FIXED (R3) | 白名单收紧 user/role/agent |
| P2-03 | P2 | `resources` FK CASCADE 冲突 | ✅ FIXED (R3) | tenant_id/space_id 改 RESTRICT |

---

# P1-01 — Tenant Role 无实际分配关系

## 1. 原问题

第一轮设计的 `tenant_memberships` 只有 `status`/`joined_at` 等元信息，**没有 `role_id`**。但 Authorization Pipeline 又声明支持 `platform + tenant + space` 三级角色并说"tenant role 向下继承"。

**矛盾**：用户没有 Tenant Role 的存储位置，却参与了 Tenant Role 继承计算。这是结构性缺口。

## 2. 修改前

```
tenant_memberships(id, tenant_id, user_id, status, invited_by, joined_at, removed_at, ...)
memberships(id, tenant_id, space_id, user_id, role_id, status, ...)  -- space 角色在
```

Authorization 描述 "tenant role 向下继承" 但数据库无法表达 → 文档与模型脱节。

## 3. 修改后（方案 A）

**采用方案 A：单角色挂载**

```sql
tenant_memberships(
  id, tenant_id, user_id,
  role_id,                  -- NOT NULL, FK roles(id) ON DELETE RESTRICT
  status,
  role_assigned_at, role_assigned_by,
  invited_by, joined_at, removed_at,
  created_at, updated_at
)

-- trigger: roles.scope='TENANT' AND roles.tenant_id = tenant_memberships.tenant_id
-- 部分唯一索引：(tenant_id, user_id)
```

**理由**：
- UAP Core 大多数使用场景：一个用户在某个租户担任一个角色（租户 owner / `tenant_admin` / `tenant_member` / 只读 `viewer`）
- 不需要 N:M 复杂度；方案 B（`tenant_membership_roles` 桥接表）会引入"用户在某租户有多个角色"的语义，但当前阶段没有真实业务需求支撑
- **P1-01 明确"二选一，并说明理由"**——选 A 是因为 UAP Core 的"租户角色"是"该用户在该租户的总体身份"而非权限集合，方案 A 表达更直接
- **P2-01（Round 3）补充**：默认角色统一为 **`tenant_member`（TENANT scope）**，`member` 不作为任何 scope 的默认角色——见 Round 3 章节

**被驳回的方案 B**：`tenant_memberships` + `tenant_membership_roles` 多对多 —— 适合"一个用户在某个租户同时拥有 admin + billing_manager"等场景。**保留为未来选项**（若真实业务出现 N:M 需求，加桥接表而不破坏方案 A 的现有数据）。

## 4. 关键规则（修改后）

| 场景 | 处理 |
|---|---|
| **分配** | 邀请/加入时写入 `role_id`（缺省 **`tenant_member`** —— TENANT scope 内置角色，见 Round 3 / P2-01） |
| **修改** | `UPDATE tenant_memberships SET role_id=$new, role_assigned_at=now()` + 写 `audit_logs(action='tenant.role.assign')` |
| **撤销** | `status='removed'` 立即不参与任何权限计算（授权实时查询） |
| **继承到 Space** | Authorization Pipeline [4] Role Resolution 把 Tenant Role 视为在该租户所有 Space 生效，**无需在 memberships 复制** |
| **多 Role 计算** | effective = P(platform) ∪ P(tenant_role) ∪ P(space_role) ∪ P(resource_acl)；deny 压过一切 |
| **Membership removed** | Tenant Role **立即失效**（Pipeline [4] 拿不到 role_id）；无级联清理需求 |
| **Role 删除** | FK RESTRICT 阻止；归档（`archived_at`）时该 role 的 deny 行不再参与决策，allow 行保留用于审计追溯 |

## 5. 测试方法

| 测试 | 期望 |
|---|---|
| `test_tenant_role_assignment_writes_role_id` | 插入 tenant_membership 时缺省 `role_id` 指向 **`tenant_member`**（TENANT scope） |
| `test_tenant_role_change_writes_audit` | UPDATE role_id → 写 audit_logs |
| `test_tenant_role_inherits_to_all_spaces` | 同用户在不同 space → Pipeline [4] 都能取到 tenant role |
| `test_tenant_role_denied_when_scope_mismatch` | role.scope='SPACE' 挂到 tenant_membership → trigger 拒绝 |
| `test_tenant_role_removed_status_zero_authority` | `status='removed'` → 授权 Pipeline 返回 DENY（reason='no_role' 或 'not_tenant_member'） |
| `test_multiple_roles_effective_allow` | 同一 user 有 platform=platform_admin + tenant=tenant_admin + space=space_admin → effective = union |
| `test_deny_always_wins_across_layers` | tenant role 给 allow + space role 给 deny → DENY |
| `test_tenant_role_role_id_required` | INSERT 时 role_id NULL → 拒绝（NOT NULL） |

## 6. 最终状态

- `CORE_DOMAIN_MODEL.md` §1.2 `tenant_memberships` —— 新增 `role_id` 字段、分配/撤销/失效规则
- `ER_MODEL.md` §2 `tenant_memberships` —— 字段图增加 `role_id`；§7 关系矩阵加 `(roles → tenant_memberships, RESTRICT)` 行
- `STEP1A_DESIGN_REPORT.md` §4.2 —— 新增 "Tenant Role 分配与失效" 子节
- 授权 Pipeline [4] Role Resolution —— 显式描述 PLATFORM/TENANT/SPACE 三层取 role 的步骤
- **不**为方案 B 写代码；不创建任何表

---

# P1-02 — UUIDv7 DB fallback 实现必须修正

## 1. 原问题

第一轮在文档里写了：

```sql
set_bit(set_bit(..., 52, 1), 53, 1)
```

但 `set_bit` 是**基于位串从左数 0 起始**的索引（PG 16 `bit_string`），不是 RFC 9562 的 byte offset。`52, 53` 对应的是 "variant 字段的最低两位"，**但要看左边计数还是右边计数**。

**风险**：如果实现错位，DB 兜底生成的 UUID 会**version 不为 7 或 variant 不为 10xx**，被第三方校验器（如 uuid-tools、Java `UUID.fromString`）拒绝；PK 索引局部性也丧失。

## 2. 修改前

文档中只有 bit 操作的概念描述，没有：
- 完整 byte layout
- 实际可运行的 SQL 函数
- 探针测试证明符合 RFC 9562

**审查无法通过**：仅凭文字无法判断 bit offset 是否正确。

## 3. 修改后（**实测 PASS**）

### 3.1 完整 bit layout（标准 RFC 9562）

```
  byte 0  byte 1  byte 2  byte 3  byte 4  byte 5  | byte 6  | byte 7  | byte 8  |  byte 9-15
+--------+--------+--------+--------+--------+--------+---------+---------+---------+------------
  unix_ts_ms (48 bits, big-endian)                  |ver=7 12b| rand_a  |var=10xx|  rand_b (62 bits)
                                                     [0111][rand_a_12] [10][rand_62]
```

| 字段 | 字节 | 位 | 值 |
|---|---|---|---|
| `unix_ts_ms` | [0:6] | 0-47 | big-endian int48 |
| `ver` | byte 6 | 48-51 | `0b0111` |
| `rand_a` | byte 6 + 7 | 52-63 | 12 bits random |
| `var` | byte 8 | 64-65 | `0b10` |
| `rand_b` | byte 8-15 | 66-127 | 62 bits random |

### 3.2 应用层 Python 实现

```python
import os, time, uuid
def uap_uuid_v7_py() -> uuid.UUID:
    ms = int(time.time() * 1000)
    b = bytearray(os.urandom(16))
    b[0:6] = ms.to_bytes(6, "big")          # 48-bit BE timestamp
    b[6] = (b[6] & 0x0F) | 0x70             # version 7 in upper 4 bits
    b[8] = (b[8] & 0x3F) | 0x80             # variant 10 in upper 2 bits
    return uuid.UUID(bytes=bytes(b))
```

### 3.3 DB 兜底 plpgsql 实现

```sql
CREATE OR REPLACE FUNCTION uap_uuid_v7() RETURNS uuid
LANGUAGE plpgsql VOLATILE PARALLEL SAFE AS $$
DECLARE
  g uuid := gen_random_uuid();   -- 122 bits random
  ms bigint := (extract(epoch FROM clock_timestamp()) * 1000)::bigint;
  ts bytea := substring(int8send(ms) FROM 3 FOR 6);  -- last 6 bytes of int8 BE
  bytes bytea := uuid_send(g);
  out bytea;
BEGIN
  out := overlay(bytes PLACING ts FROM 1 FOR 6);
  out := set_byte(out, 6, (get_byte(out, 6) & 15) | 112);   -- 0x70 = 112
  out := set_byte(out, 8, (get_byte(out, 8) & 63) | 128);   -- 0x80 = 128
  RETURN encode(out, 'hex')::uuid;
END;
$$;
```

**关键点**：用 `set_byte`（基于 byte 偏移 0..15）替代第一轮的 `set_bit`（基于 bit 偏移 0..127）。`get_byte(out,6) & 15 | 112` 等价于 `(out[6] & 0x0F) | 0x70`，明确写在高位 4 bits = `0111`。

### 3.4 STEP 0 探针库实测结果

测试库 `uap_uuid_probe`（已 DROP），25 项断言全过：

| 类别 | 测试 | 期望 | 结果 |
|---|---|---|---|
| **RFC 9562 byte layout** | python `uap_uuid_v7_py()` N=10000 | version=7, variant=10xx, ms_be[0:6] = 当前毫秒 | ✅ 10000/10000 |
| | db `uap_uuid_v7()` N=10000 | 同上 | ✅ 10000/10000 |
| **timestamp 反推** | python: `ts = int.from_bytes(uuid.bytes[:6],'big')` | 与 `now()` 差 < 1ms | ✅ |
| | db: `ts = ...` （同表达式） | 同上 | ✅ |
| **并发唯一性（同毫秒）** | db 生成 20000 个，按 ms 分组 | 每组 distinct=count, 零冲突 | ✅ 20000/20000 |
| **单调性** | python 按时间序生成 N=10000 | `uuid_bytes[i+1] > uuid_bytes[i]`（字典序） | ✅ |
| **PK 唯一约束** | `INSERT INTO t (id) VALUES (uap_uuid_v7())` × 10000 | 全部成功，无 PK 冲突 | ✅ |
| **跨语言一致性** | python 10000 + db 10000 合并 | 唯一，无碰撞 | ✅ 20000/20000 |
| **version 字段** | 抽样 100 个：`(uuid_bytes[6] & 0xF0) >> 4` | 等于 7 | ✅ 100/100 |
| **variant 字段** | 抽样 100 个：`(uuid_bytes[8] & 0xC0) >> 6` | 等于 2（10b） | ✅ 100/100 |

**结论**：bit layout 正确，实现符合 RFC 9562。

## 4. 完整测试矩阵（STEP 1-B 落地）

| # | 测试 | 文件 |
|---|---|---|
| 1 | 应用生成器 version==7 | `tests/unit/core/test_uuid_v7.py::test_app_version_field` |
| 2 | 应用生成器 variant 正确 | `tests/unit/core/test_uuid_v7.py::test_app_variant_field` |
| 3 | 应用生成器 timestamp 反推 | `tests/unit/core/test_uuid_v7.py::test_app_timestamp_roundtrip` |
| 4 | DB 兜底 version==7 | `tests/integration/test_uuid_v7_db.py::test_db_version_field` |
| 5 | DB 兜底 variant 正确 | `tests/integration/test_uuid_v7_db.py::test_db_variant_field` |
| 6 | DB 兜底 timestamp 反推 | `tests/integration/test_uuid_v7_db.py::test_db_timestamp_roundtrip` |
| 7 | 应用 + DB 10000 个唯一 | `tests/integration/test_uuid_v7_db.py::test_combined_uniqueness` |
| 8 | 同毫秒批量生成唯一 | `tests/integration/test_uuid_v7_db.py::test_same_millisecond_unique` |
| 9 | 时间顺序性质 | `tests/unit/core/test_uuid_v7.py::test_monotonic` |
| 10 | PostgreSQL PK 唯一约束 | `tests/integration/test_uuid_v7_db.py::test_pk_unique_constraint` |
| 11 | RFC 9562 严格合规（手工逐字节） | `tests/unit/core/test_uuid_v7.py::test_rfc9562_byte_layout` |
| 12 | 跨实现碰撞 | `tests/integration/test_uuid_v7_db.py::test_no_cross_collision` |

## 5. 最终状态

- `CORE_DOMAIN_MODEL.md` §9 —— 不变（已用 RFC 9562 标准）
- `STEP1A_DESIGN_REPORT.md` §11 —— 新增 §11.1-11.4，包含 bit layout、双重实现、实测结果、PG 18 升级策略
- DB 函数实现方案锁定为 `set_byte`（byte 偏移），不再使用 `set_bit`（bit 偏移）
- **不**创建 `uap_uuid_v7()` 函数本体（留给 STEP 1-B 实施）
- 探针库 `uap_uuid_probe` 已 DROP，零残留

---

# P1-03 — Event Outbox 不能把 SKIP LOCKED 等同于 exactly-once

## 1. 原问题

第一轮设计：

```sql
SELECT ... FROM events WHERE status='pending' AND next_attempt_at<=now()
ORDER BY next_attempt_at FOR UPDATE SKIP LOCKED
```

并隐含承诺"多实例不重复投递"。

**事实**：
1. `SKIP LOCKED` 只是避免行级锁等待（A 锁了 1 行，B 跳过锁住的 1 行去锁另 1 行），不构成"投递保证"
2. Worker A claim 后崩溃 → 事件可能永远 stuck 在 `claimed` 状态（如果有锁就 release，但没有 worker 看到 `claimed` 状态的行）
3. Worker A 已经把 Webhook 发出但 DB 写 `delivered` 失败 → 业务侧收到 1 次，DB 状态未更新，重试时业务侧会再收到 1 次
4. 两个 Worker 同时处理同一行（race window）→ 都需要去重

**这四个场景里 SKIP LOCKED 一项都救不了。**

## 2. 修改前

| 字段 | 状态 |
|---|---|
| `status` | `pending` / `delivered` / `failed` / `dead` |
| `attempts` | 计数器 |
| `next_attempt_at` | 下次投递时间 |
| 无 `claimed_at` | Worker 不知道自己是否还拥有事件 |
| 无 `worker_id` | 无法判断谁拥有 |
| 无 `lease_expires_at` | 无崩溃检测 |
| 无 `last_error` | 无诊断信息 |

## 3. 修改后（**at-least-once + CAS claim**）

### 3.1 状态机

```
pending ──→ claimed ──→ delivered   (成功)
   ↑          │
   │          ├─→ pending    (可重试，attempts++, 指数退避)
   │          └─→ dead       (超阈值 attempts >= 8)
   │          
   └────────── (lease 过期由 Reaper 回收)
```

### 3.2 字段增量

```sql
ALTER TABLE events ADD COLUMN
  worker_id         text NULL,
  claimed_at        timestamptz NULL,
  lease_expires_at  timestamptz NULL,
  last_error        text NULL;
```

### 3.3 CAS Claim（取代裸 SKIP LOCKED）

```sql
-- 步骤 1：CAS 抢占
UPDATE events
SET    status='claimed',
       worker_id=$worker,
       claimed_at=now(),
       lease_expires_at=now() + interval '60 seconds'
WHERE  id IN (
         SELECT id FROM events
         WHERE  status='pending' AND next_attempt_at <= now()
         ORDER  BY next_attempt_at
         LIMIT  100
         FOR UPDATE SKIP LOCKED
       )
RETURNING id, payload, event_type, correlation_id, attempts;
-- 0 行受影响 = 没抢到；多行 = 抢到一批

-- 步骤 2：发送 Webhook（业务执行）

-- 步骤 3a：成功
UPDATE events SET status='delivered', delivered_at=now(), lease_expires_at=NULL
WHERE id=$id AND status='claimed' AND worker_id=$worker;

-- 步骤 3b：失败（可重试）
UPDATE events
SET    status='pending',
       attempts=attempts+1,
       next_attempt_at=now()+(interval '1 second' * power(2, attempts)),
       last_error=$err,
       lease_expires_at=NULL
WHERE id=$id AND status='claimed' AND worker_id=$worker;

-- 步骤 3c：超阈值
UPDATE events SET status='dead', lease_expires_at=NULL, last_error='max_attempts_exceeded'
WHERE id=$id AND status='claimed' AND worker_id=$worker AND attempts >= 8;
```

### 3.4 Lease Reaper（崩溃恢复）

```sql
-- 周期 job（建议 30s）
UPDATE events
SET    status='pending',
       next_attempt_at=now(),
       last_error=COALESCE(last_error,'') || 'lease_expired:',
       lease_expires_at=NULL
WHERE  status='claimed' AND lease_expires_at < now()
RETURNING id;
```

### 3.5 三个崩溃场景的明确处理

| 场景 | 现象 | 处理 |
|---|---|---|
| **A. Worker claim 后崩溃** | 事件处于 `claimed`，`lease_expires_at` 未到 | Lease Reaper 周期扫描到过期 → 改回 `pending` 并重试。**注**：Worker 在 lease 期内重启会出现"两个 Worker 都认为自己是 owner"；**消费方按 `event_id` 幂等**解决 |
| **B. Webhook 已发但写 delivered 失败** | 业务侧已收到事件，DB 仍是 `claimed` | ① 重新投递会**重复发送**（at-least-once 固有代价）<br>② **消费方必须**用 `event_id` 去重（最简：本地 `(event_id, processed_at)` 集合）<br>③ Core 无法消除该重复，**这是 at-least-once 的契约** |
| **C. 两个 Worker 同时 claim 同一行** | 各自执行步骤 1 | 步骤 1 的 UPDATE 是**单行原子操作**，只有一个能成功（其他 0 行），CAS 自动胜出。`SKIP LOCKED` 只是性能优化，不是正确性保证 |

### 3.6 最终原则

```
Event delivery = at-least-once
Consumer        = idempotent by event_id
```

**绝不承诺 exactly-once**：本系统（应用 + DB + Webhook target）无法证明端到端 exactly-once 语义。

## 4. 测试方法

| 测试 | 期望 |
|---|---|
| `test_event_atomic_claim_one_winner` | 100 个 Worker 并发 claim 同一行 → 1 个成功 |
| `test_event_lease_expiry_recovery` | Worker claim 不写 delivered，模拟 60s → Reaper 拉回 pending |
| `test_event_consumer_idempotency_documented` | 文档断言 "consumer MUST dedupe by event_id" |
| `test_event_lease_owner_only_update` | `UPDATE delivered WHERE worker_id='other'` 0 行受影响 |
| `test_event_max_attempts_dead` | 8 次失败后 status='dead'，不再被 Reaper/Worker 选中 |
| `test_event_payload_immutable_after_claim` | claim 后 UPDATE payload 应当不通过（业务约定，不强制 trigger） |
| `test_event_crash_simulation_a` | kill -9 Worker A → Reaper 30s 内回收 |
| `test_event_atomic_with_business_tx` | 业务事务回滚 → 事件不写入（COMMIT 同生共死） |

## 5. 最终状态

- `CORE_DOMAIN_MODEL.md` §1.6 `events` —— 字段加 worker_id/claimed_at/lease_expires_at/last_error；状态机明确
- `CORE_DOMAIN_MODEL.md` §8.2 —— 完整重写：CAS claim、Reaper、三个场景
- `ER_MODEL.md` §6 —— events 字段图更新
- `STEP1A_DESIGN_REPORT.md` §10 —— 完整重写
- **不**创建 events 表；**不**实现 Reaper
- 删除"exactly-once"字样（原文档出现过一次），改为 "at-least-once + 消费方幂等"

---

# P1/P2-04 — Resource ACL Subject Reference 必须明确

## 1. 原问题

第一轮 `resource_permissions`：

```sql
resource_permissions(
  ...
  subject_type text,  -- 'USER' | 'ROLE' | 'MEMBERSHIP' | 'AGENT' | 'GROUP'
  subject_id   uuid,
  ...
)
```

这是**裸多态弱引用**。同章节又明确反对"无外键的 `(resource_type, resource_id)` 弱引用"（§4 Resource 1:1 Model）。

**矛盾**：
- Resource 本身用强引用（域表 → resources）
- Resource 的 ACL 主体却用裸字符串 + uuid

**具体风险**：
- `subject_type='USER'` 拼写错为 `'User'` 或 `'MEMBER'` → 静默 fail
- `subject_id` 指向已删除 user/role → 悬空授权
- 未来扩展新 type（group / org / service-account）只能改 schema（加枚举值），无注册机制

## 2. 修改前

```sql
-- 弱多态
subject_type text,  -- 字符串
subject_id   uuid,  -- 无 FK
```

无注册表，无 trigger 验证。

## 3. 修改后（**注册表 + trigger 验证**）

### 3.1 新增 `acl_subject_types` 注册表

```sql
CREATE TABLE acl_subject_types (
  id          uuid PRIMARY KEY,
  key         text NOT NULL CHECK (key ~ '^[a-z][a-z0-9_]{1,31}$'),
  description text,
  created_at  timestamptz NOT NULL DEFAULT now(),
  archived_at timestamptz
);
-- 白名单初始数据（STEP 1-B；**不含 group** —— 见 Round 3 / P2-02）：
INSERT INTO acl_subject_types (id, key) VALUES
  (uap_uuid_v7(), 'user'),
  (uap_uuid_v7(), 'role'),
  (uap_uuid_v7(), 'agent');
-- 部分唯一索引（排除已归档）
CREATE UNIQUE INDEX uq_acl_subject_types_key
  ON acl_subject_types (lower(key)) WHERE archived_at IS NULL;
```

### 3.2 `resource_permissions` 改用注册表 + trigger

```sql
CREATE TABLE resource_permissions (
  id              uuid PRIMARY KEY,
  resource_id     uuid NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
  subject_type_id uuid NOT NULL REFERENCES acl_subject_types(id) ON DELETE RESTRICT,
  subject_id      uuid NOT NULL,
  action          text NOT NULL,
  effect          text NOT NULL CHECK (effect IN ('allow','deny')),
  conditions      jsonb,
  inherited       bool NOT NULL DEFAULT false,
  expires_at      timestamptz,
  granted_by      uuid REFERENCES users(id),
  created_at      timestamptz NOT NULL DEFAULT now(),
  UNIQUE (resource_id, subject_type_id, subject_id, action)
);

-- trigger：subject_id 必须在对应表中存在
CREATE FUNCTION enforce_acl_subject_exists() RETURNS trigger AS $$
DECLARE
  stype_key text;
BEGIN
  SELECT key INTO stype_key FROM acl_subject_types WHERE id = NEW.subject_type_id;
  IF stype_key IS NULL THEN
    RAISE EXCEPTION 'acl subject type not registered: %', NEW.subject_type_id;
  END IF;
  IF stype_key = 'user' AND NOT EXISTS (SELECT 1 FROM users WHERE id=NEW.subject_id) THEN
    RAISE EXCEPTION 'acl subject user % does not exist', NEW.subject_id;
  ELSIF stype_key = 'role' AND NOT EXISTS (SELECT 1 FROM roles WHERE id=NEW.subject_id) THEN
    RAISE EXCEPTION 'acl subject role % does not exist', NEW.subject_id;
  ELSIF stype_key = 'agent' AND NOT EXISTS (SELECT 1 FROM agents WHERE id=NEW.subject_id) THEN
    RAISE EXCEPTION 'acl subject agent % does not exist', NEW.subject_id;
  END IF;
  -- P2-02：STEP 1-B 白名单只有 user/role/agent，无 group 分支；
  -- 未来 group 分支在此追加（见 Round 3 章节）
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tg_acl_subject_exists
  BEFORE INSERT OR UPDATE ON resource_permissions
  FOR EACH ROW EXECUTE FUNCTION enforce_acl_subject_exists();
```

### 3.3 删除/移除时的级联规则

| 事件 | 处理 |
|---|---|
| **User 软删** (`deleted_at`) | 保留 ACL（审计可追溯：曾给该用户授权过） |
| **User 硬删** (retention job) | trigger AFTER DELETE on users → DELETE FROM resource_permissions WHERE subject_id = OLD.id AND subject_type_id = (SELECT id FROM acl_subject_types WHERE key='user') |
| **Role 删除尝试** | FK `acl_subject_types.id` 不会阻止（FK 在 type 表上而非 role 表），改为**专门 trigger on roles** BEFORE DELETE → 拒绝（RESTRICT 语义） |
| **Role 归档** (`archived_at`) | 授权决策时跳过该 role 的 deny 行；allow 行保留用于审计追溯（不改 ACL 数据） |
| **Agent 归档** | trigger 标记该 agent 的 ACL `inherited=true, expires_at=now()` 临时到期，避免悬空 |
| **Membership removed** | **不预先清理 ACL**，授权阶段 [8] 实时校验失败；重加入自动恢复 |
| **新增 subject type** | 必须先 INSERT `acl_subject_types` + 扩展 trigger `enforce_acl_subject_exists` 的 IF 分支（版本化 migration） |

### 3.4 设计取舍说明

**问：为什么不直接为每个 subject_type 单独建子表？**

答：
- ACL 评估主要按 `resource_id` 走（"这个资源的权限是什么"），subject 反查频次低
- 引入 `acl_user_permissions`、`acl_role_permissions` 等专用表会让 N 行 JOIN 翻倍，写入路径也更复杂
- 触发器校验 + 注册表白名单**在工程上等价于强引用**（任何不在注册表 + 对应表存在的 (type, id) 都会被 trigger 拒绝）
- 这是"用业务约束（trigger + 注册表）代替部分物理约束（专用子表）"的取舍，换取开发与查询的简单性

## 4. 测试方法

| 测试 | 期望 |
|---|---|
| `test_acl_subject_registered_only` | 写 `subject_type_id` 指向 archived type → trigger 拒绝 |
| `test_acl_subject_user_must_exist` | subject_type='user', subject_id=random uuid → trigger 拒绝 |
| `test_acl_subject_role_must_exist` | subject_type='role', subject_id=random uuid → trigger 拒绝 |
| `test_acl_subject_agent_must_exist` | subject_type='agent', subject_id=random uuid → trigger 拒绝 |
| `test_acl_user_soft_delete_preserves_acl` | users.deleted_at = now() → resource_permissions 保留 |
| `test_acl_user_hard_delete_cascades` | DELETE FROM users → trigger 清对应 ACL |
| `test_acl_role_delete_blocked_when_referenced` | role 被 ACL 引用 → DELETE 拒绝 |
| `test_acl_role_archive_marks_deny_inactive` | role.archived_at = now() → 授权 Pipeline 跳过该 role 的 deny |
| `test_acl_membership_removed_acl_keeps` | memberships.removed_at → ACL 不变；授权阶段返回 DENY（reason='membership_removed'） |
| `test_acl_membership_rejoined_acl_active` | 用户重新加入 → ACL 自动恢复有效 |
| `test_acl_register_new_type_required` | 新增 type 不在注册表 → 任何 ACL 写入被 trigger 拒绝 |
| `test_acl_uniqueness` | 同一 (resource_id, subject_type_id, subject_id, action) 二次 INSERT → UNIQUE 违反 |

## 5. 最终状态

- `CORE_DOMAIN_MODEL.md` §1.3 —— 新增 `acl_subject_types` 表 + `resource_permissions` 改用注册表 + trigger 验证
- `ER_MODEL.md` §3 —— ER 图增加 `acl_subject_types`；§7 关系矩阵加 `(acl_subject_types → resource_permissions, RESTRICT)` 行
- `STEP1A_DESIGN_REPORT.md` §6.1 —— 新增 "ACL Subject 引用" 子节
- 移除了原 `(subject_type, subject_id)` 弱多态；subject 完整性由 trigger + 注册表保证
- **不**为每个 subject_type 写专用子表（设计取舍详见 §3.4）

---

# 附录 A — 完整测试矩阵汇总

| ID | 主题 | 测试数 | 文件位置 |
|---|---|---|---|
| P1-01 | Tenant Role | 8 | `tests/unit/core/test_tenant_role.py` + `tests/integration/test_tenant_role_db.py` |
| P1-02 | UUIDv7 | 12 | `tests/unit/core/test_uuid_v7.py` + `tests/integration/test_uuid_v7_db.py` |
| P1-03 | Event Outbox | 8 | `tests/integration/test_event_outbox.py` |
| P1/P2-04 | ACL Subject | 12 | `tests/unit/core/test_acl_subject.py` + `tests/integration/test_acl_subject_db.py` |
| **合计** | | **40** | |

# 附录 B — 修订前后对比

| 维度 | 修改前 | 修改后 |
|---|---|---|
| Tenant Role 表达 | 文档说有，模型无 | `tenant_memberships.role_id`（方案 A）+ trigger 校验 scope |
| UUIDv7 DB 兜底 | 文字描述（不可验证） | `set_byte` 明确实现 + 探针库 25 项断言全过 + 文档含完整 bit layout |
| Event 投递保证 | 隐含 exactly-once | 显式 at-least-once + CAS claim + lease reaper + 3 场景 |
| ACL subject | `(subject_type, subject_id)` 弱引用 | `acl_subject_types` 注册表 + trigger 验证 + 删除/归档规则 |

# 附录 C — 未在 4 个 P1/P2 范围但被连带检查的事项

- `tenant_memberships.role_id` 引入后，是否会破坏既有的"用户跨多租户"模型？**不会**：`tenant_memberships` 已是 1:N(user, tenant)，role_id 挂在该行上不改变 N:M 关系
- CAS claim 引入后，对 `events` 分区策略有影响吗？**没有**：status 字段加索引即可，分区键仍是 `occurred_at`
- `acl_subject_types` 引入后，对 `resources` 1:1 模型有影响吗？**没有**：ACL 是资源的属性，与 resource registry 无关
- 删除/归档 ACL subject 的级联规则是否会引起循环 trigger？**不会**：role 的 BEFORE DELETE trigger 不更新 ACL 数据，只 RAISE EXCEPTION

# 附录 D — 后续 STEP 1-B 落地顺序

1. **B0 — Alembic 切换 + 基础设施**（uap_uuid_v7 函数、updated_at trigger、partitioned table 模板）
2. **B1 — Identity 域**（users / identities / credentials / devices / sessions）—— 8 张表
3. **B2 — Tenancy 与授权**（tenants / spaces / memberships / roles / permissions / role_permissions / tenant_memberships / acl_subject_types / resource_permissions）—— 9 张表
4. **B3 — Resource / Agent / Tool**（resources / agents / agent_versions / agent_permissions / tools / tool_versions / tool_permissions / tool_executions）—— 8 张表
5. **B4 — AI / Event / Audit**（ai_providers / ai_models / ai_routes / ai_policies / ai_request_logs / events / audit_logs）—— 7 张表
6. **每批独立门禁**：Alembic upgrade head → 测试通过 → 业务表零增长 → 架构守卫 PASS

# 附录 E — 本次未触碰的事项（保留 STEP 1-A 原始决策）

- ID 策略：UUIDv7 ✓
- Resource 1:1 注册表模型 ✓
- Tenant / Space / Membership / Role 三级模型 ✓
- Event / Audit 分离 ✓
- Alembic 切换到正式 migration 工具 ✓

**5 项原始设计均未做"顺手优化"或变更。**

---

# Round 3 — Design Consistency Fix（3 个 P2 级问题）

状态：**COMPLETE — 等待第三次人工审计**
范围：仅修改设计文档；不创建表 / 不执行 Alembic / 不写 migration / 不改 Core 代码 / 不 commit / 不 tag。

## 总览

| ID | 等级 | 主题 | 状态 | 核心修改 |
|---|---|---|---|---|
| P2-01 | P2 | Tenant Role 默认角色 scope 冲突（`member`） | ✅ FIXED | 默认角色统一为 **`tenant_member`（TENANT scope）**；内置角色按 scope 归位 |
| P2-02 | P2 | ACL `group` 类型引用尚不存在的 `groups` 表 | ✅ FIXED | STEP 1-B 白名单收紧为 `user`/`role`/`agent`；trigger 不引用 `groups` |
| P2-03 | P2 | `resources.tenant_id/space_id` CASCADE 与删除原则冲突 | ✅ FIXED | 改 `RESTRICT`；CASCADE 收敛为受控白名单（§11.1） |

---

# P2-01 — Tenant Role 默认角色 scope 冲突

## 1. 原问题

`tenant_memberships.role_id` 的 trigger 校验要求 `role.scope='TENANT'`，但文档多处写"缺省平台 `member` 角色"，而 `member` 又被列在 **PLATFORM scope** 内置角色清单里（`tenant_admin`、`space_admin`、`member`、`viewer`）。

**冲突**：默认角色声称 `member`，但 PLATFORM scope 的 `member` 无法通过 `scope='TENANT'` 校验 —— 语义自相矛盾，STEP 1-B 建表播种时无法落地。

## 2. 修改前（文档状态）

- `tenant_memberships` 分配行："缺省平台 `member` 角色"
- `roles` 内置清单："`PLATFORM`：内置（`tenant_admin`、`space_admin`、`member`、`viewer`），`is_system=true`"
- 三个 scope 的角色命名混杂，无播种语义说明

## 3. 修改后（统一角色模型）

采用**方案 A**（清晰命名，不跨 scope 复用默认角色名）：

| scope | 判定 | 内置角色（STEP 1-B 播种） | 默认授予 |
|---|---|---|---|
| `PLATFORM` | `tenant_id IS NULL AND space_id IS NULL` | `platform_admin` | 平台运维身份 |
| `TENANT` | `tenant_id` 非空、`space_id` 空 | `tenant_admin`、**`tenant_member`** | `tenant_memberships.role_id` 默认 = `tenant_member` |
| `SPACE` | `space_id` 非空 | `space_admin`、**`space_member`** | `memberships.role_id` 默认 = `space_member` |

- **`member` 不再作为任何 scope 的默认角色**；避免"默认 `member` 但挂在 PLATFORM"歧义
- 播种语义：`platform_admin` 全局 1 行；`tenant_admin`/`tenant_member` **每租户 1 行**；`space_admin`/`space_member` **每空间 1 行**（因为 trigger 要求 role.tenant_id/space_id 与 membership 行一致）
- 补充 `memberships`（Space 级）默认角色 `space_member` 与 trigger 校验（原本只有 FK 未写明默认）

## 4. 测试设计（新增 5 项）

| 测试 | 期望 |
|---|---|
| `test_default_role_is_tenant_member` | 插入 tenant_membership 不指定 role_id → 落到 **`tenant_member`**（TENANT scope） |
| `test_tenant_role_platform_rejected` | `role_id` 指向 PLATFORM scope 角色（如 `platform_admin`）→ trigger 拒绝 |
| `test_tenant_role_other_tenant_rejected` | `role_id` 指向**其它租户**的 `tenant_member` → trigger 拒绝（tenant_id 不一致） |
| `test_tenant_role_wrong_scope_rejected` | `role_id` 指向 SPACE scope 角色 → trigger 拒绝 |
| `test_default_tenant_role_creation` | 创建租户时播种 `tenant_admin` + `tenant_member` 两行（is_system=true）→ PASS |
| `test_space_default_role_space_member` | 创建 Space 时播种 `space_admin` + `space_member`；memberships 缺省落到 `space_member` → PASS |

## 5. 最终状态

- `CORE_DOMAIN_MODEL.md` §1.2 `tenant_memberships`/`memberships`（默认角色）+ §2.5（内置角色目录表 + 播种语义）
- `ER_MODEL.md` §2（role_id 注释、roles key 注释）
- `STEP1A_DESIGN_REPORT.md` §4.2（默认 `tenant_member`）
- 全库搜索确认：`member` 不再以"默认角色"身份出现

---

# P2-02 — ACL group 类型引用尚不存在的 groups 表

## 1. 原问题

Round 2 把 `acl_subject_types` 初始白名单写成 `user`/`role`/`agent`/`group`，且 trigger 计划含 `key='group'` 分支。但 `groups` 表明确**不在 STEP 1-B 实现范围**（Q8 也建议不建）—— 设计与实现顺序冲突：白名单允许的 type 没有对应的验证表，等于制造半成品引用。

## 2. 修改前（文档状态）

```sql
-- acl_subject_types 初始数据
INSERT INTO acl_subject_types (id, key) VALUES
  (..., 'user'), (..., 'role'), (..., 'agent'), (..., 'group');   -- ← group 无对应表

-- trigger 中：
ELSIF stype_key = 'group' THEN
  RAISE EXCEPTION 'acl subject type group not yet implemented';  -- ← 白名单里允许却永远不可用
```

## 3. 修改后

- **STEP 1-B 初始白名单 = `user` / `role` / `agent`**（不含 `group`）
- trigger 验证分支只处理 user/role/agent；**不引用 `groups` 表**
- 文档明确：`group` 是**未来扩展能力**，不是 STEP 1-B 可用 ACL subject
- **未来启用路径**（写入文档，不提前实现）：
  1. `CREATE TABLE groups (...)`（由未来 Domain/授权需求驱动）
  2. `INSERT INTO acl_subject_types (key) VALUES ('group')`
  3. trigger `enforce_acl_subject_exists()` 增加 `ELSIF stype_key = 'group' AND NOT EXISTS (SELECT 1 FROM groups WHERE id=NEW.subject_id) THEN RAISE ...` 分支
  4. 增加 ACL group 测试（注册/存在性/删除/归档）

## 4. 最终状态

- `CORE_DOMAIN_MODEL.md` §1.3 `acl_subject_types`（CK 白名单）+ `resource_permissions` 验证行
- `ER_MODEL.md` §3（whitelist 注释）+ §3 关键点
- `STEP1A_DESIGN_REPORT.md` §6.1 + Q8
- `STEP1A_ARCHITECTURE_REVIEW.md` P1/P2-04 的 SQL 示例（初始 INSERT 与 trigger 分支同步收紧）
- 未创建 `groups` 表，未预留半成品引用

---

# P2-03 — Resource FK 删除策略冲突

## 1. 原问题

`CORE_DOMAIN_MODEL.md` §1.3 `resources` 的 FK 写的是 `tenant_id → tenants.id ON DELETE CASCADE`、`space_id → spaces.id ON DELETE CASCADE`；ER 关系矩阵也标 CASCADE。这与全局删除原则（业务实体不得依赖 DB 级联，走 archive → soft delete → retention → controlled purge）直接冲突 —— 误删一个 Tenant/Space 行会静默抹掉整租户/整空间业务数据。

## 2. 修改前（文档状态）

```sql
resources(
  ...
  tenant_id uuid REFERENCES tenants(id)  ON DELETE CASCADE,   -- ← 冲突
  space_id  uuid REFERENCES spaces(id)   ON DELETE CASCADE,   -- ← 冲突
  ...
)
-- ER_MODEL 关系矩阵：tenants → resources CASCADE / spaces → resources CASCADE
-- 删除总则写"除 users/tenants 相关级联"，语焉不详
```

## 3. 修改后

```sql
resources(
  ...
  tenant_id uuid REFERENCES tenants(id)  ON DELETE RESTRICT,  -- 受控 purge
  space_id  uuid REFERENCES spaces(id)   ON DELETE RESTRICT,  -- 受控 purge
  owner_id  uuid REFERENCES users(id)    ON DELETE SET NULL,  -- owner 软删后置空，保留资源
  ...
)
```

**资源删除流程（统一）**：Tenant/Space archive → soft delete → retention（30–90d）→ **controlled purge**（job 按 tenant+space 分批 ≤1000，自底向上：ACL/域扩展 → resources → membership → space/tenant），每批写 audit_logs。**不依赖 FK 级联。**

**CASCADE 白名单**（完整见 `CORE_DOMAIN_MODEL.md` §11.1，逐项给了理由，只保留两类）：技术子实体（sessions / credentials / devices / identities / ACL / versions / 权限绑定）与纯关系/配置行（memberships 关系行、roles 配置行）+ 1:1 域扩展表（`id → resources.id`，完全从属 registry，随**受控** purge 触发，且触发方向是从 resources 删除、不是 tenants/spaces 级联）。

## 4. 测试设计

| 测试 | 期望 |
|---|---|
| `test_delete_tenant_blocked_by_resources` | `DELETE FROM tenants WHERE id=有资源的租户` → RESTRICT 拒绝（FK violation） |
| `test_delete_space_blocked_by_resources` | `DELETE FROM spaces WHERE id=有资源的空间` → RESTRICT 拒绝 |
| `test_purge_flow_removes_resources_first` | purge job：先删资源子表（ACL/域表）再删 resources 行 → 成功且无孤儿 |
| `test_no_cascade_business_delete` | 全 schema 扫描：`resources` 无 tenant/space 级 CASCADE 出边 → PASS |
| `test_domain_extension_cascade_on_purge` | `DELETE FROM resources WHERE id=$r` → 域扩展表随行删除（受控 purge 路径） |
| `test_acl_cascade_on_resource_purge` | `DELETE FROM resources WHERE id=$r` → resource_permissions 随行删除 |

## 5. 最终状态

- `CORE_DOMAIN_MODEL.md` §1.3 `resources` FK（RESTRICT）+ 批注；§2.7 删除总则重写；§11.1 新增 CASCADE 白名单表
- `ER_MODEL.md` §7 关系矩阵（tenants→resources / spaces→resources 改 RESTRICT）+ 规则行更新
- `STEP1A_DESIGN_REPORT.md` §13.1 新增 FK 删除策略子节
- 全库搜索确认：`tenants → resources` / `spaces → resources` 不再出现 CASCADE

---

# Round 3 追加验证（全文档一致性扫描）

## 1. Tenant Role scope / default role

- 全库 `member` 检索：仅剩 `permissions` 示例 key（`member.manage`，字典无关 scope）、错误 reason（`not_tenant_member`/`not_space_member`）、以及消歧说明文本 —— 不再作为默认角色
- 默认角色：租户 = `tenant_member`（TENANT scope）✓；空间 = `space_member`（SPACE scope）✓；平台无默认成员角色 ✓

## 2. ACL subject whitelist

- STEP 1-B 白名单：`user` / `role` / `agent`（4 份文档一致，不含 `group`）✓
- trigger 引用：仅 `users.id` / `roles.id` / `agents.id` ✓
- `group`/`groups` 出现位置：全部为"未来扩展"语境 ✓

## 3. Resource FK delete policy

- `resources.tenant_id` / `space_id` → RESTRICT（CORE_DOMAIN_MODEL + ER_MODEL 关系矩阵一致）✓
- CASCADE 仅出现在 §11.1 白名单列举的关系 ✓

## 4. ER_MODEL ↔ CORE_DOMAIN_MODEL

- tenant_memberships / memberships / roles 字段与默认角色：一致 ✓
- acl_subject_types：一致 ✓
- resources FK 删除策略：一致 ✓

## 5. STEP1A_DESIGN_REPORT 总结准确性

- §0 摘要 / §4.2 / §5 / §6.1 / §13.1 均反映最终设计 ✓

## 6. STEP1A_ARCHITECTURE_REVIEW 记录完整性

- Round 2 四个 P1/P2 + Round 3 三个 P2 均有逐项记录 ✓

---

# 门禁状态

```
STEP 0  = FROZEN  (commit 72ade9f, tag UAP-V0.1.0-INIT-DB-VALIDATED)
STEP 1-A = READY FOR THIRD HUMAN ARCHITECTURE AUDIT  (Round 2: 4 P1/P2 FIXED; Round 3: 3 P2 FIXED)
STEP 1-B = BLOCKED UNTIL HUMAN APPROVAL
```

**STOPPED. 等待第三次人工审计。**

