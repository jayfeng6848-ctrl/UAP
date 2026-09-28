# UAP — P14 ACCEPTANCE DECISION MAPPING

> ## 轮次与边界
>
> ```text
> 轮次      = P14_RUNTIME_SLICE — HUMAN DECISION SHEET PREPARATION（Phase 6）
> 性质      = 只读映射（Acceptance item → Required Decision → Evidence Needed）
> 规则      = **不修改** P14_RUNTIME_SLICE_ACCEPTANCE_MATRIX.md（本轮仅新增本映射文件）
> 基线      = 矩阵当前 11 维度 / 49 条目（§2 27 + §5 22）· Decision status PENDING
> 本轮未做   = 无 schema 变更 · 无 migration · 无 GRANT/REVOKE · 无 DML · 无 runtime code · 未 commit/tag/push
> ```

---

# 1. 映射总览

```text
条目总数            = 49
需 Decision 的条目   = 27
不需 Decision 的条目 = 22（由既有冻结约束即可判定，可在裁定期间**先行**验证）
涉及 Decision      = OQ-P14-01 / 02 / 03 / 04 / 05 / 08 / 09 / 10 / 11 / 12 / 13
```

---

# 2. 矩阵 §2 条目映射（27 条目）

## 2.1 Architecture boundary

```text
ABC-1 分层依赖不变量保持
  Required Decision : 无（既有守卫 G-1…G-4）
  Evidence Needed   : pytest tests/architecture 退出码 + 用例数摘要

ABC-2 硬门保持通过
  Required Decision : 无（D-PLAT-17）
  Evidence Needed   : 每硬门正向 + 负向样例的命令与结果

ABC-3 不得削弱断言
  Required Decision : 无（纪律 Rule 10）
  Evidence Needed   : 守卫文件 diff 摘录 + 审查结论

ABC-4 无新增越界依赖
  Required Decision : OQ-P14-07（services 结构决定新增 import 落点）
  Evidence Needed   : AST 依赖扫描输出 + 新增文件清单
```

## 2.2 Security boundary

```text
SEC-1 身份分离未削弱
  Required Decision : 无（D-PLAT-10 / D-OP101-10 既有）
  Evidence Needed   : migration / runtime 两条连接的 current_user / session_user 实测

SEC-2 C2 / CC-7 未放宽
  Required Decision : 无（D-P13-03 / D-P13-15）
  Evidence Needed   : C2 md5（期望 185e95be8bc4304edbcd3f4d5cda1eff）+ runtime INSERT 拒绝探针

SEC-3 无可伪造信任判据
  Required Decision : 无（D-P13-15 + FD-1…FD-7）
  Evidence Needed   : 代码/配置检索（GUC / application_name / session var / temporary flag）

SEC-4 凭据与 secret 边界
  Required Decision : OQ-P14-02
  Evidence Needed   : 存储字段不可逆证明 + 仓库检索无明文 + 日志抽样

SEC-5 审计面语义
  Required Decision : OQ-P14-13（是否写 / 如何写审计）
  Evidence Needed   : 定义的事件清单 + 实际写入行对照

SEC-6 权限面未扩张
  Required Decision : OQ-P14-13
  Evidence Needed   : role_table_grants + nspacl + pg_default_acl 前后对照
```

## 2.3 Identity flow

```text
IDF-1 首个主体建立路径可用且受控
  Required Decision : OQ-P14-01
  Evidence Needed   : 按裁定路径的成功执行记录 + 未授权路径的拒绝记录

IDF-2 凭据生命周期符合裁定
  Required Decision : OQ-P14-02
  Evidence Needed   : 建立/存储/轮换/失效四动作证据 + 无明文存储证明

IDF-3 设备/主体关联符合词汇分离
  Required Decision : OQ-P14-03
  Evidence Needed   : acl_subject_types 精确集合（{user, role, agent}）+ 未混入 identity 词汇的检索结果
```

## 2.4 Authorization enforcement

