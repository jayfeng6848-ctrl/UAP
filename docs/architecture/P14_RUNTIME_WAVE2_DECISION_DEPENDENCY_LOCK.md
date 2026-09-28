# UAP — P14 RUNTIME WAVE 2 DECISION DEPENDENCY LOCK

> ## 状态
>
> ```text
> 状态      = **DECISION PREPARATION**（依赖锁 · 未实施）
> 依据      = Wave 2 HUMAN DECISION SHEET（36 项）· Wave 2 DEPENDENCY MAP
> 铁律      = 不制造不存在的依赖；确实独立的 Decision 允许形成并行分支
> ```

---

# 1. 推荐裁决顺序（主链）

```text
Batch 0  Governance / Root
   SCOPE-W2-01（节点组成）
   VOC-W2-01…04（聚合根 / 词表 —— **Root Blockers**）
        ↓
Batch 1  Identity
   ID-W2-01 → ID-W2-02 → ID-W2-03 / ID-W2-04 → ID-W2-05
        ↓
Batch 2  Device
   DV-W2-01 → DV-W2-03 → DV-W2-02 → DV-W2-04 → DV-W2-05
        ↓
Batch 3  Session
   SS-W2-01 → SS-W2-02 → SS-W2-03 → SS-W2-04 → SS-W2-05
        ↓
Batch 4  Authenticated Context
   CTX-W2-01 → CTX-W2-02 → CTX-W2-04 → CTX-W2-03
        ↓
Batch 5  Authorization Integration
   AUTH-W2-01 → AUTH-W2-02 → AUTH-W2-03
        ↓
Batch 6  API Adaptation
   API-W2-01 → API-W2-02 → API-W2-03 → API-W2-04
        ↓
Batch 7  Security / Abuse
   SEC-W2-01…05（可与 Batch 1–6 并行设计；但其结论为 Acceptance 前置）
        ↓
Wave 2 Implementation Authorization（W2-AUTH-01…07 逐项授权）
```

---

# 2. 逐项依赖（depends_on / blocks / 可否提前）

```text
Decision      | depends_on                    | blocks                                   | can proceed before
--------------|-------------------------------|------------------------------------------|-------------------
SCOPE-W2-01   | —                             | 全部 36 项之外的范围性决策                  | —（最先）
VOC-W2-01     | SCOPE-W2-01（若含 ID/DV/SS）    | VOC-W2-02…04 · ID/DV/SS 全部 · CTX-W2-04  | —
VOC-W2-02     | VOC-W2-01                     | ID-W2-04 · SEC-W2-05 · DV-W2-03（若用 (i)）| —
VOC-W2-03     | VOC-W2-01                     | DV-W2-02/04/05 · SS-W2-03                | —
VOC-W2-04     | VOC-W2-01                     | ID-W2-01/02/05 · SS-W2-01/03             | —
ID-W2-01      | VOC-W2-01/04 · SCOPE-W2-01     | ID-W2-02…05 · DV-W2-01                   | —
ID-W2-02      | ID-W2-01 · VOC-W2-04           | ID-W2-05 · SS-W2-01/02                   | —
ID-W2-03      | ID-W2-01                       | ID-W2-04（identifier 绑定）· SEC-W2-01    | 可与 ID-W2-02 并行
ID-W2-04      | ID-W2-01 · VOC-W2-02           | SEC-W2-05 · SS-W2-01                     | 可与 ID-W2-02/03 并行
ID-W2-05      | ID-W2-02 · ID-W2-04            | DV-W2-04 · SS-W2-03                      | —
DV-W2-01      | ID-W2-01 · SCOPE-W2-01（含 DV） | DV-W2-02…05                             | —
DV-W2-02      | DV-W2-01 · VOC-W2-03           | SS-W2-01 · DV-W2-04（连带语义）            | —
DV-W2-03      | DV-W2-01 · VOC-W2-02（若用 (i)）| DV-W2-04 · SEC-W2-02 · SEC-W2-04          | 可与 DV-W2-02 并行
DV-W2-04      | DV-W2-02 · DV-W2-03 · ID-W2-05  | SS-W2-03                                 | —
DV-W2-05      | DV-W2-02 · DV-W2-04            | SEC-W2-02（并发 enrollment）              | 可与 DV-W2-04 并行
SS-W2-01      | ID-W2-02 · DV-W2-02 · CTX-W2-01 | SS-W2-02…05                             | —
SS-W2-02      | SS-W2-01                       | SS-W2-03…05                              | —
SS-W2-03      | SS-W2-02 · ID-W2-05 · DV-W2-04  | AUTH-W2-03 · SEC-W2-03                   | —
SS-W2-04      | SS-W2-02                       | SEC-W2-02 · SS-W2-05                     | 可与 SS-W2-03 并行
SS-W2-05      | SS-W2-02                       | SEC-W2-02 · CTX-W2-01                    | 可与 SS-W2-03/04 并行
CTX-W2-01     | SS-W2-02（状态名）· VOC-W2-03/04 | SS-W2-01 · AUTH-W2-01 · API-W2-03        | —
CTX-W2-02     | CTX-W2-01                      | AUTH-W2-01 · SEC-W2-03 · API-W2-04        | —
CTX-W2-03     | —（独立）                       | SEC-W2-04 · API-W2-04                    | 可任意时点（并行）
CTX-W2-04     | VOC-W2-01 · AUTH-W2-01          | AUTH-W2-02 · API-W2-03                    | —
AUTH-W2-01    | CTX-W2-01/04 · SS-W2-01/03      | AUTH-W2-02 · API-W2-03 · SEC-W2-03        | —
AUTH-W2-02    | AUTH-W2-01                     | API-W2-03 · API-W2-04                    | —
AUTH-W2-03    | SS-W2-03 · SEC-W2-04            | Wave 2 Acceptance（审计面）                | 可与 API 批并行
API-W2-01     | —（独立宣言）                   | API-W2-02…04                             | 可任意时点（并行）
API-W2-02     | SCOPE-W2-01 · API-W2-01         | API-W2-03/04 · Wave 2 Scope 定稿           | —
API-W2-03     | API-W2-01 · CTX-W2-01 · AUTH-W2-01 | API-W2-04                              | —
API-W2-04     | API-W2-03 · CTX-W2-03            | Wave 2 Acceptance（API 面）               | —
SEC-W2-01     | ID-W2-03                       | ID-W2-01 实现可测性                       | 可与 Batch 1 并行设计
SEC-W2-02     | DV-W2-03 · SS-W2-04 · SS-W2-05   | DV/SS 实现可测性                          | 可与 Batch 2/3 并行设计
SEC-W2-03     | CTX-W2-02 · AUTH-W2-01 · SS-W2-03 | Wave 2 Acceptance（授权 deny 面）         | 可与 Batch 4/5 并行设计
SEC-W2-04     | DV-W2-03 · CTX-W2-03 · AUTH-W2-03 | ID/DV/SS 实现（secret 边界）               | 可与 Batch 1–5 并行设计
SEC-W2-05     | ID-W2-04 · VOC-W2-02            | 凭据实现（algorithm/rotation）             | 可与 Batch 1 并行设计
```

