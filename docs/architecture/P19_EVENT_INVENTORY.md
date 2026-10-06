# P19 EVENT INVENTORY

```text
性质 = P19 PREP 附件（只读实测 · 2026-10-01）· 基线 UAP-V0.1.17-P18-CONTROL-PLANE（08a0485b）
```

## 1. Schema（events · 实测 22 列）

```text
id uuid PK default uap_uuid_v7()      occurred_at timestamptz NN
event_type text NN                    schema_version int NN
tenant_id uuid NULL                   space_id uuid NULL
actor_type text NULL                  actor_id uuid NULL
subject_type text NULL                subject_id uuid NULL
payload jsonb NN                      correlation_id uuid NULL
causation_id uuid NULL                status text NN
worker_id text NULL                   claimed_at timestamptz NULL
lease_expires_at timestamptz NULL     attempts int NN
next_attempt_at timestamptz NULL      last_error text NULL
delivered_at timestamptz NULL         created_at timestamptz NN
```

```text
分区：RANGE(occurred_at) · events_202609 · events_202610（无 DEFAULT 分区）
触发器：0（无 audit 式不可变触发器；状态由 consumer 条件 UPDATE 管理）
行数：0
```

## 2. 授权矩阵（实测）

```text
uap_runtime  : INSERT, SELECT, UPDATE（parent + 2 分区 · 无 DELETE）
uap_migrator : 全权限（schema authority）
uap_control  : 无（events 在 P18 禁止面 · 控制面不发布生产事件）
uap_app      : 无
```

## 3. 消费者组件（实测）

```text
services/consumer/kernel.py  : 冻结常量（MAX_ATTEMPTS 10 · BACKOFF 5×2 上限 600 · lease 120s ·
                               heartbeat 40s · batch 10 · worker 1×4）· 终态原因 6 种 ·
                               可重试类别 {connection, persistence} · IDEMPOTENCY_PROOFS ·
                               EventHandlerSpec / EventAllowlist / production_allowlist() ·
                               冻结 SQL 7 段（claim · heartbeat · complete×3 · recover×2）
services/consumer/claim.py   : ClaimService（领取 / 心跳 / 完成 / 恢复 · 行数校验）
services/consumer/worker.py  : 轮询循环 · 默认 handlers = production_allowlist()
apps/worker/main.py          : worker 进程入口 · production_allowlist() 注入
```

## 4. 生产者清单

```text
（空）全仓非测试代码 `INSERT INTO events` 命中 = 0
现有写入 events 的仅测试夹具（P15 claim/worker 测试 · 运行后净零清理）
⇒ 生产事件生产者为 0：无 tenant.created / space.created / membership.bootstrap 等发布点
```

## 5. 处理器清单

```text
（空）production_allowlist() 返回空 EventAllowlist（specs = {}）
EventHandlerSpec 注册要求四项资格同时成立：
  has_producer_evidence · has_authorization_semantics · has_acceptance_coverage · provable_idempotency
⇒ 当前无任何 event type 具备注册资格；worker 启动后任何被领取事件都将终态化为 unsupported_event_type
```

## 6. 事件类型（候选 · 未冻结）

```text
历史讨论中出现但**未激活、未定义契约**的候选类型：
  tenant.created / space.created / tenant.archived / space.deleted /
  membership.created / membership.updated / membership.deleted / membership.bootstrapped /
  resource.provisioned
状态：全部 NOT ACTIVE（PDL 附录 V / Z / AA 明确拒绝激活）
```

**END OF P19 EVENT INVENTORY（生产者 0 · 处理器 0 · events 0 行 · Allowlist EMPTY；2026-10-01）**
