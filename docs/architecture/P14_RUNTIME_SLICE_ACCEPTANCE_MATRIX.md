# UAP — P14_RUNTIME_SLICE ACCEPTANCE MATRIX

> ## 阶段与边界
>
> ```text
> 阶段      = `P14_RUNTIME_SLICE`（FROZEN 编号 · PDL 附录 M.1）
> 本文档性质 = PREP 设计产物（**DRAFT · NOT FROZEN**）
> 依据      = RUNTIME_DOCUMENT_SET_DECISION.md §2（本文件为其中 ACCEPTANCE_MATRIX）
> 本矩阵只建立**验证维度与判据形态**；**不填写任何实施结果**（实施尚未授权）
> 状态词表   = DRAFT（维度已定义，判据待实施轮固化）· PENDING（等待 Human Decision 的 OQ）
>              · PLANNED（实施期验证）· PASSED / FAILED 仅在实施后使用（本文件当前为 0）
> ```

---

# 1. 判定原则

```text
① 每条判据必须**可机械判定**（给定实施结果即可判 PASS / FAIL），不得依赖设计再解释
② 证据必须可复核：命令 + 退出码 + 输出摘要（沿用 D-PLAT-17 ⑦ 的留证要求）
③ 硬门（D-PLAT-17 的 G-1…G-4/G-6/G-7）在实施前后均须保持通过
④ 禁止为通过验收而削弱断言 / 引入 fallback / 扩大 scope（Rule 10）
⑤ 本路线内的任何 schema / 权限扩面需求 ⇒ 一律转「独立授权」，不得在本矩阵内消化
```

---

# 2. 验证维度

## 2.1 Architecture boundary

```text
条目      = ABC-1 … ABC-4
ABC-1  分层依赖不变量保持
       判据 = tests/architecture 全量执行退出码 = 0，且既有用例数不减少
       证据 = pytest tests/architecture -q（命令 + 退出码 + 摘要）
ABC-2  硬门保持通过
       判据 = G-1 ~ G-4 · G-6 · G-7 全部 PASS（含各硬门的**负向样例**可使其失败）
       证据 = 每门一组正向 + 一组负向样例，记录命令与结果
ABC-3  不得为通过而削弱断言
       判据 = 对比实施前后守卫文件差异：不得删除/放宽既有断言
       证据 = git diff 摘录 + 审查结论
ABC-4  无新增越界依赖
       判据 = 新增 imports 全部落在允许层内（AST 判定，禁止字符串匹配）
状态   = DRAFT（判据形态已定；阈值与样例待实施轮固化）
```

## 2.2 Security boundary

```text
条目      = SEC-1 … SEC-6（对齐 SCOPE §4 的 SB-1…SB-6）
SEC-1  身份分离未削弱
       判据 = migration 路径 current_user = session_user = uap_migrator；
              runtime 路径 = uap_app；runtime 无法执行任何 migration-only 操作（负向探针）
SEC-2  C2 / CC-7 未放宽
       判据 = C2 函数 md5 未变（当前 185e95be8bc4304edbcd3f4d5cda1eff）；
              runtime 对 acl_subject_types 的 INSERT / DELETE 仍被拒
SEC-3  无可伪造信任判据
       判据 = 代码与配置中不出现 GUC / application_name / session variable / temporary flag 判据
SEC-4  凭据与 secret 边界
       判据 = 无明文 / 可逆 / 伪造密码；无环境变量注入初始密码；secret 不落盘仓库
SEC-5  审计面语义
       判据 = runtime 写 audit_logs 的行符合实施轮定义的 action / actor 语义（待 OQ-P14 裁定）
SEC-6  权限面未扩张
       判据 = uap_app 显式授权项数 = 实施轮经授权后的既定值（当前 5）；
              无新增 GRANT / REVOKE / ALTER OWNER / default ACL
状态   = DRAFT · SEC-5 依赖 OQ-P14-13 等裁定 → PENDING
```

## 2.3 Identity flow

```text
条目      = IDF-1 … IDF-3
IDF-1  首个可登录主体建立路径可用且受控（依赖 OQ-P14-01）
       判据 = 按 Human 裁定的路径可完成「建主体 + 设凭据」；未授权路径不可用
IDF-2  凭据生命周期符合裁定（依赖 OQ-P14-02）
       判据 = 建立 / 存储 / 轮换 / 失效四个动作均有可复核证据；无明文存储
IDF-3  设备 / 主体关联符合 D-AUTH-18 词汇分离
       判据 = acl_subject_types 仍为 {user, role, agent}；未把 identity kind/provider 词汇
              混入授权主体类型
状态   = PENDING（依赖 Identity 三项 OQ）
```

