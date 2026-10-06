# P11 — DECISION RESOLUTION PACKAGE（Triggers / Cross-table Constraints）

> **状态声明（先读）**
>
> ```text
> 本文档 = DECISION RESOLUTION PACKAGE（PREP 层）
> 本文档 = DECISION FREEZE APPLIED（2026-09-25）
> ```
>
> **更新（2026-09-25）**：Human 通过 `UAP P11 — HUMAN DECISION RESOLUTION` 逐项裁定 ——
> **14 项 OQ 全部 `FROZEN`，0 项未决**；`CF-1`…`CF-4` 亦已处置（`CF-1`/`CF-2`/`CF-3` CLARIFIED ·
> `CF-4` INTENTIONAL / FROZEN）。本文件已据此同步：`HUMAN DECISION` 由 `PENDING` 更新为**选定决策**，
> `STATUS` 由 `PROPOSED` 更新为 `FROZEN`（**14 / 14**）。
> **冻结正文写入 `PLATFORM_DECISION_LOG.md` 的 `D-P11-01`…`D-P11-14` —— 该处为唯一权威。**
>
> ⚠ **编号重映射（canonical，非静默）**：本轮 Human Decision 中
> **`OQ-P11-06` = Version Immutability（`K`）**、**`OQ-P11-07` = Tenant / Space / Authorization 边界**；
> PREP 轮此二主题的编号**相反**。**canonical 编号以 `D-P11-*` 为准**，本文件 §7/§8 已按 canonical 重排，
> 并在两节内各附重映射说明。
>
> **历史记录（上一轮原状，保留不改）**：本文件初次产出时为 READ-ONLY PREP 轮，
> 14 项 `HUMAN DECISION = PENDING` / `STATUS = PROPOSED`，**未写入** `PLATFORM_DECISION_LOG.md`。
>
> ⚠ **阅读约定**：§2–§15 的 `Current Evidence` / `Option A·B·C` / `Impact` / `Recommended Direction`
> 为**过程分析材料**（保留原貌）；其**结论**一律以 `D-P11-*` 与本节 `选定` 为准。
---

## 0.1 OQ 状态总表

| OQ | 主题 | HUMAN DECISION | STATUS |
|---|---|---|---|
| `OQ-P11-01` | trigger inventory ownership（含 6 项清单缺口处置） | **FROZEN** | `FROZEN` |
| `OQ-P11-02` | G/H/I/J exact semantics | **FROZEN** | `FROZEN` |
| `OQ-P11-03` | trigger timing | **FROZEN** | `FROZEN` |
| `OQ-P11-04` | trigger failure semantics | **FROZEN** | `FROZEN` |
| `OQ-P11-05` | cross-table consistency（V-4 不对称） | **FROZEN** | `FROZEN` |
| `OQ-P11-06` | Version immutability（`K` 不被重建/改语义/移所有权） | **FROZEN** | `FROZEN` |
| `OQ-P11-07` | Tenant / Space / Authorization 边界（授权决策不入 trigger） | **FROZEN** | `FROZEN` |
| `OQ-P11-08` | security-definer / search_path 政策 | **FROZEN** | `FROZEN` |
| `OQ-P11-09` | recursion policy（含 J 的受控 hidden DML） | **FROZEN** | `FROZEN` |
| `OQ-P11-10` | P10 / P11 ownership（四项禁止） | **FROZEN** | `FROZEN` |
| `OQ-P11-11` | P11 / P12 dependency | **FROZEN** | `FROZEN` |
| `OQ-P11-12` | P11 / P13 dependency | **FROZEN** | `FROZEN` |
| `OQ-P11-13` | **（本轮新增）** 清单缺口 `GAP-INV-1` 处置 | **FROZEN** | `FROZEN` |
| `OQ-P11-14` | **（本轮新增）** 既有 P3 文档不一致处置（`CF-2`/`CF-3`） | **FROZEN** | `FROZEN` |

> **统计**：`PENDING` **14** / `FROZEN` **0** / `DEFERRED` **0** / `SUPERSEDED` **0**。
> 指令 §9 要求至少覆盖 `OQ-P11-01`…`OQ-P11-12` ⇒ **12/12 覆盖**；新增 2 项**均有实测证据**（§4.3 / §11），**未凭空扩大**。

---

## 1. 已由冻结材料确定、**不设 OQ** 的约束（继承面）

| ID | 内容 | 来源 |
|---|---|---|
| **GP-1** | `P11 = Triggers / 跨表约束`；**必须在 seed 前全部就位** | `STEP1B_SCHEMA_DEPENDENCY.md:172` |
| **GP-2** | `D-PLAT-09` 路线 A：`P10 → P11 → P12 → P13 → Runtime`（**未 supersede**） | `D-PLAT-09` |
| **GP-3** | `P11` **纳入 G/H/I/J**，并在 P11 设计阶段冻结清单、依赖与验收范围 | `D-PLAT-10` |
| **GP-4** | `D-B14-02 = A`：G/H/I/J **最早 = P09 后**，**实际按 P11 集中**；`D-P09-06 = A`：G/H/I/J **不在 P09 实施** | `D-PLAT-10` 依据段 |
| **GP-5** | **`tg_audit_immutable` = P10-owned**；`P10 owns audit-local immutability` · `P11 owns remaining trigger / cross-table constraints` | `D-P10-11`（FROZEN，2026-09-25） |
| **GP-6** | `P00–P10 无 seed；P13 才有 seed`；trigger 必须**先于** P13 seed | `STEP1B_SCHEMA_DEPENDENCY.md:193` |
| **GP-7** | trigger **不得引用尚未存在的表**；`groups` 不出现在任何 trigger 依赖（P2-02） | `STEP1B_TRIGGER_INVENTORY.md` 首节 |
| **GP-8** | `G/H/I/J` 的**冻结语义**（表 / 时机 / 目的）见 `TRIGGER_INVENTORY` §G/§H/§I/§J —— 本轮**只确认，不改写** | 清单原文 |
| **GP-9** | **trigger ≠ authorization decision / ≠ ACL evaluation / ≠ application policy engine**；只承担**结构性不变量** | 本轮指令 §3 |
| **GP-10** | CASCADE 白名单（`CORE` §11.1）：被 ACL 引用的 role 一律 `RESTRICT`，业务实体禁止 CASCADE | `CORE_DOMAIN_MODEL` §11.1 |

