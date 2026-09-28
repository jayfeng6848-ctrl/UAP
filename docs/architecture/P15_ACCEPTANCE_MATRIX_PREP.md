# UAP — P15 ACCEPTANCE MATRIX PREP

> 轮次 = STEP 3 · P15 PREP（验收维度预备 · **不创建任何测试代码**）
> 状态 = 全部 `PLANNED`（P15 scope 未冻结 ⇒ 无法确定具体条目）

```text
维度                       适用性（当前）      说明
functional tests           PLANNED          随 P15 scope 决定
security tests             PLANNED          任何新特权/新路径都必须覆盖
authorization tests        PLANNED          复用 Stage 2 · 覆盖 default deny / deny precedence
negative tests             PLANNED          拒绝面优先（fail-closed）
transaction tests          PLANNED          复合动作原子性（沿用 P14 use-case 拥有事务）
replay tests               PLANNED          challenge/token/幂等键类材料
concurrency tests          PLANNED          并发会话 / 并发 enrollment / 并发消费
observability tests        PLANNED          白名单字段 · 无 secret · operational ≠ audit
API tests                  PLANNED          8 类错误映射 · 安全类模糊化
regression tests           PLANNED          Wave 1 + Wave 2 allowlist 必须保持 PASS
schema verification        PLANNED          仅当出现 SCHEMA DECISION 时适用
privilege verification     PLANNED          51/6/5/0/245 与 default_acl 必须保持
DB no-mutation checks      PLANNED          正式库 prestate == poststate · 测试库边界锚点不变

执行治理（继承 P14）
  · 测试必须使用 CF-C-4 逐文件 allowlist（禁止目录级 pytest）
  · 19 个 CF-C-4 文件 + OI-G-4 文件保持 NOT RUN
  · integration/security 测试使用 UAP_RUNTIME_TEST_DSN（缺省 SKIP · 不回退）
  · 审计表 append-only ⇒ 使用 delta 断言（不得要求 audit_logs == 0）
```

**END OF P15 ACCEPTANCE MATRIX PREP（2026-09-28 · 13 维度 · 全 PLANNED · 未创建测试代码 · HARD STOP ACTIVE）**
## C-5 具体化（2026-09-28 · Human Decision 后追加 · test code = NOT CREATED）
以下为 P15 primary theme（C-5 Events / Outbox Consumer）所需测试类别，状态仍全部 `PLANNED`：
- event eligibility：pending + next_attempt_at 到期判定；索引 ix_events_dispatch 命中
- claim concurrency：两 worker 并发 claim 同一事件 ⇒ 仅一个成功（rowcount=1）
- duplicate delivery：同一 (id, occurred_at) 重复投递 ⇒ 无不可接受重复副作用
- idempotency：幂等键语义验证（含"无法天然幂等 ⇒ 不纳入首批"的排除准则）
- retry：retryable 分类 + attempts 递增 + next_attempt_at backoff（上界待冻结）
- terminal failure：达到上界 ⇒ status='dead' + last_error 脱敏
- transaction rollback：副作用与状态推进同事务；失败 ⇒ rollback 且状态一致
- authorization denial：consumer 不得绕过 P14 authorization；deny ⇒ 不执行
- tenant isolation：missing tenant_id ⇒ DENY；无跨租户执行
- space isolation：space 缺失/歧义 ⇒ DENY 或显式解析
- worker shutdown：graceful（停 claim → 等在途 → 释放 lease → dispose）
- worker restart：崩溃后 lease 过期恢复语义（O-1 未冻结 ⇒ 该用例当前为 PLANNED-OPEN）
- DB unavailable：不 claim/不执行 + bounded retry + 无降级执行
- observability：event received / claim attempt / execution started / success / denied / retry /
                 terminal failure 可观测；无 secret；operational ≠ audit
- audit semantics：consumer 不新增 audit vocabulary；audit_logs 保持 append-only（无 UPDATE/DELETE）
- regression：Wave 1（211 含 D-02 记录）+ Wave 2（72）保持 PASS · CF-C-4 逐文件 allowlist
- schema/privilege no-mutation：0017 不变 · 51/6/5/0/245 · default_acl 0 · 正式库 prestate == poststate
执行治理：仍禁止目录级 pytest；19 个 CF-C-4 文件 + OI-G-4 文件保持 NOT RUN。
**END OF P15 ACCEPTANCE MATRIX PREP — C-5 ADDENDUM（2026-09-28 · 17 类别 · 全 PLANNED · 未创建测试代码 · HARD STOP ACTIVE）**
## C-5 Acceptance Matrix — FINALIZED（2026-09-28 · 契约冻结后 · test code = NOT CREATED）
状态全部 `PLANNED / FROZEN-DESIGN`（设计冻结，尚未实现）：
```text
 1 claim correctness              （条件 UPDATE + rowcount=1 才是所有权）
 2 concurrent claim safety         （两 worker 并发 ⇒ 仅一个成功）
 3 lease ownership                 （worker_id/claimed_at/lease_expires_at 一致）
 4 expired lease recovery          （O-1：attempts<10 → pending；attempts 不再增加）
 5 retryable failure               （瞬态 ⇒ pending + next_attempt_at）
 6 terminal failure                （非瞬态 ⇒ dead，不浪费 attempts）
 7 max attempts                    （MAX_ATTEMPTS=10 到达即 dead）
 8 deterministic backoff           （5/10/20/40/80/160/320/640/600 秒可断言 · 无 jitter）
 9 duplicate delivery              （同 (id, occurred_at) 重复投递无不可接受副作用）
10 idempotency                     （A/B/C 之一可证 · 不可证 ⇒ 不纳入）
11 authorization denial            （deny ⇒ dead；不按 transient 重试）
12 tenant isolation                （tenant 缺失 ⇒ DENY · 无跨租户）
13 space isolation                 （space 歧义/缺失 ⇒ DENY 或显式解析）
14 worker shutdown                 （stop claiming → 完成有界操作 → 持久化 → 释放 → exit）
15 worker crash recovery           （lease 过期 → O-1；不依赖 graceful shutdown）
16 DB unavailable                  （不 claim/不执行 + bounded retry + 无降级）
17 observability/audit separation  （operational ≠ audit；audit 仅按既有语义）
18 unsupported event_type          （dead · reason=unsupported_event_type）
19 malformed payload               （非可解析/不符 schema ⇒ dead，不重试）
20 worker heartbeat ownership loss （rowcount≠1 ⇒ 必须安全停止执行）
21 delivered terminality           （delivered 不回 pending）
22 dead terminality                （dead 不自动回 pending；replay = 未来 Decision）
23 no privilege expansion          （51/6/5/0/245 · default_acl 0 不变）
24 no schema mutation              （0017 不变 · 0018+ = 0）
25 no runtime dependency on D-01 defective Repository helper（读取必须走 SafeReader）
```
执行治理：CF-C-4 逐文件 allowlist · 禁目录级 pytest · 19 个 CF-C-4 文件 + OI-G-4 文件保持 NOT RUN。
**END OF P15 ACCEPTANCE MATRIX PREP — FINALIZED（2026-09-28 · 25 类别 · 设计冻结 · 未创建测试代码 · HARD STOP ACTIVE）**