## 2.4 Authorization enforcement

```text
条目      = AUT-1 … AUT-4
AUT-1  default deny 生效
       判据 = 无任何授权绑定的主体执行受保护动作 ⇒ 拒绝
AUT-2  deny 优先生效
       判据 = 同时存在 allow / deny 时，判定结果为拒绝（注意：P13 基线**无 deny 行**，
              该判据需在实施轮构造测试数据）
AUT-3  FAIL CLOSED 生效
       判据 = 判定依赖不可用 / 结果不确定时 ⇒ 拒绝（不得放行、不得降级）
AUT-4  授权判定位置符合裁定（依赖 OQ-P14-04 / OQ-P14-05）
       判据 = 判定发生在 Human 指定层；越层判定 = FAIL
状态   = DRAFT · AUT-2/AUT-4 → PENDING
```

## 2.5 Operational readiness

```text
条目      = OPS-1 … OPS-4
OPS-1  liveness / readiness 语义符合既有决策
       判据 = /health = liveness（不随 DB 状态失败）；/ready = readiness（DB 异常 ⇒ 503）
              探针超时 = 2000 ms（D-PLAT-16）· 失败不重试不降级
OPS-2  期望 revision 校验来自构建期只读工件
       判据 = 运行时不可覆盖（D-PLAT-15 v2）；缺失/无效 ⇒ error + critical
OPS-3  bootstrap 路径可执行且不可重开
       判据 = 条件 = platform_state='uninitialized' AND PM 无行；成功后路径永久关闭
              （依赖 OQ-P14-09）
OPS-4  部署与可观测最小集可用（依赖 OQ-P14-10 / OQ-P14-11）
       判据 = 按裁定产出的部署与观测面清单逐项可验证
状态   = DRAFT · OPS-3/OPS-4 → PENDING
```

## 2.6 Failure handling

```text
条目      = FAL-1 … FAL-3
FAL-1  依赖不可用时的行为符合裁定（依赖 OQ-P14-08）
       判据 = 超时 / 连接失败 / 部分失败三类场景各有明确定义的行为与证据
FAL-2  幂等性
       判据 = 相同请求重复执行不产生重复副作用（或以明确语义拒绝）
FAL-3  错误可观测且不泄密
       判据 = 错误响应不含 secret / 内部结构细节；日志中不出现凭据材料
状态   = PENDING（依赖 Service 三项 OQ）
```

## 2.7 Audit behavior

```text
条目      = AUD-1 … AUD-3
AUD-1  审计写入语义符合实施轮定义（依赖 OQ-P14-13 / SEC-5）
       判据 = 规定的 runtime 事件**恰好**产生预期 audit_logs 行（不多不少）
AUD-2  审计不可变性未被破坏
       判据 = tg_audit_immutable 仍启用；对 audit_logs 的 UPDATE / DELETE 仍被拒
AUD-3  actor 语义正确
       判据 = actor_type / actor_id 取值符合定义（system vs user）；
              不因 audit_logs 无 users FK 而写入不可解释的 actor
状态   = PENDING
```

---

# 3. 汇总

```text
维度总数 = 7（Architecture · Security · Identity · Authorization · Operational ·
              Failure · Audit）
条目总数 = 4 + 6 + 3 + 4 + 4 + 3 + 3 = 27
当前状态 = 全部 DRAFT 或 PENDING（实施尚未授权）
PASSED = 0 · FAILED = 0（本文件不填实施结果）

阻塞依赖 = OQ-P14-01…13（共 13 项 OPEN · 见 P14_RUNTIME_SLICE_PREP_REPORT §2）
```

---

# 4. 边界

```text
本文档 = DRAFT · NOT FROZEN。未产生实施授权。P14 IMPLEMENTATION = NOT AUTHORIZED。
本轮工程变更：DDL = 0 · DML = 0 · migration = 0 · runtime = 0 · commit/tag/push = 0
```

---

## 5. 补充验证维度（append-only · 2026-09-27 · DECISION PREPARATION ROUND）

> 本节为**追加**：不改写 §1–§4；仅新增验证维度，**不新增任何实现结果**。
> 全部条目状态保持 `DRAFT` 或 `PENDING`（实施尚未授权）。