---

## 2. `OQ-P11-01` — Trigger Inventory Ownership

| 字段 | 内容 |
|---|---|
| **Question** | A–M 清单的**归属**如何界定？已实现的 9 项（A/B/C/C2/D/E/F/F2/K）是否正式"归 P11 复核"？§4.3 的 **6 项清单缺口**（`GAP-INV-1`）如何登记？ |
| **Current Evidence** | **实测**：`CREATE TRIGGER` 语句 **24** 条，分布于 **8** 个 migration（0003–0008/0010/0011），全部为**内联实施**（建表时挂），**未走 P11**；A–M 清单中 **9 项已实现**、`L` = P10-owned、`M` 无对象、**`G/H/I/J` 未实现**；另有 **6 项已实现触发器不在 A–M 清单内**（§4.3）。清单成文（STEP 1-B/B0）**早于** 0005/0006/0011 |
| **Option A** | **P11 = 仅 G/H/I/J**（实施面）；已实现 9 项**仅做 P11 复核/验收登记**，不重做；6 项缺口**追加 append-only 注记**，**不重排** letter |
| **Option B** | P11 重建全部 trigger（含已实现者，统一在 P11 集中）⇒ 与 `DEPENDENCY §7`「可统一在 P11 执行（更易审计）」字面一致 |
| **Option C** | P11 仅做 G/H/I/J；6 项缺口**不提**（保持清单原状） |
| **Engineering Impact** | A：**零重做**、语义稳定、留痕完整；B：**会重写 24 条 DDL**（含 P09/P10 面）⇒ 巨大回归面 + 破坏"内联 phases"的既有落地；C：**清单长期不完整**（治理缺口） |
| **Security Impact** | A/C 不改变既有安全属性；B 在重写窗口内**可能出现不变量真空** |
| **Migration Impact** | A：0（仅新增 G/H/I/J）；B：需重写/迁移既有 trigger；C：0 |
| **Future Runtime Impact** | A 保持既有不变量在位；B 引入无必要风险 |
| **Recommended Direction** | **Option A**（技术后果：唯一不重做已验证 DDl 的选项；**6 项缺口以 append-only 注记留痕**；letter 编号**不重排**） |
| **Human Decision** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**A** — P11 canonical delivery scope = **G/H/I/J**（`tg_acl_subject_exists` · `tg_acl_user_hard_delete` · `tg_acl_role_delete_block` · `tg_agent_acl_expire`）；`A/B/C/C2/D/E/F/F2/K` = 已有阶段实现 · `L` = P10-owned · `M` = events 无 DB trigger；**不得再次实现或复制已有对象** |
| **Status** | `FROZEN` |

---

## 3. `OQ-P11-02` — G/H/I/J Exact Semantics

| 字段 | 内容 |
|---|---|
| **Question** | G/H/I/J 的**表 / 时机 / 目的**是否**逐字确认**为 `TRIGGER_INVENTORY` §G/§H/§I/§J 所载？ |
| **Current Evidence** | 清单原文（**本轮未凭记忆推导**）：<br>**G** `tg_acl_subject_exists` @ `resource_permissions` · BEFORE INSERT OR UPDATE OF `subject_type_id`,`subject_id` · subject 必须存在于对应表（user→users / role→roles / agent→agents）<br>**H** `tg_acl_user_hard_delete` @ `users` · AFTER DELETE · 清理该 user 的 ACL<br>**I** `tg_acl_role_delete_block` @ `roles` · BEFORE DELETE · 被 ACL 引用则 RAISE<br>**J** `tg_agent_acl_expire` @ `agents` · AFTER UPDATE OF status(→archived) 或 AFTER DELETE · 使该 agent 的 ACL 到期（`inherited=true, expires_at=now()`，**agent 行不删**）<br>**实测佐证**：`resource_permissions` 确有 `inherited boolean NOT NULL` + `expires_at timestamptz NULL`（0007）；`agents.status IN ('draft','active','disabled','archived')`（0011）；`acl_subject_types.key IN ('user','role','agent')`（0007） |
| **Option A** | **逐字确认**（四者表/时机/目的照原文冻结） |
| **Option B** | 确认但**修正一处**（须明确指出） |
| **Option C** | 重新设计（**无证据支持**） |
| **Engineering Impact** | A：与清单 + `B1-4_SCHEMA_DESIGN` §4.2/§4.3 一致；B/C 需文档修订 |
| **Security Impact** | A 维持既有冻结安全语义；C 无依据 |
| **Migration Impact** | A：4 个 trigger + 4 个 function；B/C：视修正而定 |
| **Future Runtime Impact** | 决定 G/H/I/J 的最终形态 |
| **Recommended Direction** | **Option A**（四者语义在 `TRIGGER_INVENTORY` + `B1-4_DEPENDENCY` §3 + `B1-4_SCHEMA_DESIGN` §4.2/§4.3 **三处一致**，且与实测列/状态值吻合 ⇒ **无修正依据**） |
| **Human Decision** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**A + Human 细化** — **G** `BEFORE INSERT OR UPDATE OF subject_type_id, subject_id` on `resource_permissions`（user→users / role→roles / agent→agents；拒绝不存在 subject；**不得引用 `groups`**；**不得承担 Authorization Evaluation**）；**H** `AFTER DELETE` on `users`（**仅硬删除流程**清理该 user ACL；**软删除不得通过 H 清理**）；**I** `BEFORE DELETE` on `roles`（被 ACL 引用则拒绝；语义 = **ACL reference protection**，**不是授权求值器**）；**J** `AFTER UPDATE OF status OR AFTER DELETE` on `agents`（`inherited=true` · `expires_at=now()`；**J 不负责删除 agent 本身**） |
| **Status** | `FROZEN` |

