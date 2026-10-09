# 2.5D 画中游引擎 · `lib/engine.py`

五个分段共用。一段 = 一个 Python 文件（`build()` 返回 dict，或 `SEG = {...}`），也可以是 JSON。
示例：`lib/demo_xishan.py`（溪山立轴全貌 → 缓推，5 秒，成片 `lib/demo.mp4`）；模块近景自检：`lib/test_modules.py`。

## 命令

```bash
S=${CHINA_ART_ROOT:-$HOME/claude-projects/china-art}/series   # 本机默认位置，可用 CHINA_ART_ROOT 覆盖
# 只做速度检查（不渲染；首次会建缓存，所以也要走锁）
lockf -k $S/.heavy.lock python3 $KIT/engine/engine.py seg.py out.mp4 --check
# 抽帧（帧号，输出 out_f0045.png …）
lockf -k $S/.heavy.lock python3 $KIT/engine/engine.py seg.py $KIT/engine/review/x.png --stills 0,45,149
# 成片（超过 1 分钟一律后台 + 轮询日志）
nohup lockf -k $S/.heavy.lock python3 $KIT/engine/engine.py seg.py out.mp4 [--res 1080] [--frames 300:450] > log 2>&1 &
```

- 输出：ffmpeg 管道，libx264 `-crf 12`（`--crf` 可改），yuv420p，+faststart。`--frames a:b` 只渲 [a,b)。
- `--res 720`（草稿，默认）/ `--res 1080`（终版）。所有几何量都在世界坐标里，字号按 720p 写、自动随分辨率缩放，段文件不用改。
- 2× 超采样（`'ss': 2`），INTER_AREA 缩回；`'sharpen'`（默认 0.25）轻微反锐化抵消缩放软化。
- 每次运行先做**速度检查**，超限直接报 `ENGINE ERROR: 超速: 2.67–3.87s 平移峰 … 推拉峰 …%/s` 并退出（退出码 2）。

## 坐标与相机

- **世界坐标 = 主图的原图像素**（溪山就是 `work_full.npy` 的 24176×11105 像素）。其他层用 `origin`（层像素 (0,0) 左上角的世界坐标）+ `unit`（每层像素等于几个世界像素）对齐。
- 相机状态 `{cx, cy, vh}`：屏幕中心对准的世界点，以及屏幕高度对应多少世界像素（`vh` 小 = 推近）。**不旋转**（没有这个参数）。
- `camera = {'rest': 状态, 'keys': [{t, cx, cy, vh, ease?}, ...]}`
  - 相邻两帧状态相同就是停；不同就是一次运动，按**相似变换对数插值**：缩放对数匀速，同时推移时围绕"不动点"缩放，屏幕上不会多出漂移。
  - 速度曲线是梯形：每端 `ease` 秒线性加速/减速（写在目标关键帧上，默认 `min(1.5, 段长/2)`），**小于 1 s 报错**。
  - `rest`：各层对齐原画的状态（视差为零的位置）。一般设成本段的全貌或本次运动的中点。
- 速度检查（逐帧、覆盖所有视差系数的层）：屏幕中心画面点的位移 ≤ **6 px/帧 @720p**（1080p 自动换算），缩放 ≤ **6 %/s**。推荐平移 2–3.3 px/帧。

## 层 `layers`（从下往上画）

```python
{'name': 'mid', 'src': 'x.npy 或 png/jpg', 'origin': [x, y], 'unit': 2,
 'par': 1.01,      # 视差系数：1 = 跟画面走；>1 近景平移更快（建议 1.00–1.03，即 2–3% 画宽）
 'zpar': 0.03,     # 推拉视差：推近时近景放大得略快（0–0.1）
 'crop': [x0, y0, x1, y1], 'feather': 80,   # 世界坐标裁切 + 柔边
 'opacity': 1.0 或 [[t, a], ...], 't0': .., 't1': ..,
 'cache_name': 'xishan_mid'}
```

- RGB = 不透明；RGBA 视为直通 alpha，缓存时转预乘。
- **mip 缓存**：首次使用按行分块建金字塔，存 `lib/cache/mips/<name>_<hash>/L*.npy`，渲染时 mmap，只读可见区域的那一级（层级之间三线性混合，不会跳）。RGB 的 `.npy` 源直接 mmap，不复制。源文件改了（大小/mtime 变）自动重建。
- 层接缝、补洞：只用绢/纸纹理（spike 的 far/mid 已按这个规则补好；新作品照 `spike/build_layers.py` 做）。

## 局部活化 `fx`

每个 fx 用 `'layer'`（或 `'after'`）指定画在哪一层之后，并继承该层的视差；`'__top__'` / `'__bottom__'` 表示最上/最下。都支持 `t0/t1`。

**flow**：遮罩内沿方向的纹理流动（瀑布、河水、水纹）。用原画自己的像素做双相位平移（交叉淡化，无跳变），外加沿方向滚动的细长亮纹。
```python
{'type': 'flow', 'layer': 'far', 'mask': 'wf_mask.npy', 'origin': [x, y], 'unit': 2,
 'src': None,          # 省略则从该层 L0 裁同一块（要求 unit 相同）；或给 RGB npy + 'src_rect'
 'dir': [0, 1], 'speed': 90, 'period': 60,   # 世界像素/秒、世界像素
 'streak': 16, 'strength': 1.0}
```

**drift**：刚体小位移（驴队、船）。位移超过一个身长（`body`，世界像素）报错；起伏角 `tilt.deg` > 1° 报错。父层必须已是"干净底板"（精灵原位置已用绢纹补好，如 spike 的 mid）。
```python
{'type': 'drift', 'layer': 'mid', 'sprite': 'caravan.npy', 'origin': [x, y], 'unit': 2,
 'path': [[0, 0, 0], [16, -110, 0]],        # [t, dx, dy] 世界像素，分段 smoothstep
 'tilt': {'deg': 0.6, 'period': 5}, 'body': 120}
```

