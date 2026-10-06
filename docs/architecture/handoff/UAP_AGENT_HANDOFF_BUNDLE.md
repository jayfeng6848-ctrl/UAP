# UAP_AGENT_HANDOFF_BUNDLE — 一页式完整交接文档

> 2026-09-27 · STRICT READ-ONLY TRANSFER MODE 生成 · 供全新 Agent 直接接管 · 与 `handoff/00–15` 配套（本文件为合集）

---

# PART 1 · Project（UAP 是什么）

**UAP = 通用平台基座（platform foundation）**：业务无关的多租户 AI Agent 平台底座。
不是单体业务系统、不是 Todo/Chat/家庭助手（小智/家庭小窝为独立代码线，与 UAP 完全隔离）。
未来可插拔板块：Company / Commercial / Entertainment / Industry customization / AI Gateway（已建）。
核心目标：practical · usable · stable · reliable · privacy/security · multi-user · multi-device · pluggable · external AI API capable。
工作方式：分阶段 Stop-Gated 治理（PREP 只读 → Human Freeze → Gate → 显式授权 → 实施 → Gate → 另授权 commit/tag）；决策冻结于 `docs/architecture/PLATFORM_DECISION_LOG.md`（sha256[:16] `a83fde5c57605252`）。

# PART 2 · Architecture（边界）

分层 `apps→agent→services→intelligence→core→infrastructure`，domains 旁挂；**Core→Domain 越界 = 0（Guard = 9 passed，AST 强制）**；core 禁行业词；厂商 SDK 只经 Provider Adapter；Agent 禁直连 DB；services/ 为持久化唯一归属；仅文档规则必须落为 tests/architecture。
数据铁律：UUIDv7 · timestamptz(3) · 默认 deny/deny 优先/FAIL CLOSED · events=outbox · audit_logs 不可变 · 删除 RESTRICT。
**最重要安全边界 = migration/runtime 身份分离**：

```text
DATABASE_URL               → runtime → settings.DATABASE_URL → uap_app
UAP_MIGRATION_DATABASE_URL → Alembic → uap_migrator（env.py FAIL-CLOSED + 角色断言）
DATABASE_URL ↛ migration；UAP_MIGRATION_DATABASE_URL ↛ runtime（双向禁 fallback）
```

⚠️ env.py 当前带 P0 缺陷（PART 7），修复未授权前不得触碰。

# PART 3 · Frozen Decisions（不得重新解释）

**D-OP101-01…14（RM-D/NOSUPERUSER/0016 归属/deployment 预置/CP-F+CC-7/readonly DEFER/最小 grants/DB-enforced no DDL/full ownership/双键/testkit 双 DSN/REVOKE+retain role/isolation 判据/guard rationale）= FROZEN**（PDL 附录 L）。
**D-P13-01…14 = FROZEN**：12 permission seeds（tenant.read/tenant.admin/space.read/space.admin/member.read/member.admin/resource.read/resource.update/resource.delete/agent.execute/tool.execute/audit.read）；`D-P13-04=A` 仅注册 agent subject type（零 Agents/Versions/Permissions/Runs）；`D-P13-05=B` 无 bootstrap tenant；`D-P13-07=A` 无 platform_memberships；`D-P13-08=B` 无 tenant memberships；`D-P13-12=C` FAIL-CLOSED downgrade；`D-P13-03/09/10/11/13/14`（migration-controlled seed 路径/十步拓扑/WHERE NOT EXISTS 幂等/39 triggers 全启用下执行/credentials=0/不新增 marker）。
**D-P13-15（Trust Boundary Precondition）**：允许未来受信 migration context 建 system registry seed，**前提身份隔离已成立**；does NOT authorize migration / C2 change / implementation。
**BATCH-C Decision（消息通道 8/8+3/3 · Record sha256[:16] `9efbc3fe031387d0`）**：START=AUTHORIZED；CF-C-1=A（仅 uap_migrator 窗口期 schema CREATE）·CF-C-2=A（NOSUPERUSER 保持）·CF-C-3=A（ownership 不变）·CF-C-4=C（integration 延后 BATCH-D）·CC-7 MODEL=CUSTOM（=CP-F 信任模型；形态 → INLINE）·ROLE POLICY=A（uap_migrator-only）·OWNERSHIP=A（preserve）·CF-C-5=B（窗口期 GRANT→verify→REVOKE→retain role）·CF-C-6=A（0016 仅 CC-7）·CF-C-7=CONFIRM。

# PART 4 · Completed Work（里程碑）

```text
72ade9f INIT-DB-VALIDATED → e9766fb V0.1.4 RESOURCE-ACL(0007) → d8c6cd2 V0.1.5 timestamptz(3)(0009)
→ 964ea2c recover baseline → a64c06b V0.1.6 AI-GATEWAY(0010：73列/8FK/2UQ/8CK/5索引/4触发器/分区/38-38)
→ eb6d4cb V0.1.7 GOVERNANCE-GATE → 71c36c1 V0.1.7 P09(0011：4表/54列/语义冻结)
→ 034ee97 V0.1.8 AUTHORIZATION（HEAD · tag object e9c83330384bc1d7582b0ae8a3bf857470063161）
P10(0013 ✅12/12) → P11(0014 ✅20/20) → P12(0015 ✅20/20 · head) · 全量回归 636 passed（此后 integration 禁跑）
本周 OPEN-P10-1：BATCH-A PASS → BATCH-B FINAL PASS → BATCH-C BLOCKED
```

# PART 5 · Security（数据库安全基线 · 实测）