### 5.1 Privilege boundary verification（PRV）

```text
PRV-1  runtime 授权面与授权清单**精确一致**
       判据 = uap_app 的 non-owner 显式授权项集合 == 实施轮经 Human 授权的既定集合
              （多一项 / 少一项 / 动词不符 = FAIL）
       证据 = information_schema.role_table_grants + nspacl 摘录（前后各一次）
PRV-2  runtime 不持任何 DDL
       判据 = has_schema_privilege('uap_app','public','CREATE') = false；
              且 runtime 执行 CREATE TABLE / ALTER / DROP 均被拒（负向探针）
PRV-3  migration 身份不被 runtime 取得
       判据 = runtime 身份无法 SET ROLE 到 uap_migrator；无法以 uap_migrator 身份连接
       证据 = 负向探针（错误文本记录）
PRV-4  default ACL 未引入
       判据 = pg_default_acl 计数 = 0
PRV-5  ownership 拓扑未变
       判据 = public 下 pg_class 全部 owner = uap_migrator · 残留 = 0
PRV-6  OI-G-1 状态与本轮授权一致
       判据 = 若已扩权 ⇒ OI-G-1 已被 Human 明确处理（关闭或重述）；
              若未扩权 ⇒ OI-G-1 保持 REGISTERED 且 runtime 权限面未变
状态   = PENDING（依赖 OQ-P14-13 裁定）
```

### 5.2 Identity lifecycle verification（IDL）

```text
IDL-1  主体建立：恰按裁定路径产生主体行，且不产生额外主体
       判据 = 建立 1 个主体的操作 ⇒ users 计数 +1（且仅 +1）；无旁路主体产生
IDL-2  凭据：不以明文 / 可逆形式落库
       判据 = 存储字段（如口令哈希）不可逆；库内与日志中不出现原始口令
IDL-3  凭据轮换与失效：轮换后旧凭据失效、新凭据可用
       判据 = 轮换前后各做一次认证尝试（旧失败 / 新成功）
IDL-4  主体状态机：status 取值始终 ∈ {pending, active, suspended, locked, deleted}
       判据 = 全生命周期采样均满足 ck_users_status
IDL-5  身份与授权词汇分离（D-AUTH-18）
       判据 = acl_subject_types 仍精确 = {user, role, agent}；
              未把 identity kind/provider 值写入授权主体类型
IDL-6  设备关联（若裁定启用，OQ-P14-03）
       判据 = 关联关系可建立 / 可撤销；未引入授权主体类型变化
状态   = PENDING（依赖 OQ-P14-01 / 02 / 03）
```

### 5.3 Runtime failure mode verification（FLM）

```text
FLM-1  依赖不可用 ⇒ FAIL CLOSED（拒绝，不放行不降级）
       判据 = 制造依赖失败（DB 不可达 / 超时）⇒ 受保护操作被拒；日志有明确错误
FLM-2  超时语义符合裁定
       判据 = 超时阈值与行为与 Human 裁定一致（readiness 侧沿用 2000 ms · D-PLAT-16）
FLM-3  幂等：重复请求不产生重复副作用
       判据 = 相同请求重复执行后，目标表计数与首次一致（或语义化拒绝）
FLM-4  部分失败不留下半成品
       判据 = 多步操作失败后，事务回滚或补偿后状态与操作前一致（无半写）
FLM-5  错误信息不泄密
       判据 = 响应与日志中不含凭据 / 连接串 / 内部结构细节
状态   = PENDING（依赖 OQ-P14-08 等）
```

### 5.4 Audit boundary verification（AUDX）

```text
AUDX-1 审计写入**恰好**符合定义（不多不少）
       判据 = 规定事件 ⇒ audit_logs 增加 1 行（或裁定条数）；未规定事件 ⇒ 不增加
AUDX-2 actor 语义正确
       判据 = actor_type / actor_id 与裁定语义一致（system vs user）；
              注意 audit_logs **无 users FK** ⇒ 不允许写入不可解释的 actor
AUDX-3 审计不可变性保持
       判据 = 对 audit_logs 的 UPDATE / DELETE 仍被 tg_audit_immutable 拒绝
AUDX-4 分区授权连续性（OI-G-2 连带）
       判据 = 若存在新分区且 runtime 需写审计 ⇒ 该分区授权已被显式处理
              （否则为新分区的写入失败；pg_default_acl 保持 0）
AUDX-5 审计不含敏感材料
       判据 = metadata 中不出现凭据 / secret / 完整连接串
状态   = PENDING（依赖 OQ-P14-13 / SEC-5 / OQ-P14-02）
```

