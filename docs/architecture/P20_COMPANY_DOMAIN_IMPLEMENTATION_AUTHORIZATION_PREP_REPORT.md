# P20 COMPANY DOMAIN IMPLEMENTATION AUTHORIZATION PREP REPORT

```yaml
Stage: P20 Company Domain Implementation — AUTHORIZATION PREP (documentation only)
Baseline: UAP-V0.1.17-P18-CONTROL-PLANE (08a0485b) + PDL Appendix AF + 0019_p20_company (ACCEPTED)

Implementation readiness: BLOCKED
  Reason: 2 项 Human Decision 未决（GAP-G1 权限授予时机与载体 · GAP-G2 集合资源投影归属与时机）

Migration: DONE
Schema: FROZEN
Domain: NOT IMPLEMENTED
API: NOT IMPLEMENTED
Event: NOT IMPLEMENTED
Worker: NOT IMPLEMENTED
Commit: NO
Tag: NO
Push: NO
Hard Stop: ACTIVE
```

## 1. CURRENT BASELINE REPORT（Phase 0 · 只读实测）

```text
git baseline
  HEAD = 08a0485 release: UAP v0.1.17 P18 control plane · staged = 0

权威文档
  PDL 附录 AF = 存在（P20 COMPANY DOMAIN DECISION FREEZE · D-P20D-01…11）
  P20_COMPANY_DOMAIN_DECISION_FREEZE_REPORT.md = 存在
  0019_p20_company migration = 存在 · sha256 3F4767B9CBA7550C4676F783222C69AEB23DCDCFA6CB678231C2332C756828F0
  alembic heads = ['0019_p20_company']（单 head）

数据库事实（一次性隔离库实测 · 创建→验证→DROP）
  permissions            = 23（平台 12 + Company 11）
  company permissions    = 11
  acl_subject_types      = 3（USER / ROLE / AGENT）
  roles                  = 1（与共享库一致 → unchanged）
  role_permissions       = 12（Company 相关 = 0 → 未授予）
  company 表             = 2（company_employees / company_assignments）
  events                 = 0 · production allowlist = EMPTY
  uap_runtime Company 授权 = INSERT,SELECT,UPDATE（无 DELETE）

架构守卫
  Core → Domain = 0       PASS（tests/architecture/test_dependency_rules.py = 14 passed）
  domains 纯度守卫         PASS（无 sqlalchemy / 无 "create table" / 无 services|infrastructure 导入）

常驻环境未受影响
  共享测试库 uap_b1_test = 0017_p13_seed · permissions 12 · company 表 0 · events 0
  正式库 uap = 0 public 表 · 探针库已 DROP · 无残留临时库
```

## 2. Phase 1 交付物

```text
docs/architecture/P20_COMPANY_DOMAIN_IMPLEMENTATION_CONTRACT.md
  §1 Domain Boundary（domains/company/ 允许/禁止项 + 建议模块布局）
  §2 Service Boundary（services/company/ 职责与禁令）
  §3 Repository Contract（EmployeeRepository / AssignmentRepository / ResourceProjectionPort · 仅接口）
  §4 Use Case Matrix（10 个用例 × 权限键 × 资源目标 × 授权点 × 审计 action × 事务要求）
  §5 Resource Projection Contract（resource_type / natural_key / tenant scope / instance scope=NONE）
  §6 Audit Contract（8 条变更 action · 同事务 · 无事件）
  §7 Error Contract（域/服务错误码 + DB 约束映射 + 禁止泄露项）
  §8 Test Contract（L1–L5 测试层级设计 · 本轮不创建测试文件）
  §9 实现顺序建议 · §10 可追溯性（契约 ↔ D-P20D-01…11）
```

## 3. Phase 2 交付物（未决事项）

```text
docs/architecture/P20_DOMAIN_IMPLEMENTATION_GAP_REPORT.md
  G1 [阻断] 权限授予时机与载体（迁移 0020 / 受控脚本 / 实现轮一次性动作；授予范围 11 or 6）
  G2 [阻断] 集合资源投影归属与时机（首写同事务自建 / 控制面扩展 / 运维 backfill）
  G3 [待确认] manifest 与 manifest 守卫的修改授权（AF D-P20D-10 明确需显式授权）
  G7 [待确认] 共享测试库是否迁移到 0019
  G8 [待确认] V1 是否含 list 用例（当前 11 条权限键中 5 条不使用：list×2 · delete×2 · admin）
  R1–R4 [已解析] natural_key 取值 · 仓储实现落点 · 审计形态 · 生命周期门禁
```

## 4. 就绪性判定

```text
设计侧：完成 —— 契约已覆盖 Domain/Service/Repository/UseCase/Projection/Audit/Error/Test 八个契约域，
        且与 D-P20D-01…11 及 0019 结构逐条可追溯
运行侧：未就绪 —— 无权限授予（G1）则所有用例恒 DENY；无投影归属（G2）则 create 用例无法构造授权目标

⇒ Implementation readiness = BLOCKED（等待 G1 / G2 的 Human Decision）
⇒ 即使授权，也只在 G1/G2 裁定后才可能产出"可授权 + 可审计"的端到端证据
```

## 5. 本轮未执行（边界声明）

```text
未修改任何 Python 代码（core / services / domains / infrastructure / apps / tests 零改动）·
未创建 domain implementation / service / use_case / repository / API / Worker / Event ·
未修改 manifest 或架构守卫 · 未修改 migration · 未修改数据库 ·
未 GRANT / REVOKE · 未 seed role permission · 未创建任何 resources 或业务数据行 ·
未创建任何测试文件 · 未 commit / tag / push
本轮仓库写入仅 3 份文档（本报告 + 实现契约 + 缺口报告）
```

```java
P20 COMPANY DOMAIN DECISION = FROZEN
P20 DOMAIN IMPLEMENTATION = NOT AUTHORIZED
P20 API = NOT AUTHORIZED
P20 EVENT = NOT AUTHORIZED
P20 WORKER = NOT AUTHORIZED
COMMIT/TAG/PUSH = NO
HARD STOP = ACTIVE
```

```text
下一阶段（须独立授权）：P20 COMPANY DOMAIN IMPLEMENTATION AUTHORIZATION
  前置：先裁定 GAP-G1 与 GAP-G2（并确认 G3 / G7 / G8）
  届时范围：domain contracts · repository interfaces · services/use_cases ·
            authorization integration · tests（API / Worker / Event 仍不在范围内）
  禁止：因本准备报告自动进入实现
```

**END OF P20 COMPANY DOMAIN IMPLEMENTATION AUTHORIZATION PREP REPORT（Implementation readiness = BLOCKED（G1/G2 未决）· Migration DONE · Schema FROZEN · Domain/API/Event 未实现 · 未 commit；2026-10-02）**
