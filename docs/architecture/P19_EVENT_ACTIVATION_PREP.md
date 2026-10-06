# P19 EVENT ACTIVATION PREP

# PRODUCTION EVENT ACTIVATION — READ-ONLY DISCOVERY → DECISION OPTIONS

```text
性质   = PREP + 决策已冻结（见 PDL 附录 AB）：P19-D01 = OPTION D ⇒ 契约冻结、激活未授权
基线   = UAP-V0.1.17-P18-CONTROL-PLANE = RELEASED（commit 08a0485b · tree d0af7d5c · tags 16）
权威   = PDL 附录 A–AA（唯一决策权威）· P15 事件/消费者契约 · P16/P17/P18 契约与证据
日期   = 2026-10-01
本轮   = 无实现 · 无 migration · 无 event 激活 · 无 DDL/DML/GRANT · 无 commit/tag/push
```

## 1. Current state（实测）

```text
Production Event Allowlist = EMPTY（production_allowlist().is_empty = True）
Production Handlers       = 0（worker 以空 allowlist 启动）
events 行数                = 0
事件生产者（非测试代码）    = 0（全仓 `INSERT INTO events` 命中数 = 0）
events 分区                = events_202609 · events_202610（按月 RANGE 分区 · 无 DEFAULT 分区）
events 触发器              = 0（不可变性由 consumer 语义 + 权限约束，而非 DB 触发器）
```

## 2. Architecture（既有基础设施 · 已实现且冻结）

```text
services/consumer/kernel.py   —— 冻结常量与语义：MAX_ATTEMPTS=10 · BACKOFF 5×2 上限 600s ·
                                WORKER_PROCESS_COUNT=1 · WORKER_CONCURRENCY=4 · CLAIM_BATCH_SIZE=10 ·
                                LEASE_SECONDS=120 · HEARTBEAT_SECONDS=40 ·
                                终态原因（lease_expired_max_attempts / unsupported_event_type /
                                non_retryable_failure / max_attempts_reached / malformed_payload /
                                authorization_denied）· 可重试类别 {connection, persistence} ·
                                IDEMPOTENCY_PROOFS · EventHandlerSpec（4 项资格）· EventAllowlist ·
                                冻结 SQL（claim / heartbeat / complete(delivered|pending|dead) /
                                recover_expired / recover_expired_dead）
services/consumer/claim.py    —— 领取/心跳/完成/恢复（条件 UPDATE + 行数校验）
services/consumer/worker.py   —— 轮询循环（默认 handlers = production_allowlist()）
apps/worker/main.py           —— worker 入口（以空 allowlist 启动）
```

```text
状态机（实测列）：pending → claimed（worker_id/claimed_at/lease_expires_at）→ delivered | dead
                  attempts 递增 · next_attempt_at 退避 · last_error 记录安全诊断
lease 恢复：过期 lease 由 recover_expired（=> pending）或 recover_expired_dead（=> dead）处理
```

## 3. Event identity / envelope（实测列）

```text
events(id, occurred_at, event_type, schema_version, tenant_id, space_id,
       actor_type, actor_id, subject_type, subject_id, payload,
       correlation_id, causation_id, status, worker_id, claimed_at, lease_expires_at,
       attempts, next_attempt_at, last_error, delivered_at, created_at)
```

```text
标识：UUIDv7（应用侧生成 · 时间有序 · 与 audit 同源 new_event_id 能力）
租户：tenant_id / space_id 可空；空值语义须由本阶段决策明确（平台级 vs 未定）
主体：actor_* 与 subject_* 分离（委派语境）
```

## 4. Producers / Handlers（实测）

```text
生产者：无。P15/P16/P17/P18 均未引入生产事件发布；membership/control-plane 变更只写 audit。
处理器：无。allowlist 为空 ⇒ 任何被领取的事件都会因 unsupported_event_type 进入终态（fail-closed）。
Event Allowlist 结构：EventHandlerSpec 要求四项资格同时成立才可注册：
  producer evidence · authorization semantics · acceptance coverage · provable idempotency
```

## 5. 关键依赖与分离（不得混同）

```text
Event ≠ Audit（audit_logs 为不可变历史事实；event 为可重试的可投递消息）
Event ≠ Control Plane（结构生命周期不发布生产事件；只写 audit）
Event ≠ Agent Runtime（Agent Run 台账与事件表互不替代）
Event ≠ Business Module（业务语义必须等模块冻结后再定 event type）
```

## 6. 生产激活的前置条件（当前全部未满足）

