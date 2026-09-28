# UAP — P14_RUNTIME_SLICE SCOPE

> ## 阶段与边界
>
> ```text
> 阶段      = `P14_RUNTIME_SLICE`（正式编号 · FROZEN · PDL 附录 M.1）
> 路线      = `STEP 2 — Runtime Slice`
> 本文档性质 = PREP 设计产物（DRAFT · NOT FROZEN）—— 定义范围与边界，**不含实施**
> 文档集合   = 依 RUNTIME_DOCUMENT_SET_DECISION.md §2（4 份 · 本文件为其中 SCOPE）
> 本轮未做   = 未创建 runtime code / services 实现 / API endpoint / worker / scheduler / CLI 实现 /
>              未创建 0018+ migration · 未改 schema · 未改 P13 seed · 未改冻结 Decision 正文
> ```

---

# 1. Runtime Mission（Runtime 为什么存在）

```text
问题（P13 结束时的真实状态）：
  · 数据库已具备完整结构 + 授权基线（registry 3 · permissions 12 · role_permissions 12），
    但**没有任何可运行的服务面**：P09 = SCHEMA ONLY（D-P09-07 = A）明确推迟了
    API / Socket / Worker / Scheduler / Celery 与 Agent/Tool/AI runtime。
  · 没有任何**可登录主体**：P13 不创建 users、不创建凭据、不创建任何 membership
    （IMPL-01 = A · D-P13-06/13）。平台处于「基线就绪、无人可用」状态。
  · `platform_memberships = 0` ⇒ 按 R4/R5，平台尚未初始化；第一个平台管理员必须由
    受信 bootstrap CLI 建立。

Runtime Slice 存在的理由：
  把已冻结的 Schema + Authorization/Data Baseline 转化为**可运行、可认证、可授权、可审计**
  的实际服务能力，并**在不改变 schema、不改变授权模型、不扩权**的前提下完成
  「从基线到可操作平台」的最后一段。

成功的样子（目标态）：
  · 一个可按受控流程上线/下线的 runtime 执行层
  · 一条受控的 identity onboarding 路径（建立首个可登录主体 + 凭据，走安全流程）
  · 一次受信的 platform bootstrap（写首个 platform_memberships 行 + 翻转 platform_state + 审计）
  · runtime 侧在既有 RBAC/ABAC/resource ACL 面上**执行**授权判定
  · 可运维：健康 / readiness / 观测面可用（复用 D-PLAT-14/16 已有门）
```

---

# 2. Included Capability（6 项 · 每项 Input / Output / Dependency）

## 2.1 runtime execution layer

```text
Input       = 既有代码分层（apps → agent → services → intelligence → core → infrastructure）
              + 既有配置面（config/settings.py 的 DATABASE_URL → uap_app）
Output      = 进程 / 服务宿主与生命周期（启动、依赖装配、优雅关闭）
Dependency  = D-PLAT-02/03/04（层规则与守卫）· D-PLAT-09（阶段序，Runtime 在 P13 之后）
              既有 G-1…G-7 硬门（D-PLAT-17）在实施前后均须保持通过
```

## 2.2 API / service boundary

```text
Input       = 领域服务面（services/ 为业务持久化的唯一归属 · D-PLAT-01/03）
Output      = 对外接口层与其契约面（请求/响应契约、错误语义、版本策略）
Dependency  = 既有授权判定面（0005/0007/0012）· 既有审计面（0013 audit_logs）
              PDL 附录 C 的 C-5（services/ 内部结构与模块粒度）与 C-6（domains 公开契约载体）
              均为**未决项**（留待 Runtime PREP 收敛，见 PREP_REPORT 的 OPEN 清单）
```

## 2.3 identity onboarding

```text
Input       = 空的 users 表（0 行）· 空的 tenants/spaces（0 行）· platform_state = uninitialized
Output      = 首个可登录主体（users 行 + 凭据）与随后的租户/空间与 membership 建立流程
Dependency  = D-PLAT-11①（首个正式可登录主体只经 P13 建立 ⇒ 现由 Runtime 承接其
              「可登录」完成机制：onboarding 设密流）· D-P13-06/13（凭据边界与零明文）
              P13_PREP_REPORT §… 已登记：users 行无凭据不可登录 ⇒ 设密流程属 Runtime Slice
标记        = 具体流程形态为 **OPEN**（见 PREP_REPORT §1）
```

## 2.4 authorization enforcement