---

## 4. `OQ-P11-03` — Trigger Timing

| 字段 | 内容 |
|---|---|
| **Question** | G/I = `BEFORE`、H/J = `AFTER` 是否确认？**J 是否同时挂 `AFTER UPDATE OF status` 与 `AFTER DELETE`**？ |
| **Current Evidence** | 清单：G `BEFORE INSERT OR UPDATE OF …` · H `AFTER DELETE` · I `BEFORE DELETE` · J `AFTER UPDATE OF status（→archived）或 AFTER DELETE`。既有先例：BEFORE = 校验型（B/C/D/E/F/F2/C2/K）· AFTER = 清理型（无先例，H/J 为**首批 AFTER**） |
| **Option A** | **照清单**（G/I BEFORE · H/J AFTER；J 双事件 `UPDATE OF status` + `DELETE`） |
| **Option B** | J 仅挂 `AFTER UPDATE OF status`（不含 DELETE） |
| **Option C** | H/J 改为 BEFORE（**不可行**：BEFORE DELETE 无法在删除后清理子行） |
| **Engineering Impact** | A：与清单一致；B：agent 硬删时 ACL 悬空；C：语义错误 |
| **Security Impact** | A 完整覆盖生命周期；B 留下悬空 ACL 面（虽 agent 少硬删） |
| **Migration Impact** | A/B：各 1 个 trigger，事件数不同 |
| **Future Runtime Impact** | 决定归档/删除路径的语义完整性 |
| **Recommended Direction** | **Option A**（清单原文含 DELETE；且 agent **正常路径不删只归档**，DELETE 分支为 purge 兜底 ⇒ 保留更安全） |
| **Human Decision** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**A** — 保持既定 timing：**G = BEFORE · H = AFTER · I = BEFORE · J = AFTER**，不调整为其他相位（理由：保持既有 trigger contract 与当前行为语义一致） |
| **Status** | `FROZEN` |

---

## 5. `OQ-P11-04` — Trigger Failure Semantics

| 字段 | 内容 |
|---|---|
| **Question** | 失败语义是否统一为 `RAISE EXCEPTION` + 事务回滚？是否允许"吞异常"（`EXCEPTION WHEN … THEN NULL`）？ |
| **Current Evidence** | 既有先例：全部校验型 trigger 一律 `RAISE EXCEPTION`（全仓 `RAISE EXCEPTION` 共 **37** 处，分布于 0004/0005/0006/0007/0008/0011/0012）· 无一处吞异常；`D-AUTH-12` 冻结 **FAIL CLOSED** |
| **Option A** | **统一 `RAISE EXCEPTION`（fail closed）；禁止吞异常** |
| **Option B** | 允许个别吞异常（**无证据支持**） |
| **Option C** | 部分转为 WARNING（不阻断） |
| **Engineering Impact** | A：与既有先例 + `D-AUTH-12` 一致；B/C：引入静默失败面 |
| **Security Impact** | **A 最强**（不变量不可被绕过）；C 会使非法写入**静默入库** |
| **Migration Impact** | 0（语义层） |
| **Future Runtime Impact** | 决定调用方能否依赖"非法即失败" |
| **Recommended Direction** | **Option A**（技术后果：唯一与 `D-AUTH-12` 及 37 处既有先例一致的选项；**J 的 hidden DML 失败亦须回滚整体事务**） |
| **Human Decision** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**A** — 任何违反 P11 trigger invariant ⇒ **`RAISE` → 当前事务失败 → 当前相关 DML 回滚**；**H/J 的内部 DML 若失败 ⇒ 整个外层操作失败并回滚**；**禁止** `silently ignore` / `warn-only` / `partial success` / `best-effort continuation` |
| **Status** | `FROZEN` |

---

## 6. `OQ-P11-05` — Cross-table Consistency（**V-4 不对称**）