---

# 3. Root Blockers（未裁决 ⇒ 实现一律不得开始）

```text
ROOT-1  SCOPE-W2-01   节点组成未定 ⇒ 无法确定任何实现范围
ROOT-2  VOC-W2-01     聚合根未定 ⇒ Identity/Device/Session 的持久化形态无法确定
ROOT-3  VOC-W2-02     credential type 词表未定 ⇒ 凭据实现无法确定
ROOT-4  VOC-W2-03     device status 词表未定 ⇒ device 状态机无法确定
ROOT-5  VOC-W2-04     identity/user 状态词表未定 ⇒ 状态机无法确定（且 §六 举例的
                      `pending → verified → active` 不存在于任何现行契约/schema）

⇒ 5 项 Root Blocker 全部裁决前：
     Wave 2 Implementation = NOT STARTED（强制）
```

---

# 4. 并行分支（明确允许）

```text
PAR-1  CTX-W2-03（observability 白名单）与所有权衡独立，可并行裁决
PAR-2  API-W2-01（transport 定位宣言）独立于 Identity 实现，可先行裁决
PAR-3  SEC-W2-01…05 为"设计与测试設計"，可与 Batch 1–6 并行编写（**仅设计**）
PAR-4  ID-W2-03 / ID-W2-04 之间无相互依赖，可并行
PAR-5  DV-W2-03 / DV-W2-02、SS-W2-03/04/05 内部可并行

⇒ 不制造额外依赖；上述并行项不改变 §1 的主链裁决顺序建议
```

---

# 5. 本轮工程变更

```text
新增文档 = 本文件（+ 同轮 8 份）· runtime code = 0 · DB 写 = 0 · migration = 0
commit / tag / push = 0
```

**END OF P14 RUNTIME WAVE 2 DECISION DEPENDENCY LOCK（2026-09-28 · 5 Root Blockers · 36 decisions · HARD STOP ACTIVE）**

---

# 6. 裁决后最终依赖链（§四十三 · 2026-09-28 Human Freeze）

```text
Schema / Persistence Vocabulary
  （0017 = persistence truth · 不修改；anti-corruption mapping 为入口条件）
        ↓
Identity Boundary
  （VOC-W2-01/02/04 · ID-W2-01…05）
        ↓
Credential
  （VOC-W2-02 · ID-W2-04 · SEC-W2-05 算法/参数口径）
        ↓
Device
  （VOC-W2-03 · DV-W2-01…05）
        ↓
Session
  （SS-W2-01…05）
        ↓
Authenticated Context
  （CTX-W2-01 … CTX-W2-04）
        ↓
Tenant / Space Context
  （CTX-W2-02 的矩阵在此生效 · tenant/space 经 active membership 校验）
        ↓
Stage 2 Authorization
  （AUTH-W2-01 effect 仅 allow/deny · AUTH-W2-02 判定位置 · §二十九 评估顺序）
        ↓
Service
  （use-case 编排 + 事务所有权 + revoke 传播矩阵 ID/DV/SS-SEC-W2-04）
        ↓
API Adaptation
  （API-W2-01…04 · transport only）
```

```text
说明
  · 本链与既有 P14_RUNTIME_SLICE_DEPENDENCY_MAP / DEPENDENCY_LOCK（DL-1…DL-5）**同源**，
    是其派生细化，**不构成第二套 dependency model**。
  · 实际不依赖的关系**未加入**：例如 CTX-W2-03（observability 白名单）与 API-W2-01
    （transport 定位）为**并行独立**项；SEC-W2-01…05 为并行设计项（见 §4 PAR-1…PAR-5）。
  · Root Blocker 状态：SCOPE-W2-01 + VOC-W2-01…04 的裁决已完成 ⇒ **解除**；
    但"实现是否开始"仍取决于 **W2-AUTH-01…07 的独立 Human 授权**（本轮未授权）。
  · §二十九 的评估顺序（Authentication → Identity validity → Device trust → Session validity →
    Tenant membership → Space membership → Stage 2 Authorization → Use-case）在本链中
    体现为 Context 与 Tenant/Space 之间的强制前置校验点。
```

**END OF DEPENDENCY LOCK §6（2026-09-28 · 裁决后最终链 · Root Blocker 解除但实现未授权 · HARD STOP ACTIVE）**
