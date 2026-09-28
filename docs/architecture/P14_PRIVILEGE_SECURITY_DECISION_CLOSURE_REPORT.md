# UAP — P14 PRIVILEGE / SECURITY DECISION CLOSURE REPORT

> ## 状态
>
> ```text
> 轮次      = P14 PRIVILEGE / SECURITY HUMAN DECISION — 正式裁决与闭环
> 载体      = P14_PRIVILEGE_SECURITY_HUMAN_DECISION_SHEET.md（**HUMAN DECISION RESOLVED** ·
>             Resolution Registry 为权威记录）
> 基线      = HEAD c420403d5469241e8b03855428ebce435d539c9e · migration 0017_p13_seed ·
>             DB = 0017_p13_seed · 0018+ = 0
> 本轮未做   = CREATE ROLE / ALTER ROLE / GRANT / REVOKE / ALTER DEFAULT PRIVILEGES = 0 ·
>             DDL = 0 · DML = 0 · migration = 0 · runtime code = 0 · database onboarding = 0 ·
>             bootstrap implementation = 0 · commit / tag / push = 0 · 未开启 P15
> ```

---

# 1. Decision Resolution（14 / 14）

```text
SEC-P14-01  Runtime Principal Model          = **OPTION C — DEDICATED RUNTIME PRINCIPAL**
SEC-P14-02  Runtime Trust Boundary           = **TRUSTED INTERNAL SERVICE BOUNDARY**
SEC-P14-03  Runtime Required Read Scope      = **explicit required-read allowlist**（UNKNOWN → DENY）
SEC-P14-04  Runtime Required Write Scope     = **use-case + operation 精确授予**（未明确 = DENY）
SEC-P14-05  Tenants / Spaces                 = **RUNTIME = SELECT ONLY**
SEC-P14-06  Memberships                      = 普通 memberships 受控 use-case（service-mediated）；
                                               platform_memberships 属 Bootstrap 边界
SEC-P14-07  Events / Resources               = SELECT / INSERT / UPDATE（use-case 限定）· DELETE = DENY
SEC-P14-08  Credential Lifecycle             = **NO PHYSICAL DELETE**（issue → active → rotate → revoke/expire）
SEC-P14-09  Resource Permission Write Side   = **RUNTIME WRITE = DENY**（禁 self-escalation）
SEC-P14-10  Authorization Read Path          = **HYBRID**（Central Authorization Service + Restricted DB Read）
SEC-P14-11  Bootstrap Execution Identity     = **DEDICATED ONE-TIME BOOTSTRAP PRINCIPAL**
SEC-P14-12  Bootstrap Credential Source      = **LOCAL OPERATOR-CONTROLLED INTERACTIVE SECRET INPUT**
                                               （受控环境可 LOCAL SECRET FILE / CONTAINER SECRET）
SEC-P14-13  platform_memberships / state     = **BOOTSTRAP-OWNED INITIALIZATION**
SEC-P14-14  Privilege Grant Strategy         = **EXACT LEAST-PRIVILEGE GRANT STRATEGY**

合计：resolved 14 / 14
```

---

# 2. Closure Proof（本指令 §十五 B 要求逐项证明）

```text
① 14 / 14 resolved                        = ✅（上表逐项 + Sheet 的 Resolution Registry）
② 0 unresolved                            = ✅
③ 0 UNKNOWN                               = ✅（Security Gate 意义上的 UNKNOWN 已由
                                              SEC-03 / 04 / 05 / 06 / 07 / 08 / 09 全部裁决清零；
                                              见 §3 的逐项闭合）
④ 0 undocumented bootstrap gap             = ✅（SEC-11 身份 · SEC-12 凭据 · SEC-13 授权边界
                                              三处空白全部闭合；见 §4）
⑤ 0 implicit option                        = ✅（Sheet 内 93 个勾选框保持未勾选；
                                              裁决仅记录于 Resolution Registry；无隐藏默认选择）
⑥ 0 Contract conflict left unresolved      = ✅（原 MODEL A / MODEL B-复用 的 CONTRACT CONFLICT
                                              因选定 MODEL C 而**避免**；见 §5）
⑦ 0 implementation authorization leakage   = ✅（本轮零 DB 变更、零角色/授权变更、零实现；
                                              Security Decision ≠ Implementation Authorization）
```

---

# 3. UNKNOWN 闭合明细（前轮 Security Gate → 本轮裁决）

```text
前轮 UNKNOWN                              → 本轮裁决
tenants / spaces                          → SEC-P14-05（SELECT ONLY）
tenant_memberships / memberships          → SEC-P14-06（受控 use-case；platform 面除外）
events                                    → SEC-P14-07（S/I/U 允许 · DELETE DENY）
resources                                 → SEC-P14-07（S/I/U 允许 · DELETE DENY）
resource_permissions 写侧                  → SEC-P14-09（写 = DENY）
credential DELETE                          → SEC-P14-08（NO PHYSICAL DELETE）

⇒ UNKNOWN 剩余 = **0**
   注：SEC-P14-03 / 04 要求把 Privilege Matrix 的每对象重算为
       REQUIRED / NOT REQUIRED / DENY（**不得留 UNKNOWN**），该重算已在本轮完成（见 §6）。
```

