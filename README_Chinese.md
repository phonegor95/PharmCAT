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
guidelines[].recommendations[].population
```

Population 直接保存在中文 `prescribing_guidance.json` 中；null 保持不变。当前 v3.4.0 的 56 个非空标签均已翻译。`verify.py` 直接对照英文参考检查覆盖、数字、null 值及相同标签的翻译一致性。GenDecoder 从中文报告读取 Population，无需独立映射文件或运行时翻译服务。

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

新增或实质变化的临床文本应逐项对照英文审阅。不要提交 JAR、SIF 或临时工作文件。

## 构建 pharmcat-3.4.0-bilingual.sif

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
- 构建版本由可达的 `v*` 发布 tag 推导；例如 `v3.4.0` 之后的 fork 提交生成 `3.4.0-<提交数>-g<提交>`。缺少 tag 时构建会失败，不再生成 `0.0.0`。先获取匹配的上游 tag 及历史，再重建 JAR 和新命名的 SIF；不要修改已有镜像的 manifest。
- 有足够空间且适合 Singularity sandbox 提取的**本地 scratch**。此部署 `/mnt/SA127` 是 `nodev`，不能拿它做 sandbox 临时目录；不要默认 `/tmp` 足够大。
- 在已分配的 SLURM **计算节点**上执行以下构建和 Singularity 验证，不在登录节点执行。按站点配置申请资源。
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

SOURCE_COMMIT=$(git -C "$FORK" rev-parse --short=8 HEAD)
IMAGE="$SINGULARITY_IMAGE_DIR/pharmcat-3.4.0-bilingual-zhcn-$SOURCE_COMMIT.sif"
singularity exec "$IMAGE" java -jar /pharmcat/pharmcat.jar -version
singularity exec "$IMAGE" java -jar /pharmcat/pharmcat-zh-cn.jar -version
singularity inspect --labels "$IMAGE"
sha256sum "$IMAGE" > "$IMAGE.sha256"
```

镜像文件名记录源提交。重建相同版本时使用新的输出路径；不要覆盖正在使用的镜像。已存在的基础 `pharmcat-3.4.0.sif` 会被复用，因此应确认基础镜像来源可信。

在计算节点用公共/测试 VCF 分别生成英文和中文报告，确认版本一致、中文处方正文存在且结构化调用一致，再推广镜像。使用本版本支持的 CLI 参数（`java -jar ... -help`），不要以真实患者样本作为文档示例。版本输出本身不能证明翻译或临床报告正确。

验证通过后，把 GenDecoder `config/sites.conf` 的 `PHARMCAT_IMG` 指向新 SIF 的绝对路径。若使用已合并了站点配置迁移的其他版本，按该版本的部署文档设置；本指南不假设未合并配置已在 main 可用。保留旧生产镜像以便回滚。

## 升级上游版本

获取对应上游 tag，在合并时保留匹配的英文参考。直接编辑中文 guidance 中的三个翻译字段，保持其他字段与上游一致。更新英文参考文件名后运行 `verify.py --upstream-tag <tag>`、Python 验证测试以及 Gradle 构建。人工审阅语义变化后，用新版本和提交命名的新镜像发布。

英文参考历史上修正过少量转义字符；结构检查仍以上游 tag 为准。HTML 实体、标签、剂量、变异和人群限制必须完整保留。已知上游页脚例外由 `pgcore.UPSTREAM_ARTIFACTS` 明确记录，不应削弱一般检查。

## 验证工具

`src/scripts/translation/verify.py` 是构建和 CI 的验证入口，`pgcore.py` 提供共享规则和参考读取功能。中文 guidance 本身是翻译结果的唯一来源。
