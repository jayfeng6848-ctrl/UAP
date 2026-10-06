# P19 EVENT DEPENDENCY MAP

```text
性质 = P19 PREP 附件（依赖与边界映射 · 只读勘验结论 · 未冻结）
基线 = UAP-V0.1.17-P18-CONTROL-PLANE（commit 08a0485b · tree d0af7d5c）
```

## 1. 阶段继承链

```text
P13 canonical permissions / role model      → event handler 的授权语义必须复用该词表（12 条）
P14 DB security principals                 → 生产者/消费者主体边界（uap_runtime / worker 主体）
P15 event / consumer foundation            → 事件表 · 分区 · claim/lease/heartbeat/recovery · allowlist
P16 Agent Runtime                          → Agent Run 台账 ≠ 事件；事件不得成为 Agent 执行捷径
P17 identity / tenant / space runtime      → tenant/space 上下文与生命周期门禁（D14）适用
P18 control plane                          → 结构变更只写 audit；不发布生产事件
P19 production event activation            → 待裁定（本 PREP 不冻结任何内容）
```

## 2. 边界（不得混同）

```text
Event ≠ Audit
  audit_logs：append-only 历史事实（无 UPDATE/DELETE）· 结构/成员/授权变更的记录
  events    ：可重试的可投递消息（status/attempts/lease）· 语义由 handler 定义
  ⇒ 不得以 audit 派生事件（会引入第二条写路径），不得以事件替代审计

Event ≠ Control Plane
  结构生命周期（P18）只写 audit；不发布 tenant.created / space.created 等生产事件

Event ≠ Agent Runtime
  Agent Run 的结果台账与 ToolGate 授权路径独立；事件消费不得绕过 canonical 授权

Event ≠ Business Module
  业务语义（订单/内容/账单等）必须等模块冻结后再定 event type 与 payload 契约
```

## 3. 运行时依赖

```text
worker（apps/worker/main.py）
   ↓ handlers = production_allowlist()（当前空）
consumer kernel（常量 / 终态原因 / 退避 / allowlist）
   ↓ 冻结 SQL
events（分区表 · uap_runtime INSERT/SELECT/UPDATE）
   ↓ 需要（若激活）
生产者的投递语义 + 授权语义 + 幂等证明 + 接受测试覆盖
```

## 4. 未来模块依赖

```text
Company / Commercial / Entertainment 等模块若需要事件：
  ① 先定义 event type 命名与 schema_version 策略
  ② 提供 producer evidence（真实发布点）
  ③ 映射到既有 canonical 授权（scope/permission，不新增词表）
  ④ 提供 idempotency proof（自然键 / 去重依据）
  ⑤ 通过 acceptance coverage
  ⑥ 由 Human Decision 修改 allowlist（该修改本身即安全决策）
```

## 5. 与冻结边界的一致性

```text
P15/P16/P18 冻结：Production Event Allowlist = EMPTY · Handlers = 0
P19 PREP 未改变该状态；任何激活都必须由新的 Human Decision 在 PDL 中登记
P18-D14 生命周期门禁：租户/空间 inactive 时的运行时行为已定义（消费侧需在激活决策中明确对齐）
```

**END OF P19 EVENT DEPENDENCY MAP（未冻结 · 待 Human Decision；2026-10-01）**