---

# 4. Bootstrap 空白闭合明细

```text
前轮空白                          → 本轮裁决
bootstrap execution identity      → SEC-P14-11（DEDICATED ONE-TIME BOOTSTRAP PRINCIPAL）
bootstrap credential source       → SEC-P14-12（LOCAL OPERATOR-CONTROLLED INTERACTIVE SECRET INPUT）
platform_memberships / state 归属  → SEC-P14-13（BOOTSTRAP-OWNED INITIALIZATION）

⇒ bootstrap gap 剩余 = **0**
   关键不变量：Bootstrap Authority ≠ Runtime Authority；
               bootstrap principal ∉ {uap_migrator, uap_app, runtime principal}
```

---

# 5. Contract 冲突处置

```text
前轮标记的冲突（P14_PRIVILEGE_SECURITY_HUMAN_DECISION_SHEET §SEC-P14-01）

CONFLICT-C1  MODEL A（直接扩 uap_app）vs Contract §12 PB-1 / PB-2
             ⇒ 本轮**未选 MODEL A** ⇒ 冲突**不存在**（0 unresolved）
CONFLICT-C2  MODEL B-复用 uap_app / uap_migrator / uap_seed 的三种复用情形
             ⇒ 本轮**未选复用**（SEC-01 明确不复用任一既有角色；SEC-11 明确 bootstrap
               不用 uap_migrator）⇒ 冲突**不存在**（0 unresolved）

⇒ Contract Conflicts = **0 / 0**
   说明：本轮**不需要**修改 Contract 冻结正文；
        6 项 "CANDIDATE amendment"（SEC-05 / 07 / 08 / 10 / 11 / 12 / 13 / 14 中部分）
        均为**未来 Security Implementation Gate** 的细化候选，不构成本轮冲突。
        若未来实施需要修改冻结语义 ⇒ 届时须**先 STOP、提出 amendment proposal**，
        不得擅自覆盖旧冻结内容。
```

---

# 6. Privilege Matrix 状态推进与闭合重算

```text
矩阵文件：P14_RUNTIME_PRIVILEGE_MATRIX.md
状态推进：PROPOSED → **HUMAN-DECISION-RESOLVED / IMPLEMENTATION INPUT**（见该文件 §8 增补）

重算结果（依 SEC-03 / 04 / 05 / 06 / 07 / 08 / 09 · 无 UNKNOWN 残留）：

对象                     SELECT   INSERT   UPDATE   DELETE    依据
----------------------   ------   ------   ------   ------    -------------------------------
users                      R        R        R        DENY     SEC-01/03/04（onboarding）
identities                 R        R        R        DENY     同上
credentials                R        R        R        DENY     SEC-08（no physical delete）
devices                    R        R        R        DENY     SEC-04（enrollment/revoke=UPDATE）
sessions                   R        R        R        R        SEC-04（session lifecycle）
tenants                    R       DENY     DENY     DENY     SEC-05（SELECT ONLY）
spaces                     R       DENY     DENY     DENY     SEC-05（SELECT ONLY）
tenant_memberships         R        R        R        R        SEC-06（受控 use-case）
memberships                R        R        R        R        SEC-06（受控 use-case）
roles                      R       DENY     DENY     DENY     platform-controlled
permissions                R       DENY     DENY     DENY     platform-controlled
role_permissions           R       DENY     DENY     DENY     platform-controlled
acl_subject_types          R       DENY     DENY     DENY     migration-controlled（C2/CC-7）
resource_permissions       R       DENY     DENY     DENY     SEC-09（write = DENY）
events                     R        R        R       DENY     SEC-07
resources                  R        R        R       DENY     SEC-07
audit_logs                 R        R       DENY     DENY     audit 不可变（tg_audit_immutable）
platform_memberships       R       DENY     DENY     DENY     SEC-13（bootstrap-owned）
platform_state             R       DENY     DENY     DENY     SEC-13（bootstrap-owned）
agents                     R       DENY     DENY     DENY     SEC-03（读取以支持 subject 解析）
agent_versions             R       DENY     DENY     DENY     同上
agent_permissions          R       DENY     DENY     DENY     同上
tools                      R       DENY     DENY     DENY     同上
alembic_version            R       DENY     DENY     DENY     readiness（既有授权已含）
sequence                  DENY     DENY     DENY     DENY     无序列（实测 0）
function EXECUTE          DENY     DENY     DENY     DENY     未采用函数路径（SEC-14：仅必要时）

⇒ UNKNOWN 残留 = **0** · 全部为 REQUIRED(R) 或 DENY
   注：以上为**授权输入（IMPLEMENTATION INPUT）**，**不是已授予权限**；
       实际 GRANT 须在独立 Security Implementation Gate 授权后执行。
```

