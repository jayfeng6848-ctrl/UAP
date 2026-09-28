# UAP — P14 IMPLEMENTATION DECISION ORDER

> ## 轮次与边界
>
> ```text
> 轮次      = P14_RUNTIME_SLICE — DECISION IMPACT ANALYSIS ROUND（Phase 5）
> 性质      = **顺序建议**（Human Decision Order）；不含任何 OPTION 选择、不含内容裁定
> 依据      = P14_DECISION_DEPENDENCY_GRAPH.md（拓扑序）· P14_DECISION_IMPACT_ANALYSIS.md（影响面）
> 本轮未做   = 未创建 runtime code / API / CLI / migration / schema · 无 DDL / DML ·
>             未改 GRANT / REVOKE · 未 commit / tag / push
> ```

---

# 1. 排序总览

```text
批次 0   登记位置先决        : ADD-2（P14 决策登记于 PDL 附录 vs Contract 内附录）
批次 1   根阻塞              : OQ-P14-13（runtime privilege boundary）
批次 2   安全边界声明        : OQ-P14-12（C2 trust boundary usage）
批次 3   Identity 骨架       : OQ-P14-01 → OQ-P14-02
批次 4   Authorization 骨架  : OQ-P14-04 → OQ-P14-05
批次 5   Bootstrap           : OQ-P14-09
批次 6   载体与服务结构       : ADD-1（Contract 载体）· OQ-P14-07（C-5 services 结构）
批次 7   对外契约            : OQ-P14-06（API boundary）
批次 8   运行与部署          : OQ-P14-10 · OQ-P14-03
批次 9   实施期细化（可后置） : OQ-P14-08 · OQ-P14-11
⇒ 之后            : 更新 ACCEPTANCE_MATRIX 的 PENDING 项 → 提交 P14 IMPLEMENTATION AUTHORIZATION
```

---

# 2. 逐批次说明（原因 · 解锁什么）

## 批次 0 — ADD-2（决策登记位置）

```text
为什么最先：它是"裁定写在哪里"的元决策。
  若登记位置在第一批 OQ 裁定之后才定，已裁内容可能需要二次搬运（重复劳动 + 漂移风险）。
  与内容无关（不触碰任何架构选择），但决定后续所有裁定的落点。
解锁：为批次 1 起的全部裁定提供登记载体。
```

## 批次 1 — OQ-P14-13（runtime privilege boundary）★

```text
为什么最先（内容层）：它是依赖图的**根节点**，且是唯一的"存在性"问题——
  未定之前，onboarding / bootstrap / 授权读取**全部无法落地**（当前 uap_app 连 SELECT 都没有）。
  同时它是唯一会触碰 GRANT 面的决策，牵动 D-OP101-07 与 OI-G-1 两项既有登记。
解锁：OQ-01 / 02 / 03 / 04（读侧）/ 09 的可实现性；以及"是否需要独立授权轮承载 GRANT"的判定。
```

## 批次 2 — OQ-P14-12（C2 trust boundary usage）

```text
为什么第二：它是一句边界声明（Runtime 是否完全不触碰 registry），成本低但价值高——
  它把批次 1 的候选空间收窄（排除"通过改 registry 绕开权限问题"这一分支），
  并直接对应验收项 SEC-2 / IDL-5。
解锁：批次 3–5 的安全前提；使 OPTION 比较在明确边界内进行。
```

## 批次 3 — OQ-P14-01 → OQ-P14-02（Identity 骨架）

```text
为什么此时：二者共同定义"平台如何获得第一个可用主体"，
  是批次 1 的写权限需求能否收敛的具体来源（决定要写哪几张表、写什么）。
  01 先于 02：主体形态未定则凭据无宿主。
解锁：identity runtime 设计、onboarding flow 形态、IDL-1…IDL-6 判据固化。
```

## 批次 4 — OQ-P14-04 → OQ-P14-05（Authorization 骨架）

```text
为什么此时：判定位置与强制边界决定"读哪些表、在哪一层读"，
  与批次 1 的读权限面直接耦合；04 先于 05（位置先于边界强度）。
解锁：services/authorization 的建立方式（D-AUTH-16 记「包尚不存在」）、
      AUT-1…AUT-4 的可判定性、以及是否触发"DB 兜底 ⇒ schema 边界"的判定。
```

## 批次 5 — OQ-P14-09（Bootstrap）

```text
为什么此时：bootstrap 是平台最高权限入口，其写入面
  （platform_memberships / platform_state）在批次 1 已确定路径后才有意义；
  同时它依赖批次 3 的凭据结论。
解锁：平台初始化能力、OPS-3 判据、audit('platform.admin.bootstrap') 的写入语义。
```

## 批次 6 — ADD-1（Contract 载体）· OQ-P14-07（C-5 services 结构）

```text
为什么此时：前 5 批已产出足够的架构结论（身份/判定/引导），
  此时才可能写出"实施规则"（F-4）而不空转；services 结构也随之可定。
解锁：实施规则载体（OPTION 1/2/3 的落地）、模块边界、守卫对应义务。
```

## 批次 7 — OQ-P14-06（API boundary）

```text
为什么此时：对外契约依赖判定层（批次 4）与服务结构（批次 6）。
解锁：OPS-1 之外的接口面判据、错误与版本语义、C-6 契约载体。
```

## 批次 8 — OQ-P14-10（deployment）· OQ-P14-03（device/user）

```text
为什么此时：部署与 secret 注入依赖凭据方案（批次 3）；
  设备关联属身份模型的延伸，可在骨架确定后收敛。
解锁：OPS-4 判据（含 C-10 部署手册）、IDF-3 / IDL-6。
```

## 批次 9 — OQ-P14-08（failure handling）· OQ-P14-11（observability）

```text
为什么最后：二者属实施期细化（分类 C），在 API 与部署形态确定后即可在实施轮内决定；
  提前裁定反而可能因信息不足而反复。
解锁：FAL-* / FLM-* / OPS-4 的最终阈值与范围。
```

## 终态 — 进入 P14 IMPLEMENTATION AUTHORIZATION 的条件

```text
必要条件（建议）：
  ① 批次 0–7 全部裁定并登记（含 ADD-2 登记位置、ADD-1 载体）
  ② ACCEPTANCE_MATRIX 中所有 PENDING 项已随裁定转为 DRAFT-可判定（或明确保留到实施轮）
  ③ 若批次 1 结论要求 GRANT 面变更 ⇒ 已另行取得"授权轮"授权（本路线 Excluded 不含扩权）
  ④ 无遗留 active contradiction
⇒ 之后方可提交 P14 IMPLEMENTATION AUTHORIZATION（独立 Human 指令）
```

---

# 3. 顺序依据摘要（机读）

```text
拓扑要求：13（根）· 12（边界声明）→ 01/04 → 02/05/07 → 03/06/09/11 → 08
本建议把"元决策（ADD-2）"提前到 0，"载体决策（ADD-1）"后移到 6，
理由是：前者影响所有裁定的落点；后者需要前 5 批的结论才有内容可写。
本建议**不改变**任何 OQ 的内容取向；仅给出执行次序。
```

---

# 4. 本轮工程变更

```text
DDL = 0 · DML = 0 · migration = 0 · runtime code = 0
新增文档 = 本文件（+ 同轮 3 份）· commit = 0 · tag = 0 · push = 0
P14 IMPLEMENTATION = NOT AUTHORIZED。
```

---

**END OF P14 IMPLEMENTATION DECISION ORDER（2026-09-27 · 批次 0–9 顺序建议 · 未作内容裁定 · 未选择任何 OPTION）**
