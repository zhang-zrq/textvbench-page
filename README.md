# TextVBench project page

独立的英文论文主页，适用于 GitHub Pages。已经生成的 HTML 可直接托管：无需 Node、Python 后端、数据库、外部字体或 CDN。

仓库：<https://github.com/zhang-zrq/textvbench-page>。本仓库只包含论文主页及其构建工具，评测代码与完整数据集使用各自的资源入口。

## 许可证与发布审核

原创网站代码、脚本、样式、模板与测试采用 [MIT](LICENSE)。论文文字和图表、数据集记录与参考图、宣传视频及生成插图不包含在此代码许可证内；来源和使用范围见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) 与 [素材说明](docs/asset-sources.md)。

发布前的检查结果、修复内容和检查边界见 [开源审核记录](docs/open-source-audit.md)。提交使用 GitHub 的 noreply 邮箱，避免公开维护者的私人邮箱。安全检查说明见 [SECURITY.md](SECURITY.md)。

## 本地预览

在本目录执行：

```bash
python3 scripts/serve.py
```

访问 <http://127.0.0.1:8080/>。该脚本支持视频分段请求和拖动定位，仅用于本地预览。请通过 HTTP 预览；直接双击 HTML 的 `file://` 模式不作为交互验收环境。

## 内容与结构

- 标题、作者/机构、Paper / Code / Dataset 入口。
- 16:9 宣传视频播放器，使用网站目录内的 `TextVBench_full.mp4` 和本地封面。
- 论文摘要、T2V / Ref2V 构造、各两个发布版输入样例。
- T2V 和 Ref2V 独立的六步理解性匹配演示，含每步目的、输入/输出、可展开 JSON、播放和步进。
- 两条 track 的论文结果、难度分析与引用模板。

```text
index.html                          已生成的主页
data/site.json                      作者、资源链接、宣传视频与引用配置
data/examples.json                  四个发布版输入样例
data/results.json                   论文结果的完整精度数据
data/abstract.txt                    论文摘要
data/walkthrough-audit.json          教学示例的观测与计算结果
assets/css/style.css                主页样式
assets/js/main.js                   标签切换、图片放大、引用复制等
assets/videos/TextVBench_full.mp4    完整宣传视频
assets/images/video-poster.webp      从宣传视频提取的播放器封面
assets/diagrams/evaluation-t2v.html  可独立打开的 T2V 演示
assets/diagrams/evaluation-ref2v.html 可独立打开的 Ref2V 演示
templates/                         内容模板及演示样式/控制器
scripts/build.py                   可选的内容更新工具（Python 标准库）
scripts/import_assets.py            可选的原始素材导入工具
docs/asset-sources.json             素材路径、转换说明、SHA-256
tests/                             内容核验与浏览器检查
```

## 后续修改

`index.html` 和两个演示 HTML 是已生成的静态产物。调整内容时编辑 `data/`、`templates/` 或 `scripts/build_walkthrough.py`，再运行：

```bash
python3 scripts/build.py
python3 tests/validate.py
```

这不是发布所需的前端构建步骤；静态文件已随目录提供。不建议直接修改生成 HTML，否则下次内容刷新会覆盖这些修改。

### 作者和机构

编辑 `data/site.json`，机构编号从 1 开始，例如：

```json
{
  "authors": [{"name": "Author Name", "url": "https://example.com/", "affiliations": [1]}],
  "affiliations": ["Institution Name"]
}
```

当前页面已填入 Ruiqiang Zhang、Hengyi Wang、Chang Liu、Guanjie Wang、Zehua Ma 和 Weiming Zhang；前两位标记为共同一作。

### 论文和外部资源

在 `links` 中填写 `paper`、`code`、`dataset`。支持相对文件路径和 HTTP(S) URL。当前 Paper 已链接到 arXiv：`https://arxiv.org/abs/2610.13412`；Code 和 Dataset 在资源准备好后再补充，未填写的资源呈现不可点击的 `Coming soon`。

