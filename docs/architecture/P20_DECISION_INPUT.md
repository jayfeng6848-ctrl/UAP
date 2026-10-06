# P20 DECISION INPUT

```text
性质 = P20 PREP 附件（供 Human Decision 的裁定清单 · 未冻结）
```

## 1. 需要裁定的问题

```text
D-A1 首个业务模块 = ？（Company / Commercial / Entertainment / Industry Templates / 其他）
D-A2 模块与 tenant/space 的映射（公司 = tenant？部门/门店/频道 = space？）
D-A3 actor 模型（是否引入平台外主体？若引入 ⇒ 新的身份/授权决策）
D-A4 是否需要新的业务 schema（表/列）？若需要 ⇒ 独立 migration 决策
D-A5 业务操作到 canonical 授权的映射（12 条词表 · 是否新 resource_type）
D-A6 首个 release 的最小范围（交付什么 / 明确排除什么）
D-A7 是否要求该模块产生首个生产事件（若要求 ⇒ 必须补齐 P19-D02…D18 全部证据）
D-A8 领域代码落位与依赖方向（domains/ vs services/ · Core → Domain = 0 的守卫方式）
```

## 2. PREP 建议（NOT FROZEN）

```text
建议 1：先选定 **Company** 作为首个业务模块 —— 它最贴近既有平台语义
        （员工 ↔ tenant membership；部门 ↔ space），可最大限度复用 P17/P18，最小化新概念。
建议 2：首个 release 只交付"组织内人员与部门的最小 CRUD + 授权 + 审计"，
        明确排除事件、外部主体、复杂工作流。
建议 3：**不要求**首模块产生生产事件（与 P19-D01 OPTION D 一致）；
        事件激活留待模块语义稳定后的独立决策。
建议 4：若首模块需要业务表，作为**独立 migration 决策**单独裁定，不与模块实现合并。
```

## 3. 结论

```text
本轮不产生任何实现、不激活任何事件、不新增 schema；
等待 Human Decision 冻结 A1–A8 后，方可进入 P20 IMPLEMENTATION。
```

**END OF P20 DECISION INPUT（待 Human Decision；2026-10-01）**