```text
角色 4：uap(superuser, deployment-ops authority) · uap_seed · uap_migrator · uap_app（后三 NOSUPERUSER 全 false）
membership 0 · default_acl 0
所有权 178/178（pg_class 156 + pg_proc 22）→ uap_migrator · residual 0
uap_app grants = 5（SCHEMA USAGE / alembic_version SELECT / audit_logs+分区 INSERT,SELECT）
uap_migrator CREATE on public = false（默认态；窗口期临时 true 必须回收）
OI-G-3 决定性证据：CREATE TABLE → denied；CREATE OR REPLACE 自有函数 → denied（仍需 schema CREATE）
C2 = enforce_acl_subject_types_protect（0007:78 首建 · 触发器 tg_acl_subject_types_protect · O）
     md5(pg_get_functiondef)=6867874166ae36966763c1026ab2af19 · 语义：runtime INSERT/DELETE 拒 + key 不可变
触发器 39（父级）· registry 0 行 · agents 族 0 行 · 正式库 uap 0 表
```

# PART 6 · Current State（当前真实状态）

```text
Git      HEAD 034ee97c315e5d483acb7ac4b7e8e0eb992ef10e · main · tags 8 · remote 0 · dirty 104（67??+36M+1D）
Migration 单头 0015_p12_indexes（活体一致）· .py 16（含未持久执行的 0016）· 0017 ABSENT
DB       uap_b1_test @0015 · 全锚点见 PART 5
未授权面 env.py 修改 · 0016 重执行 · 0017 · P13 · Runtime cutover · commit/tag/push
```

# PART 7 · Blocker（P0 · REAL · OPEN）

**0016 = CREATED（静态审计 PASS）/ NOT PERSISTED（upgrade 静默回滚）**。根因链：

```text
env.py:197 _assert_effective_role → SELECT current_user, session_user（configure 之前）
→ SA2.0 autobegin（隐式开事务）→ alembic migration.py:154 _in_external_transaction=True
→ begin_transaction() 返回 nullcontext → migration 执行（"Running upgrade" 打印）
→ COMMIT never called → 连接关闭 → DBAPI ROLLBACK → exit 0 静默"成功"
```

定性：**REAL ENGINEERING DEFECT · P0**（非 harness / 非环境 / 非损坏）。B-1/B-2 探针为 at-head no-op 恰好掩盖。
证据：`uap-stage3-evidence/batch_c_0016_implementation.log`（DBAPI/Context 层插桩）。
窗口已回收，基线完整恢复（version=0015 · C2 md5 未变 · CREATE=false · grants 5 · registry 0 行）。

# PART 8 · Fix Options（仅候选 · NOT AUTHORIZED）

Fix A（推荐 · 1 行）：env.py `:197` 断言后 `connection.rollback()`（归零 autobegin，交还 alembic 事务管理）。
Fix B：断言用独立短连接（+3~5 行）。CUSTOM：Human 自定义。
授权后强制序列：new baseline → gate → env.py fix → **真实前进证明（version 前移 + post-image 指纹 + 落库）** → 0016 upgrade → 探针矩阵 → downgrade（恢复 md5 68678741…）→ 再 upgrade → I01…I30 → REVOKE → 回归。

# PART 9 · Evidence（地图）

仓库外 `…\uap-stage3-evidence\`：`batch_a\`（17 工件 · A1–A5+GATE）· `batch_b\`（B1B2_probes/B1_role_assertion/B3_*/B4_gate/B5_gate/B6_final_gate）· 根目录（open_p10_1_* 全序列 Gate · batch_c_authz_request 86/86 · decision_review×3 40/40 · decision_register 39/39 · implementation_preflight 23/23 · **batch_c_0016_implementation.log（BLOCKER 插桩）** · `cc7_c2_functiondef_preflight.sql`）。
仓库内 `docs/architecture\`：REQUEST/BLOCK/RECORD/REVIEW/PRE-FLIGHT/BLOCKER REPORT + Contract + PDL + `handoff/`（00–15 + 本 BUNDLE）。

# PART 10 · Rules（10 条铁律 · 全文见 14）

1 PREP ≠ IMPLEMENTATION · 2 Human Decision ≠ inferred decision · 3 FROZEN 不得重新解释 ·
4 真实 blocker ⇒ STOP/REPORT/WAIT · 5 harness 缺陷与产品缺陷分开归因 ·
6 migration 序列（static audit→pre-image→窗口→identity probe→前进证明→rollback 证明→post-image）·
7 权限窗口 open→prove→execute→revoke→prove final · 8 禁 `import migrations_alembic.env` ·
9 会 reset 的 19 个测试禁跑（CF-C-4=C）· 10 绝不为 PASS 作弊（weaken/fallback/扩scope/藏失败）。
**探针铁律：必须断言 version 表前移 + 副作用落库；at-head no-op 探针 = 没测。**

# PART 11 · Next Action（唯一合法入口）

```text
P0 ENV FIX AUTHORIZATION PREP   ← 当前唯一合法下一步
P0 ENV FIX = NOT AUTHORIZED · 0016 REEXECUTION = NOT AUTHORIZED
BATCH-C CONTINUATION = BLOCKED · 0017 = NOT STARTED · P13 = NOT STARTED
授权后：P0 ENV FIX IMPLEMENTATION（序列见 PART 8）→ 不得直接进入 0017/P13
```

---

**END OF UAP_AGENT_HANDOFF_BUNDLE（2026-09-27 · `HANDOFF = COMPLETE` · `IMPLEMENTATION PERFORMED THIS ROUND = NO`）**