填写最终 `canonical_url` 后，生成器会同时添加 canonical 与 Open Graph URL。当前 `citation` 已使用正式 arXiv BibTeX；后续只需在代码或数据公开后补充对应资源链接。

### 宣传视频

完整宣传视频已随仓库提供，路径为 `assets/videos/TextVBench_full.mp4`，SHA-256 与原文件一致。打包发布时保留整个网站目录即可，无需依赖原始视频目录。当前配置：

```json
{
  "video": {
    "src": "assets/videos/TextVBench_full.mp4",
    "poster": "assets/images/video-poster.webp",
    "captions": null
  }
}
```

封面取自视频第 2 秒。有字幕时，`captions` 可指向英文 WebVTT。后续替换视频或封面后运行 `python3 scripts/build.py` 更新页面。播放器提供标准控件，不自动播放，使用 `preload="none"`，初次打开网页只加载封面。

### 演示内容

演示是可复现的教学示意，不运行 OCR/VLM，不使用实验录像。场景、候选数据和解释定义在 `scripts/build_walkthrough.py`，数字从四个预设观测计算。它刻意包含：

1. 同一目标被 OCR 拆成两个框。
2. 完全正确的字符串出现在错误载体上。
3. 属于正确目标的观测存在字符错误；匹配后保留该错误。
4. 不活动观测与活动时缺失的区别。

T2V 使用目标长度加权；Ref2V 示例的两个参考各有一个目标，按参考等权平均。Ref2V 多参考场景是能力示意，不表示所选发布数据样例含多个参考。见 `data/walkthrough-audit.json`。

T2V 的 Define targets 使用 `paper-figure-gen` / `gpt-image-2` 生成的 RGB 店铺图（`assets/images/define-targets-layout.webp`，1536 × 1024）。招牌上的 FRESH ORANGE JUICE 和海报上的 OPEN DAILY 由模型直接生成在图像中，与载体材质、光照自然融合。第一步不叠加目标文字或标注框；目标编号和载体对应关系在图下列出。生成记录见 `docs/generated-assets.json`，提示词见 `docs/define-targets-image-prompt.txt`。图像在构建时嵌入独立演示 HTML，浏览器不调用图像 API。

Ref2V 的 Define targets 同样使用直接生成文字的 RGB 图（`assets/images/ref2v-define-targets-layout.webp`，1536 × 1024）：左侧 R01 纸盒印有 ORANGE JUICE，右侧 R02 易拉罐印有 ZERO SUGAR。两幅参考产品照片并排展示，图下保留参考 ID、目标 ID 与文字的对应关系。提示词见 `docs/ref2v-define-targets-image-prompt.txt`；这两幅是教学用参考示意，并非发布数据集样本。

两条轨道的 Follow targets 均包含 0.0、0.5、1.0、1.5 s 四帧 RGB 图像（每帧 768 × 512）。T2V 展示店铺镜头横移、下移和回拉，Ref2V 展示产品平移、旋转、离场与返回。文字直接生成在图像中；保留 JU1CE 错字、1.0 s 的第一目标 inactive、1.5 s 的第二目标 missing，以及错误载体上未匹配的正确短语。它们是图像模型制作的动态场景示意序列，不是实际视频模型的实验输出。

点击时间按钮或原表格的时间表头可逐帧查看，当前列同步高亮。Play frames 可播放四帧后停止；切换步骤、切换轨道或播放整个流程时会暂停帧播放。手机端表格紧随图片，目标编号列固定。静态、打印、减少动态效果和无 JavaScript 模式均展示四帧。

原始生成图和提示词分别保存在 `figures/` 和 `docs/*follow*prompt.txt`；网站使用质量 88 的 WebP 帧副本，`data/sequence-assets.json` 记录尺寸、SHA-256 及对应状态。重新导出原始帧后，需要重新生成 WebP 副本并更新哈希记录，再运行构建。PNG 中间帧被 Git 忽略。