### 5.5 汇总（补充维度）

```text
新增维度 = 4（PRV / IDL / FLM / AUDX）
新增条目 = 6 + 6 + 5 + 5 = 22
累计（§2 + §5）= 维度 11 · 条目 49
全部状态 = DRAFT / PENDING · PASSED = 0 · FAILED = 0
```

---

## 7. Decision Sync（append-only · 2026-09-27 · 依 PDL 附录 N）

> 本节为**追加**：不改写 §1–§6；仅登记「每个 PENDING 条目现由哪条**已冻结**决策约束」。
> **所有条目的判定状态保持 PENDING**（实施前不得填写 PASS / FAIL）。

```text
条目              ← 已冻结决策（PDL 附录 N）
ABC-4            ← OQ-P14-06（handler 不直接 SQL）· OQ-P14-07（services/domains 边界）
SEC-4            ← OQ-P14-02（Argon2id hash · 禁 plaintext · 禁 secrets 写日志）
SEC-5            ← OQ-P14-11（audit 与 operational logs 分离）· OQ-P14-13（审计写入不经宽泛扩权）
SEC-6            ← OQ-P14-13（uap_app 保持最小权限 · 本轮不新增 role/GRANT）
IDF-1            ← OQ-P14-01（staged onboarding · 客户端不得直接访问 DB）
IDF-2            ← OQ-P14-02（credential 独立生命周期）
IDF-3            ← OQ-P14-03（1 User : N Device · 1 Device : 1 User）
AUT-4            ← OQ-P14-04（centralized precheck + service enforcement）·
                    OQ-P14-05（application/service boundary · 不使用 DB RLS 作主授权机制）
OPS-3            ← OQ-P14-09（local operator-controlled CLI · one-time · state lock · 无公开 endpoint）
OPS-4            ← OQ-P14-10（single-host baseline + container-friendly）·
                    OQ-P14-11（vendor-neutral structured observability）
FAL-1 / FAL-2    ← OQ-P14-08（fail-closed · 错误分类 · rollback · bounded retry · no blanket retry）
FLM-2/3/4        ← OQ-P14-08
AUD-1 / AUD-3    ← OQ-P14-11（分离）· OQ-P14-09（bootstrap audit）· OQ-P14-13
PRV-1 / PRV-6    ← OQ-P14-13（OPTION B：uap_app 最小权限 · 独立 trusted principal · 新 privilege 另开 Gate）
IDL-5            ← OQ-P14-12（CC-7/C2 仅 migration trust boundary）
IDL-6            ← OQ-P14-03
AUDX-1 / AUDX-2  ← OQ-P14-13 · OQ-P14-09
AUDX-4           ← OQ-P14-13（分区授权连续性属未来 Gate）
AUDX-5           ← OQ-P14-02（secret 不得进入日志/审计 metadata）
（未列出的条目）  ← 不受决策约束，依既有冻结约束（守卫 / C2 / readiness 语义 / 状态机 / 审计不可变性）
```

```text
新增条目（依冻结决策登记为 PENDING）：
  PRV-7  Privilege Precondition 未被误当作已完成
        判据 = 存在明确登记：uap_app 权限不足 + 解决方式 = Trusted Internal Service Boundary +
                新 principal/GRANT 属独立 Gate；且本轮未执行任何 GRANT / CREATE ROLE
        状态 = PENDING（实施期核验）
  PRV-8  Runtime 未使用 uap_migrator 身份
        判据 = runtime 路径的连接身份 ≠ uap_migrator；无 SET ROLE / 无 migration 凭据使用
        状态 = PENDING
```

```text
状态汇总（未变）：全部条目 PENDING（或既有 DRAFT）· PASSED = 0 · FAILED = 0
本节不写任何实现结果；Acceptance 判定须待 Runtime 真正实施后执行。
P14 IMPLEMENTATION = NOT AUTHORIZED（未变）。
```

---

**END OF P14_RUNTIME_SLICE ACCEPTANCE MATRIX（2026-09-27 · PREP · §2 27 + §5 22 + §7 新增 2 = 51 条目 / 11 维度 · §7 Decision Sync 追加 · 全部 PENDING · `P14 IMPLEMENTATION = NOT AUTHORIZED`）**
