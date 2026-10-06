# UAP — P13 ACCEPTANCE MATRIX（Seed / Bootstrap · PREP 层）

> ## 状态
>
> ```text
> READ-ONLY · DESIGN PREPARATION
> P13 DECISION FREEZE = NOT YET
> P13 IMPLEMENTATION  = NOT AUTHORIZED
> ```
>
> **状态词表**：`PENDING`（OQ 未裁定）· `PASSED`（只读核验通过 / **已由 `D-P13-*` 裁定**）·
> `PROPOSED`（方向已登记待裁）· `BLOCKED`（阻塞，如 OQ-12）。
> **§0 口径声明**：状态**一律从最后一格（状态单元）解析**（去 `` ` ``/`*`、归一空白、casefold），
> **禁止**扫描整行正文判定（bilateral normalization）。
> 指令节引用（§n）= `# UAP P13 PREP — SEED / BOOTSTRAP` 的节号。

---

## 1. SEED — 种子清单完备性（OQ-P13-01）

| ID | 检查 | 权威 / 证据 | 状态 |
|---|---|---|---|
| SEED-01 | SEED MATRIX 覆盖 SEED_STRATEGY §1 十步全部条目（S-01…S-11） | PREP §3 | **PASSED** |
| SEED-02 | 每条 seed 含 15 字段登记（identity/columns/values/purpose/authority/ownership/dependency/idempotency/uniqueness/FK/trigger/index/downgrade…） | PREP §3 | **PASSED** |
| SEED-03 | permissions canonical list **已裁定 = 12 项**（取代 13 项草稿；`manage→admin` · `write→update`；排除 `system.*`；无 deny 行） | `D-P13-01`（2026-09-26） | **PASSED** |
| SEED-04 | MANDATORY / OPTIONAL / TEST FIXTURE / RUNTIME 四分类完成 | PREP §3 | **PASSED** |

## 2. OWN — 所有权映射（OQ-P13-02/05/06/07/08）

| ID | 检查 | 权威 / 证据 | 状态 |
|---|---|---|---|
| OWN-01 | `platform_admin` = 0005-owned（实测 1 行）；P13 不重复纳入 | 指令 §6 · PREP §4 | **PASSED** |
| OWN-02 | `platform_state` = 0006-owned（uninitialized） | R5 · 实测 | **PASSED** |
| OWN-03 | `platform_memberships` 首行 = bootstrap CLI（R4/R5），P13 禁写（`ACCEPT OPTION A`） | `D-P13-07`（2026-09-26） | **PASSED** |
| OWN-04 | tenant/space 四角色 = onboarding/补种模式；**P13 零播种**（无 bootstrap tenant；无 membership） | `D-P13-02` · `D-P13-05`(B) · `D-P13-08`(B) | **PASSED** |
| OWN-05 | 首管理员凭据 = onboarding；seed 零凭据（**FROZEN**：identity row allowed · credentials forbidden · 可登录 ≠ 主体记录） | OQ-06/13（FROZEN 2026-09-26） | **PASSED** |

## 3. DEP — 依赖 / 顺序（OQ-P13-09）

| ID | 检查 | 权威 / 证据 | 状态 |
|---|---|---|---|
| DEP-01 | 静态依赖图无环（PREP §5）· 无 deferred FK | 实测 `condeferrable=false` | **PASSED** |
| DEP-02 | 顺序 = SEED_STRATEGY §1 十步序为**唯一拓扑**（step 4 / 6 / 9 = no seed） | `D-P13-09`(A) | **PASSED** |
| DEP-03 | 无循环 seed dependency | PREP §5 | **PASSED** |

## 4. TRG — Trigger 兼容（OQ-P13-03/11）

| ID | 检查 | 权威 / 证据 | 状态 |
|---|---|---|---|
| TRG-01 | G/H/I/J 对 seed 零副作用（语义逐项实测） | PREP §5 | **PASSED** |
| TRG-02 | C2 拦 registry INSERT ⇒ seed = **migration-controlled path**（FROZEN：runtime INSERT FORBIDDEN · C2 保持/不得长期关闭；具体机制在实施契约冻结） | OQ-03（FROZEN 2026-09-26） | **PASSED** |
| TRG-03 | 其余形状/一致性触发器对 seed 行为天然满足（B/C/D/E/F/F2/tm 族） | PREP §5 | **PASSED** |
| TRG-04 | P11 triggers 先于 seed 就位（已满足：0014 在链上） | `D-P11-12` | **PASSED** |

