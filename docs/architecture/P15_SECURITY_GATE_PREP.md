# UAP — P15 SECURITY GATE PREP

> 轮次 = STEP 3 · P15 PREP（安全影响预备 · 未做任何安全边界变更）

## 1. 继承自 P14 的安全不变量（P15 不得放宽）

```text
· 唯一 runtime DB principal = uap_runtime（51 exact row-grants）· 无双向 fallback
· migration identity = uap_migrator（独立）· bootstrap = uap_bootstrap（一次性 · RTA-09 = OPTION B）
· default_acl = 0 · 无 role membership 扩权 · 无 GRANT ALL / ON ALL TABLES
· C2（enforce_acl_subject_types_protect · md5 185e95be…）与 CC-7 受信迁移分支保持
· P13 seed（3/12/12）不变 · REQUIRES_APPROVAL 不得折叠为 allow/deny
· credential 无物理删除（SEC-08）· 六面禁泄露 secret（logs/trace/metrics/audit/response/exception）
· runtime 无 DDL / 无 migration / 无 schema 自愈
· fail-closed：任何不确定 ⇒ DENY（默认拒绝优先）
```

## 2. P15 candidate 的安全影响矩阵

```text
candidate                        影响等级                需要的新 Decision
C-1 D-01 修复                    No impact               foundation change 授权
C-2 管理类能力                    Authorization impact    **SECURITY DECISION REQUIRED**
                                 （admin-on-behalf-of）   （可能 + SCHEMA DECISION）
C-3 engine 统一                  No impact               无
C-4 Bootstrap CLI                Privilege boundary      **SECURITY DECISION REQUIRED**
                                 impact                  （一次性特权路径）
C-5 outbox consumer              Runtime security impact **SECURITY DECISION REQUIRED**
                                 （新后台写入者）          （幂等/重放/审计）
C-6 AI 启用                      Runtime/Audit impact    **SECURITY DECISION REQUIRED**
                                 （外部调用 + 凭据）       （provider 凭据注入策略）
C-7 Frontend                     No impact               无（但需 API 面授权）
C-8 审计深化                     Audit impact            **SECURITY DECISION REQUIRED**
                                 （导出/上报语义）         （不得改 audit 不可变语义）
```

## 3. 新攻击面 / 新增主体 / 新增授权

```text
new principals      = 0（P15 PREP 未创建任何角色/主体）
new grants          = 0（GRANT/REVOKE 全程禁止）
new credentials     = 0
new API attack surface = 取决于 scope（当前 = 0 新增端点）
new authorization paths = 0（Stage 2 未改动；词表 12 未变）
new data exposure   = 0（未新增读写对象）
new audit requirements = 由 C-2/C-6/C-8 决定（未授权前不新增审计语义）
replay / idempotency   = 由 C-4/C-5/C-6 决定（须在实现前冻结语义）
tenant isolation / space isolation = 继承 P14（无 active membership ⇒ DENY）
```

## 4. 结论

```text
**No new security boundary identified**（P15 PREP 阶段未引入任何新安全边界）
但：C-2 / C-4 / C-5 / C-6 / C-8 若被选入 P15 ⇒ `SECURITY DECISION REQUIRED`
本阶段未创建任何新的 security decision，也未变更任何既有安全边界。
```

**END OF P15 SECURITY GATE PREP（2026-09-28 · 无新安全边界 · 5 项候选需 Security Decision · HARD STOP ACTIVE）**