```text
Input       = 既有 RBAC（platform/tenant/space） + ABAC + resource ACL 结构 ·
              role_permissions 基线（platform_admin × 12 allow）
Output      = runtime 侧**执行**授权判定（default deny / deny 优先 / FAIL CLOSED）
Dependency  = 既有模型（**不新增模型**）· D-P13-01（无 deny 行 · 12 项 canonical）
标记        = 判定执行位置（API 层 / service 层 / policy 层）为 **OPEN**（见 PREP_REPORT §2）
```

## 2.5 operational interface

```text
Input       = 既有 readiness/health 机制（D-PLAT-14 配置键与失败语义 · D-PLAT-16 2000 ms 探针）
Output      = 可观测的运维面（/health liveness · /ready readiness 503 语义）
Dependency  = D-PLAT-08/14/15 v2/16（已 FROZEN）· D-PLAT-17 ⑦（本路线不建 CI）
标记        = observability 深度（日志/指标/追踪）为 **OPEN**（C-10 部署手册缺失亦在此列）
```

## 2.6 bootstrap CLI

```text
Input       = platform_state = uninitialized · platform_memberships = 0（PMB-2 条件）
Output      = 首个平台管理员写入 platform_memberships + 翻转 platform_state +
              audit(action='platform.admin.bootstrap', actor='system') 同事务（R4/R5）
Dependency  = R4/R5（FROZEN 增补）· D-P13-07（P13 零 PM 写入）·
              tg_pm_bootstrap_gate / tg_pm_last_admin 既有保护
标记        = CLI 实现形态与凭据来源为 **OPEN**（见 PREP_REPORT §4）
```

---

# 3. Explicit Exclusion（明确不属于 Runtime Slice）

指令强制要求包含的六项：

```text
· schema evolution          —— 不新增/修改任何表、列、约束、索引、触发器、函数
· permission model redesign —— 不改 RBAC/ABAC/ACL 模型
· authorization vocabulary change —— 不改 D-AUTH-05 canonical action 词表 ·
                              不改 P13 的 12 项 permission · 不新增 subject type
· migration ownership       —— 不改 178 对象所有权拓扑（全 uap_migrator）
· database privilege change —— 不新增 GRANT / REVOKE / default ACL
· P13 seed modification     —— registry 3 / permissions 12 / role_permissions 12 一律不得改动
```

附加排除（本轮一并冻结）：

```text
· 创建 0018+ migration（任何 schema 需求都必须另立独立授权，不得纳入本路线）
· 放宽 C2 / CC-7 · DISABLE TRIGGER · 引入 GUC / application_name 信任
· 修改 env.py 的 P0 修复语义（迁移事务归属）· 修改 0016 / 0017 内容
· 修改任何冻结 Decision 正文（只能 append-only 登记）
· 建立 CI（D-PLAT-17 ⑦：硬门由人工执行并留证）
· 恢复 API / 自动化恢复路径（R4/R5：恢复 = 独立维护程序 + 人工批准 + 审计）
```

---

# 4. Security Boundary（**强制章节** · 依 RUNTIME_DOCUMENT_SET_DECISION §4）

```text
SB-1 身份分离不得被削弱
     migration identity = uap_migrator · runtime identity = uap_app · 双向禁 fallback。
     Runtime **不得**获得任何 migration-only 能力（DDL / registry 写 / 角色管理）。

SB-2 C2 / CC-7 不得被放宽
     acl_subject_types 保护保持（runtime INSERT 仍拒 · CC-7 受信分支仅对
     current_user = session_user = uap_migrator 放行）。Runtime 不得尝试注册 subject type。

SB-3 不得引入可伪造的信任判据
     禁止：普通 GUC 信任 · application_name 判断 · session variable · temporary flag
     （依据 D-P13-15 + FD-1…FD-7 实测）。

SB-4 凭据与 secret 边界
     延续 D-P13-13：明文/可逆/伪造密码 = 0；onboarding 设密必须走受控安全流程；
     不得以环境变量注入初始密码。

SB-5 审计面
     runtime 事件是否写 audit_logs、actor 语义（actor_type/actor_id）属 Runtime 决策；
     audit_logs 不可变（tg_audit_immutable）⇒ 写入语义须先定义后实施。
     标记 = **OPEN**（见 PREP_REPORT §5）

SB-6 权限面不得扩张
     不得新增 GRANT / REVOKE / ALTER OWNER / default ACL；
     uap_app 的 5 项显式授权为当前封顶，扩张须独立 Human 授权。
```

---

# 5. 与 P13 / Governance Slice 的接口

