# P20 GAP RECORD

```text
性质 = P20 PREP 附件（缺口登记 · OPEN · 未粉饰）
```

## GAP-P20-1 首个业务模块未选定（MODULE SELECTION）

```text
Observation：仓库与权威文档中无任何业务模块被 Human Decision 选定；
             Company / Commercial / Entertainment / Industry Templates 仅为文档示例。
Impact     ：模块范围、实体、授权映射、事件策略均无法冻结。
状态       ：OPEN（本 PREP 的核心决策输入）
```

## GAP-P20-2 业务 schema 决策缺失（SCHEMA DECISION）

```text
Observation：无任何业务表；如需业务数据，必须新增表/迁移。
Impact     ：与"新 schema = 新 Human Decision"的既有治理直接相关，不得在实现轮顺带建表。
状态       ：OPEN（模块选定后必须单独裁定）
```

## GAP-P20-3 授权映射缺失（AUTHORIZATION MAPPING）

```text
Observation：12 条 canonical permission 未覆盖任何业务 resource_type；
             业务操作如何映射（是否为既有 resource/action 组合）尚未定义。
Impact     ：无法定义控制面/运行时对外业务操作的授权判定。
状态       ：OPEN
```

## GAP-P20-4 事件资格缺失（EVENT ELIGIBILITY）

```text
Observation：P20_EVENT_CANDIDATE_MATRIX 中 D02/D03/D04/D07/D09/D11/D15/D18 均为 OPEN。
Impact     ：首个生产事件不可激活（与 P19-D01 OPTION D 一致）。
状态       ：OPEN
```

## GAP-P20-5 平台外主体模型缺失（EXTERNAL ACTOR MODEL）

```text
Observation：Commercial（顾客）与 Entertainment（观众）可能涉及平台外主体；
             当前平台主体模型仅覆盖 user/agent/role。
Impact     ：若首模块涉及外部主体，需要新的身份/授权决策（不得隐含引入）。
状态       ：OPEN（取决于模块选择）
```

## GAP-P20-6 领域包结构未定（DOMAIN PACKAGE STRUCTURE）

```text
Observation：`domains/` 存在但无实现；业务代码的落位（domains/ vs services/）与依赖方向未冻结。
Impact     ：影响 Core → Domain = 0 的架构守卫与后续模块复用方式。
状态       ：OPEN（建议随首模块一并裁定）
```

**END OF P20 GAP RECORD（GAP-P20-1…6 = OPEN；2026-10-01）**
