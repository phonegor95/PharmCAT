# PharmCAT 简体中文处方指导

`chinese-translation` 分支在上游 PharmCAT **v3.4.0** 的基础上提供简体中文处方指导。实现是**纯数据翻译**：Java、Handlebars 模板、匹配器、表型推断器和药物名称均保持上游行为。

## 翻译范围

仅翻译：

```text
guidelines[].recommendations[].text.html
guidelines[].recommendations[].implications[]
```

文件位置：

```text
src/main/resources/org/pharmgkb/pharmcat/reporter/prescribing_guidance.json
```

未翻译的同版本英文参考：

```text
src/main/resources/org/pharmgkb/pharmcat/reporter/prescribing_guidance.v3.4.0.json
```

药物名称、基因型、表型名称、数据来源和建议等级等结构化字段仍保持英文。GenDecoder 在提取 CSV 时通过自己的 `assets/pharmcat/data/zh-cn/*.json` 翻译这些字段；两层术语由 GenDecoder 的跨层校验器检查一致性。

## 验证

每次修改翻译后必须运行：

```bash
python3 src/scripts/translation/verify.py
python3 -m unittest discover \
  -s src/test/python/translation -p 'test_*.py' -v
./gradlew test
./gradlew shadowJar
```

`verify.py` 会硬性检查：

- 除 `text.html` 和 `implications[]` 外，JSON 与上游 v3.4.0 完全一致；
- 所有实质性文本均已翻译；
- HTML 标签、实体、换行和嵌套正确；
- 非词汇化数字、剂量、百分比、PMID 和 rsID 未丢失；
- 术语全部使用 `src/scripts/translation/pgcore.py` 中的规范写法。

生成完整的中英文并排审校页：

```bash
python3 src/scripts/translation/make_review.py --all \
  -o /tmp/pharmcat-zh-cn-review.html
```

该文件只在本地生成，不应提交到仓库。

## 构建

```bash
./gradlew clean shadowJar
java -jar build/libs/pharmcat-*-all.jar -version
```

GenDecoder 的生产运行不使用浮动的 `phonegor95/pharmcat:chinese` Docker 标签。它通过 GenDecoder 仓库中的 `bin/build_pharmcat_image.sh` 将经验证的中文 JAR 注入官方、固定版本的 PharmCAT 基础镜像，生成同时包含英文和中文 JAR 的 Singularity 镜像。

## 更新上游版本

升级至新 PharmCAT 版本时，不要手工合并大型 guidance JSON。严格按照 [`docs/translation-workflow.md`](docs/translation-workflow.md) 执行：构建翻译记忆、生成待翻译清单、应用翻译、对齐 HTML、运行验证器并人工审校。

## 术语

| English | 简体中文 |
|---|---|
| Poor Metabolizer | 慢代谢者 |
| Intermediate Metabolizer | 中间代谢者 |
| Normal Metabolizer | 正常代谢者 |
| Rapid Metabolizer | 快代谢者 |
| Ultrarapid Metabolizer | 超快代谢者 |
| Activity Score | 活性评分 |
| Reference | 参考型 |

新增或修改术语时，必须同步更新 `pgcore.CANONICAL` 和 GenDecoder 的结构化字段词典/跨层校验规则。