```text
AUT-1 default deny 生效
  Required Decision : 无（D-AUTH-12）
  Evidence Needed   : 无绑定主体执行受保护动作的拒绝记录

AUT-2 deny 优先生效
  Required Decision : 无（D-AUTH-07）
  Evidence Needed   : 构造 allow+deny 并存的测试数据 + 判定结果（注意 P13 基线无 deny 行）

AUT-3 FAIL CLOSED 生效
  Required Decision : 无（D-AUTH-12）
  Evidence Needed   : 判定依赖不可用 / 不确定场景下的拒绝记录

AUT-4 授权判定位置符合裁定
  Required Decision : OQ-P14-04 · OQ-P14-05
  Evidence Needed   : 判定调用链证据 + 越层判定不存在证明
```

## 2.5 Operational readiness

```text
OPS-1 liveness / readiness 语义
  Required Decision : 无（D-PLAT-14 / D-PLAT-16）
  Evidence Needed   : /health 与 /ready 在各依赖状态下的响应（含 503 与 2000 ms 探针）

OPS-2 期望 revision 来自构建期只读工件
  Required Decision : 无（D-PLAT-15 v2）
  Evidence Needed   : 工件内容 + 运行时不可覆盖的负向探针

OPS-3 bootstrap 可执行且不可重开
  Required Decision : OQ-P14-09
  Evidence Needed   : 首次执行成功 + 二次执行被拒（bootstrap gate）+ audit 行

OPS-4 部署与可观测最小集可用
  Required Decision : OQ-P14-10 · OQ-P14-11
  Evidence Needed   : 按裁定清单逐项验证记录（部署面 + 观测面）
```

## 2.6 Failure handling

```text
FAL-1 依赖不可用时行为符合裁定
  Required Decision : OQ-P14-08
  Evidence Needed   : 超时 / 连接失败 / 部分失败三类场景的行为证据

FAL-2 幂等性
  Required Decision : OQ-P14-08
  Evidence Needed   : 重复请求前后目标表计数对照

FAL-3 错误可观测且不泄密
  Required Decision : 无（安全基线）
  Evidence Needed   : 错误响应与日志抽样（无 secret / 无内部结构细节）
```

## 2.7 Audit behavior

```text
AUD-1 审计写入语义符合定义
  Required Decision : OQ-P14-13（+ SEC-5 的裁定）
  Evidence Needed   : 规定事件清单 + audit_logs 增行对照（不多不少）

AUD-2 审计不可变性未被破坏
  Required Decision : 无（tg_audit_immutable）
  Evidence Needed   : UPDATE / DELETE 被拒探针 + 触发器仍启用

AUD-3 actor 语义正确
  Required Decision : OQ-P14-13 · OQ-P14-09
  Evidence Needed   : actor_type / actor_id 抽样与语义对照
```

---

# 3. 矩阵 §5 条目映射（22 条目）

## 3.1 Privilege boundary verification

```text
PRV-1 runtime 授权面与授权清单精确一致
  Required Decision : OQ-P14-13
  Evidence Needed   : role_table_grants / nspacl 前后对照 + 与裁定清单逐项比对

PRV-2 runtime 不持任何 DDL
  Required Decision : 无（D-OP101-08）
  Evidence Needed   : has_schema_privilege 断言 + CREATE/ALTER/DROP 负向探针

PRV-3 migration 身份不被 runtime 取得
  Required Decision : 无（基线 + D-PLAT-10）
  Evidence Needed   : SET ROLE / 以 migration 身份连接 的拒绝记录

PRV-4 default ACL 未引入
  Required Decision : 无（基线）
  Evidence Needed   : pg_default_acl 计数 = 0

PRV-5 ownership 拓扑未变
  Required Decision : 无（D-OP101-09）
  Evidence Needed   : pg_class owner 分布 + 残留计数 = 0

PRV-6 OI-G-1 状态与本轮授权一致
  Required Decision : OQ-P14-13
  Evidence Needed   : OI-G-1 的处置记录（关闭或重述）+ 权限面变更记录
```

## 3.2 Identity lifecycle verification