```text
C1 至少一个 event type 的 EventHandlerSpec 四项资格全部具备（尤其 producer evidence + acceptance）
C2 幂等可证明（IDEMPOTENCY_PROOFS ∩ 该 type 的投递语义）
C3 授权语义明确（谁在何 scope 下允许投递/消费 · 与 canonical 授权一致）
C4 租户/空间语义明确（tenant_id/space_id 空值规则 · deleted/archived 后的事件处理）
C5 事件与审计/控制面/Agent 的边界在契约中明示
C6 激活仅通过显式 Human Decision（allowlist 变更本身即安全决策）
```

## 7. 生产激活候选选项（供裁定）

```text
OPTION A（本轮建议）：继续保持 Production Event Allowlist = EMPTY
  理由：无生产者 ⇒ 无真实事件可消费；激活 handler 只会制造 unsupported 终态噪音；
        先做业务模块（Company 等）设计，再由其定义 event type 与 idempotency proof。
OPTION B：仅激活一个"平台基础事件"（例如 tenant.provisioned / space.provisioned），
  由 control plane 作为生产者、worker 作为消费者，作为端到端管道验证。
  代价：需要为每个 type 出具 producer evidence + authorization semantics + acceptance coverage +
        idempotency proof；需要明确 tenant/space 空值与 deleted/archived 语义；
        需要新增（或复用）投递下游（当前无真实订阅者 ⇒ 仍可能是"自产自销"验证）。
OPTION C：仅激活消费者而不激活任何生产者（读取既有 audit 派生事件）。
  代价：需要在 audit → events 之间引入派生器（新的写路径）⇒ 与"audit ≠ event"边界冲突风险高。
OPTION D：先行冻结 event type 命名与 envelope 的**契约**（不激活、不发布），
  为业务模块提供稳定接口；激活仍留待模块级 Human Decision。
```

## 8. Decision questions（必须由 Human 裁定）

```text
Q1 本轮是否继续维持 Allowlist = EMPTY（OPTION A）？
Q2 若要激活，选哪个 event type（命名 · schema_version 策略 · payload 契约）？
Q3 该 type 的 producer 是谁（control plane / runtime / business module）？evidence 形式？
Q4 其 authorization semantics 如何映射到既有 canonical 授权（scope · permission）？
Q5 其 idempotency proof 是什么（自然键 / 去重依据 / 不能重复的语义）？
Q6 tenant_id / space_id 为空的语义（平台级事件 vs 未定）？
Q7 目标租户/空间处于 suspended/archived/deleted 时，事件如何处置（投递/丢弃/终态）？
Q8 delivery 下游是什么（当前无订阅者 ⇒ 激活的验收标准是什么）？
Q9 retry/backoff/lease 参数是否保持 P15 冻结值（10 次 · 5×2 上限 600s · lease 120s · hb 40s）？
Q10 是否需要新的 privilege（当前 uap_runtime 已可 INSERT/SELECT/UPDATE events；worker 侧需何种主体）？
```

## 9. Risks

```text
R1 无生产者时激活 = 纯噪音（unsupported_event_type 终态堆积）
R2 误把 audit 当作 event 源 ⇒ 破坏 append-only 历史与可重试消息的边界
R3 事件载荷携带敏感数据（secret/token/凭据）⇒ 必须在契约层禁止
R4 跨租户投递（consumer 缺少 tenant 谓词）⇒ 与 P16 历史缺陷同类
R5 幂等证明缺失导致重复副作用（未来业务模块最危险）
R6 allowlist 变更属安全决策：若不在 PDL 记录，将失去可审计性
R7 激活后无法回头（历史事件终态不可重写）⇒ 需要显式回退策略
```

## 10. P19 PREP SUCCESS CRITERIA（本轮）

```text
[x] 事件基础设施/标识/envelope 只读勘验完成
[x] 生产者 / 处理器 / allowlist 现状取证（全部为空）
[x] 依赖与边界（audit / control plane / agent / business module）记录
[x] 激活前置条件（C1–C6）列明
[x] 候选选项 A–D 与评估矩阵准备
[x] 决策问题 Q1–Q10 登记
[x] 风险 R1–R7 登记
[x] 测试矩阵提案（P19_EVENT_TEST_MATRIX.md）
[x] 缺口登记（P19_EVENT_GAP_RECORD.md）
[x] Formal DB 未触碰 · Git 基线未变
```

## 11. 本轮明确未做

```text
未实现任何代码 · 未新增/修改 migration（head 仍 0018）· 未新增表/列/约束 ·
未新增 event type / handler / allowlist 条目 · 未激活任何生产事件 · 未 GRANT/REVOKE ·
未 commit / tag / push · 未改写 PDL 附录 A–AA
Production Event Allowlist = EMPTY（保持）· Handlers = 0（保持）
```

**END OF P19 EVENT ACTIVATION PREP（PREP ONLY · Allowlist 保持 EMPTY · 待 Human Decision；2026-10-01）**