| 字段 | 内容 |
|---|---|
| **Question** | **同一类生命周期事件**在机制上不对称：**role 归档 → 授权层检查 `archived_at`（无 DB 动作）**，而 **agent 归档 → trigger J（UPDATE ACL）**。**保留不对称**还是**统一机制**？ |
| **Current Evidence** | 冻结原文佐证不对称：`B1-4_SCHEMA_DESIGN.md:136`「role 归档 \| deny 行不参与决策、allow 行保留 \| **授权层检查 `archived_at`** \| 授权层阶段 \| ✅（本阶段无 DB 动作）」；`:137`「agent 归档 \| 该 agent ACL 临时到期 \| **`tg_agent_acl_expire`** \| P09 后 \| ❌ 不实施」。另见 `CORE_DOMAIN_MODEL.md:263`（role 归档"由 trigger 写 audit"）与 `B1-4_DEPENDENCY.md:103`（记为 **P3 文档不一致**） |
| **Option A** | **保留既有不对称**（各自理由独立；role 的 deny 行需**保留用于审计追溯**，agent 则需**临时到期**） |
| **Option B** | **统一为授权层**（取消 J） ⇒ 需**修订** `TRIGGER_INVENTORY` / `B1-4_SCHEMA_DESIGN`（冻结文档） |
| **Option C** | **统一为 trigger**（为 role 归档新增 trigger） ⇒ **新增对象 = scope 扩张** |
| **Engineering Impact** | A：零文档修订、零新增；B：可减少 1 个 AFTER trigger，但**修改冻结清单**；C：**扩张 P11 范围**（新增未冻结 trigger） |
| **Security Impact** | A：两者各自安全（role 的 allow 行保留支撑审计）；B：需确认"临时到期"语义是否仍被满足；**C 最危险**（为审计面写 trigger，与 V-15/V-16 本体论冲突） |
| **Migration Impact** | A：4 个 trigger；B：3 个；C：5+ 个（超范围） |
| **Future Runtime Impact** | 决定授权层与 DB 的责任边界 |
| **Recommended Direction** | **Option A**（技术后果：既有不对称**已冻结在三处文档**，且两路径语义不同（**allow/deny 保留 vs ACL 临时到期**）；统一化属**冻结文档修订事项**，不得在 P11 静默处理） |
| **Human Decision** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**A（INTENTIONAL / FROZEN）** — **保留机制不对称，不强行统一**：`Archived Role → ACL 数据保留 + Authorization Layer 依 `archived_at` 排除/拒绝`；`Archived Agent → J trigger 使 ACL 到期 + 数据保留`。该不对称是**有意保留的机制差异**，**非 P11 缺陷**；P11 **不新增** `role archive → ACL mutation`，**不移除 J** |
| **Status** | `FROZEN` |

---

## 7. `OQ-P11-06` — Existing Version Immutability Boundary

> **编号重映射（canonical）**：本轮 Human Decision 中 `OQ-P11-06` 的主题为 **Version Immutability（`K`）**；
> PREP 轮该主题曾被编在 `OQ-P11-07`。**canonical 编号以 `PLATFORM_DECISION_LOG.md` 的 `D-P11-06` 为准。**

| 字段 | 内容 |
|---|---|
| **Question** | `K`（`tg_version_immutable`）**已实现**（0008 `tool_versions` / 0011 `agent_versions`）；P11 是否**仅确认边界**、不重做、不改语义、不移所有权？ |
| **Current Evidence** | **实测**：`tg_version_immutable` 在 `0008` 与 `0011` **各 1 处已实现**（`D-B15-03 = A`：统一名与 P09 `agent_versions` 共用）；`tg_audit_immutable`（L）**未实现**且为 **P10-owned**（`D-P10-11`） |
| **Option A** | **确认**：K 属既有阶段；P11 **MUST NOT** recreate / modify semantics / move ownership；**P11 只负责 G/H/I/J** |
| **Option B** | P11 重建并复核 K（**无必要重做**） |
| **Option C** | P11 顺带实施 L（**越界**：违反 `D-P10-11` 的 P10 ownership） |
| **Engineering Impact** | A：0 动作、语义稳定；B：无收益的重写；C：越界并造成双重责任 |
| **Security Impact** | C 会**分散**审计不可变的 ownership（两阶段都提供 ⇒ 一处被改即出现可变窗口） |
| **Migration Impact** | A：0；B：2 个 trigger 重写；C：越界 |
| **Future Runtime Impact** | 决定不可变性 ownership 的清晰度 |
| **Recommended Direction** | **Option A**（= 本轮 Human Decision） |
| **Human Decision** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**A** — `K = tg_version_immutable` **已属既有阶段**；P11 **MUST NOT** recreate K · **MUST NOT** modify K semantics · **MUST NOT** move K ownership；**P11 只负责 G/H/I/J** |
| **Status** | `FROZEN` |

---

## 8. `OQ-P11-07` — Tenant / Space / Authorization Boundary

> **编号重映射（canonical）**：本轮 Human Decision 中 `OQ-P11-07` 的主题为
> **Tenant / Space / Authorization 边界**；PREP 轮该主题曾被编在 `OQ-P11-06`。**canonical 编号以 `D-P11-07` 为准。**

