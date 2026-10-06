# P20 DOMAIN IMPLEMENTATION GAP REPORT（Phase 2 · 未决事项 · 需 Human Decision）

```text
性质 = 缺口/未决事项报告；**本文件不裁定任何事项，也不实现任何内容**
依据 = PDL 附录 AF（D-P20D-01…11）+ P20_COMPANY_DOMAIN_IMPLEMENTATION_CONTRACT（本轮草案）+
       Phase 0 只读基线（本轮实测）
规则 = 需要 Human Decision 的事项一律 BLOCKED 处理，禁止自行补齐
```

## 1. 阻断实现授权的未决事项（必须裁定）

### G1 权限授予的时机与载体

```text
现状事实（本轮实测）
  * 0019 已 seed 11 条 Company 权限；role_permissions 中 Company 相关行 = 0
  * platform_admin 现有 12 条平台权限（role_permissions = 12）
  * 结论：在授予发生前，任何 Company 用例都会得到 DENY（默认拒绝）

已冻结（AF · D-P20D-01）
  platform_admin 先行持有 Company 权限；授予动作不在冻结轮执行，须由实现轮的独立授权完成

未定（需 Human Decision）
  ① 载体：新增迁移（如 0020_p20_domain_grants）追加 role_permissions allow 行
           ／ 受控运维脚本 ／ 并入实现轮一次性授权动作
  ② 范围：11 条全部授予 platform_admin，或仅授予实现轮实际使用的 6 条
  ③ 可逆性要求：是否需要与之配套的 downgrade（撤销 Company 授予）

影响
  未定 ⇒ 实现轮无法完成端到端验证（授权恒 DENY），无法产出 P20 DOMAIN 可用证据
```

### G2 集合资源投影的归属与创建时机

```text
现状事实（本轮实测）
  * resources 表存在；Company 相关投影行 = 0（从未创建）
  * 授权引擎按 resources.id 解析资源；缺失 = DENY，且不得运行时自愈补建（P17-AUTH-Q1）

已冻结（AF · D-P20D-02）
  tenant 级集合资源（每 tenant × 每 resource_type 一行）；投影必须与业务写入同事务完成；
  缺投影 = DENY；不需要新 GRANT（uap_runtime 已有 resources INSERT/UPDATE）

未定（需 Human Decision）
  ① 归属：业务首写同事务自建（services/company/projection.py）
          ／ 控制面 provisioning 扩展（触碰 P18 冻结范围）
          ／ 运维 backfill 预建 + 业务路径只读
  ② 时序冲突处理：若采用"业务首写自建"，与"缺投影 = DENY 且不得自愈"的冻结表述如何一致
     （例如：首写用例在授权之前无法引用集合资源 id ⇒ 需要 pre-resource 路径或预建策略）
  ③ 既有 tenant 的预建责任方（平台当前无自动 Company 投影路径）

影响
  未定 ⇒ 无法确定 create 类用例（E1/A1）的授权目标构造方式，契约 §5 无法落地
```

## 2. 需一并确认的事项（不阻断契约，但阻断对应步骤或事实同步）

```text
### G3 manifest 与架构守卫的修改授权
现状：`domains/company/manifest.py` 为 placeholder（tables=[]）；守卫
      `test_domain_manifests_are_placeholders` 断言所有域 status=placeholder 且 tables=[]。
AF：D-P20D-10 明确"修改 manifest 守卫需显式未来授权"。
需确认：① 何时改（实现轮 STEP 6 或更晚）② 改法（白名单已实现域 vs 保持全 placeholder）
       ③ 是否同步更新 manifest 的 tables/permissions 字段
影响：不动则 domains/company 元数据长期与 0019 事实不同步（仅在实现轮 STEP 6 触发）。

### G8 V1 用例范围（list 权限未使用）
现状：本轮指令给出的用例矩阵含 10 个用例（employee：create/read/update/suspend/terminate/bind_user；
      assignment：create/read/update/end_assignment），**未含 list**；
      而 0019 冻结了 company_employee.list / company_assignment.list 两条权限键。
结果：11 条权限键中 6 条被使用，5 条不使用（list×2 · delete×2 · admin×1）。
需确认：① V1 是否确实不提供 list 用例（若是，两条 list 权限键一并登记为 reserved）
       ② 若需要 list，应并入实现轮还是独立轮次（会影响 contract §4 与测试矩阵）

### G7 共享测试库策略
现状：uap_b1_test = 0017_p13_seed（company 表不存在）；0019 仅在一次性验证库中执行过。
需确认：① 保持共享库冻结（Company 测试使用一次性库）② 或迁移共享库到 0019（改变既有基线）
影响：影响实现轮集成测试的落点与证据形态（不影响契约设计）。
```

## 3. 已由冻结决策委派或先例解析（无需新决策 · 仅登记）

```text
R1 natural_key 取值 → 由本契约确定（AF D-P20D-02 明确"属实现细节，由实现轮契约确定"）
   契约取值：company_employee → `employees` · company_assignment → `assignments`
   依据：`uq_resources_natural (tenant_id, resource_type, natural_key)`；两类型各自命名空间
   说明：若 Human 另有命名偏好，属一次性修正，不影响语义

R2 仓储实现落点 → services/company/repository.py
   依据：既有守卫 G-4（domains 禁 import services/infrastructure）+ P16/P18 先例
        （services/agent/repository.py · services/control_plane/repository.py）
   说明：纯契约（ports）留在 domains/company/，实现留在 services/company/，无新语义

R3 审计形态 → 沿用 P18 先例（同事务 INSERT audit_logs；仅成功行，V1 不记录拒绝行）
   依据：AF D-P20D-09（无事件）+ D-P20S-11（复用 audit_logs）

R4 生命周期门禁 → tenant active 必需；涉及 space 的用例要求 space active
   依据：AF D-P20D-06（不修改 P18、不自动级联）+ P18-D14 门禁先例
```

## 4. 若未裁定即推进的后果（影响分析）

```text
不裁定 G1 ⇒ 域可编码但恒 DENY；无法产出"授权通过 + 审计落行"的端到端证据
            ⇒ 实现轮只能产出"结构正确但不可用"的代码
不裁定 G2 ⇒ create 用例无法确定授权目标（集合资源 id 从何而来）
            ⇒ 契约 §5 无法落地，E1/A1 无法通过授权
不裁定 G3 ⇒ domains/company 元数据与 0019 事实长期不一致（守卫仍绿，但描述失真）
不裁定 G8 ⇒ 5 条权限键长期无归属，验收时"覆盖率"口径不明
不裁定 G7 ⇒ 共享库基线与实现轮测试落点存在歧义
```

## 5. 声明

```text
本报告不裁定、不实现、不授予；未修改任何代码/测试/迁移/数据库/manifest/守卫；
未执行 GRANT/REVOKE；未 seed role_permission；未 commit / tag / push。
在 G1 与 G2 获得 Human Decision 之前：
  Implementation readiness = BLOCKED
  Domain Implementation    = NOT AUTHORIZED
```

**END OF P20 DOMAIN IMPLEMENTATION GAP REPORT（2 项阻断性未决 G1/G2 + 3 项待确认 G3/G7/G8 + 4 项已解析 R1–R4 · 禁止自行决定；2026-10-02）**
