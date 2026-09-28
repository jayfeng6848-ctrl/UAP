# UAP — P14 ACCEPTANCE DEPENDENCY NOTE

> ## 轮次与边界
>
> ```text
> 轮次      = P14_RUNTIME_SLICE — DECISION IMPACT ANALYSIS ROUND（Phase 6）
> 性质      = 只读分析说明；**不修改** P14_RUNTIME_SLICE_ACCEPTANCE_MATRIX.md
> 目的      = 登记「验收条目 ← 依赖哪些决策」，供 Human 裁定后快速定位需重估的条目
> 被引用对象 = P14_RUNTIME_SLICE_ACCEPTANCE_MATRIX.md（§2 的 27 条目 + §5 的 22 条目 = 49）
> 本轮未做   = 未修改矩阵 · 未创建 runtime code / migration / schema · 无 DDL / DML · 未 commit/tag/push
> ```

---

# 1. 汇总

```text
条目总数            = 49（§2 27 + §5 22）
不依赖任何 OQ       = 22（由既有冻结约束即可判定）
依赖至少 1 个 OQ    = 27
依赖的 OQ 集合      = OQ-P14-01 / 02 / 03 / 04 / 05 / 08 / 09 / 10 / 11 / 12 / 13
                      （OQ-P14-06 / 07 仅间接影响，见 §5）
```

---

# 2. 逐条目依赖映射（矩阵 §2：27 条目）

```text
ABC-1 分层依赖不变量保持              = 独立（既有守卫）
ABC-2 硬门保持通过                    = 独立（D-PLAT-17）
ABC-3 不得削弱断言                    = 独立（纪律）
ABC-4 无新增越界依赖                  = 间接 ← OQ-P14-07（services 结构决定新增 import 落点）

SEC-1 身份分离未削弱                  = 独立（D-PLAT/OP101 既有）
SEC-2 C2 / CC-7 未放宽                = 独立（D-P13-03/15）
SEC-3 无可伪造信任判据                = 独立（D-P13-15 + FD-1…FD-7）
SEC-4 凭据与 secret 边界              = ← OQ-P14-02
SEC-5 审计面语义                      = ← OQ-P14-13（runtime 是否写/如何写审计）
SEC-6 权限面未扩张                    = ← OQ-P14-13

IDF-1 首个主体建立路径可用且受控        = ← OQ-P14-01
IDF-2 凭据生命周期符合裁定              = ← OQ-P14-02
IDF-3 设备/主体关联符合词汇分离          = ← OQ-P14-03

AUT-1 default deny 生效                = 独立（D-AUTH-12）
AUT-2 deny 优先生效                    = 独立（D-AUTH-07）
AUT-3 FAIL CLOSED 生效                 = 独立（D-AUTH-12）
AUT-4 授权判定位置符合裁定              = ← OQ-P14-04 · OQ-P14-05

OPS-1 liveness / readiness 语义        = 独立（D-PLAT-14 / D-PLAT-16）
OPS-2 期望 revision 来自构建期只读工件   = 独立（D-PLAT-15 v2）
OPS-3 bootstrap 可执行且不可重开         = ← OQ-P14-09
OPS-4 部署与可观测最小集可用             = ← OQ-P14-10 · OQ-P14-11

FAL-1 依赖不可用时行为符合裁定           = ← OQ-P14-08
FAL-2 幂等性                           = ← OQ-P14-08
FAL-3 错误可观测且不泄密                 = 独立（安全基线）

AUD-1 审计写入语义符合定义               = ← OQ-P14-13
AUD-2 审计不可变性未被破坏               = 独立（tg_audit_immutable）
AUD-3 actor 语义正确                    = ← OQ-P14-13 · OQ-P14-09
```

---

# 3. 逐条目依赖映射（矩阵 §5：22 条目）

