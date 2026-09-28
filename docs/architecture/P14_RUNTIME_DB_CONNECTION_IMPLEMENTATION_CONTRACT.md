# UAP — P14 RUNTIME DB CONNECTION IMPLEMENTATION CONTRACT

> ## 状态
>
> ```text
> 轮次      = P14 SECURITY CLOSURE + RUNTIME IMPLEMENTATION AUTHORIZATION PREPARATION（§十四）
> 性质      = 实现契约（**设计** · 未实施）
> 依据      = SEC-P14-01/02/11/12/14 ・ P14_RUNTIME_CONNECTION_SECURITY_NOTE
>             ・ 已实施之 Security DB Boundary（uap_runtime 51 / uap_bootstrap 6 · ACCEPTED）
> 基线      = HEAD c420403d… · migration 0017_p13_seed · 0018+ = 0
> 本轮未做   = 未修改任何连接配置 / 未创建凭据 / 未写代码
> ```

---

# 1. Identity Binding（身份绑定）

```text
DC-1  Runtime service 使用 **`uap_runtime`** 连接数据库（唯一 runtime 身份）
DC-2  **不允许**读取 / 使用 `uap_migrator` credential
DC-3  **不允许**读取 / 使用 `uap_bootstrap` credential（bootstrap 属独立一次性路径）
DC-4  **不允许**复用 `uap_app` / `uap_seed` credential 作为 runtime 身份
DC-5  连接建立后必须**正向断言**：current_user = session_user = 'uap_runtime'；
      断言失败 ⇒ FAIL-CLOSED 拒绝启动（沿用 env.py 的角色断言思路）
DC-6  断言不得依赖可伪造判据（GUC / application_name / session variable / temporary flag）
```

---

# 2. Credential Source（凭据来源）

```text
DC-7  credential **不进入 repository**（源码 / 配置文件模板 / 测试 fixture 皆不得含明文）
DC-8  credential 经部署面注入（与既有 DATABASE_URL 通道同族：环境变量 / secret 注入）
DC-9  credential **不得**出现在：operational log · audit payload · exception message ·
      错误响应 · 测试 evidence 文件
DC-10 违反 DC-7/DC-8/DC-9 的实现 ⇒ BLOCKED（须立即修正并重新验证）
```

---

# 3. Connection Pool（连接池）

```text
DC-11 连接池**不得跨身份复用**（runtime / migration / bootstrap 三者物理隔离）
DC-12 池**不得泄露 secret**：连接串不得出现在日志、异常、监控标签、trace 属性中
DC-13 支持凭据轮换语义：
        · 设置连接存活期上限（max_lifetime）或在轮换后重建池
        · 轮换期间允许"新旧并存窗口"（见 Connection Security Note §3）
DC-14 支持撤销语义：
        · 撤销后既有连接不会自动断开 ⇒ 须配套终止活动会话 + 重连
        · 实施轮须以负向探针验证"撤销后旧池不再可用"
DC-15 池参数（size / timeout）属部署配置，不属于本项目 schema 或权限面
```

---

# 4. Transaction Boundary（事务边界）

```text
DC-16 事务边界由 **service / use-case** 控制（Contract §7 SC-2）：
        一个 use-case = 一个事务（或明确划分的多个事务），由 service 层开启/提交/回滚
DC-17 repository / adapter **不得**自行提交或回滚（不得持有事务所有权）
DC-18 handler **不得**开启事务（handler = transport/adaptation）
DC-19 需要原子性的复合动作必须在单一事务内完成，例如：
        · device revoke + 其 active sessions 撤销（SEC-P14-03 / OQ-P14-03）
        · bootstrap：插 PM + 翻转 platform_state + audit（R4/R5）
DC-20 事务内失败必须 **rollback**（不得留下半成品 · Contract §10 FR-3）
```

---

# 5. Rollback Semantics

```text
DC-21 任何未处理的异常必须触发事务回滚（不吞异常、不静默提交）
DC-22 回滚后连接必须回到可复用状态（不得留下 aborted transaction 影响后续请求）
DC-23 部分失败场景必须有明确语义（要么整体回滚，要么明确补偿；不得"半写"）
DC-24 回滚不得影响其他并发事务（正确隔离级别由既有默认承担）
```

---

# 6. Bounded Retry

```text
DC-25 retry 仅限**幂等 / 安全**场景（Contract §10 FR-4）
DC-26 retry 必须 **bounded**（有上限 + 退避）；**no blanket retry**
DC-27 非幂等写操作默认**不重试**（依赖失败 ⇒ 拒绝并上报）
DC-28 重试不得跨越事务边界造成重复副作用（需幂等键或天然幂等）
```

---

# 7. Fail-Closed

```text
DC-29 数据库不可达 / 超时 / 授权判定不确定 ⇒ **拒绝**（不放行、不降级）
DC-30 连接身份断言失败 ⇒ 拒绝启动（DC-5）
DC-31 权限不足（如误用未授权对象）⇒ 受控错误（见 §8），不得静默降级为"无数据"
DC-32 readiness 语义沿用既有决策：探针失败 ⇒ /ready 503（D-PLAT-14 / D-PLAT-16）
```

---

# 8. Unexpected Privilege Failure → Controlled Error

```text
DC-33 若 runtime 命中未授权对象（InsufficientPrivilege），必须表现为**受控错误**：
        · 不暴露内部结构细节 / 不泄露连接串 / 不泄露对象清单
        · 记录为可观测错误（operational log 层面，不含 secret）
        · 不重试（属配置 / 授权缺陷，重试无意义）
DC-34 受控错误不得被上层吞掉转为"成功"或"空结果"
DC-35 该类错误计数应可观测（monitoring/metrics 现有面可承载）
```

---

# 9. 与 Security DB Boundary 的关系

```text
DC-36 本契约**只消费**已实施的授权面（uap_runtime 的 51 row-grants），**不新增任何授权**
DC-37 若实现过程中发现缺少某项授权 ⇒ **BLOCKED**：须重开 Security Decision
       （OI-G-1 已 CLOSED 不构成自动扩权许可）
DC-38 Security DB Boundary 为**冻结资产**（见 Closure Report §16）；连接实现不得修改它
```

---

# 10. 本轮工程变更

```text
未修改任何文件 · 未创建凭据 · 未改动 env.py / settings.py / compose / alembic.ini
DDL / DML / migration / runtime code = 0 · new role / grant / revoke = 0
新增文档 = 本文件（+ 同轮 6 份）· commit = 0 · tag = 0 · push = 0
P14 RUNTIME IMPLEMENTATION = NOT AUTHORIZED
```

---

**END OF P14 RUNTIME DB CONNECTION IMPLEMENTATION CONTRACT（2026-09-27 · 38 条实现契约（DC-1…DC-38）· 未实施 · 未改动任何配置）**
