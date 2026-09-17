# STEP 1-B / B0 — Event Outbox Implementation Readiness

Status: **DESIGN PREPARATION — 不创建任何表**
来源：STEP 1-A Round 2 P1-03 修正 + Round 3 冻结设计
配套：[CORE_DOMAIN_MODEL.md §8.2](./CORE_DOMAIN_MODEL.md)、[STEP1A_ARCHITECTURE_REVIEW.md §P1-03](./STEP1A_ARCHITECTURE_REVIEW.md)

> **核心承诺：Event delivery = At-Least-Once。消费方按 `event_id` 幂等。禁止宣称 Exactly-Once。**

---

## 1. 表结构与状态机（B1 落地）

```sql
events (
  id                uuid,             -- = event_id（幂等键）
  occurred_at       timestamptz,      -- 分区键（UTC 月边界）
  event_type        text NOT NULL,
  schema_version    int NOT NULL,
  tenant_id         uuid NULL,        -- 无强制 FK（避免长期历史阻塞租户 purge）
  space_id          uuid NULL,
  actor_type        text NULL, actor_id uuid NULL,
  subject_type      text NULL, subject_id uuid NULL,
  payload           jsonb NOT NULL,
  correlation_id    uuid NULL, causation_id uuid NULL,

  status            text NOT NULL,    -- pending | claimed | delivered | dead
  worker_id         text NULL,        -- claim owner
  claimed_at        timestamptz NULL,
  lease_expires_at  timestamptz NULL, -- Reaper 回收依据
  attempts          int NOT NULL DEFAULT 0,   -- CHECK attempts BETWEEN 0 AND 100
  next_attempt_at   timestamptz NULL,
  last_error        text NULL,
  delivered_at      timestamptz NULL,
  created_at        timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id, occurred_at)
) PARTITION BY RANGE (occurred_at);
```

**状态机**：

```
pending ──CAS claim──→ claimed ──投递成功──→ delivered
   ▲                      │
   │                      ├── 失败可重试 ──→ pending (attempts++, 指数退避)
   │                      ├── attempts>=8 ─→ dead (+告警)
   └── lease 过期 ──Reaper──┘
```

---

## 2. CAS Claim（必须原子 UPDATE，不能只靠 SKIP LOCKED）

```sql
-- 步骤 1：CAS 抢占（单行 UPDATE = 乐观锁；多实例只有一个成功）
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
         FOR UPDATE SKIP LOCKED        -- 性能优化（避免锁等待），非正确性保证
       )
RETURNING id, event_type, payload, correlation_id, attempts;

-- 步骤 2：业务投递（Webhook / handler）

-- 步骤 3a 成功：
UPDATE events SET status='delivered', delivered_at=now(), lease_expires_at=NULL
WHERE  id=$id AND status='claimed' AND worker_id=$worker;

-- 步骤 3b 失败可重试：
UPDATE events SET status='pending',
                  attempts=attempts+1,
                  next_attempt_at=now() + (interval '1 second' * power(2, attempts)),
                  last_error=$err, lease_expires_at=NULL
WHERE  id=$id AND status='claimed' AND worker_id=$worker;

-- 步骤 3c 超阈值：
UPDATE events SET status='dead', lease_expires_at=NULL, last_error='max_attempts_exceeded'
WHERE  id=$id AND status='claimed' AND worker_id=$worker AND attempts >= 8;
```

- **步骤 3a/3b/3c 的 WHERE 都带 `worker_id=$worker`**：防止租约到期后其它 worker 已接管，旧 worker 误改状态
- CAS 是正确性来源；`FOR UPDATE SKIP LOCKED` 只是减少并发锁等待

---

## 3. Lease Reaper（Worker 崩溃恢复）

```sql
-- 周期 job（建议 30s，独立 worker/定时任务）
UPDATE events
SET    status='pending',
       next_attempt_at=now(),
       last_error=COALESCE(last_error,'') || 'lease_expired:',
       lease_expires_at=NULL
WHERE  status='claimed' AND lease_expires_at < now()
RETURNING id;
```

---

## 4. 三个崩溃场景（B1 必须测试）

| 场景 | 机制 | 备注 |
|---|---|---|
| A. Worker claim 后崩溃 | lease（60s）过期 → Reaper 置回 pending → 其它 worker 接管 | 若 worker 在租约内重启，消费方幂等兜底 |
| B. Webhook 已发但写 delivered 失败 | 事件**必然重发**（at-least-once 固有代价） | 消费方按 `event_id` 去重，收到重复即 ack 不执行 |
| C. 两 worker 同 claim 一行 | 单行 UPDATE 原子，仅 1 个成功（0/1 行返回） | CAS 语义；SKIP LOCKED 只是减少等待 |

---

## 5. 幂等保障（消费方义务 + Core 支持）

| 层 | 机制 |
|---|---|
| 事件层 | `event_id`（=PK id）为幂等键；消费方维护 `(event_id, processed_at)`，重复即跳过 |
| 投递层 | CAS claim + lease 保证不会两个 worker 同时"执行同一投递"（只有一个拿到 claimed） |
| Tool 层（独立） | `tool_executions.(tool_id, idempotency_key)` 部分唯一约束 |

---

## 6. 失败与死信策略

| 状态 | 触发 | 处理 |
|---|---|---|
| `dead` | attempts ≥ 8（默认） | 写 `audit_logs(result='error', action='event.delivery.failed', risk_level='HIGH')` + 告警 |
| dead 复投 | 人工 | `attempts=0, status='pending', next_attempt_at=now()` 后重新入队 |
| dead 保留 | 90 天 | 超期由 retention 清理（复盘窗口） |
| 消费方宕机 | 无限 | 事件留在队列，lease 机制保证可恢复；无 TTL 丢弃（除非业务定义） |

---

## 7. 与业务事务的原子性（Outbox 写入）

```sql
BEGIN;
  INSERT INTO resources (...);                       -- 业务写入
  INSERT INTO events (id, occurred_at, event_type, payload,
                      status='pending', attempts=0, next_attempt_at=now(), ...)
  VALUES (...);
COMMIT;   -- 业务成功 ⇔ 事件必然存在
```

**禁止**把事件投递放进业务事务（网络 I/O 不入本地事务）。

---

## 8. 测试矩阵（B1 落地）

见 [STEP1B_SCHEMA_TEST_MATRIX.md](./STEP1B_SCHEMA_TEST_MATRIX.md) §6，至少：CAS 单赢家 / 并发 100 worker / lease 到期回收 / attempts 退避 / dead 阈值 / 消费方幂等 / 业务事务回滚不产生事件 / worker_id 归属校验。