```text
PRV-1 runtime 授权面与授权清单精确一致    = ← OQ-P14-13
PRV-2 runtime 不持任何 DDL               = 独立（D-OP101-08 · 基线）
PRV-3 migration 身份不被 runtime 取得     = 独立（基线）
PRV-4 default ACL 未引入                  = 独立（基线）
PRV-5 ownership 拓扑未变                  = 独立（基线）
PRV-6 OI-G-1 状态与本轮授权一致            = ← OQ-P14-13

IDL-1 主体建立恰按裁定路径                = ← OQ-P14-01
IDL-2 凭据不以明文/可逆形式落库            = ← OQ-P14-02
IDL-3 凭据轮换与失效                      = ← OQ-P14-02
IDL-4 主体状态机约束                      = 独立（ck_users_status）
IDL-5 身份与授权词汇分离（D-AUTH-18）       = ← OQ-P14-12
IDL-6 设备关联（若启用）                   = ← OQ-P14-03

FLM-1 依赖不可用 ⇒ FAIL CLOSED            = 独立（D-AUTH-12）
FLM-2 超时语义符合裁定                    = ← OQ-P14-08
FLM-3 幂等：重复请求不产生重复副作用        = ← OQ-P14-08
FLM-4 部分失败不留下半成品                 = ← OQ-P14-08
FLM-5 错误信息不泄密                       = 独立（安全基线）

AUDX-1 审计写入恰好符合定义（不多不少）     = ← OQ-P14-13
AUDX-2 actor 语义正确                     = ← OQ-P14-13（+ OQ-P14-09）
AUDX-3 审计不可变性保持                    = 独立（tg_audit_immutable）
AUDX-4 分区授权连续性（OI-G-2）            = ← OQ-P14-13
AUDX-5 审计不含敏感材料                    = ← OQ-P14-02（凭据形态决定泄密面）
```

---

# 4. 反向视图：裁定后需重估的条目

```text
OQ-P14-01（onboarding flow）        → IDF-1 · IDL-1
OQ-P14-02（credential lifecycle）   → SEC-4 · IDF-2 · IDL-2 · IDL-3 · AUDX-5
OQ-P14-03（device/user）            → IDF-3 · IDL-6
OQ-P14-04（判定位置）               → AUT-4（+ 间接 ABC-4）
OQ-P14-05（强制边界）               → AUT-4（+ 可能触发 schema 边界 ⇒ 影响 SCOPE Excluded 判定）
OQ-P14-06（API boundary）           → 间接：FLM-2/3/4 的判据形态（阈值与语义）
OQ-P14-07（services 结构）          → 间接：ABC-4 的 import 落点判定
OQ-P14-08（failure handling）       → FAL-1 · FAL-2 · FLM-2 · FLM-3 · FLM-4
OQ-P14-09（bootstrap）              → OPS-3 · AUD-3 · AUDX-2
OQ-P14-10（deployment）             → OPS-4
OQ-P14-11（observability）          → OPS-4
OQ-P14-12（C2 boundary）            → IDL-5
OQ-P14-13（privilege boundary）★    → SEC-5 · SEC-6 · AUD-1 · AUD-3 · PRV-1 · PRV-6 ·
                                       AUDX-1 · AUDX-2 · AUDX-4（共 9 条目）
```

---

# 5. 观察（分析 · 非裁定）

```text
① OQ-P14-13 的验收牵连面最大（9 条目），与其实施依赖面一致 ⇒ 印证其根阻塞地位。
② 22 条独立条目（约 45%）可在裁定前预先执行（架构守卫、C2 不变性、readiness 语义、
   状态机约束、audit 不可变性等）⇒ Human 裁定期间即可先行验证，缩短后续实施轮。
③ OQ-P14-06 / 07 不直接绑定条目，仅间接影响判据形态 ⇒ 可后置（与分类 B 一致）。
④ 若 OQ-P14-05 结论为"需 DB 兜底"⇒ 将突破 SCOPE 的 Excluded（schema evolution），
   届时需同步重估 SCOPE §3 与矩阵 SEC-2 / AUT-3 的表述，并另立独立授权。
```

---

# 6. 本轮工程变更

```text
DDL = 0 · DML = 0 · migration = 0 · runtime code = 0
未修改 P14_RUNTIME_SLICE_ACCEPTANCE_MATRIX.md（本轮仅新增本说明文件）
新增文档 = 本文件（+ 同轮 3 份）· commit = 0 · tag = 0 · push = 0
P14 IMPLEMENTATION = NOT AUTHORIZED。
```

---

**END OF P14 ACCEPTANCE DEPENDENCY NOTE（2026-09-27 · 49 条目 ← OQ 依赖映射 · 独立 22 / 依赖 27 · 未修改矩阵）**
