# UAP — P14 IMPLEMENTATION BOUNDARY PREVIEW

> ## 轮次与边界
>
> ```text
> 轮次      = P14_RUNTIME_SLICE — HUMAN DECISION SHEET PREPARATION（Phase 5）
> 性质      = **条件性预览**（"若全部 Decision 完成，则…"）；**不是实施授权**
> 前提      = 15 项 Decision 全部完成且已按 ADD-2 登记；必要时另立授权轮
> 本轮未做   = 未创建任何 runtime code / API / CLI / migration / schema · 无 DDL / DML ·
>             未改 GRANT/REVOKE · 未 commit/tag/push
> 重要声明   = 本文件**不改变**当前状态：`P14 IMPLEMENTATION = NOT AUTHORIZED`（保持）
> ```

---

# 1. 若全部 Decision 完成 —— 允许进入的面

```text
以下为**条件性允许面**（全部以对应 Decision 已完成、且已按 ADD-2 登记为前提）：

1. Runtime implementation
   · 进程 / 服务宿主与生命周期实现（依 OQ-P14-04 判定的分层归属）
   · 依赖装配与优雅关闭
   · 前提：OQ-P14-07（services 结构）· OQ-P14-04（判定层）· ADD-1（规则载体）

2. API boundary
   · 对外接口层与其契约实现（依 OQ-P14-06 选定的协议与版本策略）
   · 错误语义 / 分页 / 幂等约定实现（依 OQ-P14-08）
   · 前提：OQ-P14-06 · OQ-P14-07 · OQ-P14-08

3. Onboarding flow
   · 首个可登录主体建立路径实现（依 OQ-P14-01 选定形态）
   · 凭据建立 / 轮换 / 失效实现（依 OQ-P14-02）
   · 设备关联（若 OQ-P14-03 选择启用）
   · 前提：OQ-P14-13（写路径）· OQ-P14-01 · OQ-P14-02（· OQ-P14-03）

4. Authorization enforcement
   · 授权判定执行实现（default deny · deny 优先 · FAIL CLOSED）
   · policy 链与调用契约（依 OQ-P14-05 的强制边界）
   · 前提：OQ-P14-04 · OQ-P14-05

5. Bootstrap process
   · 首个平台管理员建立流程实现（依 OQ-P14-09 选定的执行形态）
   · audit('platform.admin.bootstrap') 写入
   · 前提：OQ-P14-13 · OQ-P14-02 · OQ-P14-09

6. Operational surface
   · 部署与配置面落地（依 OQ-P14-10）
   · 可观测最小集落地（依 OQ-P14-11）
   · 前提：OQ-P14-02（secret）· OQ-P14-10 · OQ-P14-11

7. 与上述相关的测试与证据
   · 依 ACCEPTANCE_MATRIX（11 维度 / 49 条目）执行并留证
   · 硬门（G-1…G-4 / G-6 / G-7）人工执行并留证（D-PLAT-17 ⑦：不建 CI）
```

---

# 2. 即使全部 Decision 完成 —— 仍然禁止的面

```text
A. schema redesign
   · 不新增 / 修改任何表、列、约束、索引、触发器、函数
   · 不修改既有 156 个 pg_class 对象与 22 个 pg_proc 对象

B. migration
   · 不创建 0018+ migration 文件
   · 不修改 0001–0017（尤其 0016 / 0017）
   · 若某 Decision 结论要求 schema 变更（如 OQ-P14-05 选 B/C）
     ⇒ 必须**另立独立授权轮**，不得纳入本路线

C. permission vocabulary changes
   · 不改 D-AUTH-05 的 canonical action 词表
   · 不改 P13 的 12 项 permission（tenant.read … audit.read）
   · 不新增 subject type（acl_subject_types 维持 {user, role, agent}）
   · 不新增 deny 行（D-P13-01）

D. database governance
   · 不改 178 对象 ownership 拓扑（全 uap_migrator）
   · 不改角色拓扑与属性（RM-D 四角色）
   · 不改 default ACL（pg_default_acl 保持 0）
   · 除经 OQ-P14-13 裁定的授权轮外，不新增 GRANT / REVOKE

E. 安全边界
   · 不放宽 C2 / CC-7 · 不 DISABLE TRIGGER · 不引入 GUC / application_name 信任
   · 不修改 env.py 的 P0 修复语义 · 不改 0016 的 CC-7 实现
   · 不引入第二套 bootstrap / dev 身份路径（D-PLAT-11②）
   · 不建立恢复 API（R4/R5）

F. 流程边界
   · 不建 CI（D-PLAT-17 ⑦）
   · 不 commit / tag / push（各自独立授权）
   · 不修改冻结 Decision 正文（只能 append-only 登记）
   · 不修复 OI-G-4（BATCH-D / maintenance 范围）
   · 不进入 P15+ 或任何未来阶段编号
```

---

# 3. 边界触发停止条件（实施轮适用 · 预览）

```text
若实施过程中出现以下情形 ⇒ 停止并要求独立授权（沿用项目既有纪律）：
  ① 发现需要 schema 变更
  ② 发现需要修改 P13 seed / 0017 / 0016 / env.py
  ③ 发现需要新增权限模型或词表变更
  ④ 发现需要放宽 C2 / 引入新信任判据
  ⑤ 发现需要扩充 uap_app 授权而未经 OQ-P14-13 裁定的授权轮
  ⑥ 阶段边界不清或与其他阶段表述冲突
```

---

# 4. 与当前状态的关系

```text
当前：Decision status = PENDING · Decision filled = 0/15
      ⇒ 上述 §1 的"允许进入"**全部未生效**
      ⇒ 上述 §2 的"仍然禁止"**当前全部生效**（其中多数亦为本轮 HARD RULES 的复述）
P14 IMPLEMENTATION = NOT AUTHORIZED（保持）
```

---

# 5. 本轮工程变更

```text
DDL = 0 · DML = 0 · migration = 0 · runtime code = 0
新增文档 = 本文件（+ 同轮 3 份）· commit = 0 · tag = 0 · push = 0
```

---

**END OF P14 IMPLEMENTATION BOUNDARY PREVIEW（2026-09-27 · 条件性预览 · 未生效 · P14 IMPLEMENTATION = NOT AUTHORIZED）**