## 5. IDX — Index readiness（OQ / 指令 §12）

| ID | 检查 | 权威 / 证据 | 状态 |
|---|---|---|---|
| IDX-01 | P12 = complete（19 索引在位 · T-1 ABSENT） | 实测 @0015 | **PASSED** |
| IDX-02 | seed 查询/唯一性路径由 PK/UQ/P12 承载 ⇒ 无 seed-specific 索引需求 | PREP §5 | **PASSED** |

## 6. IDEM — 幂等（OQ-P13-10）

| ID | 检查 | 权威 / 证据 | 状态 |
|---|---|---|---|
| IDEM-01 | registry/permissions = `WHERE NOT EXISTS`（§6/0005 先例）；membership 类冲突即**显式失败**；**禁**统一 `ON CONFLICT DO NOTHING` | `D-P13-10`(A) | **PASSED** |
| IDEM-02 | 禁止无证据统一 `ON CONFLICT DO NOTHING` | 指令 §10 | **PASSED** |

## 7. SEC — Security（OQ-P13-13）

| ID | 检查 | 权威 / 证据 | 状态 |
|---|---|---|---|
| SEC-01 | credentials = 0 · plaintext secrets = 0 · fabricated passwords = 0（**FROZEN** 2026-09-26） | OQ-13 | **PASSED** |
| SEC-02 | 「首个可登录主体」与「P13 创建主体记录」区分；登录能力 = onboarding / runtime credential establishment（**FROZEN** 2026-09-26） | OQ-06 | **PASSED** |

## 8. DOWNG — Downgrade / Runtime-data protection（OQ-P13-12/14 · **BLOCKING**）

| ID | 检查 | 权威 / 证据 | 状态 |
|---|---|---|---|
| DOWNG-01 | 可精确识别行（registry/permissions/系统角色）与不可区分行（首租户/用户/空间）已分列 | PREP §7 | **PASSED** |
| DOWNG-02 | 降级 = **FAIL-CLOSED**（无法证明 clean baseline ⇒ RAISE ⇒ 整条回滚 ⇒ 0 DELETE）；**禁** `DELETE WHERE key IN (...)` 作默认行为；**禁**新增 ownership marker 列 | `D-P13-12`（`ACCEPT OPTION C`） | **PASSED** |
| DOWNG-03 | runtime 数据保护 = natural-key filtering + existing FK protection + `D-P13-12` fail-closed + pre-downgrade verification；**不新增** schema marker | `D-P13-14`(A) | **PASSED** |

## 9. XSCAN — 跨决策扫描（指令 §2 / Charter §7）

| ID | 检查 | 权威 / 证据 | 状态 |
|---|---|---|---|
| XSCAN-01 | 全部权威材料已读（PDL · 三份 IMPLEMENTATION_CONTRACT · SEED_STRATEGY · SCHEMA_DEPENDENCY · CONSTRAINT_MATRIX · TRIGGER_INVENTORY · CORE_DOMAIN_MODEL · ER_MODEL · ARCHITECTURE · DEPENDENCY_RULES） | PREP §2/§9 | **PASSED** |
| XSCAN-02 | 全文关键词搜索完成（seed/bootstrap/INSERT INTO/system role/五角色/registry…） | PREP §9 | **PASSED** |
| XSCAN-03 | 陈旧声明扫描：raw 11+ · adjudicated 0（全部为现行有效描述） | PREP §9 | **PASSED** |
| XSCAN-04 | supersession 恒 = 1 · 无新增决策 · 无冻结正文改写 | PREP §9 | **PASSED** |
| XSCAN-05 | D-PLAT-11 × R4/R5 张力（「可登录」vs「无凭据」）已登记为 OQ-06 | PREP §8 | **PASSED** |

## 10. SCOPE / GATE — 本轮只读核验