---

# 7. OI-G-1 状态与新增证据

```text
OI-G-1 = **OPEN**（本轮不关闭）

本轮新增证据（已决定项）：
  · principal 已决定            = YES（SEC-01 = DEDICATED RUNTIME PRINCIPAL）
  · required read scope 已决定   = YES（SEC-03 + §6 重算）
  · write scope 已决定           = YES（SEC-04 + §6 重算）
  · bootstrap identity 已决定    = YES（SEC-11）
  · bootstrap credential source 已决定 = YES（SEC-12）
  · authorization path 已决定    = YES（SEC-10 = HYBRID）
  · grant strategy 已决定        = YES（SEC-14）

仍未满足关闭条件的原因：
  · Security Implementation 尚未执行（principal / role / GRANT 尚未创建与授予）
  · 授权执行后的**负向探针与正向断言证据**尚不存在
  ⇒ 依"仅当后续 Security Implementation Gate 真正具备完整证据时才考虑关闭"
     ⇒ **OI-G-1 = OPEN**（本报告 + 矩阵重算 = 其更新证据）
```

---

# 8. Zero-Guess Security Decision Closure

```text
Decision IDs = 14 unique          ✅
resolved = 14                     ✅
unresolved = 0                    ✅
UNKNOWN = 0                       ✅
bootstrap UNKNOWN = 0             ✅
candidate ≠ selected              ✅（候选保留于 Sheet；裁决记录于 Resolution Registry）
selected ≠ implementation         ✅（Security Decision = FROZEN；Implementation = NOT AUTHORIZED）
no hidden privilege expansion     ✅（无 GRANT/REVOKE/CREATE ROLE 执行）
no hidden role creation           ✅（roles 仍为 4）
no hidden grant                   ✅（uap_app grants 仍为 5；uap_seed 0）
no Contract conflict silently accepted ✅（0 unresolved；未来 amendment 须 STOP + proposal）

⇒ ZERO-GUESS SECURITY DECISION CLOSURE = **PASS**
```

---

# 9. Integrity Gate（§十七）

```text
Git
  HEAD 未变            = c420403d5469241e8b03855428ebce435d539c9e ✔
  branch 未变           = main ✔
  tag 未增加            = 9 ✔
  remote push          = 0 ✔
  staged               = 0（未 stage 历史 dirty set）✔
  本轮写入              = 仅 Security Decision Closure 所需文档 ✔

DB
  alembic_version      = 0017_p13_seed ✔
  migrations           = 17 ✔ · 0018+ = 0 ✔
  roles                = 4 ✔
  uap_app grants       = 5 ✔ · uap_seed grants = 0 ✔
  default_acl          = 0 ✔
  pg_class             = 156 ✔ · pg_proc = 22 ✔
  registry / permissions / role_permissions = 3 / 12 / 12 ✔
  C2 md5               = 185e95be8bc4304edbcd3f4d5cda1eff ✔（CC-7 未变）
  uap_app / uap_migrator 属性与权限面 = 未变 ✔
⇒ P14 SECURITY HUMAN DECISION PREP DB/GIT INTEGRITY = **PASS**
```

---

# 10. 待办与开放项（登记 · 不自行处理）

```text
OPEN-1  PDL canonical registration（附录级登记）：
        本轮未把 14 项 Security Decision 追加至 PLATFORM_DECISION_LOG.md（本指令未授权该写入面；
        且 §17 限定"本轮只能写 Security Decision Closure 所需文档"）。
        若 Human 希望以 PDL 附录（例如附录 O）形式做 canonical 登记 ⇒ 须另行授权。

OPEN-2  Contract 细化候选（6 项 CANDIDATE）：SEC-05 / 07 / 08 / 10 / 11 / 12 / 13 / 14 中的部分，
        属未来 Security Implementation Gate 的文档细化；本轮不修改冻结正文。

OPEN-3  Security Implementation Gate：principal / role / GRANT 的实际创建与授予，
        须另行授权（本轮明确禁止）。
```

---

# 11. 本轮工程变更

```text
CREATE ROLE = 0 · ALTER ROLE = 0 · GRANT = 0 · REVOKE = 0 · ALTER DEFAULT PRIVILEGES = 0
DDL = 0 · DML = 0 · migration = 0 · runtime code = 0 · database onboarding = 0 ·
bootstrap implementation = 0 · commit = 0 · tag = 0 · push = 0 · P15 = 未开启
新增文档 = 本报告（+ 同轮 3 份文档更新）
```

---

**END OF P14 PRIVILEGE / SECURITY DECISION CLOSURE REPORT（2026-09-27 · `resolved 14/14` · `UNKNOWN 0` · `bootstrap gap 0` · `Contract conflict 0` · **Security Decision = FROZEN** · `Security Implementation = NOT STARTED` · `P14 IMPLEMENTATION = NOT AUTHORIZED`）**
