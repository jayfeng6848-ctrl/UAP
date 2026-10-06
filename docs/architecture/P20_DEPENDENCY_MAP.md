# P20 DEPENDENCY MAP

```text
性质 = P20 PREP 附件（依赖与边界映射 · 未冻结）
```

## 1. 阶段依赖链

```text
P13 权限词表 → P14 主体边界 → P15 事件基础设施 → P16 Agent Runtime →
P17 identity/tenant/space runtime → P18 control plane → P19 event activation decision →
P20 首个业务模块（待选定）
```

## 2. 业务模块必须依赖（不得重建）

```text
identity/session（P14/P17）· tenant/space 上下文（P17）· 结构生命周期（P18 control plane）·
membership/role（P17 + P18 角色自举）· canonical 授权（P13）· audit_logs（append-only）·
events/consumer（P15 · 当前未激活）
⇒ 业务模块不得自建 users/tenants/spaces/roles/membership/authorization 第二套系统
```

## 3. 边界

```text
业务表：若需要，属**新 schema** ⇒ 必须独立 Human Decision（不得随模块实现顺带建表）
业务 API：必须走 use-case 层 + canonical 授权 + audit；不得绕过 P17 上下文
业务事件：必须满足 P19-D02…D18 后才可激活（P19-D01 OPTION D）
业务 worker：复用 P15 consumer；不得新建第二套投递机制
```

## 4. 未来依赖（模块选定后）

```text
模块范围冻结 → 实体/表决策 → 授权映射（resource_type/permission）→ 事件决定（audit vs event）→
测试矩阵 → 验收 → 发布
```

**END OF P20 DEPENDENCY MAP（未冻结；2026-10-01）**
