# STEP 1-B / B0 — Schema Test Matrix

Status: **DESIGN PREPARATION — 不执行测试（测试在 B1 落地）**
来源：STEP 1-A 全部测试设计 + B0 文档（Round 2/3 修正后）
目录：`tests/integration/`（真实 PG 用 `uap_test` 库）+ `tests/unit/`

> 本矩阵是 **B1 验收清单**。执行前提：Docker PostgreSQL（uap-postgres）+ 独立库 `uap_test`。

---

## 1. Schema（结构测试）

| # | 测试 | 期望 |
|---|---|---|
| S1 | 29+1 张表全部存在 | table_exists（正式表 0 以外的业务表不存在） |
| S2 | 每表 PK 为 uuid（分区表 PK=(id, occurred_at)） | information_schema 校验 |
| S3 | 全部 FK 方向/删除行为符合 CONSTRAINT_MATRIX | 逐条比对 |
| S4 | UNIQUE 与部分唯一索引存在且生效 | 二次插入冲突报错 |
| S5 | CHECK 生效（status/scope/risk/classification/enum 类） | 非法值拒绝 |
| S6 | NOT NULL / NULL 符合矩阵 | 缺列报错 / 允许 NULL 通过 |
| S7 | 非 PK 索引存在（INDEX_STRATEGY §1） | pg_indexes 比对 |
| S8 | **无 `groups` 表** | 扫描 information_schema 无 groups（P2-02） |

## 2. UUIDv7

| # | 测试 | 期望 |
|---|---|---|
| U1 | app 生成器 version==7 / variant==10xx | 抽样 100% |
| U2 | DB `uap_uuid_v7()` version/variant | 同上 |
| U3 | timestamp 反推 ≈ 生成时刻 | < 1ms |
| U4 | app + DB 各 10,000 唯一 / 合并零碰撞 | 通过 |
| U5 | 同毫秒批量唯一 | 20000 零冲突 |
| U6 | PK DEFAULT = `uap_uuid_v7()` 兜底可用 | 省略 id INSERT 成功 |
| U7 | RFC 9562 逐字节 | 见 unit test_uuid_v7 |

## 3. Identity

| # | 测试 | 期望 |
|---|---|---|
| I1 | user 创建/软删/部分唯一（重名 email 排除软删） | 通过 |
| I2 | identity (provider,issuer,subject) 唯一；email 部分唯一 | 通过 |
| I3 | credential rotation：同 identity 仅 1 份有效 password | 通过 |
| I4 | device 注册/撤销；多 session 单 device 多开 | 通过 |
| I5 | session 过期/撤销；identity RESTRICT（有 session 不可删 identity） | 通过 |

## 4. Tenant / Space / Role

| # | 测试 | 期望 |
|---|---|---|
| T1 | tenant isolation：跨租户查询被应用层拒绝（+ 可选 RLS） | DENY |
| T2 | spaces.tenant_id RESTRICT（有空间不可删租户） | 拒绝 |
| T3 | **tenant_memberships.role_id → TENANT role PASS**（P2-01） | 通过 |
| T4 | **tenant_memberships.role_id → PLATFORM role REJECT** | trigger RAISE |
| T5 | **tenant_memberships.role_id → 其它租户 role REJECT** | trigger RAISE |
| T6 | **tenant_memberships.role_id → SPACE role REJECT** | trigger RAISE |
| T7 | **default tenant role = tenant_member** | 创建租户播种两行 |
| T8 | **memberships.role_id → SPACE role PASS / TENANT / PLATFORM REJECT** | 同上 |
| T9 | **default space role = space_member** | 通过 |
| T10 | memberships.tenant_id == spaces.tenant_id 一致性 | 通过 |
| T11 | role scope 形状校验（PLATFORM/TENANT/SPACE ↔ tenant_id/space_id） | 通过 |
| T12 | is_system role 禁改删 | 拒绝 |

## 5. Resource（P2-03）

