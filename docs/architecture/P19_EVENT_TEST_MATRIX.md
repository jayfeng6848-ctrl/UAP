# P19 EVENT TEST MATRIX

```text
性质 = P19 PREP 附件（测试矩阵提案 · 未执行 · 未冻结）
基线 = UAP-V0.1.17-P18-CONTROL-PLANE（08a0485b）
```

## 1. 现状基线（已存在并可复跑的冻结测试）

```text
tests/unit/test_p15_consumer_kernel.py      （kernel 常量/退避/资格/allowlist 语义）
tests/unit/test_p15_worker.py               （worker 循环/终态/异常归类）
tests/unit/test_p15_worker_entry.py         （worker 进程入口/allowlist 注入）
tests/integration/test_p15_claim.py         （真实 DB：claim/lease/heartbeat/recovery/terminal）
--------------------------------------------------------------
P15 合计 = 65 passed / 0 failed（本轮回归基线，必须保持）
```

## 2. 激活后必须新增的测试（提案 · 依裁定 OPTION 而定）

```text
生产者侧
  T1 producer 在真实事务中写入 events（status=pending · tenant/space 正确）
  T2 producer 授权失败 ⇒ 不写事件（canonical 授权先于写入）
  T3 payload 契约（schema_version · 必填字段 · 禁止 secret/token/凭据）
  T4 生产者不写 audit 之外的状态（事件与审计分离）

消费者侧
  T5 handler 资格四项齐备才可注册（缺一 ⇒ 拒绝注册）
  T6 支持类型：正常投递 ⇒ delivered（attempts=1 · delivered_at 非空）
  T7 不支持类型 ⇒ dead（terminal_reason=unsupported_event_type）
  T8 可重试类别 ⇒ pending + 退避（next_attempt_at 递增 · 上限 600s）
  T9 不可重试类别 ⇒ dead（terminal_reason=non_retryable_failure）
  T10 达到 MAX_ATTEMPTS ⇒ dead（max_attempts_reached）
  T11 malformed payload ⇒ dead（malformed_payload）
  T12 授权拒绝 ⇒ dead（authorization_denied）

并发 / 租约
  T13 双 worker 竞争同一事件 ⇒ 恰一个 claim 成功（条件 UPDATE + rowcount）
  T14 lease 过期 ⇒ recover_expired（回 pending）或 recover_expired_dead（达上限 ⇒ dead）
  T15 heartbeat 延长 lease（未过期不重复领取）

多租户 / 生命周期（P17/P18 对齐）
  T16 事件 tenant_id 与 consumer 上下文不一致 ⇒ 拒绝（跨租户投递 = 0）
  T17 tenant/space 非 ACTIVE 时的事件处置（按裁定语义：丢弃 / 保持 pending / 终态）
  T18 tenant_id/space_id 为空的平台级事件语义（按裁定）

可观测 / 安全
  T19 last_error 只记录安全诊断（无 SQL / stack / secret）
  T20 事件载荷无敏感数据（扫描断言）
```

## 3. 治理约束（沿用）

```text
显式 allowlist（禁止 pytest / 目录级）· forbidden tests = 0 ·
skip/xfail/deselect = 0 · 正式库 uap 不得被测试触碰 ·
所有真实 DB 测试使用一次性隔离库 + 官方 migration + 官方授权物化
```

## 4. 与 P18 回归的关系

```text
激活实现若触及 consumer/worker 之外的任何 P15/P16/P17/P18 语义，须先 STOP；
P18 冻结基线（P18 33/0 · P17 97/0 · P16 24/0+8/0 · P15 65/0 · guards 63/0 · Core → Domain 0）
必须保持。
```

**END OF P19 EVENT TEST MATRIX（提案 · 未执行 · 待裁定；2026-10-01）**
