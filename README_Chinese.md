# PharmCAT 简体中文指南

本指南统一说明中文翻译、贡献检查、上游升级和双语 Singularity 镜像构建。当前翻译基于上游 **v3.4.0**；上游应用的通用说明仍见 [README.md](README.md)。

## 两个仓库的职责

- [phonegor95/PharmCAT](https://github.com/phonegor95/PharmCAT)：上游应用、中文处方指导、翻译工具和测试。
- [quantumlifetech/GenDecoder](https://github.com/quantumlifetech/GenDecoder)：Nextflow 编排、OutsideCall、CSV 字段翻译和部署镜像组装。访问该仓库可能需要授权。

保持两个仓库独立，不复制 Java 源码，也不需要子模块。GenDecoder **构建镜像时**需要本仓库的 checkout；生产运行只需要预先生成的镜像。

## 翻译范围和术语

只允许修改 `src/main/resources/org/pharmgkb/pharmcat/reporter/prescribing_guidance.json` 中的：

```text
guidelines[].recommendations[].text.html
guidelines[].recommendations[].implications[]
```

其他结构和字段必须与对应上游版本一致。不引入中文专用 Java、模板、匹配、表型推断或序列化逻辑。相邻的 `prescribing_guidance.v3.4.0.json` 是翻译工具的英文参考；真正的上游结构比较使用 Git tag 中的文件，不应通过修改检查器来掩盖差异。

药物名称、基因型、表型、来源和建议等级等结构化字段保持英文，由 GenDecoder 的 `assets/pharmcat/data/zh-cn/*.json` 在提取 CSV 时翻译。`recommendation.json` 是建议等级词典，不是临床处方正文。修改术语时同步检查这些词典和 `src/scripts/translation/pgcore.py` 中的规范；当前 GenDecoder main 没有可供调用的独立跨层校验器，不应把它写成已存在的发布门禁。

| English | 简体中文 |
|---|---|
| Poor / Intermediate / Normal Metabolizer | 慢代谢者 / 中间代谢者 / 正常代谢者 |
| Rapid / Ultrarapid Metabolizer | 快代谢者 / 超快代谢者 |
| Activity Score | 活性评分 |
| Reference | 参考型 |

保留 HTML 标签、`id` 锚点、实体、基因符号、星号等位基因、变异、rsID、PMID、剂量、单位、百分比，以及 implications 中的英文 `GENE: ` 前缀。`pgcore.CANONICAL` 限定术语；`ALLOWED_VARIANTS` 记录有意保留的语义区别。

## 验证和贡献

从 **PharmCAT 仓库根目录**执行（不是 GenDecoder 根目录）：

```bash
git cat-file -e v3.4.0:src/main/resources/org/pharmgkb/pharmcat/reporter/prescribing_guidance.json
python3 src/scripts/translation/verify.py --upstream-tag v3.4.0
python3 -m unittest discover -s src/test/python/translation -p 'test_*.py' -v
./gradlew test
./gradlew shadowJar
```

必须看到 `structure OK`，不能只看退出码：缺少 Git tag 或在错误仓库运行会导致结构检查被跳过。检查覆盖率、HTML 实体/标签/嵌套、数字、剂量、标识符和规范术语。自动检查不等于临床正确性验证。

生成本地审校页：

```bash
python3 src/scripts/translation/make_review.py --all -o /path/to/scratch/pharmcat-zh-cn-review.html
```

由临床医生或药师审阅新增或实质变化的临床文本；机械 HTML 对齐不能替代审阅。不要提交 JAR、SIF、审校 HTML、翻译记忆或临时工作文件。

## 构建 pharmcat-3.4.0-bilingual-zhcn-<commit>.sif

构建脚本属于 **GenDecoder**：[bin/build_pharmcat_image.sh](https://github.com/quantumlifetech/GenDecoder/blob/main/bin/build_pharmcat_image.sh)。需要包含验证门禁和拒绝覆盖检查的脚本版本；记录实际使用的两个仓库提交，不能只依赖分支名。

它**不构建 Docker 镜像**：先构建中文 fat JAR，将官方 `docker://pgkb/pharmcat:3.4.0` 拉取为基础 SIF，再加入中文 JAR，最终输出一个双语 SIF：

| 镜像内路径 | 用途 |
|---|---|
| `/pharmcat/pharmcat.jar` | 官方英文 JAR |
| `/pharmcat/pharmcat-zh-cn.jar` | 本 fork 的中文 JAR |

两者共用官方预处理器，各自在 JAR 内携带对应 guidance，不用外部 classpath 覆盖资源。不要使用已废弃的浮动 `phonegor95/pharmcat:chinese` 或 `latest` 作为生产来源；历史标签曾包含与预期不符的旧版本。

### 前提

- 已授权访问 GenDecoder，并准备好两个仓库的明确提交及 PharmCAT 的 `v3.4.0` tag。
- Java 17、Python 3、Git、可用的 Gradle wrapper/依赖，以及支持 `--fakeroot` 的 Singularity。
- 有足够空间且适合 Singularity sandbox 提取的**本地 scratch**。此部署 `/mnt/SA127` 是 `nodev`，不能拿它做 sandbox 临时目录；不要默认 `/tmp` 足够大。
- 此部署的 SIF **构建在本地管理节点执行，不提交到 SLURM**；构建前确认该节点为当前用户配置了 `/etc/subuid` 和 `/etc/subgid` fakeroot 映射。使用上述本地 scratch。报告运行和独立的 Singularity/bcftools 验证仍按 GenDecoder 的运行约定提交到 SLURM 计算节点。
- 首次预置 Gradle 依赖和基础镜像可能需要联网；离线生产运行前必须完成缓存。

### 命令

替换 scratch/output 路径；输出使用新的空目录，绝不覆盖生产 SIF：

```bash
set -euo pipefail
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy
FORK=/mnt/SA127/methylation/PharmCAT
GENDECODER=/mnt/SA127/methylation/GenDecoder
export TMPDIR=/path/to/large-local-scratch/pharmcat-build
export SINGULARITY_IMAGE_DIR=/path/to/new-image-directory
mkdir -p "$TMPDIR" "$SINGULARITY_IMAGE_DIR"

# 记录提交前，拒绝暂存、未暂存或未忽略的未跟踪文件；忽略的构建产物不受影响。
for repo in "$FORK" "$GENDECODER"; do
    status=$(git -C "$repo" status --porcelain --untracked-files=all)
    if [[ -n "$status" ]]; then
        printf 'ERROR: checkout is not clean: %s\n%s\n' "$repo" "$status" >&2
        exit 1
    fi
done
{
    git -C "$FORK" rev-parse HEAD
    git -C "$GENDECODER" rev-parse HEAD
} > "$SINGULARITY_IMAGE_DIR/source-commits.txt"

(
    cd "$FORK"
    git cat-file -e v3.4.0:src/main/resources/org/pharmgkb/pharmcat/reporter/prescribing_guidance.json
    python3 src/scripts/translation/verify.py --upstream-tag v3.4.0
    python3 -m unittest discover -s src/test/python/translation -p 'test_*.py' -v
    ./gradlew test
)
bash "$GENDECODER/bin/build_pharmcat_image.sh" 3.4.0 "$FORK"

SOURCE_COMMIT=$(git -C "$FORK" rev-parse HEAD)
IMAGE="$SINGULARITY_IMAGE_DIR/pharmcat-3.4.0-bilingual-zhcn-${SOURCE_COMMIT:0:8}.sif"
singularity exec "$IMAGE" java -jar /pharmcat/pharmcat.jar -version
singularity exec "$IMAGE" java -jar /pharmcat/pharmcat-zh-cn.jar -version
singularity inspect --labels "$IMAGE"
sha256sum "$IMAGE" > "$IMAGE.sha256"
```

上述命令要求使用支持提交命名的 GenDecoder 构建脚本：默认输出 `pharmcat-<version>-bilingual-zhcn-<commit前8位>.sif`，其中 commit 必须是实际构建的 PharmCAT 源提交，而不是分支名称。要发布默认分支的镜像，先将修改 PR 合并到本仓库默认分支 `chinese-translation`，再从该分支合并后的明确提交构建；不要把尚未合并的修复镜像标成旧默认分支提交。相同提交重新构建时更换 `SINGULARITY_IMAGE_DIR`，不覆盖已有镜像。已存在的基础 `pharmcat-3.4.0.sif` 会被复用，因此应确认基础镜像来源可信。

在计算节点用公共/测试 VCF 分别生成英文和中文报告，确认版本一致、中文处方正文存在且结构化调用一致，再推广镜像。使用本版本支持的 CLI 参数（`java -jar ... -help`），不要以真实患者样本作为文档示例。版本输出本身不能证明翻译或临床报告正确。

验证通过后，把 GenDecoder `config/sites.conf` 的 `PHARMCAT_IMG` 指向新 SIF 的绝对路径。若使用已合并了站点配置迁移的其他版本，按该版本的部署文档设置；本指南不假设未合并配置已在 main 可用。保留旧生产镜像以便回滚。

## 升级上游版本

以下以将来 `v3.5.0` 为例，不表示该版本已翻译。先建立翻译记忆，再合并；不要尝试 stash 未解决的合并冲突。

```bash
# 在干净的 PharmCAT checkout 中执行，SCRATCH 必须指向可写目录。
SCRATCH=/path/to/scratch/pharmcat-upgrade
mkdir -p "$SCRATCH"
python3 src/scripts/translation/build_tm.py -o "$SCRATCH/tm.json"
git fetch upstream --tags
git show v3.5.0:src/main/resources/org/pharmgkb/pharmcat/reporter/prescribing_guidance.json > "$SCRATCH/new.json"
python3 src/scripts/translation/plan_merge.py --tm "$SCRATCH/tm.json" --new "$SCRATCH/new.json" -o "$SCRATCH/todo.json"
git merge v3.5.0
```

合并 guidance 冲突是预期情况。暂停并检查其他冲突，不手工文本合并大型 guidance JSON。逐项对照当前英文填写 `todo.json` 中的 `cn`；最近似的旧中文仅供参考，可能含有旧错误。

### Gemini 辅助源文本编写（可选，非生产运行）

`translate_gemini.py` 默认自动读取版本化的 [gemini-review-todo-v1.md](src/scripts/translation/prompts/gemini-review-todo-v1.md)，作为每个批次和单项回退请求的 system instructions。提供 `plan_merge.py` 生成的 todo 和已批准的药物/表型 JSON 词汇表（字符串到字符串的映射，例如 `{"brexpiprazole": "布瑞哌唑"}`）。脚本还单独提供 `pgcore.CANONICAL` 中的中文别名/规范值约束，不自动替换译文。这是离线生产流程之外的**源文本编写**步骤，不会在报告生成时调用 Gemini；不得输入患者数据。旧仓库的 API 脚本与 source-only 缓存不参与此流程。

以下命令**会调用 Gemini**，只在明确准备好发送源文本时执行。仅实际请求需要在独立编写环境安装可选 `google-genai`；帮助和 mock 测试只需 Python 标准库。通过环境安全设置 `GEMINI_API_KEY` 或 `GOOGLE_API_KEY`（前者优先），不要把密钥写进命令、文件或日志。`--model` 必填，由操作者选择实际可用的明确模型 ID，没有臆测的“最新”默认值。

```bash
# 先配置模型 ID、API 密钥和已批准的 glossary.json；所有输出使用新的 scratch 路径。
python3 src/scripts/translation/translate_gemini.py \
    --todo "$SCRATCH/todo.json" --glossary "$SCRATCH/glossary.json" \
    --model "$GEMINI_MODEL" --output "$SCRATCH/todo.draft.json" \
    --cache "$SCRATCH/gemini-draft-cache.json"

# 完全离线，不安装 SDK、不使用密钥，也不发送请求：
python3 -S src/scripts/translation/translate_gemini.py --help
python3 -S -m unittest discover -s src/test/python/translation -p 'test_translate_gemini.py' -v
```

输出始终为**未经人工审校的草稿**：保持顶层 JSON 数组、条目数量和顺序、`kind`（`text`/`impl`）、原始 `en`、键及可选 `hint_en`/`hint_cn`/`hint_similarity` 的值和类型，只填写 `cn`。已有非空 `cn` 原样保留，不发送、不加入缓存。默认每批 10 项（`--batch-size` 可调）；只有无效 JSON、契约或机械保真检查失败才回退到单项。单项仍失败则保留空 `cn`；模型主动返回空白也保留，不重试、不缓存。退出码 **0** 仅表示草稿无空白项，**2** 表示已写出仍有待解决项的草稿，**1** 表示输入/文件/请求错误。认证、配额或网络错误直接中止，不逐项重试，不打印 SDK 异常内容；修复后使用新输出路径重试。

脚本检查字面 HTML 标签/属性的顺序、实体、数字、常见标识符、单位和 implication 基因前缀；这些保守检查比旧翻译的部分豁免更严格，可能将合理的译法留空。它们不能证明临床语义正确或识别所有变异/占位符。由双语审校者检查完整性、否定、条件、可能性、统计量、阈值边界和术语；新增或实质变化的临床文字仍需临床医生或药师审阅。解决全部空白并审阅后，另存为 `todo.reviewed.json`，下面的 `apply.py` 才可使用这个文件；脚本绝不自动 apply 或修改 guidance。

草稿旁自动生成 `<output>.provenance.json`，记录模型、时间、参数、提示词文件名及 SHA-256、有效词汇表 SHA-256（含 canonical 约束）、输入/输出 SHA-256、未解决项索引和 `unreviewed_draft` 状态，不向 todo 插入元数据。所有草稿、sidecar、缓存输出都必须是新文件；拒绝覆盖、路径别名和应用资源目录。可选 `--cache` **仅写新缓存**，可选 `--cache-input` **只读**上次草稿缓存；二者必须使用不同路径。缓存隔离包含格式版本、模型、生成参数/批大小、提示词和词汇表哈希、`kind`、精确原始 `en` 及提示字段；配置变化不复用，旧 source-only 缓存拒绝读取。缓存不是经过审校的翻译记忆，即使命中仍需人工审阅。不要提交草稿、缓存、翻译记忆、响应或 provenance 临时文件。

审阅后生成结果（手工填写 todo 的流程也先另存为 `todo.reviewed.json`）：

```bash
python3 src/scripts/translation/apply.py \
    --tm "$SCRATCH/tm.json" --new "$SCRATCH/new.json" --todo "$SCRATCH/todo.reviewed.json" \
    --reference-out src/main/resources/org/pharmgkb/pharmcat/reporter/prescribing_guidance.v3.5.0.json
git rm src/main/resources/org/pharmgkb/pharmcat/reporter/prescribing_guidance.v3.4.0.json
python3 src/scripts/translation/html_align.py --write
python3 src/scripts/translation/verify.py --upstream-tag v3.5.0
python3 -m unittest discover -s src/test/python/translation -p 'test_*.py' -v
python3 src/scripts/translation/make_review.py --base-rev v3.4.0 -o "$SCRATCH/review.html"
./gradlew test shadowJar
```

确认新英文参考被工具正确选择，解决其余冲突，审阅并完成合并；再按上一节用新版本号和新输出目录构建镜像。翻译记忆优先精确匹配，其次进行 markup 规范化匹配，不要把旧翻译覆盖到语义已经变化的上游文本上。

### 已知陷阱

- v3.2.0 上游删除了旧 `Other Considerations` 内容，不应在翻译中自行恢复。
- 英文参考历史上修正过少量转义字符，不一定逐字等于 tag 原文。结构比较以 tag 为准，复用匹配由 `pgcore.match_key()` 处理。
- `&quot;` 可能标记 FDA/EMA 标签的原文引用，不能为了通过检查而随意删除；引用范围需要人工判断。
- 上游抓取的页脚垃圾由 `pgcore.UPSTREAM_ARTIFACTS` 明确豁免；新增豁免必须有理由，不要削弱一般检查。
- 审校范围包括此次改动的旧翻译，而不只是新增字符串。自动生成的审阅意见也需要对照真实英文核实。

## 翻译工具速查

工具均在 `src/scripts/translation/`，参数以各自 `--help` 为准。

| 工具 | 用途 |
|---|---|
| `pgcore.py` | 结构比较、规范术语、已知上游例外 |
| `build_tm.py` | 从当前英中数据构建翻译记忆 |
| `plan_merge.py` | 计算新版本复用覆盖率和待翻译内容 |
| `translate_gemini.py` | 可选 Gemini 源文本起草；默认强提示词，输出未审草稿/溯源信息，不自动应用；mock 测试离线运行 |
| `apply.py` | 应用记忆和新翻译，生成 guidance/英文参考 |
| `html_align.py` | HTML 的机械对齐，不替代临床审校 |
| `verify.py` | 结构、覆盖、实体、标签、数字和术语门禁 |
| `make_review.py` | 本地英中并排审校页 |