| 字段 | 内容 |
|---|---|
| **Question** | P11 trigger 是否只保护**已明确的结构性跨表不变量**？**G 是否需追加同租户/同 space 比较**？哪些内容**禁止**塞进 trigger？ |
| **Current Evidence** | 清单 §G 的 purpose **仅**为存在性（user→users / role→roles / agent→agents）；`B1-4_DEPENDENCY.md:53` 定位为"受控多态完整性"；同族先例 F2/C2 均**显式声明**"structural integrity only / registry governance only，**不做 authorization evaluation**，**不引入 RLS**"。**注**：`users` 表**无 `tenant_id`** ⇒ 对 user 主体**同租户比较结构性不可实现** |
| **Option A** | **仅结构性不变量**；`G = subject existence` **≠** `subject is authorized for this resource`；授权判定**继续由 Authorization Layer 负责** |
| **Option B** | 在 trigger 内加入租户级授权判定（对 user 主体不可实现） |
| **Option C** | 在 trigger 内做 ACL DENY/ALLOW 求值 |
| **Engineering Impact** | A：与清单逐字一致、0 新语义；B/C：**职责重叠**且无冻结依据 |
| **Security Impact** | B/C 会把**授权语义**放进 DB 层（与 `D-AUTH-*` 的授权层归属冲突），并引入"DB 判定与授权层判定不一致"的风险 |
| **Migration Impact** | A：4 trigger（结构不变量）；B/C：需新查询路径与逐类型强制 |
| **Future Runtime Impact** | 决定 trigger 与授权层的边界 |
| **Recommended Direction** | **Option A**（= 本轮 Human Decision） |
| **Human Decision** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**A** — P11 trigger **只保护已明确的结构性跨表不变量**；**不得**塞入 `cross-tenant authorization decision` / `ACL DENY/ALLOW evaluation` / `membership real-time authorization` / `resource classification policy` / `delegation semantics` / `authorization policy evaluation`。**`G = subject existence` ≠ `subject is authorized for this resource`**；Tenant / Space / policy authorization **继续由 Authorization Layer 负责**（`D-AUTH-01..25`） |
| **Status** | `FROZEN` |

---

## 9. `OQ-P11-08` — Security-definer / search_path 政策

| 字段 | 内容 |
|---|---|
| **Question** | 是否**强制 schema-qualified 对象引用**？是否**设 `search_path`**？是否**永久禁止 `SECURITY DEFINER`**（除非显式批准）？ |
| **Current Evidence** | **实测**：全仓 `SECURITY DEFINER` = **0**（8 个 migration、24 条 CREATE TRIGGER、15 个函数**全部默认 `SECURITY INVOKER`**）；**无任何** `SET search_path` 语句；既有 function 体使用不限定表名（依赖默认 `search_path`） |
| **Option A** | **冻结政策**：① 默认 `SECURITY INVOKER`；② **禁止** `SECURITY DEFINER`（除**显式 Human 批准 + 最小权限 + 固定 `search_path`**）；③ 新函数**建议** schema-qualified（`public.<table>`） |
| **Option B** | 强制 schema-qualified + `SET search_path`（对 **G/H/I/J** 四点执行） |
| **Option C** | 保持现状（不设政策） |
| **Engineering Impact** | A：与 24 条先例一致、零回归；B：**与既有 24 条不一致**（仅新 4 条特殊）⇒ 风格分叉；C：无治理 |
| **Security Impact** | A：**消除提权面**（无 SECURITY DEFINER）；B 额外降低"search_path 劫持"面，但引入风格不一致；C：`search_path` 依赖**运行期配置**（未冻结） |
| **Migration Impact** | A：0 额外对象；B：4 个函数体内加限定名 |
| **Future Runtime Impact** | 决定未来所有 trigger 的安全基线 |
| **Recommended Direction** | **Option A**（技术后果：与全仓 24 条先例一致；**明确禁止 SECURITY DEFINER**；schema-qualified 作为**建议**而非强制，避免单点风格分叉；`search_path` 的**运行期**配置另见既有 `D-PLAT` 治理面） |
| **Human Decision** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**A** — **`SECURITY INVOKER` = canonical**；**明确禁止引入 `SECURITY DEFINER`**（除非未来产生**新的独立 Human Decision**）；保留 `unqualified object resolution risk` · `search_path risk` · `privilege escalation risk` 为**实施期安全检查项**；**本轮不得引入任何 `SECURITY DEFINER` function** |
| **Status** | `FROZEN` |

---

## 10. `OQ-P11-09` — Recursion Policy

| 字段 | 内容 |
|---|---|
| **Question** | 递归防护政策如何冻结？**J 的 hidden DML 是否为唯一受控例外**？ |
| **Current Evidence** | **本轮分析**：G/I **无 hidden DML**（只读校验）；**H 有 DELETE**（清理 ACL）但 `resource_permissions` **无 DELETE 触发器**、G 为 `BEFORE INSERT OR UPDATE` ⇒ H **不触发任何 trigger**；**J 有 UPDATE**（`inherited`/`expires_at`）而 **G 是 `UPDATE OF subject_type_id, subject_id`** ⇒ J 的 SET 列表**不含** subject 列 ⇒ **G 不触发**；`resource_permissions` 上无会回写 `agents` 的触发器 ⇒ **无互递归** |
| **Option A** | **冻结**：① 禁止 trigger 写入**自身表**（除 H/J 的受控清理/失效）；② 禁止 trigger 写入 **P10 对象**（`events`/`audit_logs`/outbox）；③ **J 的 `UPDATE resource_permissions` 限定为唯一受控 hidden DML**，且**禁止**其 SET 列表出现 `subject_type_id` / `subject_id`（否则触发 G）；④ 禁止 trigger 写入 `acl_subject_types`（受 C2 保护） |
| **Option B** | 仅作原则性声明（不留具体禁令） |
| **Option C** | 不加限制 |
| **Engineering Impact** | A：可测（可断言 SET 列表）；B/C：未来变更可能引入递归 |
| **Security Impact** | A 防止"trigger 链"造成的隐式权限/审计面（尤其 C 项对 P10 对象的禁令） |
| **Migration Impact** | 0（政策层） |
| **Future Runtime Impact** | 决定未来 trigger 的可用形态 |
| **Recommended Direction** | **Option A**（技术后果：把本轮已验证的"无递归"结论**变成可强制的禁令**，尤其"J 不得写 subject 列"） |
| **Human Decision** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**A** — `J` 的隐藏 DML **限定于 ACL 生命周期失效**（`UPDATE resource_permissions SET inherited=true, expires_at=now()`）；**J MUST NOT UPDATE `subject_type_id`** · **MUST NOT UPDATE `subject_id`** ⇒ **不得通过 J 人为触发 G**；`G`（subject identity validation）与 `J`（agent ACL expiration）**不得合并**；**禁止增加 trigger chain** |
| **Status** | `FROZEN` |