```text
IDL-1 主体建立恰按裁定路径
  Required Decision : OQ-P14-01
  Evidence Needed   : users 计数变化（+1 且仅 +1）+ 无旁路主体

IDL-2 凭据不以明文/可逆形式落库
  Required Decision : OQ-P14-02
  Evidence Needed   : 存储字段不可逆证明 + 库内检索

IDL-3 凭据轮换与失效
  Required Decision : OQ-P14-02
  Evidence Needed   : 轮换前后认证尝试（旧失败 / 新成功）

IDL-4 主体状态机约束
  Required Decision : 无（ck_users_status）
  Evidence Needed   : 全生命周期 status 取值采样

IDL-5 身份与授权词汇分离
  Required Decision : OQ-P14-12
  Evidence Needed   : acl_subject_types 精确集合 + 词汇混用检索

IDL-6 设备关联（若启用）
  Required Decision : OQ-P14-03
  Evidence Needed   : 关联建立/撤销记录 + 授权主体类型未变证明
```

## 3.3 Runtime failure mode verification

```text
FLM-1 依赖不可用 ⇒ FAIL CLOSED
  Required Decision : 无（D-AUTH-12）
  Evidence Needed   : 依赖失败场景下的拒绝记录 + 明确错误

FLM-2 超时语义符合裁定
  Required Decision : OQ-P14-08
  Evidence Needed   : 阈值与行为对照（readiness 侧沿用 2000 ms）

FLM-3 幂等：重复请求不产生重复副作用
  Required Decision : OQ-P14-08
  Evidence Needed   : 重复执行前后计数对照

FLM-4 部分失败不留下半成品
  Required Decision : OQ-P14-08
  Evidence Needed   : 多步失败后状态一致性证据（回滚或补偿）

FLM-5 错误信息不泄密
  Required Decision : 无（安全基线）
  Evidence Needed   : 响应/日志抽样
```

## 3.4 Audit boundary verification

```text
AUDX-1 审计写入恰好符合定义
  Required Decision : OQ-P14-13
  Evidence Needed   : 事件清单 ↔ 实际行数对照

AUDX-2 actor 语义正确
  Required Decision : OQ-P14-13（+ OQ-P14-09）
  Evidence Needed   : actor 取值抽样 + 语义对照（注意无 users FK）

AUDX-3 审计不可变性保持
  Required Decision : 无（tg_audit_immutable）
  Evidence Needed   : UPDATE/DELETE 拒绝探针

AUDX-4 分区授权连续性（OI-G-2）
  Required Decision : OQ-P14-13
  Evidence Needed   : 新分区授权处理记录 + pg_default_acl = 0

AUDX-5 审计不含敏感材料
  Required Decision : OQ-P14-02（凭据形态决定泄密面）
  Evidence Needed   : metadata 抽样检索
```

---

# 4. 反查：裁定 → 需重估的条目

```text
OQ-P14-01 → IDF-1 · IDL-1
OQ-P14-02 → SEC-4 · IDF-2 · IDL-2 · IDL-3 · AUDX-5
OQ-P14-03 → IDF-3 · IDL-6
OQ-P14-04 → AUT-4（+ 间接 ABC-4）
OQ-P14-05 → AUT-4（+ 可能触发 SCOPE Excluded 重估）
OQ-P14-06 → 间接：FLM-2/3/4 判据形态
OQ-P14-07 → 间接：ABC-4
OQ-P14-08 → FAL-1 · FAL-2 · FLM-2 · FLM-3 · FLM-4
OQ-P14-09 → OPS-3 · AUD-3 · AUDX-2
OQ-P14-10 → OPS-4
OQ-P14-11 → OPS-4
OQ-P14-12 → IDL-5
OQ-P14-13 → SEC-5 · SEC-6 · AUD-1 · AUD-3 · PRV-1 · PRV-6 · AUDX-1 · AUDX-2 · AUDX-4（9 条）
```

---

# 5. 本轮工程变更

```text
DDL = 0 · DML = 0 · migration = 0 · runtime code = 0
未修改 P14_RUNTIME_SLICE_ACCEPTANCE_MATRIX.md
新增文档 = 本文件（+ 同轮 3 份）· commit = 0 · tag = 0 · push = 0
本文件不含 Decision；P14 IMPLEMENTATION = NOT AUTHORIZED。
```

---

**END OF P14 ACCEPTANCE DECISION MAPPING（2026-09-27 · 49 条目 × Required Decision × Evidence Needed · 矩阵未修改）**
