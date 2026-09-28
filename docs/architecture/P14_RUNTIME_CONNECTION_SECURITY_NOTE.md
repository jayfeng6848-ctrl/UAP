# UAP — P14 RUNTIME CONNECTION SECURITY NOTE

> ## 状态
>
> ```text
> 轮次      = P14 SECURITY CANONICAL REGISTRATION + IMPLEMENTATION GATE PREPARATION
> 状态      = 设计说明（**仅设计** · 未实施）
> 依据      = PDL 附录 O（SEC-P14-01 / 02 / 11 / 12 / 14）· P14 Connection 相关冻结约束
> 基线      = HEAD c420403d… · pg_hba：容器内 socket trust / 宿主 TCP 经 bridge → scram（需口令）
> 本轮未做   = 未创建任何角色 / 凭据 · 未执行 GRANT / REVOKE · 未修改 env.py / settings / compose
> ```

---

# 1. 身份与连接拓扑（目标状态）

```text
Runtime service
      │  使用 dedicated runtime principal 的凭据
      ▼
Trusted Internal Service Boundary（SEC-02）
      │  经宿主 TCP（scram 认证）
      ▼
PostgreSQL（uap_b1_test / 未来正式库）

其余身份**不参与** Runtime 连接：
  · uap_migrator  → 仅 migration 执行（UAP_MIGRATION_DATABASE_URL）
  · uap_seed      → 仅 seed 受信 context（不承担 runtime 角色）
  · uap_app       → 保持现状（5 项授权）· 不因 Runtime 缺口扩权
  · bootstrap principal → 仅一次性本地 operator bootstrap（SEC-11）
```

---

# 2. Credential 获取（依 SEC-12）

```text
Runtime principal 凭据来源（设计）：
  · 受信内部 Service Boundary 的部署面注入（与既有 DATABASE_URL 通道同族）
  · **不得**进入 source code · **不得**进入 repository
  · **不得**进入普通日志（operational log）· **不得**进入 audit
  · **不得**出现在 CLI argument · **不得** hard-code

Bootstrap principal 凭据来源（依 SEC-12 · 仅设计）：
  · 默认 = LOCAL OPERATOR-CONTROLLED INTERACTIVE SECRET INPUT
  · 受控部署环境允许 LOCAL SECRET FILE / CONTAINER SECRET
  · 不得进入 CLI argument / hard-code / shell history / 日志 / audit / 明文持久化
```

---

# 3. Rotation（轮换）

```text
RT-1  Runtime principal 凭据**独立轮换**（SEC-01：与 migration / seed lifecycle 分离）
RT-2  轮换流程须支持"新旧凭据并存窗口"（避免连接中断）：
        step 1 生成新凭据并更新部署面 secret
        step 2 滚动重启 / 重连使新凭据生效
        step 3 确认无旧凭据连接后废弃旧凭据
RT-3  轮换不得要求 schema 变更 / 不得修改 pg_hba 规则文件之外的信任模型
RT-4  bootstrap 凭据**不参与** Runtime 轮换（SEC-12：完成后不得自动成为 runtime credential）
```

---

# 4. Revocation（撤销）

```text
RV-1  Runtime principal 凭据撤销后，既有连接**必须在有限时间内失效**：
        · 撤销 ≠ 立即断开既有会话（PostgreSQL 不自动断开）
        · 因此须配套：终止该 principal 的活动会话（pg_terminate_backend）+ 重连
        · 该动作属实施轮运维规程，不在本轮执行
RV-2  principal 层面的撤销（角色禁用 / 移除授权）同样需要"断连 + 重连"配合
RV-3  bootstrap principal 在 one-time bootstrap 完成后进入**不可再用**状态（SEC-11 / 12 / 13）
```

---

# 5. Connection Pool 行为（设计约束）

```text
CP-1  连接池**不得**跨身份复用连接（runtime / migration / bootstrap 三者隔离）
CP-2  credential 轮换或撤销后，池内既有连接**仍持有旧身份**⇒ 必须支持：
        · 池重建（restart）或
        · 连接存活期上限（max_lifetime）与回收
        · 并在实施轮以负向探针验证"撤销后旧池不再可写"
CP-3  连接参数不得携带可伪造信任判据：
        禁止 application_name 作为信任判据 · 禁止 GUC 作为信任判据 ·
        禁止 session variable / temporary flag 作为信任判据（D-P13-15）
CP-4  连接身份必须在启动时**正向断言**（current_user = session_user = 目标 principal），
      失败即 FAIL-CLOSED 拒绝启动（沿用 env.py 的角色断言思路）
CP-5  连接池实现不得引入新的 DB 角色或 default ACL
```

---

# 6. 凭据隔离矩阵（设计）

```text
凭据类别                 使用方                       可否复用
----------------------   -------------------------   --------------------------------
migration credential     Alembic（UAP_MIGRATION_…）   **不得**被 runtime 使用
seed credential（如需）   seed 受信路径                 **不得**被 runtime 使用
runtime credential       受信内部 Service Boundary     **独立**（不与上两者共享）
bootstrap credential     本地 operator one-time        **一次性**；完成后不得转为 runtime
uap_app credential       现状应用面（若仍使用）         不得因 Runtime 需求扩大其权限
```

---

# 7. 与既有权衡的边界

```text
· 本 Note **不修改** env.py / settings.py / compose / alembic.ini
· 本 Note **不创建**任何角色或凭据
· 本 Note **不改变** pg_hba / scram 约定
· 本 Note 的所有条目均为**实施轮输入**（Security Implementation Gate 的执行对象）
```

---

**END OF P14 RUNTIME CONNECTION SECURITY NOTE（2026-09-27 · 设计说明 · 未实施 · 未创建角色/凭据）**