| ID | 检查 | 证据 | 状态 |
|---|---|---|---|
| SCOPE-01 | `0016+` = ABSENT · versions = 15 · 单头 0015 · 0010–0015 sha 未变 | harness | **PASSED** |
| SCOPE-02 | INSERT/UPDATE/DELETE/DDL/DML/migration/code/test/config = 0 | harness | **PASSED** |
| SCOPE-03 | 本轮新增文件 = 仅 3 份设计文档（+仓库外 harness/证据） | harness | **PASSED** |
| SCOPE-04 | commit = 0 · tag = 0 · push = 0 | harness | **PASSED** |
| GATE-01 | `P13 DECISION FREEZE = NOT YET` · `P13 IMPLEMENTATION = NOT AUTHORIZED` · `Runtime = NOT AUTHORIZED` | 指令 §18 | **PASSED** |

## 11. TRACE — OQ ↔ Matrix 100% 追溯

| TRACE | OQ | Matrix 行 |
|---|---|---|
| TRACE-01 | OQ-P13-01 canonical inventory | SEED-01..04 |
| TRACE-02 | OQ-P13-02 system role ownership | OWN-01/04 |
| TRACE-03 | OQ-P13-03 acl_subject_types seed | TRG-02 · SEED-01 |
| TRACE-04 | OQ-P13-04 agent subject seed | SEED-01（S-13 = 不建实际 Agent）· OWN-05 |
| TRACE-05 | OQ-P13-05 bootstrap tenant | OWN-04 · DEP-02 · DOWNG-01 |
| TRACE-06 | OQ-P13-06 bootstrap user | OWN-05 · SEC-02 |
| TRACE-07 | OQ-P13-07 platform membership | OWN-03 |
| TRACE-08 | OQ-P13-08 tenant/space membership | OWN-04 · DEP-02 |
| TRACE-09 | OQ-P13-09 seed ordering | DEP-01..03 |
| TRACE-10 | OQ-P13-10 idempotency | IDEM-01/02 |
| TRACE-11 | OQ-P13-11 trigger interaction | TRG-01..04 |
| TRACE-12 | OQ-P13-12 downgrade safety | DOWNG-01/02 |
| TRACE-13 | OQ-P13-13 environment secrets | SEC-01 |
| TRACE-14 | OQ-P13-14 runtime-data protection | DOWNG-03 |

## 12. 汇总（**脚本实测** · `DECISION RESOLUTION EXECUTION` 复核；TRACE 表不计状态）

| 分组 | 行数 | `PASSED` | `PROPOSED` | `PENDING/BLOCKED` |
|---|---|---|---|---|
| DEP | 3 | 3 | 0 | 0 |
| DOWNG | 3 | 3 | 0 | 0 |
| GATE | 1 | 1 | 0 | 0 |
| IDEM | 2 | 2 | 0 | 0 |
| IDX | 2 | 2 | 0 | 0 |
| OWN | 5 | 5 | 0 | 0 |
| SCOPE | 4 | 4 | 0 | 0 |
| SEC | 2 | 2 | 0 | 0 |
| SEED | 4 | 4 | 0 | 0 |
| TRG | 4 | 4 | 0 | 0 |
| XSCAN | 5 | 5 | 0 | 0 |
| **合计** | **35** | **35** | **0** | **0** |

**GATE 结论（2026-09-26 **DECISION RESOLUTION EXECUTION**）**：`OQ` 14 项**全部已裁定** ⇒ `D-P13-01`…`D-P13-14` **已写入 PDL**（附录 J）·
**`P13 DECISION FREEZE = PASS`**；`P13 IMPLEMENTATION = NOT AUTHORIZED`（须再次显式授权）·
未授权面：`0016+ = ABSENT` · `DDL/DML = 0` · `commit/tag/push = 0`。

> 历史（Freeze Gate 时点）：FROZEN 3 · PENDING 10 · BLOCKING 1 ⇒ 14/14 未满足 ⇒ `BLOCKED`（登记于 PDL 附录 I.10）。

**END OF P13 ACCEPTANCE MATRIX（2026-09-26 · `DECISION RESOLUTION EXECUTION` · `P13 DECISION FREEZE = PASS`）**