---

## 11. `OQ-P11-10` — P10 / P11 Ownership

| 字段 | 内容 |
|---|---|
| **Question** | 是否**正式冻结**四项禁止：`P11 MUST NOT duplicate / replace / weaken / relocate` `tg_audit_immutable`？ |
| **Current Evidence** | `D-P10-11`（FROZEN）已冻结："`tg_audit_immutable` = **P10-owned**；`P10 = Event/Audit persistence + Audit-local immutability protection`；`P11 = remaining trigger / cross-table constraints`；**P11 不得成为 `audit_logs` 基础 immutable security property 的前置条件**"。**实测**：G/H/I/J 均**不触及** `events` / `audit_logs` / outbox（零交叠） |
| **Option A** | **正式确认四项禁止**（并确认 G/H/I/J 与 P10 对象**零交叠**） |
| **Option B** | 仅确认"P10-owned"，不列四项禁止 |
| **Option C** | 允许 P11 在 P10 未就位时临时提供不可变性 |
| **Engineering Impact** | A：边界清晰、可测；B：弱化；C：**双重责任** |
| **Security Impact** | C **危险**：两个 stage 都提供 `audit_logs` 不可变性 ⇒ 未来一处被改即出现可变窗口 |
| **Migration Impact** | A/B：P11 不含 L；C：可能包含 L |
| **Future Runtime Impact** | 决定 P10/P11 的 trigger 面归属 |
| **Recommended Direction** | **Option A**（技术后果：把 `D-P10-11` 的 ownership 转成**可断言的禁令**；P11 的实施清单**不含** L） |
| **Human Decision** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**A** — 严格固定 `P10 = Event / Audit persistence + tg_audit_immutable`；`P11 = G/H/I/J + remaining cross-table trigger constraints` ⇒ **`L = OUT OF P11`**；P11 **不得** CREATE/MODIFY `audit_logs` 或 `events` 的 trigger、**不得** replace `tg_audit_immutable`；**特别确认 `tg_audit_immutable = P10-owned`** |
| **Status** | `FROZEN` |

---

## 12. `OQ-P11-11` — P11 / P12 Dependency

| 字段 | 内容 |
|---|---|
| **Question** | P11 是否**不新增任何索引**？P12 是否**不得**为 trigger 重复建索引？ |
| **Current Evidence** | **实测**：`ix_rp_subject`（`resource_permissions(subject_type_id, subject_id)`）**已在 0007 创建**（P06）⇒ G/I/J 的查询路径**已有索引**；`STEP1B_INDEX_STRATEGY.md` §3「FK 反查强制清单」含 `ix_rp_subject`；P12 定义 = "非 PK 索引 … P12 **只保留'纯查询索引'**" |
| **Option A** | **P11 不新增索引**（G/H/I/J 复用 `ix_rp_subject`）；**P12 不重复**为 trigger 建索引（除非新证据） |
| **Option B** | P11 顺带补索引 |
| **Option C** | P12 为 G/I/J 新建专门索引 |
| **Engineering Impact** | A：0 新对象、无重复索引；B/C：**职责越界**（索引属 P12） |
| **Security Impact** | 无直接安全影响（性能面） |
| **Migration Impact** | A：0；B/C：+index |
| **Future Runtime Impact** | 决定 P12 的输入面 |
| **Recommended Direction** | **Option A**（技术后果：`ix_rp_subject` 已存在且服务于该查询模式；索引归属 P12，P11 不得侵入） |
| **Human Decision** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**A** — P11 **不创建"顺手索引"**（索引属 **P12**）；若 trigger 所需性能支持尚未存在 ⇒ **记录为 P12 dependency**，**不得**在 P11 migration 内私自加入 P12 index scope；`P11 semantic correctness` **MUST NOT** depend on `P12 business semantics` |
| **Status** | `FROZEN` |

---

## 13. `OQ-P11-12` — P11 / P13 Dependency