```bash
python3 scripts/split_sequence.py figures/t2v-follow-targets-sheet.png t2v
python3 scripts/split_sequence.py figures/ref2v-follow-targets-sheet.png ref2v
python3 scripts/build.py
```

Ref2V 原始四格图的首帧把 JUICE 也生成成了 JU1CE，因此另外生成 `figures/ref2v-follow-first-frame.png` 作为正确的起始观测。导出脚本会自动使用这张图并缩小到 768 × 512，不在像素中覆盖或修改文字。不同生成图之间的细小外观差异不作为测量结果；表格和分数仍来自预设教学数据。

初始介绍画面与第一步共用对应的生成图；返回起点或 Replay 也会显示该图。默认手动步进，点击 Play 才开始。顶部六个步骤是可点击的选项卡，可以直接跳转；选择步骤会暂停播放，并同步高亮与前后步进状态。选项卡支持左右方向键循环切换、Home/End 选择首末步骤、Tab 进入内容。两条轨道独立保留进度。

在演示内容或播放控件上，左右方向键前进/后退，Home 返回介绍，End 跳到最后一步，R 重播，非按钮焦点处 Space 暂停/继续。关闭 JavaScript 或启用减少动态效果时，展示完整静态流程。单独访问演示可使用 `?motion=static` 查看静态版，或 `?motion=step&step=4` 检查确定的第四步。

## 验证

Python 3.10 及以上版本即可执行构建和内容检查，无需第三方包：

```bash
python3 tests/validate.py
```

可选的原始素材导入使用显式参数，不依赖维护者的目录结构。它需要另外安装 PyMuPDF 和 Pillow；普通构建和托管不需要它们：

```bash
python3 scripts/import_assets.py --paper-dir /path/to/paper --dataset-dir /path/to/dataset --metrics-file /path/to/computed_metrics.json
```

`paper` 目录包含 `figures/*.pdf`，数据目录包含 `T2V/` 和 `Ref2V/`。导入器生成 WebP 副本，并保留素材清单中视频等独立记录。素材来源清单使用 `paper/`、`dataset/`、`metrics/`、`media/` 这些逻辑目录；如有按该结构准备的来源归档，可运行 `python3 tests/validate.py --source-root /path/to/source-archive` 核对原始数据及素材哈希。

浏览器检查使用 Playwright；网站运行本身不需要它。在仓库根目录安装开发依赖后执行：

```bash
npm install --no-save --package-lock=false playwright
npx playwright install chromium
node tests/preview.cjs
```

如使用已安装的 Chrome 或 Edge，可将环境变量 `PLAYWRIGHT_CHANNEL` 分别设为 `chrome` 或 `msedge`，无需再下载 Chromium。可用 `PLAYWRIGHT_MODULE` 指向现有的 Playwright 模块，用 `PAGE_URL` 指定预览地址。

截图保存在被 Git 忽略的 `.preview/`。具体当前验证结果见 `docs/validation.md`。

每次推送前，先暂存预期文件并检查：

```bash
git add .
python3 scripts/audit_publication.py
gitleaks git --redact --no-banner .
```

仓库提供 Gitleaks 的 pre-commit 配置；安装 `pre-commit` 后执行 `pre-commit install` 可启用提交检查。GitHub Actions 会运行索引安全检查、重新构建、内容验证及生成文件一致性检查。

## GitHub Pages

静态产物和 `.nojekyll` 随 `main` 分支提供。可在仓库 Settings → Pages 中选择从 `main` 分支的根目录发布，预计地址为 `https://zhang-zrq.github.io/textvbench-page/`。推送仓库本身不会启用 Pages 托管。所有站内资源采用相对路径，支持项目路径前缀。启用托管后再填写 `data/site.json` 的 `canonical_url` 并重新构建。

后续发布代码和数据时补齐 Code / Dataset URL。项目代码仓库的 README 与 About 链接到主页；主页 Code 链接回代码仓库。