**fog**：真实雾/绢像素做的云雾。颜色 = 原图空白雾区像素（`lighten` 提亮），浓淡 = 该区域自身的低频明暗（真实雾形）。
```python
# 画内雾带（随视差、左右无缝环绕漂移、上下柔边、轻微升降）
{'type': 'fog', 'after': 'cliff', 'par': 1.006,
 'tex': {'src': SRC, 'rect': [2800, 15200, 2600, 1300], 'ds': 4},
 'band': [x0, y0, x1, y1], 'feather': 450, 'drift': [14, 0], 'rise': [40, 9], 'opacity': 0.32}
# 满屏转场（雾吞没 / 雾散开）：cover 0→1 = 浓处先起、最后铺满；1→0 = 散开
{'type': 'fog', 'mode': 'screen', 'after': '__top__', 'tex': {...}, 'scale': 1.1,
 'drift': [0.01, -0.02],       # 屏幕高度/秒
 'opacity': 0.0, 'cover': [[19, 0], [20.5, 0.6], [21.5, 1], [22, 1], [23.5, 0]]}
```
转场做法：前一段结尾 cover→1，下一段开头同一个 fog 从 1→0（两段用同一块 `tex`，满屏时画面就是那块真实雾，衔接无缝）。

## 呈现（返回 `dict(layers, full, size)`，`full` 就是全貌相机状态）

- `E.hanging_scroll(src, name, fill_h=0.94, tex_scale=1.6, tone=(0.83,0.79,0.70))` 立轴：整轴含装裱按高度放入（占屏高 94%），两侧是**用原图左右裱边的绫合成的墙面**：随机补丁 + 余弦窗混合 + 方差归一（保留纤维与暗花），自动剔除印章/墨点补丁；样本中位色 × `tone`，灯光自然衰减，立轴在墙上有柔和投影（不漂浮）。`tex_scale` > 1 让织纹在全貌时看得见（1 = 真实尺度）。墙缓存在 `lib/cache/wall_*.npy`。
- `E.handscroll_band(src, name, samples=[(npy, [x0,y0,x1,y1])])` 手卷：整卷横带占屏宽 94%，躺在绢墙上，下方柔影。手卷原图一般没有裱边，**samples 要自己给**（卷中空白绢）。进卷首后用普通相机关键帧从右往左走。
- **手卷全貌（v2，推荐）**：`lib/scrollview.py`——整卷平铺在绢面长案上透视延伸、暖光沿卷走、绕卷首环移后俯冲降入卷首，落点 = 平面相机状态，直接交接。用法见 `lib/scrollview.READY`，实例 `segs/qingming/s3.py` 的 F 镜头。
- `E.object_photo(photo, name, fill=0.86, samples=None)` 器物：照片高占屏 86%，背景是照片边缘中位色（可再叠真实绢纹 samples），照片边缘羽化进底色。

## 展签 `labels`（字幕不烧，由总装加）

```python
{'text': ['谿山行旅圖', '北宋　范寬', '絹本淺設色', '二〇六·三×一〇三·三厘米', '臺北故宮博物院藏'],
 'x': 0.865, 'y': 0.14,        # 屏幕比例，右上角锚点，列从右往左；或 'world': [x, y] 跟画走
 't0': 0.3, 't1': 4.6, 'fade': 0.9, 'color': '#2b251d',   # 暖白用 '#EDE6D8'
 'title_size': 26, 'size': 22}   # 720p 字号；首列 Regular，其余 Light；也可 'cols': [(文字, 字号, 字重), ...]
```

## 其他键

`fps`（30）、`duration`（秒）、`grade: {gamma, gain, lift}`（溪山原图偏暗，用 gamma 0.9 / gain 1.03）、`sharpen`、`ss`、`background`（所有层都未覆盖处的底色，正常应被墙覆盖）。

## 成片复核

`python3 tools/pan_speed_check.py out.mp4` —— 逐帧相位相关求全局位移，报告超过 1/7 画宽/秒且持续 > 0.2 s 的时段（转场、推拉的边缘运动会让个别帧虚高，报警段要人眼复核）。

## 内存 / 速度（M2 8 GB 实测）

- 溪山首跑（建 mip + 墙）约 90 s，峰值约 2.46 GB（墙合成，贴着 2.5 GB 线；墙再大就把 `wall_unit` 调到 10–12）；缓存建好后 720p 每帧约 0.44 s（demo 150 帧 66 s），峰值约 0.6 GB。
- 一律 `lockf -k series/.heavy.lock`；成片后台跑。

## 已知限制

- 相机每段运动都是"停—动—停"，不支持不停顿穿过多个关键帧（需要时拆成相邻运动，中间停 0 s 也会减速到 0）。
- drift 不自己补洞，父层要预先是干净底板。
- fog 雾带纹理是水平环绕；雾带高于纹理高度时会垂直重复（用 feather 盖住，最好 band 高 ≈ rect 高）。
- 手卷的 samples 需手选；器物背景默认是纯色（给 samples 才有绢纹）。
- 速度检查看的是屏幕中心的平移 + 整体缩放；大幅推拉时画面边缘的移动更快，这部分由 `pan_speed_check.py` 成片复核。
- **未实跑**：`handscroll_band`、`object_photo`、`--res 1080`（代码已写，第一次用时先抽帧看）。已实跑：`hanging_scroll`、多层视差、flow/drift/fog（含满屏 cover 吞没，近景抽帧见 `lib/review/tm_*.png`）、展签、速度报错。
- `lib/cache/` 目前约 1 GB（溪山 mip + 墙），可删，删了下次自动重建。