| 字段 | 内容 |
|---|---|
| **Question** | 确认"trigger 先于 seed"；确认 P11 **不携带任何 seed**？ |
| **Current Evidence** | `STEP1B_SCHEMA_DEPENDENCY.md:193`：`P00-P10 均无 seed 需求；P13 才有 seed。**所有 trigger（P11）必须先于 P13 seed**`；`SEED_STRATEGY.md:138`：「seed 前必须有：全部表（P01–P10）+ **全部 trigger（P11）** + 全部 index（P12）」；**实测**：G 在 `acl_subject_types` 为空时**必然拒绝一切写入** ⇒ 与"先 trigger 后 seed"一致（且与 B1-4 的"ACL 物理不可写入"结论一致） |
| **Option A** | **确认**：trigger 先于 seed；**P11 零 seed**（不插 `acl_subject_types` / `roles` / `users` / `permissions` 任何行） |
| **Option B** | P11 为便于自测插入 seed |
| **Option C** | 顺序改为 seed 先、trigger 后 |
| **Engineering Impact** | A：与既有纪律一致；B：**越界**（seed 属 P13）+ 破坏 `D-PLAT-11`（首个主体只经 P13）；C：**违反 B0 冻结**（seed 数据绕过 trigger 校验） |
| **Security Impact** | C 会让 seed 数据**绕过**不变量校验（"带病入库"） |
| **Migration Impact** | A：0；B：+seed；C：顺序变更 |
| **Future Runtime Impact** | 决定 P13 的可行前提 |
| **Recommended Direction** | **Option A**（技术后果：与 `DEPENDENCY:193` + `SEED_STRATEGY:138` 逐字一致；**不得偷带 seed**） |
| **Human Decision** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**A** — G/H/I/J **必须在 P13 seed 之前完成挂载**（`trigger protection must exist before seed writes`）；**P11 不承担任何 P13 seed**；**特别禁止** `insert acl_subject_types seed` · `insert bootstrap user` · `insert bootstrap role` · `insert agent subject seed`；**P11 只建立 structural protection** |
| **Status** | `FROZEN` |

---

## 14. `OQ-P11-13`（新增） — 清单缺口 `GAP-INV-1` 处置

| 字段 | 内容 |
|---|---|
| **Question** | 6 项已实现但**不在** A–M 清单内的触发器（`tg_pm_role_scope` · `tg_pm_last_admin` · `tg_roles_pm_lifecycle` · `tg_platform_state_guard` · `tg_pm_bootstrap_gate` · `tg_agents_tenant_space_consistency`）如何登记？是否**重排** letter 编号？ |
| **Current Evidence** | **实测**：6 者均在 0005（4 项）/ 0006（3 项，其中 `tg_platform_state_set_updated_at` 属 A 族）/ 0011（1 项）**已实现**；`STEP1B_TRIGGER_INVENTORY.md` 成文于 STEP 1-B/B0（早于 0005/0006/0011）⇒ 清单**未含**它们；清单内**无**同名异义者 |
| **Option A** | **append-only 注记**登记（在 `STEP1B_TRIGGER_INVENTORY.md` **末尾追加**一节）；**letter 编号不重排**（遵既有 R1/F2/C2 的"插入新增、不重排"先例） |
| **Option B** | 重排 letter（A–S）⇒ 会**使既有大量文档引用失效** |
| **Option C** | 不登记（保持清单不完整） |
| **Engineering Impact** | A：留痕完整、零引用破坏；B：**破坏性改名**（`D-B14-02`/`D-B14-10`/`D-B14-12` 等均按 letter 引用）；C：治理缺口长期存在 |
| **Security Impact** | 无直接安全影响；但 C 会使**信任根相关触发器**（`tg_pm_last_admin`）无正式清单地位 |
| **Migration Impact** | 0（文档层） |
| **Future Runtime Impact** | 决定 trigger 清单的权威性与完整性 |
| **Recommended Direction** | **Option A**（技术后果：与 `F2`/`C2` 的既有先例一致；**不重排**避免破坏 letter 引用；`R1`/`R4` 已建立"插入新增 + 注记"范式） |
| **Human Decision** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**A** — 6 项已实现触发器（`tg_pm_role_scope` · `tg_pm_last_admin` · `tg_roles_pm_lifecycle` · `tg_platform_state_guard` · `tg_pm_bootstrap_gate` · `tg_agents_tenant_space_consistency`）**不属于** A–M canonical letter 清单。**DO NOT** renumber A–M · **DO NOT** insert new letters · **DO NOT** move them into G/H/I/J · **DO NOT** reclassify them as P11 delivery。保留 **`GAP-INV-1` = supplementary inventory gap** ⇒ 含义 = **`historical inventory completeness issue`**，**不是** `missing implementation`（对象**已真实存在**且属既有阶段） |
| **Status** | `FROZEN` |

---

## 15. `OQ-P11-14`（新增） — 既有 P3 文档不一致处置

