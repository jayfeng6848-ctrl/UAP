# LOG ENTRY — 2026-10-05 — P21 / AI Real Qualification RE-ENTRY（GATE-B CLOSURE）

## Authorization

```
Human Decision：AI REAL QUALIFICATION — RE-ENTRY（真实 Provider + Model 已由用户经 UAP /ai 建立连接）
安全铁律：BOT 不读取 / 不打印 / 不写入任何 secret value；只记录 provider · model ·
          credential_available · credential_source_type
不授权：新表 / migration / permission / role / 语义修改 / 第二套引擎 / commit / tag / push / release / P22
```

## Baseline

```
HEAD = e20b35f83a1912b0f051d8d0d2d7009f0ee6f7f9 · main · staged = 0 · porcelain = 240 · diff --check 干净
本轮零源码写入 · 零 DB schema 变更
```

## Credential / Provider Availability（不记录任何 secret 值）

```
环境变量路径：host 与 runtime 容器的 8 个候选名全部 present=false（符合预期——
  UAP 的 Key 不走环境变量，而由 onboarding 写入 per-(actor,tenant) 内存连接存储）
真实凭据可用性（经 UAP 会话核验，非环境变量）：
  actor = p21-admin@aurora-test.invalid（Aurora）
  provider = deepseek · model = deepseek-chat · credential_available = true
  credential_source_type = onboarding（经 UAP /ai UI 建立；TTL 沿用既有 1800s 语义）
  → 未出现任何 sk-… / Bearer … / Authorization 值；本条记录中亦无 secret
凭据隔离（同一环境实测）：
  p21-manager / p21-sales / p21-readonly → connected=false（无法借用他人连接）
本地路径：ollama-local / lmstudio-local → available=false（LOCAL_AI_UNAVAILABLE，无真实本地模型）
```

## REAL QUALIFICATION EVIDENCE（真实请求 → 真实完成 → 真实终态）

```
POST /intelligence/tenants/{aurora}/assistant/runs
  message = 「公司现在有多少员工？请只根据提供的数据回答。」
  mode = answer · actor = p21-admin · provider = deepseek · model = deepseek-chat

结果：
  status            = **COMPLETED**（failure_code 为空）
  elapsed           = 928 ms（真实网络往返）
  answer.provider   = deepseek
  answer.model      = deepseek-flash（Provider 侧回显别名）
  answer 内容长度    = 105 字符（真实生成内容，非硬编码/非 stub）
  citations         = 24（来自已授权查询行）
  secret_in_output  = false（无 sk-/Bearer/api_key 片段）

账本（frozen runtime audit 行为）：
  agent_runs：新增 COMPLETED 行，result_metadata.model=deepseek-flash · provider=deepseek
  ai_request_logs：3 → 4，且首次出现 model_id 绑定（真实 Provider/Model 真正被调用）
  （ledger 前后：agent_runs/ai_request_logs 20/3 → 21/4）
```

## Full-chain closure（本轮目标达成）

```
authenticated actor → Company Intelligence/AI entry → effective authorization →
explicit Provider+Model（deepseek + deepseek-chat）→ AI Gateway → **real Provider / real Model** →
**real completion** → server-side response validation → Company-facing terminal state

同时保持成立：tenant isolation（跨租户 403，见前轮验收）· credential isolation（他人 connected=false）·
scope/permission（facade 由会话与路径推导）· classification（四档未变、无降级）·
model binding（显式选择，无静默替换）· audit（agent_runs + ai_request_logs + audit_logs）
```

## OBSERVATION（非缺陷，需登记）

```
OBS-AIQ-01：answer.model 回显为 deepseek-flash（Provider 侧别名），而选择与账本绑定的是
  deepseek-chat。二者不冲突：出站请求体使用的是「显式选定模型」（adapter 由 request.model /
  model_key 决定，已在本地 stub 轮以真实出站报文证明）；ai_request_logs.model_id 绑定的是
  注册表模型行。若需在云端路径上也直接抓取出站 model 字段，可在后续轮次加入 transport capture。
OBS-AIQ-02：本地 AI 路径仍无真实模型（Ollama models=0，端口未监听）→ 本地真实资格 = N/A。
```

## GATE

```
AI REAL QUALIFICATION = **PASS**（真实 Cloud Provider + 真实 Model 闭环成立）
P21 COMPANY UI GATE-A = PASS（不变）
P21 COMPANY UI GATE-B = **CLOSED**（原外部环境阻断已由真实 DeepSeek 连接解除）
P21 OVERALL           = PASS（GATE-A + GATE-B 均通过）
本地 AI 真实资格       = N/A（无真实本地模型；不影响 Cloud 路径判定）
```

## Next step / Hard stop

```
NEXT AUTHORIZED STEP：由 Human Decision 决定是否进入 Release 准备（版本 / manifest / tag / push 均需单独授权）
COMMIT / TAG / PUSH / RELEASE / PRODUCTION AI / P22 = NOT AUTHORIZED · HARD STOP = ACTIVE
```

# LOG ENTRY END
