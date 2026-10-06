# P20 FIRST BUSINESS MODULE PREP

```text
性质   = PREP ONLY（只读发现 + 架构准备 + 决策输入；NOT FROZEN · NOT AUTHORIZED）
基线   = UAP-V0.1.17-P18-CONTROL-PLANE = RELEASED（commit 08a0485b · tags 16）
         + P19 DECISION FREEZE（PDL 附录 AB · P19-D01 = OPTION D · 激活未授权）
本轮   = 无业务表 / 无 migration / 无 API / 无 worker / 无 producer / 无 handler / 无 event 激活
```

## 1. 只读基线核验（本轮实测）

```text
Git   = HEAD = origin/main = 08a0485b · tags 16 · staged 0 · 无 0019
平台  = P13–P18 已发布；P19 决策冻结（Allowlist EMPTY · Handlers 0 · events 0 行 · 生产者 0）
主体  = uap_migrator（schema）· uap_bootstrap（一次性引导）· uap_control（24? 实际 23 grants 结构面）·
        uap_runtime（56 grants 运行面）· uap_app（就绪/审计）· uap_seed（无权限）
正式库 = uap public 表 0（未使用）；测试库 = uap_b1_test / uap_test
业务域 = 仓库内**不存在**任何业务模块实现（无 domains 业务代码 · 无业务表 · 无业务 API）
```

## 2. 候选业务模块（区分事实与推断）

| 候选 | 来源 | 状态 | 说明 |
|---|---|---|---|
| Company（公司/组织：员工、部门） | P17/P18/P19 文档中作为"未来可复用平台上下文的消费方"被反复提及 | **已提出但未冻结**（文档提及，非 Human Decision） | 文档只把它列为将来会复用 tenant/space/membership 的模块示例 |
| Commercial（餐饮/商业：门店、菜单、订单） | 同上（P18/P19 文档示例） | 已提出但未冻结 | 同上 |
| Entertainment（娱乐内容） | 同上 | 已提出但未冻结 | 同上 |
| Industry Templates（行业模板） | 同上 | 已提出但未冻结 | 同上 |

```text
已冻结事实：无任何业务模块被 Human Decision 选定
已提出未冻结：上述四个名称出现在平台文档中，仅作为"未来消费方"示例
BOT 推导（明确标注 · 不得当作决定）：若以"最少新概念 + 最贴近已有平台语义"为准则，
  Company 是最小天真的候选（员工 ↔ tenant membership、部门 ↔ space 语义最接近）
尚未决定：首个模块的选定与范围
```

## 3. 候选模块 PREP 级评估（DESIGN PROPOSAL / NOT FROZEN）

| 维度 | Company | Commercial | Entertainment |
|---|---|---|---|
| purpose | 组织内人员与部门结构 | 门店/菜单/订单交易 | 内容与分发 |
| actor model | 员工（= 平台 user）+ 管理者（tenant/space 管理员角色） | 员工 + 顾客（可能是平台外部主体） | 创作者 + 观众 |
| tenant scope | 天然 tenant 内（公司 = tenant 或 tenant 内组织） | tenant 内（多门店） | tenant 内 |
| space scope | 部门 ≈ space（可映射 P17 space） | 门店 ≈ space | 频道/栏目 ≈ space |
| core entities | employee · department · assignment | store · menu · order · order_item | content · collection · release |
| principal operations | 入职/调动/离职（成员与角色） | 下单/支付/退款 | 发布/下架 |
| likely mutations | membership/role 变更 + 业务表 | 订单状态机（强事务） | 内容状态机 |
| async reactions | 通知、报表、外部系统同步 | 支付回调、库存、对账 | 转码、分发 |
| 是否天然需要 event | Partial（多数可由同步事务 + audit 覆盖） | Yes（支付/对账天然异步） | Yes（转码/分发天然异步） |
| event 生产位置（候选） | 员工/部门变更后的集成点 | 订单状态跃迁 | 内容状态跃迁 |
| event 消费位置（候选） | 通知/报表服务 | 支付/库存/对账 | 转码/分发/审核 |

```text
注意：上表全部为 DESIGN PROPOSAL / NOT FROZEN —— 不得作为实施依据。
```

## 4. 与 P19 Event Authority 的对齐要求

任何模块若要成为首个生产事件来源，必须逐项满足 PDL 附录 AB 的 P19-D02…D18
（10 项 eligibility + producer/handler/actor/authorization/tenant-space/lifecycle/idempotency/
retry-lease/versioning/audit-boundary/control-plane/agent/payload/failure/observability/first-gate）。
逐项矩阵见 `P20_EVENT_CANDIDATE_MATRIX.md`（当前全部为 OPEN 或 PARTIAL —— 因为尚无模块被选定）。

## 5. 本轮是否产生首个 Production Event？

```text
结论（PREP 建议 · NOT FROZEN）：**不产生**
理由：
  · 无任何业务模块被 Human Decision 选定 ⇒ 无真实 producer 代码路径
  · P19-D01 = OPTION D 明确：无 producer + qualified handler + 幂等证明 ⇒ 不得激活
  · 在模块范围冻结前提出 event type 会把业务语义写入平台权威，属越界
建议顺序：选定首个模块 → 冻结其范围与实体 → 再按 P19-D02 逐类型裁定 event 激活
```

## 6. 决策输入（供 Human Decision）

```text
Q1 首个业务模块选哪个（Company / Commercial / Entertainment / Industry Templates / 其他）？
Q2 该模块的 tenant/space 语义（公司 = tenant 还是 tenant 内实体？部门 = space？）
Q3 该模块的 actor 模型（员工是否恒为平台 user？是否存在平台外主体？）
Q4 该模块是否需要 event（若需要，哪些状态跃迁是事件、哪些只是 audit）？
Q5 该模块的最小可用范围（首个 release 交付什么 · 明确排除什么）？
Q6 该模块的授权映射（复用 12 条 canonical permission · 是否出现新 resource_type？）
Q7 该模块与 P18 控制面的边界（是否引入新的结构对象？如需新表/迁移则必须单独决策）
```

## 7. 风险

```text
R1 把 P20 候选名当作已决定（文档提及 ≠ Human Decision）
R2 先写业务表/迁移再补边界 ⇒ 破坏"无新 schema 需决策"的既有治理
R3 把 audit 当 event 或反之（P19-D12）
R4 业务模块绕过 P17 上下文/P18 控制面，自建 tenant/space/role 语义
R5 首个模块范围过大（应选最小可验证切片）
R6 在模块语义未冻结前定义 event type ⇒ 后续 schema_version 被迫演进
```

**END OF P20 FIRST BUSINESS MODULE PREP（PREP ONLY · 无模块被选定 · 不产生生产事件 · 待 Human Decision；2026-10-01）**