| # | 测试 | 期望 |
|---|---|---|
| R1 | **resources.tenant_id → tenants RESTRICT**（删有资源的租户被拒） | FK violation |
| R2 | **resources.space_id → spaces RESTRICT** | 同上 |
| R3 | resources soft delete → purge 受控流程（先子后父分批） | 无孤儿 |
| R4 | purge 时 domain 扩展表随 `DELETE resources` 级联 | 通过（受控方向） |
| R5 | owner SET NULL（owner 硬删资源保留） | 通过 |
| R6 | classification 只升不降（应用层） | DENY + audit |
| R7 | natural_key 部分唯一 | 通过 |

## 6. Event Outbox（P1-03）

| # | 测试 | 期望 |
|---|---|---|
| E1 | CAS claim 单赢家（100 并发 worker 同事件仅 1 成功） | 通过 |
| E2 | 业务事务回滚 → 事件不产生 | 通过 |
| E3 | lease 到期（60s）→ Reaper 置回 pending | 通过 |
| E4 | 失败退避 attempts++ → next_attempt_at 递增 | 通过 |
| E5 | attempts>=8 → dead + audit（risk=HIGH） | 通过 |
| E6 | 消费方按 event_id 幂等（重复投递不重复执行） | 通过 |
| E7 | 3a/3b/3c WHERE 带 worker_id，他人不可改 | 0 行影响 |
| E8 | 状态机非法迁移拒绝（delivered→pending 无路径） | 通过 |

## 7. ACL（P1/P2-04 + P2-02）

| # | 测试 | 期望 |
|---|---|---|
| A1 | acl_subject_types 白名单 = user/role/agent；**group INSERT 被 CK 拒绝** | 通过 |
| A2 | subject user/role/agent 存在性 trigger 通过 | 通过 |
| A3 | 伪造 subject（随机 id）→ trigger RAISE | 拒绝 |
| A4 | user 软删保留 ACL；硬删清 ACL | 通过 |
| A5 | role 被 ACL 引用禁删；归档 deny 失效 allow 保留 | 通过 |
| A6 | agent 归档 → ACL 到期 | 通过 |
| A7 | resource soft delete ACL 保留；purge 级联清理 | 通过 |
| A8 | membership removed → ACL 保留但授权 DENY；重加入恢复 | 通过 |

## 8. Migration（Alembic）

| # | 测试 | 期望 |
|---|---|---|
| M1 | 空库 upgrade head → 全部表就位 | 通过 |
| M2 | 重复 upgrade → 幂等（version 表无重复） | 通过 |
| M3 | 中途失败 → 事务回滚无半成品 | 通过 |
| M4 | downgrade base → 全部对象撤销 | 通过 |
| M5 | 并发 migration（双进程同时 upgrade）→ 单赢家 | 通过 |
| M6 | seed 幂等重放（ON CONFLICT 保护） | 通过 |
| M7 | checksum/漂移检测 | 篡改即报错 |
| M8 | 分区表子分区创建正确 | 通过 |

## 9. 安全（Schema 层）

| # | 测试 | 期望 |
|---|---|---|
| SEC1 | `uap_app`（DML）无 DDL 权限；`uap_migrator` 仅迁移窗口；`uap_readonly` 只读 | 权限矩阵 |
| SEC2 | audit_logs 仅 INSERT/SELECT + trigger 拦截 UPDATE/DELETE | 拒绝 |
| SEC3 | agent_versions/tool_versions published 不可变 | 拒绝 |
| SEC4 | 无明文密钥列（CI 扫描 credentials/ai_providers/tools 等表 DDL） | 通过 |
| SEC5 | 高风险操作审计字段齐全（actor/tenant/space/resource/time/result） | 通过 |
| SEC6 | 租户级表均含 tenant_id（隔离可追溯） | schema 扫描 |

---

## 10. 执行命令（B1 验收）

```bash
# 前置：docker compose up -d postgres（用户手动启动 Docker Desktop）
docker exec uap-postgres psql -U uap -d postgres -c "CREATE DATABASE IF NOT EXISTS uap_test;"  # 幂等写法见既有流程

alembic -c config/alembic.ini upgrade head          # 应用到 uap_test（测试隔离库）
pytest -m integration -q                            # 上述 I/T/R/E/A/M/SEC 全量
pytest -q                                           # 全量（含 unit + architecture guard）
```

> 测试隔离原则：一律使用 `uap_test` 独立库；正式 `uap` 库只做只读校验，不被测试污染。
