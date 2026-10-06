# UAP PROJECT MASTER DOSSIER

> **Continuity aid only**（跨会话延续用途）。本文件**不是** architecture authority、decision authority、
schema authority，也不替代任何 contract 或 `PLATFORM_DECISION_LOG.md`。权威顺序：
PDL → 各阶段 Implementation Contract → 各阶段 Evidence → 本 dossier。

```text
最后更新 = 2026-10-02（P20 OPT-2 BLOCKER RESOLUTION 之后）
```

## 1. Project Identity

```text
项目 = UAP（Universal AI Platform）· 业务无关的 agent 平台核心
仓库 = https://github.com/jayfeng6848-ctrl/UAP
当前 release = UAP-V0.1.17-P18-CONTROL-PLANE（RELEASED）
release commit = 08a0485babf0560bc8b7d306c31361b1c1d8bdb5
release tree   = d0af7d5ca181df5872c5af67cf73ae01f2d87d4c
tag object     = 753610cdbd67eb791a4041f70694e8ffba82cac（annotated · 16 tags）
主线 = origin/main = 08a0485b
```

## 2. Architecture Principles

```text
分层   = core（契约/纯逻辑）→ services（编排）→ infrastructure（持久化）→ apps（传输）· Core → Domain = 0
四层 DB 权威（不可混同）：
  uap_migrator  = schema authority
  uap_bootstrap = one-time platform bootstrap authority
  uap_control   = structural control-plane authority（P18）
  uap_runtime   = ordinary runtime authority
授权   = 唯一 canonical AuthorizationService（RBAC + ACL + Policy；DENY 优先；默认拒绝；无缓存）
审计   = audit_logs append-only（结构/成员/授权变更记录）
事件   = events 表 + consumer kernel（claim/lease/heartbeat/recovery）· 当前未激活
原则   = 最小权限 · 默认拒绝 · 无隐式继承（owner ≠ 授权）· context ≠ authorization · visibility ≠ authorization
```

## 3. Phase History（accepted / released）

```text
P13  authorization vocabulary（permissions 12 · acl_subject_types 3 · platform_admin seed）
P14  database trust boundary（6 主体 → P18 后 7 主体 · uap_runtime 最小面）· RELEASED
P15  event / consumer foundation（events + kernel；Allowlist EMPTY）· RELEASED
P16  agent runtime（Agent Run ledger · ToolGate 单一授权路径 · 0018）· RELEASED（0.1.15）
P17  identity / tenant / space runtime（context · membership · canonical authz · 资源投影）· RELEASED（0.1.16）
P18  control plane / tenant-space lifecycle（uap_control · provisioning · lifecycle · D14 门禁）· RELEASED（0.1.17）
P19  production event activation = DECISION FROZEN（OPTION D · 未激活 · 未实现）
P20 SCHEMA = DECISION FROZEN（Department = Space · 2 张业务表 · Employee ≠ User · 无物理 DELETE · 预定 migration 0019_p20_company（未授权执行）· domains/company/）
P20  first business module = DECISION FROZEN（A1 = Company · tenant=组织根 / space=部门 · 无平台外主体 · 需独立持久化模型（非立即 migration）· 复用 canonical 12 actions · 最小 Employee+Organization View/Assignment+授权+审计 · 不要求生产事件 · domains/company/）
P20  migration blocker = RESOLVED（OPT-2 · PDL 附录 AE · D-P20S-16 = FROZEN：assignment 租户结构一致性触发器获 schema 级授权）· 0019 = 未创建 · 迁移执行 = 未授权 · 实现内容 = 无
```

## 4. Current Release

```text
Version = 0.1.17 · Tag = UAP-V0.1.17-P18-CONTROL-PLANE · Commit = 08a0485b · Tree = d0af7d5c
Migration head = 0018_p16_agent_runtime（无 0019）· permissions = 12
P20 migration = 已解锁（OPT-2）但未创建 / 未执行 / 未授权
```

## 5. Current Frozen Decisions（摘要 · 权威在 PDL）

```text
PDL 附录 A–AA（P13…P18）+ 附录 AB（P19）构成当前冻结决策集合
P18 = D01…D14 + Q14…Q20（附录 Z）· P18-AUTH-CLARIFICATION-01（附录 AA · B′）
P19 = D01…D21（附录 AB）：P19-D01 = OPTION D ⇒ 契约冻结、**激活未授权**、Allowlist 保持 EMPTY
P20 = 附录 AC / AD（首业务模块 + schema 冻结）+ 附录 AE（D-P20S-16 = OPT-2 阻断解决）
```

## 6. Security Anchors

```text
uap_runtime = 56 grants（tenants/spaces = SELECT only；无 DELETE on events/audit）
uap_control = 23 grants（写面 INSERT/UPDATE 限定 · 无任何 DELETE · 无 ACL/权限登记表写）
uap_migrator = 245 · uap_app = 7 · default ACL = 0 · public schema PUBLIC grants = 0
角色 7 个：uap · uap_app · uap_bootstrap · uap_control · uap_migrator · uap_runtime · uap_seed
Formal DB（uap）= 0 public 表（未使用）
```

## 7. Current Findings

```text
F-P18-I-01…I-04 = ALL RESOLVED（role provisioning · pre-resource 授权 · I-03 一致性（B′）· I-04 主体验分离）
P19 GAP-1…GAP-5 = OPEN（功能性缺口：无生产者 / 无合格 handler / 无 event type 契约 /
                        租户空值与生命周期语义未决 / 无下游订阅者）⇒ 因此激活未授权
```

## 8. Current Deferred Debt

```text
F-P18-S-01  uap_runtime 保留 P14 遗留的 resources INSERT/UPDATE（未使用 · 未撤销 · 未来 hardening）
F-P18-D-02  tenant membership 重邀请语义（removed 仍占唯一键）· 未来独立决策
OI-G-4      build-info 历史缺陷 · 未修（forbidden test 保持 0 执行）
```

## 9. Production Event State

```text
Allowlist = EMPTY · Handlers = 0 · events 行数 = 0 · 生产者为 0
Activation = NOT AUTHORIZED（须先满足 P19-D02/D18 的资格条件并由新的 Human Decision 授权）
```

## 10. Current Authorized Stage

```text
P19 = DECISION FROZEN（无实现授权）
P20 = SCHEMA + OPT-2 BLOCKER RESOLUTION FROZEN（结构性触发器获 schema 级授权 · 0019 未创建 · 无实现授权）
下一阶段候选：P20 MIGRATION AUTHORIZATION — RETRY AFTER OPT-2 FREEZE（需独立指令 · 授权上限见附录 AE.5）
              或 P19 IMPLEMENTATION（仅在按 D02/D18 逐类型裁定并补齐 GAP-1…5 后）
```

## 11. Next Human Decision

```text
当前待决：P20 MIGRATION AUTHORIZATION — RETRY AFTER OPT-2 FREEZE（0019_p20_company 实现授权）
建议议题：① 是否为某个具体 event type 补齐 producer/handler/幂等/授权/租户语义并激活；
          ② 或进入 P19 契约冻结后的实现轮（仅限非激活部分，如 envelope 契约校验）；
          ③ 或 Company 领域模块实现轮（0019 迁移之后：domain/core 契约 · API · 授权用例）。
```

**END OF UAP PROJECT MASTER DOSSIER（continuity aid · 2026-10-02 · 反映 P18 RELEASED(0.1.17) · P19 DECISION FROZEN(未激活) · P20 SCHEMA FROZEN + OPT-2 阻断已解决（0019 未创建/未授权））**