```text
与 P13 的接口：
  · P13 提供：registry 3 · permissions 12 · role_permissions 12 · 身份分离 ·
              C2/CC-7 受信边界 · 明确的「未建 users / 未建 membership / 未建凭据」缺口
  · Runtime 承接：onboarding（建主体+凭据）· bootstrap（首个 PM）· 授权执行 · 服务面
  · 边界：Runtime **不修改** P13 的任何 seed 行；不改 0017；不改 P13 决策

与 Governance / Gate Slice 的接口（D-PLAT-13）：
  · 该 Slice 提供：配置门 · readiness schema 门 · legacy runner 停用 · 依赖守卫（G-1…G-8）
  · Runtime 复用其守卫与 readiness 机制，**不重建**、不修改其决策（D-PLAT-14/15/16/17）
  · 该 Slice 不是 Runtime、也不是 P14；两者不可混称
```

---

# 6. 非目标（Non-Goals）

```text
· 不在本路线内解决 OI-G-4（BATCH-D / maintenance · REGISTERED / UNFIXED）
· 不在本路线内新增业务域（domains 扩展）或行业能力
· 不在本路线内重新设计平台授权模型
· 不在本路线内引入第二套 bootstrap / dev 身份路径（D-PLAT-11②）
```

---

# 7. 状态与边界

```text
本文档 = DRAFT · NOT FROZEN（PREP 产物）
未产生实施授权。P14 IMPLEMENTATION = NOT AUTHORIZED。
本轮工程变更：DDL = 0 · DML = 0 · migration = 0 · runtime = 0 · commit/tag/push = 0
```

---

## 8. Decision Sync（append-only · 2026-09-27 · 依 PDL 附录 N）

> 本节为**追加**：不改写 §1–§7；仅把已冻结的 Human Decision 映射到本文档既有章节。
> 不写实现结果。

```text
§2.1 runtime execution layer   ← OQ-P14-10（single-host baseline + container-friendly；无强制 orchestration）
§2.2 API / service boundary    ← OQ-P14-06（apps/api = transport/adaptation；handler 不直接 SQL）
                                  OQ-P14-07（services = use-case orchestration + transaction + persistence）
§2.3 identity onboarding       ← OQ-P14-01（Service-mediated staged onboarding；
                                  pending → identity verification → credential/device verification →
                                  activation/session；客户端不得直接访问 DB；bootstrap 与普通 onboarding 分离）
§2.4 authorization enforcement ← OQ-P14-04（centralized precheck + service/use-case mandatory enforcement；
                                  handler 不承载业务授权决策）
                                  OQ-P14-05（application/service boundary · default deny · deny precedence ·
                                  ABAC · **不使用 DB RLS 作为主授权机制**）
§2.5 operational interface     ← OQ-P14-11（vendor-neutral structured observability：request ID ·
                                  correlation ID · logs · metrics · trace hooks；operational logs 与 audit 分离）
                                  OQ-P14-10（readiness/health 沿用既有决策）
§2.6 bootstrap CLI             ← OQ-P14-09（local operator-controlled CLI · explicit invocation ·
                                  one-time initialization · bootstrap state lock · 无公开网络 endpoint）
§4   Security Boundary         ← OQ-P14-12（CC-7/C2 仅 migration trust boundary；runtime 不绕过 C2 ·
                                  不模拟 uap_migrator · 不继承 migration privilege）
                                  OQ-P14-02（Argon2id hash · 禁 plaintext · 禁 secrets 写日志）
§3   Explicit Exclusion        ← OQ-P14-05（不使用 DB RLS 作主授权机制）
                                  OQ-P14-13（新 privilege 不并入本轮）
§6   Non-Goals                 ← 不变（仍禁止 schema / migration / 词表变更 / ownership 变更）
```

```text
新增明确排除项（依冻结决策）：
  · 公开网络 bootstrap endpoint（OQ-P14-09）
  · DB RLS 作为主授权机制（OQ-P14-05）
  · 本轮新增 DB role / GRANT / privilege（OQ-P14-13 · TR-3）
```

```text
本节不改写 §1–§7；文档状态仍为 PREP 产物，但其中范围表述现已有 FROZEN 决策支撑。
P14 IMPLEMENTATION = NOT AUTHORIZED（未变）。
```

---

**END OF P14_RUNTIME_SLICE SCOPE（2026-09-27 · PREP · §8 Decision Sync 追加 · Security Boundary 章节已含 · `P14 IMPLEMENTATION = NOT AUTHORIZED`）**