| 字段 | 内容 |
|---|---|
| **Question** | 两项**既有已登记**的不一致如何处置：<br>**`CF-2`** `CORE_DOMAIN_MODEL.md:263`「归档 role 时**由 trigger 写 audit**」vs `B1-4_DEPENDENCY.md:103`「与 trigger 本体论（**trigger 不写 audit**）冲突」（记为 P3）<br>**`CF-3`** H/I 的"P09 后"为**显式阶段冻结**而非依赖推导（`B1-4_DEPENDENCY.md:74-76` 已载"原文不精确之处"，属**冻结文档修订事项**） |
| **Current Evidence** | 两处均为**历史轮已如实登记**的 P3 级问题（**非本轮新发现**）；`CF-2` 的两种表述互斥；`CF-3` 的 `TRIGGER_INVENTORY:177` 以"依赖 agents"概括四项，**对 H/I 理由不充分**；`B1-4_DEPENDENCY` 明确"**本 PREP 不自行裁定**" |
| **Option A** | **保持 defer + append-only clarification**（在相关文档追加注记说明属修订事项；**不改写冻结正文**；不在 P11 新增 trigger 承载 audit 写入） |
| **Option B** | **本轮提为正式修订**（改 `CORE_DOMAIN_MODEL.md:263` 表述） |
| **Option C** | 无视（不作处置） |
| **Engineering Impact** | A：零改写、留痕；B：**改写 STEP 1-A 冻结设计正文**（超本轮授权面）；C：缺口永久 |
| **Security Impact** | **三者均不得导致新增"写 audit 的 trigger"**（与 `D-P10-11` 的 P10 审计 ownership + P11 本体论冲突） |
| **Migration Impact** | 0（文档层） |
| **Future Runtime Impact** | 决定审计写入路径的唯一性（授权层 / P10） |
| **Recommended Direction** | **Option A**（技术后果：**不得**在 P11 引入写 audit 的 trigger；`CF-2`/`CF-3` 的**正文修订**属独立 Human 决策，与 P11 实施解耦） |
| **Human Decision** | **FROZEN**（2026-09-25 Human Decision）—— 选定：**A** — 「`role archive → trigger writes audit`」**NOT a P11 implementation requirement**；**正式保持 `trigger does NOT write audit`**；Audit persistence **属 `P10` Event / Audit layer**；P11 **不新增** `role archive audit trigger` / `ACL audit-writing trigger`；历史描述处置 = **append-only clarification**，**不得改写既有历史 Decision 正文** |
| **Status** | `FROZEN` |

---

## 16. 冻结请求包 —— **已执行（2026-09-25）**

原请求项（保留原貌）：若认可 §2–§15 的 Recommended Direction，**一次确认即可完成 14 项冻结**。

```text
2026-09-25 —— Human 已逐项裁定（`UAP P11 — HUMAN DECISION RESOLUTION`）；
14 项全部 FROZEN（Recommendation 与 Human Decision 逐项一致，另含 Human 细化项）。
CF-1 / CF-2 / CF-3 = CLARIFIED（append-only）；CF-4 = INTENTIONAL / FROZEN。
```

**已执行的动作**：

| 原计划动作 | 结果 |
|---|---|
| 写 `PLATFORM_DECISION_LOG.md`（`D-P11-01..14`，`FROZEN`） | ✅ **已写入 14 条**（另新增三向边界节 · canonical invariants 节 · 附录 H · 编号重映射登记） |
| `P11_PREP_REPORT.md` | ✅ **append-only 注记** |
| `P11_DECISION_RESOLUTION.md` | ✅ **本文件**（含 §7/§8 canonical 重排） |
| `P11_ACCEPTANCE_MATRIX.md` | ✅ **已完成** |
| 既有陈旧描述 | ✅ **append-only clarification**（`STEP1B_TRIGGER_INVENTORY.md` · `CORE_DOMAIN_MODEL.md`） |
| `P11 DECISION FREEZE = PASSED` | ✅ **PASSED** |

> **不变**：`DDL` / `DML` / `trigger` / `function` / `migration` / `code` / `test` / `config` /
> `commit` / `tag` / `push` = **NOT AUTHORIZED**。
>
> **`P11 IMPLEMENTATION = NOT AUTHORIZED`** · **`P12 IMPLEMENTATION = NOT AUTHORIZED`** ·
> **`P13 IMPLEMENTATION = NOT AUTHORIZED`** · **`Runtime Implementation Gate = CLOSED`**。
---

## 17. EXIT CHECK（2026-09-25 终态）

| 条件 | 上一轮实测 | **本轮终态** |
|---|---|---|
| 14/14 OQ individually resolved | ❌ 0/14 | ✅ **14/14**（`HUMAN DECISION = FROZEN` × 14） |
| or explicitly DEFERRED | ❌ 0 项 | ✅ 条目级 DEFERRED **0**（无新增开放项） |
| No silent decision | ✅ 无静默决定 | ✅ **无静默决定**（14 项逐项裁定；06/07 编号重映射**显式登记**） |
| 指令 §9 的 12 项覆盖 | ✅ 12/12 | ✅ 12/12（+ 2 项有实测证据） |
| `D-PLAT-09` 未被 supersede | ✅ | ✅ **FROZEN / NOT SUPERSEDED** |
| **P10 L ownership 保持** | ✅ | ✅ **`L = P10-owned`（OUT OF P11）** |
| `CF-1`…`CF-4` 已登记 | ✅（未代裁） | ✅ **已处置**：CLARIFIED ×3 · INTENTIONAL/FROZEN ×1 |
| trigger / function / migration / code / test / config 变更 | ✅ 全 0 | ✅ **全 0** |
| commit / tag / push | ✅ 全 0 | ✅ **全 0** |

⇒ **`P11 DECISION FREEZE = PASSED`**（2026-09-25）
⇒ **`P11 / P12 / P13 IMPLEMENTATION = NOT AUTHORIZED`** · **`Runtime Implementation Gate = CLOSED`**

---

**END OF P11 DECISION RESOLUTION（2026-09-25 · READ-ONLY PREP）**
**END OF P11 DECISION RESOLUTION（`DECISION FREEZE APPLIED` · `HUMAN DECISION` 14/14 `FROZEN`；`CF-1..CF-4` 已处置；canonical 编号见 `PLATFORM_DECISION_LOG.md` 的 `D-P11-01`…`D-P11-14`，2026-09-25）**
