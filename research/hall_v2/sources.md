# 中国厅图源审计（2026-09-29）

每件作品的最佳可用图、像素、许可与上墙适配度。机读版 `sources.json`，缩略图 `thumbs/<slug>.jpg`（≤1000 px，审阅板用）。

**口径**：墙上作品在 1389×713 窗口、dpr 2 下显示高约 1100–1300 设备像素。立轴/竖幅：原图高 ≥1300 即"够"整幅挂；手卷：画心高 ≥1400 才能横向展开并局部推近，1000–1400 只能 1:1 横移（"勉强"），<1000 "不够"；立体器物：要干净背景正面照，馆方白底/灰底图"够"，展柜实拍（背景杂、有反光）即使像素高也记"勉强"。像素来自 Commons imageinfo API、Met/Cleveland Open Access API 或本地实测；未下载原图。

**许可口径**：古代平面作品本身公有领域；Commons 上的馆方复制图按 PD-Art 标注（美国法口径），故宫名画记/数字文物库本身没有开放许可，Commons 大图是第三方拼接上传。立体物照片有摄影者版权，按文件页许可署名。用户已允许非商用展示放宽，但下表照实记录。

**总数** 83 件：够 43、勉强 28、不够 12。本地已有 26 件。

## 一、总表

| slug | 作品 | 时代 | 收藏 | 最佳图源 | 像素 | 许可 | 本地 | 上墙 |
|---|---|---|---|---|---|---|---|---|
| banpo_fish_basin | 人面鱼纹彩陶盆 | 新石器·仰韶文化半坡类型 | 中国国家博物馆 | [链接](https://commons.wikimedia.org/wiki/File:Banpo_motif.jpg) | 4999×3412 | GFDL / CC BY-SA 3.0 | ✓ | **勉强** |
| majiayao_spiral_jar | 马家窑文化旋涡纹彩陶罐 | 新石器·马家窑文化马家窑类型（前3300–前2650） | 克利夫兰艺术博物馆 2004.64 | [链接](https://www.clevelandart.org/art/2004.64) | 3758×4288 | CC0（Cleveland Open Access） |  | **够** |
| majiayao_dance_basin | 舞蹈纹彩陶盆 | 新石器·马家窑文化（青海大通上孙家寨出土） | 中国国家博物馆 | [链接](https://commons.wikimedia.org/wiki/File:%E8%88%9E%E8%B9%88%E7%BA%B9%E5%BD%A9%E9%99%B6%E7%9B%8608775.jpg) | 7550×5033 | CC BY-SA 4.0 |  | **勉强** |
| hongshan_pig_dragon | 红山文化玉猪龙 | 新石器·红山文化 | 辽宁省博物馆（另有国博、台北故宫藏品） | [链接](https://commons.wikimedia.org/wiki/File:Hongshan_Jade_pig-dragon(pendant).jpg) | 8192×5464 | CC BY-SA 4.0 |  | **勉强** |
| liangzhu_cong_king | 良渚玉琮王（补充） | 新石器·良渚文化 | 浙江省博物馆 | [链接](https://commons.wikimedia.org/wiki/File:Jade_Cong_King,_2018-06-09_01.jpg) | 6016×4016 | CC BY-SA 4.0 |  | **勉强** |
| houmuwu_ding | 后母戊鼎 | 商晚期 | 中国国家博物馆 | [链接](https://commons.wikimedia.org/wiki/File:HouMuWuDingFullView.jpg) | 3380×4400 | CC BY-SA 3.0 | ✓ | **勉强** |
| maogong_ding | 毛公鼎 | 西周晚期 | 台北故宫博物院 | [链接](https://commons.wikimedia.org/wiki/File:Ding_cauldron_of_Duke_Mao.jpg) | 2230×2470 | CC BY 4.0 |  | **够** |
| four_ram_zun | 四羊方尊 | 商晚期 | 中国国家博物馆 | [链接](https://commons.wikimedia.org/wiki/File:Late_Shang_Bronze_Zun.jpg) | 3456×5184 | CC0 |  | **勉强** |
| sanxingdui_mask | 三星堆青铜纵目面具 | 商·三星堆文化 | 三星堆博物馆 | [链接](https://commons.wikimedia.org/wiki/File:Ancient_Bronze_Mask_from_Sanxingdui_with_Protruding_Eyes_%26_Ears_a.jpg) | 4752×3168 | CC0 |  | **勉强** |
| sanxingdui_standing_figure | 三星堆青铜大立人 | 商·三星堆文化 | 三星堆博物馆 | [链接](https://commons.wikimedia.org/wiki/File:%E4%B8%89%E6%98%9F%E5%A0%86%E5%87%BA%E5%9C%9F%E9%9D%92%E9%93%9C%E5%A4%A7%E7%AB%8B%E4%BA%BA%E5%83%8F,_2017-09-17.jpg) | 4016×6016 | CC BY-SA 4.0 |  | **勉强** |
| zeng_bianzhong | 曾侯乙编钟 | 战国早期（约前433） | 湖北省博物馆 | [链接](https://commons.wikimedia.org/wiki/File:Two_Tone_Set-bells_of_Marquis_Yi_of_Zeng_(10166101994).jpg) | 4752×3168 | CC0 |  | **勉强** |
| terracotta_pit1 | 秦始皇陵兵马俑一号坑 | 秦 | 秦始皇帝陵博物院 | [链接](https://commons.wikimedia.org/wiki/File:Qin_Terracotta_Army,_Pit_1_11.jpg) | 4752×3168 | CC0 |  | **够** |
| kneeling_archer | 秦跪射俑 | 秦 | 秦始皇帝陵博物院 | [链接](https://commons.wikimedia.org/wiki/File:2019_Qin_Terracotta_Kneeling_Archer.jpg) | 4000×6000 | CC0 |  | **勉强** |
| mawangdui_t_banner | 马王堆一号墓 T 形帛画（非衣） | 西汉 | 湖南博物院 | [链接](https://commons.wikimedia.org/wiki/File:T-shaped_Painting_on_Silk_-_Google_Art_Project.jpg) | 3329×4804 | PD（PD-Art，Google Art Project） | ✓ | **够** |
| mawangdui_black_coffin | 马王堆一号墓黑地彩绘漆棺（本图实为朱地彩绘棺，见备注） | 西汉 | 湖南博物院 | [链接](https://commons.wikimedia.org/wiki/File:Mawangdui_Han_Second_Coffin_from_Tomb_-1_(10113245853).jpg) | 4752×3168 | CC0 |  | **不够** |
| changxin_lamp | 长信宫灯 | 西汉 | 河北博物院 | [链接](https://commons.wikimedia.org/wiki/File:%E9%95%BF%E4%BF%A1%E5%AE%AB%E7%81%AF_%E6%B2%B3%E5%8C%97%E5%8D%9A%E7%89%A9%E9%99%A2.jpg) | 5293×7058 | CC BY-SA 4.0 |  | **勉强** |
| bronze_galloping_horse | 铜奔马（马踏飞燕） | 东汉 | 甘肃省博物馆 | [链接](https://commons.wikimedia.org/wiki/File:%E9%9B%B7%E5%8F%B0%E6%B1%89%E5%A2%93%E9%93%9C%E5%A5%94%E9%A9%AC3.jpg) | 5456×3632 | CC BY-SA 4.0 |  | **勉强** |
| huoqubing_horse | 霍去病墓马踏匈奴 | 西汉 | 茂陵博物馆 | [链接](https://commons.wikimedia.org/wiki/File:Horse_of_Huo_Qubing_Mausoleum_(left_side).jpg) | 4439×3064 | CC BY-SA 2.0 |  | **够** |
| yulong_banner | 人物御龙帛画（补充） | 战国中晚期·楚 | 湖南博物院 | [链接](https://commons.wikimedia.org/wiki/File:Figure_Driving_a_Dragon_-_Google_Art_Project.jpg) | 3384×4512 | PD（PD-Art，Google Art Project） | ✓ | **够** |
| admonitions_scroll | 女史箴图（唐摹本） | 东晋·传顾恺之 | 大英博物馆 1903,0408,0.1 | [链接](https://commons.wikimedia.org/wiki/File:Admonitions_Scroll_(center).jpg) | 18955×1340 | PD（PD-Art） | ✓ | **勉强** |
| luoshen_scroll | 洛神赋图（宋摹本） | 东晋·传顾恺之 | 北京故宫博物院 | [链接](https://commons.wikimedia.org/wiki/File:顾恺之洛神赋图卷（宋摹）.png) | 97531×2472 | PD（PD-Art） | ✓ | **够** |
| lanting_shenlong | 兰亭序（神龙本） | 东晋·王羲之原作，唐冯承素摹 | 北京故宫博物院 | [链接](https://commons.wikimedia.org/wiki/File:LantingXu.jpg) | 4513×1480 | Public domain |  | **勉强** |
| boyuan_tie | 伯远帖 | 东晋·王珣 | 北京故宫博物院 | [链接](https://commons.wikimedia.org/wiki/File:%E7%8E%8B%E7%8F%A3%E8%A1%8C%E4%B9%A6%E4%BC%AF%E8%BF%9C%E5%B8%96%E5%8D%B7.png) | 33019×2160 | Public domain |  | **够** |
| yungang_cave20 | 云冈第 20 窟露天大佛 | 北魏 | 山西大同云冈石窟 | [链接](https://commons.wikimedia.org/wiki/File:Yungang_Grottoes_Cave_20_1.jpg) | 5712×4284 | CC BY-SA 4.0 |  | **够** |
| xiaowen_procession | 孝文帝礼佛图（龙门宾阳中洞） | 北魏 约522–523 | 大都会艺术博物馆 35.146 | [链接](https://www.metmuseum.org/art/collection/search/42707) | 3919×2941 | CC0（Met Open Access） |  | **够** |
| bamboo_sages_brick | 竹林七贤与荣启期砖画 | 南朝 | 南京博物院 | [链接](https://commons.wikimedia.org/wiki/File:Southern_Dynasty_Brick_Mural_(10152443315).jpg) | 3888×2592 | CC0 |  | **勉强** |
| dunhuang257_deer | 莫高窟 257 窟《鹿王本生》 | 北魏 | 敦煌研究院 | [链接](https://commons.wikimedia.org/wiki/File:%E9%B9%BF%E7%8E%8B%E6%9C%AC%E7%94%9F%E6%95%85%E4%BA%8B%E7%95%AB.jpg) | 6496×1114 | Public domain |  | **勉强** |
| youchun_tu | 游春图 | 隋·传展子虔 | 北京故宫博物院 | [链接](https://commons.wikimedia.org/wiki/File:%E5%B1%95%E5%AD%90%E8%99%94%E6%B8%B8%E6%98%A5%E5%9B%BE%E5%8D%B7.png) | 97407×10476 | Public domain |  | **够** |
| bunian_tu | 步辇图（宋摹） | 唐·传阎立本 | 北京故宫博物院 | [链接](https://commons.wikimedia.org/wiki/File:%E9%98%8E%E7%AB%8B%E6%9C%AC%E6%AD%A5%E8%BE%87%E5%9B%BE%E5%8D%B7.png) | 143397×9399 | Public domain |  | **够** |
| fengxian_vairocana | 龙门奉先寺卢舍那大佛 | 唐 672–675 | 河南洛阳龙门石窟 | [链接](https://commons.wikimedia.org/wiki/File:Ancient_Buddhist_Grottoes_at_Longmen-_Fengxian_Temple_Grand_Buddha_Niche_with_Colossal_Statue_of_Vairocana_Buddha.jpg) | 5184×3456 | CC0 |  | **够** |
| dunhuang45 | 莫高窟 45 窟彩塑与壁画 | 盛唐 | 敦煌研究院 | [链接](https://commons.wikimedia.org/wiki/File:HKU_%E9%A6%99%E6%B8%AF%E5%A4%A7%E5%AD%B8_Pokfulam_compus_%E5%9C%96%E6%9B%B8%E9%A4%A8_Main_Library_Building_exhibition_Cave_045_Mogao_Caves_in_art_exhibition_August_2025_N13P_01.jpg) | 3060×4080 | CC0 |  | **不够** |
| dunhuang220 | 莫高窟 220 窟（贞观十六年） | 初唐 642 | 敦煌研究院 | [链接](https://commons.wikimedia.org/wiki/File:Reproduced_Mural_of_220_cave,_Mogao_caves,_Dunhuang.jpg) | 3910×2930 | CC BY-SA 3.0 |  | **不够** |
| dunhuang103_vimalakirti | 莫高窟 103 窟维摩诘像 | 盛唐 | 敦煌研究院 | [链接](https://commons.wikimedia.org/wiki/File:Vimalakirti_debating_Manjusri,_Tang_Dynasty.jpg) | 1968×2835 | Public domain |  | **勉强** |
| dunhuang112_pipa | 莫高窟 112 窟反弹琵琶 | 中唐 | 敦煌研究院 | [链接](https://commons.wikimedia.org/wiki/File:Mogao_Caves_Pipa-Player.jpg) | 1801×2608 | Commons 标 PD（网页转载，拍摄者不明） | ✓ | **勉强** |
| jizhi_wengao | 祭侄文稿 | 唐 758·颜真卿 | 台北故宫博物院 | [链接](https://commons.wikimedia.org/wiki/File:%E7%A5%AD%E4%BE%84%E6%96%87%E7%A8%BF%E5%8D%B7.%E5%94%90.%E9%A1%8F%E7%9C%9F%E5%8D%BF.%E7%BA%B8%E6%9C%AC%E8%A1%8C%E4%B9%A6.%E5%8F%B0%E5%8C%97%E6%95%85%E5%AE%AB%E5%8D%9A%E7%89%A9%E9%99%A2%E8%97%8F_(cropped).tif) | 15610×5784 | Public domain |  | **够** |
| zhangxu_gushi_sitie | 古诗四帖 | 唐·传张旭 | 辽宁省博物馆 | [链接](https://commons.wikimedia.org/wiki/File:Zhang_Xu_Gu_Shi_Si_Tie.jpg) | 413×432 | Public domain |  | **不够** |
| huaisu_zixu | 自叙帖 | 唐 777·怀素（真伪有争议） | 台北故宫博物院 | [链接](https://commons.wikimedia.org/wiki/File:Huaisu_-_Autobiography.jpg) | 23427×480 | Public domain |  | **不够** |
| sancai_camel_musicians | 三彩骆驼载乐俑 | 唐 723 | 中国国家博物馆 | [链接](https://commons.wikimedia.org/wiki/File:Tang_Dynasty_musicians_on_camel,_723_ad.jpg) | 3456×5184 | CC0 |  | **勉强** |
| zhaoling_saluzi | 昭陵六骏·飒露紫 | 唐 636 | 宾夕法尼亚大学考古与人类学博物馆（另四骏在西安碑林） | [链接](https://commons.wikimedia.org/wiki/File:%E5%AE%BE%E5%A4%95%E6%B3%95%E5%B0%BC%E4%BA%9A%E5%A4%A7%E5%AD%A6%E5%8D%9A%E7%89%A9%E9%A6%86%E5%94%90%E4%BB%A3%E6%98%AD%E9%99%B5%E5%85%AD%E9%AA%8F%E4%B9%8B%E4%B8%80%E9%A3%92%E9%9C%B2%E7%B4%AB%E7%9F%B3%E5%88%BB.jpg) | 8064×6048 | CC BY-SA 4.0 |  | **勉强** |
| guoguo_furen | 虢国夫人游春图（宋摹） | 唐·张萱原作 | 辽宁省博物馆 | [链接](https://commons.wikimedia.org/wiki/File:%E8%99%A2%E5%9B%BD%E5%A4%AB%E4%BA%BA%E6%B8%B8%E6%98%A5%E5%9B%BE.jpg) | 4674×979 | Public domain |  | **不够** |
| hanxizai_yeyan | 韩熙载夜宴图（宋摹） | 五代南唐·传顾闳中 | 北京故宫博物院 | [链接](https://commons.wikimedia.org/wiki/File:韩熙载夜宴图.tif) | 95930×3981 | PD（PD-Art） | ✓ | **够** |
| kuanglu_tu | 匡庐图 | 五代·荆浩（传） | 台北故宫博物院 | [链接](https://commons.wikimedia.org/wiki/File:%E5%8C%A1%E5%BA%90%E5%9B%BE%E8%BD%B4.%E4%BA%94%E4%BB%A3%E6%A2%81.%E8%8D%86%E6%B5%A9%E7%BB%98.%E7%BA%B8%E6%9C%AC%E6%B0%B4%E5%A2%A8.%E5%8F%B0%E5%8C%97%E6%95%85%E5%AE%AB%E5%8D%9A%E7%89%A9%E9%99%A2%E8%97%8F.jpg) | 7473×13091 | Public domain |  | **够** |
| xishan_xinglv | 谿山行旅图 | 北宋·范宽 | 台北故宫博物院 | [链接](https://commons.wikimedia.org/wiki/File:谿山行旅图轴.溪山行旅图.宋.范宽.绢本浅设色.台北故宫博物院藏.jpg) | 11105×24176 | PD（Commons，书格转载） | ✓ | **够** |
| zaochun_tu | 早春图 | 北宋 1072·郭熙 | 台北故宫博物院 | [链接](https://commons.wikimedia.org/wiki/File:%E6%97%A9%E6%98%A5%E5%9B%BE%E8%BD%B4.%E5%8C%97%E5%AE%8B.%E9%83%AD%E7%86%99%E7%BB%98.%E7%BB%A2%E6%9C%AC%E6%B5%85%E8%AE%BE%E8%89%B2.%E5%AE%8B%E7%A5%9E%E5%AE%97%E7%86%99%E5%AE%81%E4%BA%94%E5%B9%B4.%E5%8F%B0%E5%8C%97%E6%95%85%E5%AE%AB%E5%8D%9A%E7%89%A9%E9%99%A2%E8%97%8F.tif) | 4283×6225 | Public domain |  | **够** |
| qingming_shanghe | 清明上河图 | 北宋·张择端 | 北京故宫博物院 | [链接](https://commons.wikimedia.org/wiki/File:Alongtheriver_QingMing.jpg) | 38414×1800 | PD | ✓ | **够** |
| qianli_jiangshan | 千里江山图 | 北宋 1113·王希孟 | 北京故宫博物院 | [链接](https://commons.wikimedia.org/wiki/File:王希孟千里江山图卷.png) | 153767×6110 | PD（PD-scan） | ✓ | **够** |
| ru_narcissus_basin | 汝窑青瓷无纹水仙盆 | 北宋 | 台北故宫博物院 | [链接](https://digitalarchive.npm.gov.tw/Integrate/GetJson?cid=34&dept=U) | 3068×2281（共 82 张多角度/局部） | CC BY 4.0 | ✓ | **够** |
| ruihe_tu | 瑞鹤图 | 北宋 1112·赵佶 | 辽宁省博物馆 | [链接](https://commons.wikimedia.org/wiki/File:%E7%91%9E%E9%B9%A4%E5%9B%BE%C2%B7%E5%AE%8B%C2%B7%E8%B5%B5%E4%BD%B6%C2%B7%E7%BB%A2%E6%9C%AC%E8%AE%BE%E8%89%B2%C2%B7%E4%BA%8E%E8%BE%BD%E5%AE%81%E7%9C%81%E5%8D%9A%E7%89%A9%E9%A6%86%E8%97%8F.jpg) | 35765×7272 | CC0 |  | **够** |
| wanhe_songfeng | 万壑松风图 | 北宋 1124·李唐 | 台北故宫博物院 | [链接](https://digitalarchive.npm.gov.tw/Integrate/GetJson?cid=33&dept=P) | 4876×6332（8 块 IIIF 拼接） | CC BY 4.0 | ✓ | **够** |
| tage_tu | 踏歌图 | 南宋·马远 | 北京故宫博物院 | [链接](https://commons.wikimedia.org/wiki/File:马远踏歌图轴.png) | 7831×13391 | PD | ✓ | **够** |
| hanjiang_dudiao | 寒江独钓图 | 南宋·传马远 | 东京国立博物馆 TA-140 | [链接](https://commons.wikimedia.org/wiki/File:Angler_on_a_Wintry_Lake,_by_Ma_Yuan,_1195.jpg) | 5906×3159 | PD（PD-Art） | ✓ | **够** |
| shuitu | 水图（十二段） | 南宋·马远 | 北京故宫博物院 | [链接](https://commons.wikimedia.org/wiki/File:马远水图卷.png) | 127821×3400（每段约 4560×2940） | PD | ✓ | **够** |
| pomo_xianren | 泼墨仙人 | 南宋·梁楷 | 台北故宫博物院 | [链接](https://digitalarchive.npm.gov.tw/Integrate/GetJson?cid=14658&dept=P) | 2289×3058（画页 1158×2037） | CC BY 4.0 | ✓ | **勉强** |
| guanyao_vase | 南宋官窑青瓷瓶 | 南宋 12–13 世纪 | 大都会艺术博物馆 18.56.57 | [链接](https://www.metmuseum.org/art/collection/search/52679) | 2993×3852（器身约 1505×2457） | CC0 | ✓ | **够** |
| jian_yohen_tenmoku | 建窑曜变天目茶碗 | 南宋 | 静嘉堂文库美术馆（另藤田美术馆、大德寺龙光院） | [链接](https://commons.wikimedia.org/wiki/File:Yohen_Tenmoku_Tea_Bowl(Seikado).jpg) | 2195×3941 | Public domain |  | **不够** |
| fuchun_wuyong | 富春山居图（无用师卷） | 元 1350·黄公望 | 台北故宫博物院 | [链接](https://commons.wikimedia.org/wiki/File:%E5%AF%8C%E6%98%A5%E5%B1%B1%E5%B1%85%E5%9C%96(%E7%84%A1%E7%94%A8%E5%B8%AB%E5%8D%B7).jpg) | 26134×900 | Public domain |  | **勉强** |
| rongxi_zhai | 容膝斋图 | 元 1372·倪瓒 | 台北故宫博物院 | [链接](https://commons.wikimedia.org/wiki/File:容膝齋圖.jpg) | 1788×3674 | PD（PD-Art） | ✓ | **够** |
| queshua_qiuse | 鹊华秋色图 | 元 1295·赵孟頫 | 台北故宫博物院 | [链接](https://commons.wikimedia.org/wiki/File:2_Zhao_Mengfu_Autumn_Colors_on_the_Qiao_and_Hua_Mountains_Handscroll,_ink_and_colors_on_paper,_28.4_x_93.2_cm_National_Palace_Museum,_Taipei..jpg) | 15868×900 | Public domain |  | **勉强** |
| david_vases | 大维德瓶（青花云龙纹象耳瓶） | 元 1351 | 大维德基金会 / 大英博物馆展出 | [链接](https://commons.wikimedia.org/wiki/File:David_vase_detail_BM_PDF_B.614_n01.jpg) | 2724×4100 | 照片 CC BY 2.5；器物 PD | ✓ | **勉强** |
| guiguzi_jar | 鬼谷下山图罐 | 元 | 私人收藏（2005 年佳士得伦敦拍出） | — | — | — |  | **不够** |
| moputao | 墨葡萄图 | 明·徐渭 | 北京故宫博物院 | [链接](https://commons.wikimedia.org/wiki/File:徐渭水墨葡萄图轴.png) | 6432×16303 | PD | ✓ | **够** |
| lushan_gao | 庐山高图 | 明 1467·沈周 | 台北故宫博物院 | [链接](https://commons.wikimedia.org/wiki/File:%E5%BA%90%E5%B1%B1%E9%AB%98%E5%9B%BE%E8%BD%B4.%E6%98%8E%E6%88%90%E5%8C%96%E4%BA%8C%E5%B9%B4.%E6%B2%88%E5%91%A8%E7%94%BB.%E7%BA%B8%E6%9C%AC%E6%B5%85%E8%AE%BE%E8%89%B2.%E5%8F%B0%E5%8C%97%E6%95%85%E5%AE%AB%E5%8D%9A%E7%89%A9%E9%99%A2%E8%97%8F.tif) | 3204×6140 | Public domain |  | **够** |
| hangong_chunxiao | 汉宫春晓图 | 明·仇英 | 台北故宫博物院 | [链接](https://commons.wikimedia.org/wiki/File:Spring_Morning_in_the_Han_Palace.jpg) | 52680×2683 | Public domain |  | **够** |
| qingbian_tu | 青卞图 | 明 1617·董其昌 | 克利夫兰艺术博物馆 1980.10 | [链接](https://www.clevelandart.org/art/1980.10) | 2376×6944 | CC0（Cleveland Open Access） |  | **够** |
| huanghuali_armchair | 黄花梨靠背椅（明式家具） | 明 17 世纪 | 大都会艺术博物馆 1997.92 | [链接](https://www.metmuseum.org/art/collection/search/39493) | 2667×4000 | CC0（Met Open Access） |  | **够** |
| xuande_dragon_jar | 宣德青花龙纹罐 | 明 15 世纪初（宣德） | 大都会艺术博物馆 37.191.1 | [链接](https://www.metmuseum.org/art/collection/search/39666) | 3000×4000 | CC0（Met Open Access） |  | **够** |
| chenghua_chicken_cup | 成化斗彩鸡缸杯 | 明成化（1465–1487） | 大都会艺术博物馆 1987.85（另台北故宫、北京故宫藏） | [链接](https://commons.wikimedia.org/wiki/File:%E6%98%8E%E6%88%90%E5%8C%96_%E6%99%AF%E5%BE%B7%E9%8E%AE%E7%AA%AF%E9%AC%A5%E5%BD%A9%E9%9B%9E%E7%BC%B8%E6%9D%AF-Chicken_Cup_MET_1987_85_2015AT_003.jpg) | 4000×3125 | CC0 |  | **够** |
| bada_heshi_shuiniao | 荷石水鸟图 | 清·八大山人 | 北京故宫博物院 | [链接](https://commons.wikimedia.org/wiki/File:朱耷荷石水鸟图轴.png) | 6139×16787 | PD | ✓ | **够** |
| bada_fish_rocks | 鱼石图 | 清·八大山人 | 克利夫兰艺术博物馆 1953.247 | [链接](https://www.clevelandart.org/art/1953.247) | 36789×4833 | CC0（Cleveland Open Access） |  | **够** |
| shitao_soujin | 搜尽奇峰打草稿图 | 清 1691·石涛 | 北京故宫博物院 | [链接](https://commons.wikimedia.org/wiki/File:%E7%9F%B3%E6%B6%9B%E6%90%9C%E5%B0%BD%E5%A5%87%E5%B3%B0%E5%9B%BE%E5%8D%B7.png) | 74164×5247 | Public domain |  | **够** |
| baijun_tu | 百骏图 | 清 1728·郎世宁 | 台北故宫博物院 | [链接](https://commons.wikimedia.org/wiki/File:A_Hundred_Steeds.jpg) | 16560×2022 | PD | ✓ | **够** |
| qianlong_glaze_vase | 各种釉彩大瓶 | 清乾隆 | 北京故宫博物院 | [链接](https://commons.wikimedia.org/wiki/File:13_Glazed_Vase.jpg) | 2338×3524 | CC BY 2.0 |  | **勉强** |
| falangcai_pheasant_vase | 珐琅彩锦鸡牡丹纹瓶 | 清雍正/乾隆 | 克利夫兰艺术博物馆 1971.145 | [链接](https://www.clevelandart.org/art/1971.145) | 4096×6144 | CC0（Cleveland Open Access） |  | **够** |
| qibaishi_washeng | 蛙声十里出山泉 | 1951·齐白石 | 中国现代文学馆 | [链接](http://pic.cyol.com/) | 873×3461 | © 齐白石（中国大陆已公有，美国或仍保护）；图像 中国青年报 | ✓ | **勉强** |
| qibaishi_teng | 画藤（齐白石） | 1922·齐白石 | 北京故宫博物院 | [链接](https://commons.wikimedia.org/wiki/File:%E9%BD%90%E7%92%9C%E7%94%BB%E8%97%A4%E8%BD%B4.png) | 7042×13914 | Public domain |  | **够** |
| qibaishi_shrimp | 齐白石 虾 | 近现代·齐白石 | （多件，北京画院等） | — | — | — |  | **不够** |
| wuchangshuo_zitang | 紫藤图（补充） | 近现代·吴昌硕 | 北京故宫博物院 | [链接](https://commons.wikimedia.org/wiki/File:%E5%90%B4%E6%98%8C%E7%A1%95%E7%B4%AB%E8%97%A4%E5%9B%BE%E8%BD%B4.png) | 3300×10653 | Public domain |  | **够** |
| xubeihong_horse | 奔马图 | 1941·徐悲鸿 | 徐悲鸿纪念馆等 | [链接](https://commons.wikimedia.org/wiki/File:Horse_Standing_by_Xu_Beihong,_1940.jpg) | 535×1100 | Public domain |  | **不够** |
| huangbinhong | 黄宾虹山水 | 近现代·黄宾虹 | 浙江省博物馆等 | — | — | — |  | **不够** |
| wuguanzhong_chunruxian | 春如线 | 当代·吴冠中 | 私人（拍卖图） | （拍卖图录） | 2524×2560 | © 吴冠中；图像 © 帝圖藝術拍賣 | ✓ | **勉强** |
| xubing_tianshu | 天书 | 1987–1991·徐冰 | 普林斯顿大学美术馆 2002-281 等 | [链接](https://artmuseum.princeton.edu/) | 484×843（单页）；展厅图 1354×900 | © 徐冰；图像 © Princeton University Art Museum / 徐冰工作室 | ✓ | **不够** |
| caiguoqiang | 蔡国强（火药/装置） | 当代·蔡国强 | — | [链接](https://commons.wikimedia.org/wiki/File:Cai_Guo_Qiang_installation,_Guggenheim,_New_York,_11_Feb._2008_(2259172350).jpg) | 3717×2454 | CC BY 2.0 |  | **勉强** |
| aiweiwei_sunflower_seeds | 葵花籽 | 2010·艾未未 | 泰特现代美术馆（涡轮大厅展出） | [链接](https://commons.wikimedia.org/wiki/File:Ai_Weiwei%27s_Sunflower_Seeds,_Tate_Modern,_detail.jpg) | 3888×2592 | CC0 |  | **够** |


## 二、缺图与许可风险清单

### A. 缺图或不够（上墙前必须换作品或另找图）
| 作品 | 现状 | 建议 |
|---|---|---|
| 莫高窟 45 / 220 窟 | Commons 只有复制品的观众照（港大展、复制壁画） | 敦煌厅用本地 112 窟反弹琵琶（1801×2608，只能整幅看），或走数字敦煌授权（公开传播要另签） |
| 莫高窟 257 窟九色鹿 | 6496×1114，只能 1:1 横移 | 同上 |
| 马王堆黑地彩绘漆棺 | 找到的"Second Coffin"目验是朱地彩绘棺 | 改挂朱地彩绘棺（CC0 4752×3168），或只挂 T 形帛画 |
| 建窑曜变天目 | 只有 1930 年代黑白图录照 | 改 Met 建窑兔毫盏（CC0 馆方图）；讲曜变只能用文字 |
| 张旭《古诗四帖》 | 413×432 | 狂草改用祭侄文稿（15610×5784）或拼台北故宫自叙帖分段图 |
| 怀素《自叙帖》 | Commons 全卷只有 480 高 | 拼台北故宫 IIIF 分段图（CC BY 4.0），拼完实测 |
| 虢国夫人游春图 | 4674×979 | 唐代人物画用步辇图（143397×9399） |
| 鬼谷下山罐 | 私人藏，无开放图 | 元青花用大维德瓶或 Met 鱼藻纹盘（CC0 馆方白底） |
| 富春山居图（无用师卷） | Commons 900 高 | 拼台北故宫 81 张分段图（CC BY 4.0），预计画心高约 1500 |
| 鹊华秋色 | Commons 900 高 | 拼台北故宫 15 张（CC BY 4.0） |
| 齐白石虾、黄宾虹、徐悲鸿奔马 | 无开放高清 | 齐白石用《画藤》7042×13914 或本地《蛙声》；黄宾虹、徐悲鸿需查名画记或向馆方要图 |
| 徐冰《天书》 | 单页 484×843，展厅图 ≤1354 | 向徐冰工作室/普林斯顿要图；否则只整幅小尺寸看 |
| 八大《孤禽图》 | 没找到 | 用本地《荷石水鸟图》（6139×16787）或克利夫兰《鱼石图》（CC0） |

### B. 像素够但照片是展柜实拍（背景杂、有反光）
四羊方尊、后母戊鼎、三星堆面具与大立人、曾侯乙编钟、长信宫灯、铜奔马、三彩骆驼载乐俑、红山玉猪龙、良渚玉琮、各种釉彩大瓶、大维德瓶。都不是"干净背景正面照"，上墙要抠底或压暗背景。**馆方白底图只有**：毛公鼎（台北故宫）、汝窑水仙盆（台北故宫）、南宋官窑瓶/宣德青花罐/黄花梨椅/成化鸡缸杯/孝文帝礼佛图（Met CC0）、马家窑罐/珐琅彩瓶（克利夫兰 CC0）。

### C. 许可或来源存疑（照实记录，用前要看）
- **CC BY-SA 连锁**：人面鱼纹盆（GFDL/BY-SA 3.0）、后母戊鼎（BY-SA 3.0）、舞蹈纹盆、玉猪龙、良渚玉琮、三星堆大立人、长信宫灯、铜奔马、云冈 20 窟、昭陵飒露紫（Penn 实拍）、霍去病马（BY-SA 2.0）。网站若整体按 CC 发布要带 BY-SA；逐图署名即可满足非商用展示。多数有 Gary Todd CC0 替代（玉猪龙、铜奔马、编钟、兵马俑、卢舍那、昭陵碑林四骏）。
- **来源不明的"PD"大图**：瑞鹤图 35765×7272（上传者写 Own work 却标 CC0，颜色和是否拼接待核）；汉宫春晓 52680×2683（来源不明）；清明上河图 38414×1800（来源百度贴吧，已按故宫官网图校色）；112 窟反弹琵琶（网页转载，拍摄者不明）。
- **馆方站本身不开放**：故宫名画记/数字文物库的大图（游春、步辇、千里江山、踏歌、水图、洛神、伯远帖、石涛、徐渭、八大、吴昌硕、齐白石画藤）是第三方拼接上传到 Commons，Commons 按 PD-Art 标公有领域；credit 写"故宫博物院 名画记 / Wikimedia Commons"。
- **版权期作品**：齐白石（中国大陆已公有，美国状态待核）、吴冠中（© 家属；图来自拍卖行）、徐冰、蔡国强、艾未未（作品 ©；照片另有摄影者许可）。按用户新定可用于非商用展示，credit 要写作者、出处和版权方。
- **别混的同名件**：`File:清明上河图卷.png` 是明人仿本；大阪东洋陶瓷馆的汝窑水仙盆不是台北那件；弗利尔本洛神赋图是另一个摹本；陕历博的三彩骆驼载乐俑（七男一女）不是国博那件。
- **e国宝**（寒江独钓 6122×3388）条款禁止转载，已不收；用 Commons 或 ColBase 图。

### D. 本轮新发现（相对前几轮）
- 成化斗彩鸡缸杯：Met 42515（1987.85，Chenghua mark and period），5 个角度约 4000×3100，CC0，比台北故宫 3000×2250 更大。
- 竹林七贤砖画：Gary Todd CC0 3888×2592 三张描述为"Seven worthies"（南京博物院），前轮以为只有展柜全景。是否原件待核。
- 昭陵六骏：Penn 两骏实拍 8064×6048（CC BY-SA 4.0）；另有金代赵霖《昭陵六骏图卷》70271×2530（PD，故宫），可做石刻与绘画对照。
- 四羊方尊：Gary Todd 国博实拍 3456×5184 CC0（前轮只找到约 1500 px 的图）。

## 三、逐件备注（署名文本、备选、风险）

### 人面鱼纹彩陶盆 · `banpo_fish_basin` · 勉强
- 署名：人面鱼纹彩陶盆，仰韶文化半坡类型，中国国家博物馆藏；摄影 Zhangzhugang，Wikimedia Commons，CC BY-SA 3.0
- 本地：`~/claude-projects/china-art/trailer/src/s1_neolithic/banpo_motif.jpg`
- 备选：https://commons.wikimedia.org/wiki/File:%E4%BA%BA%E9%9D%A2%E9%B1%BC%E7%BA%B9%E5%BD%A2%E5%BD%A9%E9%99%B6%E7%9B%8608736.jpg（7641×5097，CC BY-SA 4.0）；https://commons.wikimedia.org/wiki/File:%E4%BA%BA%E9%9D%A2%E9%B1%BC%E7%BA%B9%E5%BD%A2%E5%BD%A9%E9%99%B6%E7%9B%8608737.jpg（6902×5177，CC BY-SA 4.0）
- 备注：展柜实拍，非馆方图；本地 trailer/assets/s1_neolithic/work.png 1943×1326 已裁。盆内纹要俯视，08736/08737 更大（7641×5097）但角度待目验。无馆方开放图。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/banpo_fish_basin.jpg`

### 马家窑文化旋涡纹彩陶罐 · `majiayao_spiral_jar` · 够
- 署名：Jar with Spiral Designs, The Cleveland Museum of Art, Gift of Donna S. and James S. Reid Jr. in honor of Dr. Ju-hsi Chou (2004.64), CC0
- 原图：https://openaccess-cdn.clevelandart.org/2004.64/2004.64_full.tif
- 备选：https://commons.wikimedia.org/wiki/File:%E6%B6%A1%E7%BA%B9%E5%9B%9B%E7%B3%BB%E5%BD%A9%E9%99%B6%E7%BD%9008731.jpg（5304×7952，CC BY-SA 4.0）
- 备注：馆方白底正面照，CC0，最干净。国博同类旋涡纹罐只有展柜实拍。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/majiayao_spiral_jar.jpg`

### 舞蹈纹彩陶盆 · `majiayao_dance_basin` · 勉强
- 署名：舞蹈纹彩陶盆，中国国家博物馆；图像 Augusthaiho，Wikimedia Commons，CC BY-SA 4.0（来源：Own work）
- 备选：https://commons.wikimedia.org/wiki/File:%E8%88%9E%E8%B9%88%E7%BA%B9%E5%BD%A9%E9%99%B6%E7%9B%8608776.jpg（5417×4063，CC BY-SA 4.0）；https://commons.wikimedia.org/wiki/File:%E8%88%9E%E8%B9%88%E7%BA%B9%E5%BD%A9%E9%99%B6%E7%9B%8608774.jpg（3725×2483，CC BY-SA 4.0）
- 备注：马家窑最有名的一件；展柜实拍（Augusthaiho），有俯视图 08776，舞人纹在盆内壁，要目验反光。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/majiayao_dance_basin.jpg`

### 红山文化玉猪龙 · `hongshan_pig_dragon` · 勉强
- 署名：红山文化玉猪龙，辽宁省博物馆（另有国博、台北故宫藏品）；图像 名字长的让人受不了，Wikimedia Commons，CC BY-SA 4.0（来源：Own work）
- 备选：https://commons.wikimedia.org/wiki/File:Hongshan_Culture_-_Jade_Pig-Dragon_02.jpg（5184×3456，CC0）；https://commons.wikimedia.org/wiki/File:Hongshan_Jade_Dragon_1.jpg（5184×3456，CC0）；https://commons.wikimedia.org/wiki/File:Hongshan_Culture_Jade_Pig_Dragon_02.jpg（5184×3456，CC0）
- 备注：全是展柜实拍；辽博那张 8192×5464 最大。Gary Todd CC0 有台北故宫、国博、辽博多件，许可更宽。器小，推近余量足，但背景/反光要处理。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/hongshan_pig_dragon.jpg`

### 良渚玉琮王（补充） · `liangzhu_cong_king` · 勉强
- 署名：良渚玉琮王（补充），浙江省博物馆；图像 Siyuwj，Wikimedia Commons，CC BY-SA 4.0（来源：Own work）
- 备注：展柜实拍；神徽特写只有 1541×1206。补充候选，非必选。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/liangzhu_cong_king.jpg`

### 后母戊鼎 · `houmuwu_ding` · 勉强
- 署名：后母戊鼎，商晚期，中国国家博物馆藏；摄影 Mlogic，Wikimedia Commons，CC BY-SA 3.0
- 本地：`~/claude-projects/china-art/trailer/src/s2_shang/houmuwu_full.jpg`
- 备选：https://commons.wikimedia.org/wiki/File:%E5%8F%B8%E6%AF%8D%E6%88%8A%E6%96%B9%E9%BC%8E%E6%8B%93%E6%9C%AC.jpg（3930×5000，Public domain）
- 备注：展厅实拍，本地 work.png 2148×1326 已做单应校正。全形拓 3930×5000 PD（上博）可做转场/铭文素材。无馆方开放图。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/houmuwu_ding.jpg`

### 毛公鼎 · `maogong_ding` · 够
- 署名：毛公鼎，台北故宫博物院；图像 anonymous，Wikimedia Commons，CC BY 4.0（来源：國立故宮博物院器物典藏資料檢索系統）
- 备选：https://commons.wikimedia.org/wiki/File:%E6%AF%9B%E5%85%AC%E9%BC%8E.png（2122×2829，CC BY 4.0）；https://commons.wikimedia.org/wiki/File:Bronze_Mao_Gong_Ding,_Late_Western_Zhou-_Longest_Bronze_Inscription_in_the_World_a.jpg（5184×3456，CC0）；https://commons.wikimedia.org/wiki/File:Mao_Gong_ding_inscription.png（4200×3000，Public domain）
- 备注：台北故宫器物典藏官方图，干净背景，CC BY 4.0；署名按"西周晚期 毛公鼎。國立故宮博物院，臺北，CC BY 4.0 @ www.npm.gov.tw"。铭文拓本 4200×3000 PD，全形拓轴 2485×5740 PD（前轮 c1 记录）。台北故宫 Open Data 可能有多角度 6 MP 图，未查。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/maogong_ding.jpg`

### 四羊方尊 · `four_ram_zun` · 勉强
- 署名：四羊方尊，中国国家博物馆；图像 Gary Todd，Wikimedia Commons，CC0（来源：https://www.flickr.com/photos/101561334@N08/9844238033/）
- 备选：https://commons.wikimedia.org/wiki/File:Fyra_baggars_kvadripod.jpg（2600×2715，CC0）；https://commons.wikimedia.org/wiki/File:Late_Shang_Bronze_Zun_ram%27s_head.jpg（5184×3456，CC0）
- 备注：Gary Todd 国博实拍 CC0 3456×5184（描述"Hunan, 1938"即宁乡出土的四羊方尊）；有玻璃反光风险，需目验。前轮认为高清不够，这轮找到 Gary Todd 系列。 缩略图目验：是四羊方尊，展柜内拍，背景杂、有玻璃反光。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/four_ram_zun.jpg`

### 三星堆青铜纵目面具 · `sanxingdui_mask` · 勉强
- 署名：三星堆青铜纵目面具，三星堆博物馆；图像 Gary Todd，Wikimedia Commons，CC0（来源：https://www.flickr.com/photos/101561334@N08/9951417125/）
- 备选：https://commons.wikimedia.org/wiki/File:Ancient_Bronze_Mask_from_Sanxingdui_with_Protruding_Eyes_%26_Ears_(9951414745).jpg（4752×3168，CC0）；https://commons.wikimedia.org/wiki/File:Ancient_Bronze_Mask_from_Sanxingdui_with_Protruding_Eyes_%26_Ears_b.jpg（4752×3168，CC0）
- 备注：Gary Todd 2010 馆内实拍 CC0，a–e 多角度；展厅暗背景，可用但非馆方图。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/sanxingdui_mask.jpg`

### 三星堆青铜大立人 · `sanxingdui_standing_figure` · 勉强
- 署名：三星堆青铜大立人，三星堆博物馆；图像 Siyuwj，Wikimedia Commons，CC BY-SA 4.0（来源：Own work）
- 备注：展柜实拍，竖幅 4016×6016，高度充足；背景与反光待目验。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/sanxingdui_standing_figure.jpg`

### 曾侯乙编钟 · `zeng_bianzhong` · 勉强
- 署名：曾侯乙编钟，湖北省博物馆；图像 Gary Todd from Xinzheng, China，Wikimedia Commons，CC0（来源：Two Tone Set-bells of Marquis Yi of Zeng）
- 备选：https://commons.wikimedia.org/wiki/File:Bianzhong_of_Marquis_Yi_of_Zeng_Wuhan.jpg（3264×2448，CC BY-SA 3.0）；https://commons.wikimedia.org/wiki/File:%E6%9B%BE%E4%BE%AF%E4%B9%99%E7%BC%96%E9%92%9F%E9%92%9F%E7%B0%A81.jpg（8256×5504，CC BY-SA 4.0）
- 备注：整套钟架全景只有展厅实拍：Gary Todd CC0 4752×3168（多张，需挑正面全景）；钟簨横梁特写 8256×5504 CC BY-SA 4.0。无馆方开放图。 缩略图目验：当前首选是三件甬钟的局部，不是整套钟架；整套全景要在 Gary Todd 同组 10 余张里挑。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/zeng_bianzhong.jpg`

### 秦始皇陵兵马俑一号坑 · `terracotta_pit1` · 够
- 署名：秦始皇陵兵马俑一号坑，秦始皇帝陵博物院；图像 Gary Lee Todd, Ph.D.，Wikimedia Commons，CC0（来源：https://www.flickr.com/photos/101561334@N08/9895741855/）
- 备选：https://commons.wikimedia.org/wiki/File:General_view_of_a_section_of_the_terracotta_warriors_(35519047732).jpg（4928×3264，CC BY 2.0）；https://commons.wikimedia.org/wiki/File:Terracotta_Soldier_Panorama_(5258589290).jpg（6816×2148，CC BY 2.0）
- 备注：现场实拍 CC0；构图待目验（要纵深队列）。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/terracotta_pit1.jpg`

### 秦跪射俑 · `kneeling_archer` · 勉强
- 署名：秦跪射俑，秦始皇帝陵博物院；图像 Gary Todd，Wikimedia Commons，CC0（来源：https://www.flickr.com/photos/101561334@N08/32553881737/）
- 备选：https://commons.wikimedia.org/wiki/File:Terracotta_kneeling_archer_boot.JPG（1704×2004，CC BY-SA 3.0）
- 备注：Gary Todd 2019 特展实拍 CC0，竖幅 4000×6000；背景是展厅。鞋底纹特写 1704×2004。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/kneeling_archer.jpg`

### 马王堆一号墓 T 形帛画（非衣） · `mawangdui_t_banner` · 够
- 署名：T 形帛画（非衣），西汉，长沙马王堆一号墓出土，湖南博物院藏；图像 Google Art Project / Wikimedia Commons
- 本地：`~/claude-projects/china-art/trailer/src_v3/tshaped/T-shaped_Painting_on_Silk_-_Google_Art_Project.jpg`
- 备注：馆方（GA&C）图，竖挂整幅 4804 高够；但帛面上段 1651 宽、竖干约 880 宽，推近余量小（assets_v3/tshaped/meta.json）。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/mawangdui_t_banner.jpg`

### 马王堆一号墓黑地彩绘漆棺（本图实为朱地彩绘棺，见备注） · `mawangdui_black_coffin` · 不够
- 署名：马王堆一号墓黑地彩绘漆棺，湖南博物院；图像 Gary Todd from Xinzheng, China，Wikimedia Commons，CC0（来源：Mawangdui Han Second Coffin from Tomb #1）
- 备选：https://commons.wikimedia.org/wiki/File:Mawangdui_Han_Second_Coffin_from_Tomb_-1_(10113019345).jpg（4752×3168，CC0）；https://commons.wikimedia.org/wiki/File:Lacquer_Coffin_Unearthed_from_the_2nd-century-BC_Han_Tomb_No.1_at_Mawangdui_2011-07.JPG（4320×3240，CC BY-SA 4.0）
- 备注：缩略图目验：Gary Todd 标"Second Coffin"的这张是红底（朱地彩绘棺的龙纹局部），不是黑地彩绘棺——他的"second"可能从内往外数。黑地彩绘棺本轮没有确认到可用高清；同组 7 张里可能有黑地那具，需逐张看。朱地彩绘棺可用：本图 4752×3168 CC0 与 4320×3240 CC BY-SA 4.0（猫猫的日记本）。无馆方高清（湖南博物院藏品页前轮 404）。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/mawangdui_black_coffin.jpg`

### 长信宫灯 · `changxin_lamp` · 勉强
- 署名：长信宫灯，河北博物院；图像 Cangminzho，Wikimedia Commons，CC BY-SA 4.0（来源：Own work）
- 备选：https://commons.wikimedia.org/wiki/File:Changxin_Palace_Lamp_(11867682066).jpg（3456×2304，CC0）
- 备注：展柜实拍竖幅 5293×7058，像素足；背景与反光待目验。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/changxin_lamp.jpg`

### 铜奔马（马踏飞燕） · `bronze_galloping_horse` · 勉强
- 署名：铜奔马（马踏飞燕），甘肃省博物馆；图像 三猎，Wikimedia Commons，CC BY-SA 4.0（来源：Own work）
- 备选：https://commons.wikimedia.org/wiki/File:Eastern_Han_Bronze_Galloping_Horse_(10094006603).jpg（5184×3456，CC0）
- 备注：展柜实拍；CC BY-SA 4.0 那张更正，Gary Todd CC0 许可更宽。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/bronze_galloping_horse.jpg`

### 霍去病墓马踏匈奴 · `huoqubing_horse` · 够
- 署名：霍去病墓马踏匈奴，茂陵博物馆；图像 James Glazier，Wikimedia Commons，CC BY-SA 2.0（来源：https://www.flickr.com/photos/jag_jaf_travel/14441248037/）
- 备选：https://commons.wikimedia.org/wiki/File:Horse_of_Huo_Qubing_Mausoleum_(front).jpg（3409×4830，CC BY-SA 2.0）；https://commons.wikimedia.org/wiki/File:Horse_of_Huo_Qubing_Mausoleum_(right_side).jpg（3000×4000，CC BY-SA 2.0）
- 备注：James Glazier 三个角度 CC BY-SA 2.0；石雕，光线自然。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/huoqubing_horse.jpg`

### 人物御龙帛画（补充） · `yulong_banner` · 够
- 署名：人物御龙帛画，战国（楚），湖南博物院藏；图像 Google Art Project / Wikimedia Commons
- 本地：`~/claude-projects/china-art/trailer/src_v3/yulong/Figure_Driving_a_Dragon_-_Google_Art_Project.jpg`
- 备注：楚汉浪漫的另一件；本地 assets_v3/yulong 已有 meta。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/yulong_banner.jpg`

### 女史箴图（唐摹本） · `admonitions_scroll` · 勉强
- 署名：传顾恺之《女史箴图》（唐摹本），大英博物馆藏；图像 Wikimedia Commons
- 本地：`~/claude-projects/china-art/trailer/src/s4_eastern_jin/admonitions_center.jpg`
- 备选：commons:File:顾恺之女史箴图卷（宋摹）.png
- 备注：画心高 1340 < 1400，只能 1:1 横移、不能推近。大英自家图 CC BY-NC-SA 4.0 但最大约 1000 px。故宫宋摹白描本 53373×1637 无色。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/admonitions_scroll.jpg`

### 洛神赋图（宋摹本） · `luoshen_scroll` · 够
- 署名：传顾恺之《洛神赋图》（宋摹本），故宫博物院藏；图像 故宫博物院 名画记 / Wikimedia Commons
- 本地：`~/claude-projects/china-art/trailer/src_v3/luoshen/luoshen_overview_ds8.jpg`；全分辨率 `~/claude-projects/china-art/trailer/src_v3/luoshen/luoshen.png`
- 备注：原图 trailer/src_v3/luoshen/luoshen.png，画心高约 2230；work 在 assets_v3/luoshen/work_46600x2472.rgb。弗利尔本 50872×3235 是另一摹本，勿混。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/luoshen_scroll.jpg`

### 兰亭序（神龙本） · `lanting_shenlong` · 勉强
- 署名：兰亭序（神龙本），北京故宫博物院；图像 Feng Chengsu (馮承素), original by Wang Xizhi (王羲之)，Wikimedia Commons，Public domain（来源：http://www.linyi.gov.cn/xizhi/zuopin/lanting.asp）
- 备选：https://commons.wikimedia.org/wiki/File:%E7%A5%9E%E9%BE%8D%E8%98%AD%E4%BA%AD%E5%BA%8F%E5%85%A8.JPG（28549×1300，Public domain）
- 备注：本幅 4513×1480（高刚过 1400），含题跋全卷 28549×1300。故宫数字文物库可能有更大图，未查到。书法厅按"笔顺揭示"用，1:1 够看笔势。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/lanting_shenlong.jpg`

### 伯远帖 · `boyuan_tie` · 够
- 署名：伯远帖，北京故宫博物院；图像 Wang Xun，Wikimedia Commons，Public domain（来源：https://digicol.dpm.org.cn/cultural/detail?id=5eff54bf308f47faa104af37f4b614c6）
- 备注：全卷 33019×2160（含引首、题跋），帖本身估计宽 1100–1400 px，高约 2000，需裁出后实测。credit 故宫数字文物库。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/boyuan_tie.jpg`

### 云冈第 20 窟露天大佛 · `yungang_cave20` · 够
- 署名：云冈第 20 窟露天大佛，山西大同云冈石窟；图像 Thebrainchamber1，Wikimedia Commons，CC BY-SA 4.0（来源：Own work）
- 备选：https://commons.wikimedia.org/wiki/File:%E4%BA%91%E5%86%88%E7%9F%B3%E7%AA%9F%E7%AC%AC20%E7%AA%9F%E5%A4%A7%E4%BD%9B%E6%AD%A3%E9%9D%A2.jpg（4284×5712，CC BY-SA 4.0）
- 备注：现场实拍 CC BY-SA 4.0，横竖两张；按文件页署作者。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/yungang_cave20.jpg`

### 孝文帝礼佛图（龙门宾阳中洞） · `xiaowen_procession` · 够
- 署名：Emperor Xiaowen and his entourage worshipping the Buddha, The Metropolitan Museum of Art, Fletcher Fund, 1935 (35.146), CC0
- 原图：https://images.metmuseum.org/CRDImages/as/original/DP170138.jpg
- 备注：馆方图 CC0；照片可见拼合裂缝。字幕要照实说流失史。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/xiaowen_procession.jpg`

### 竹林七贤与荣启期砖画 · `bamboo_sages_brick` · 勉强
- 署名：竹林七贤与荣启期砖画，南京博物院；图像 Gary Todd from Xinzheng, China，Wikimedia Commons，CC0（来源：Southern Dynasty Brick Mural）
- 备选：https://commons.wikimedia.org/wiki/File:Southern_Dynasty_Brick_Mural_(10152446165).jpg（3888×2592，CC0）；https://commons.wikimedia.org/wiki/File:Southern_Dynasty_Brick_Mural_(10152451275).jpg（3888×2592，CC0）；https://commons.wikimedia.org/wiki/File:%E7%AB%B9%E6%9E%97%E4%B8%83%E8%B4%A4%E4%B8%8E%E8%8D%A3%E5%90%AF%E6%9C%9F%E7%A0%96%E7%94%BB05527.jpg（5015×2821，CC BY-SA 4.0）
- 备注：本轮新发现：Gary Todd CC0 三张描述为"Seven worthies of the bamboo grove"（南京博物院陶瓷馆展出，可能是复制品，需看图核）。前轮只知道 05527 展柜全景（线描看不清）。 缩略图目验：灰砖模印线刻，树与人物可辨，一幅铺满画面；是否原件未核。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/bamboo_sages_brick.jpg`

### 莫高窟 257 窟《鹿王本生》 · `dunhuang257_deer` · 勉强
- 署名：莫高窟 257 窟《鹿王本生》，敦煌研究院；图像 Unknown authorUnknown author，Wikimedia Commons，Public domain（来源：https://artsandculture.google.com/asset/%E9%B9%BF%E7%8E%8B%E6%9C%AC%E7%94%9F%E6%95%85%E4%BA%8B%E7%95%AB/cAF407gix6E1LA）
- 备注：6496×1114（GA&C 转载标 PD），横带高 1114，只能 1:1。Commons 上"璀璨敦煌 xxxpcs"是拼图成品照，不能用。更好的图只能走数字敦煌授权（公开传播需另签）。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/dunhuang257_deer.jpg`

### 游春图 · `youchun_tu` · 够
- 署名：游春图，北京故宫博物院；图像 Zhan Ziqian，Wikimedia Commons，Public domain（来源：https://minghuaji.dpm.org.cn/paint/detail?id=796340a0de3845319bae0b76a4f47b22）
- 备注：97407×10476 含裱全卷，1.36 GB；画心可推近 8× 以上。credit 故宫名画记。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/youchun_tu.jpg`

### 步辇图（宋摹） · `bunian_tu` · 够
- 署名：步辇图（宋摹），北京故宫博物院；图像 Yan Liben，Wikimedia Commons，Public domain（来源：https://minghuaji.dpm.org.cn/paint/detail?id=4b24c04a7a544661a1d523b98f74fdd3）
- 备注：143397×9399，1.79 GB，极清。credit 故宫名画记。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/bunian_tu.jpg`

### 龙门奉先寺卢舍那大佛 · `fengxian_vairocana` · 够
- 署名：龙门奉先寺卢舍那大佛，河南洛阳龙门石窟；图像 Gary Todd，Wikimedia Commons，CC0（来源：https://www.flickr.com/photos/101561334@N08/10255458934/）
- 备选：https://commons.wikimedia.org/wiki/File:Ancient_Buddhist_Grottoes_at_Longmen-_Fengxian_Temple,_Vairocana_Buddha_Head.jpg（3168×4752，CC0）
- 备注：Gary Todd CC0 全龛 5184×3456 + 头部 3168×4752；挑光线正、无游客的。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/fengxian_vairocana.jpg`

### 莫高窟 45 窟彩塑与壁画 · `dunhuang45` · 不够
- 署名：莫高窟 45 窟彩塑与壁画，敦煌研究院；图像 Haihongu KWAM LaunEC 800，Wikimedia Commons，CC0（来源：Own work）
- 备注：Commons 只有香港大学展览里复制品的观众照（CC0），不是原窟。原窟图只能走数字敦煌授权。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/dunhuang45.jpg`

### 莫高窟 220 窟（贞观十六年） · `dunhuang220` · 不够
- 署名：莫高窟 220 窟（贞观十六年），敦煌研究院；图像 Hiroooooo，Wikimedia Commons，CC BY-SA 3.0（来源：Own work）
- 备选：commons:File:敦煌莫高窟 （Dunhuang Mogao Grottoes）.jpg
- 备注：只有复制壁画的照片 3910×2930 和小图，原窟无开放高清。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/dunhuang220.jpg`

### 莫高窟 103 窟维摩诘像 · `dunhuang103_vimalakirti` · 勉强
- 署名：莫高窟 103 窟维摩诘像，敦煌研究院；图像 Chinese artist，Wikimedia Commons，Public domain（来源：Scanned from Michael Sullivan's The Arts of China: Fourth Edition (1999)）
- 备注：画册扫描 1968×2835，色不可靠；竖挂整幅勉强够高。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/dunhuang103_vimalakirti.jpg`

### 莫高窟 112 窟反弹琵琶 · `dunhuang112_pipa` · 勉强
- 署名：反弹琵琶伎乐天，莫高窟第 112 窟南壁（中唐），敦煌研究院；图像 Wikimedia Commons（已校色）
- 本地：`~/claude-projects/china-art/trailer/assets_v3/pipa112/work.png`
- 备注：整幅竖看高度够，不能推近；源为 Display P3 网页转载，已校色但没有馆方对照。许可来源存疑。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/dunhuang112_pipa.jpg`

### 祭侄文稿 · `jizhi_wengao` · 够
- 署名：祭侄文稿，台北故宫博物院；图像 Yan Zhenqing，Wikimedia Commons，Public domain（来源：https://digitalarchive.npm.gov.tw/Painting/Content?pid=3&amp;Dept=P）
- 备选：npm:台北故宫 Open Data 600 万像素 CC BY 4.0 版
- 备注：15610×5784，法书里图源最好的一件。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/jizhi_wengao.jpg`

### 古诗四帖 · `zhangxu_gushi_sitie` · 不够
- 署名：古诗四帖，辽宁省博物馆；图像 Zhang Xu，Wikimedia Commons，Public domain（来源：http://www.seattlecentral.org/faculty/cmalody/T3ma/chinacallig.htm）
- 备注：只有 413×432。狂草厅若要张旭，需向辽博要图；否则改怀素或祭侄。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/zhangxu_gushi_sitie.jpg`

### 自叙帖 · `huaisu_zixu` · 不够
- 署名：自叙帖，台北故宫博物院；图像 Huaisu，Wikimedia Commons，Public domain（来源：Decipher the Calligraphy: Autobiography. NPM's Anime Carnival (exhibit). Taipei: National Palace Museum.）
- 备选：https://commons.wikimedia.org/wiki/File:%E5%94%90%E6%87%B7%E7%B4%A0%E8%87%AA%E6%95%98%E5%B8%96_%E5%8D%B7.png（2831×2119，CC0）；npm:台北故宫 IIIF 分段图 CC BY 4.0（可拼）
- 备注：Commons 全卷只有 480 高；台北故宫分段图 CC BY 4.0（2831×2119 一张已在 Commons，CC0 标注），拼接后可能够，待实测。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/huaisu_zixu.jpg`

### 三彩骆驼载乐俑 · `sancai_camel_musicians` · 勉强
- 署名：三彩骆驼载乐俑，中国国家博物馆；图像 Gary Todd, https://www.flickr.com/photos/101561334@N08/，Wikimedia Commons，CC0（来源：https://www.flickr.com/photos/101561334@N08/9833881656/in/album-72157635681454743/）
- 备选：https://commons.wikimedia.org/wiki/File:Polychrome_glazed_tomb_figurine_of_a_troupe_of_musicians_on_a_camel,_NMC.jpg（2305×3457，CC BY-SA 4.0）
- 备注：Gary Todd CC0 3456×5184，有玻璃倒影、要修；陕历博另一件（七男一女）别混。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/sancai_camel_musicians.jpg`

### 昭陵六骏·飒露紫 · `zhaoling_saluzi` · 勉强
- 署名：昭陵六骏·飒露紫，宾夕法尼亚大学考古与人类学博物馆（另四骏在西安碑林）；图像 Patrick20242023，Wikimedia Commons，CC BY-SA 4.0（来源：Own work）
- 备选：https://commons.wikimedia.org/wiki/File:%E5%AE%BE%E5%A4%95%E6%B3%95%E5%B0%BC%E4%BA%9A%E5%A4%A7%E5%AD%A6%E5%8D%9A%E7%89%A9%E9%A6%86%E5%94%90%E4%BB%A3%E6%98%AD%E9%99%B5%E5%85%AD%E9%AA%8F%E4%B9%8B%E4%B8%80%E6%8B%B3%E6%AF%9B%E4%AF%84.jpg（8064×6048，CC BY-SA 4.0）；https://commons.wikimedia.org/wiki/File:Six_Steeds_of_Zhao_Mausoleum_(9913023045).jpg（5184×3456，CC0）；https://commons.wikimedia.org/wiki/File:%E8%B5%B5%E9%9C%96%E6%98%AD%E9%99%B5%E5%85%AD%E9%AA%8F%E5%9B%BE%E5%8D%B7.png（70271×2530，Public domain）
- 备注：Penn 两骏实拍 8064×6048 CC BY-SA 4.0；碑林四骏 Gary Todd CC0。另有金代赵霖《昭陵六骏图卷》70271×2530 PD（故宫），可做书画对照。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/zhaoling_saluzi.jpg`

### 虢国夫人游春图（宋摹） · `guoguo_furen` · 不够
- 署名：虢国夫人游春图（宋摹），辽宁省博物馆；图像 Zhang Xuan，Wikimedia Commons，Public domain（来源：Zhang Xuan）
- 备选：https://commons.wikimedia.org/wiki/File:The_Spring_Travel_of_the_Guo_State_Queen.jpg（4573×979，Public domain）
- 备注：只有 4674×979，高 <1000。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/guoguo_furen.jpg`

### 韩熙载夜宴图（宋摹） · `hanxizai_yeyan` · 够
- 署名：传顾闳中《韩熙载夜宴图》（宋摹本），故宫博物院藏；图像 书格 / Wikimedia Commons
- 本地：`~/claude-projects/china-art/trailer/assets_v3/yeyan/overview_painting_ds16.jpg`；全分辨率 `~/claude-projects/china-art/trailer/src_v3/yeyan/yeyan.tif`
- 备注：原图 trailer/src_v3/yeyan/yeyan.tif（588 MB）；听乐段 work 已切好。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/hanxizai_yeyan.jpg`

### 匡庐图 · `kuanglu_tu` · 够
- 署名：匡庐图，台北故宫博物院；图像 Jing Hao，Wikimedia Commons，Public domain（来源：https://www.shuge.org/meet/topic/115745/）
- 备选：npm:台北故宫 Open Data 600 万像素 CC BY 4.0
- 备注：7473×13091（书格），文件名写"纸本"是错的，馆方著录绢本。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/kuanglu_tu.jpg`

### 谿山行旅图 · `xishan_xinglv` · 够
- 署名：范宽《谿山行旅图》，台北故宫博物院藏；图像 Wikimedia Commons（书格）
- 本地：`~/claude-projects/china-art/trailer/assets_v3/xishan/preview_s8.jpg`；全分辨率 `~/claude-projects/china-art/trailer/assets_v3/xishan/work_full.npy`
- 备选：npm:台北故宫 IIIF cid=1195 全图 1793×3904 + 局部约 7 MP，CC BY 4.0（对色参照）
- 备注：work_full.npy 已在 assets_v3/xishan；偏暗偏黄未对色。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/xishan_xinglv.jpg`

### 早春图 · `zaochun_tu` · 够
- 署名：早春图，台北故宫博物院；图像 Guo Xi，Wikimedia Commons，Public domain（来源：https://www.shuge.org/meet/topic/20092/）
- 备选：npm:台北故宫 IIIF cid=47 全图 2212×3164 + 25 张局部，CC BY 4.0
- 备注：4283×6225（书格），竖挂够；也可像万壑松风一样拼 IIIF 局部。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/zaochun_tu.jpg`

### 清明上河图 · `qingming_shanghe` · 够
- 署名：张择端《清明上河图》，故宫博物院藏；图像 Wikimedia Commons（来源百度贴吧，已按故宫官网图校色）
- 本地：`~/claude-projects/china-art/series/assets/qingming/qingming_cc_preview_4000.jpg`；全分辨率 `~/claude-projects/china-art/series/assets/qingming/qingming_cc_38414x1800.rgb`
- 备选：commons:File:清明上河图卷.png（⚠ 明人仿本，别用）
- 备注：主用 series/assets/qingming/qingming_cc_38414x1800.rgb（已校色）；画心高约 1750，刚够。名画记可缩放图可能拼得更大，未试。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/qingming_shanghe.jpg`

### 千里江山图 · `qianli_jiangshan` · 够
- 署名：王希孟《千里江山图》，北宋，故宫博物院藏；图像 故宫博物院 名画记
- 本地：`~/claude-projects/china-art/trailer/assets_v3/qianli/qianli_full_ds16_9610x381.rgb`；全分辨率 `~/claude-projects/china-art/trailer/src/s5_northern_song/qianli_ds3_51255x2036.rgb`
- 备注：全图 trailer/src/s5_northern_song/qianli_full.png（2 GB，只能流式）；ds3 51255×2036 memmap。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/qianli_jiangshan.jpg`

### 汝窑青瓷无纹水仙盆 · `ru_narcissus_basin` · 够
- 署名：北宋 汝窯青瓷無紋水仙盆。國立故宮博物院，臺北，CC BY 4.0 @ www.npm.gov.tw
- 本地：`~/claude-projects/china-art/series/assets/ru/ru_full_front_PAE.jpg`
- 备选：https://commons.wikimedia.org/wiki/File:%E9%9D%92%E7%A3%81_%E6%B0%B4%E4%BB%99%E7%9B%86_NARCISSUS_BASIN,_celadon.jpg（10000×9155，CC BY 4.0）
- 备注：馆方灰底干净正面照；82 张可做"把玩"转看。大阪东洋陶瓷馆另一件 10000×9155 CC BY 4.0，不是同一件，勿混。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/ru_narcissus_basin.jpg`

### 瑞鹤图 · `ruihe_tu` · 够
- 署名：瑞鹤图，辽宁省博物馆；图像 Yoohhee1982，Wikimedia Commons，CC0（来源：Own work）
- 备选：https://commons.wikimedia.org/wiki/File:Songhuizong5.jpg（9079×1846，Public domain）
- 备注：35765×7272 标 CC0，但上传者写"Own work"，来源不明，颜色与是否拼接待核；Songhuizong5 9079×1846 PD 作对照。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/ruihe_tu.jpg`

### 万壑松风图 · `wanhe_songfeng` · 够
- 署名：宋李唐萬壑松風圖　軸。國立故宮博物院，臺北，CC BY 4.0 @ www.npm.gov.tw（多張局部圖拼接）
- 本地：`~/claude-projects/china-art/series/ep02_nansong/assets/wanhe/wanhe_mosaic_preview_ds8.jpg`；全分辨率 `~/claude-projects/china-art/series/ep02_nansong/assets/wanhe/wanhe_mosaic_4876x6332.rgb`
- 备注：拼接自检残余错位中位 0.10 px；另有 3.3–4× 局部瓦片。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/wanhe_songfeng.jpg`

### 踏歌图 · `tage_tu` · 够
- 署名：马远《踏歌图》轴，南宋，故宫博物院藏；图像：故宫名画记（Wikimedia Commons，公有领域）
- 本地：`~/claude-projects/china-art/series/ep02_nansong/assets/tage/tage_preview_ds8_978x1673.jpg`；全分辨率 `~/claude-projects/china-art/series/ep02_nansong/assets/tage/tage_full_7831x13391.rgb`
- 备注：题诗逐字框已测（poem_chars.json）。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/tage_tu.jpg`

### 寒江独钓图 · `hanjiang_dudiao` · 够
- 署名：传马远《寒江独钓图》，南宋，东京国立博物馆藏；图像：emuseum.jp（Wikimedia Commons，公有领域）
- 本地：`~/claude-projects/china-art/series/ep02_nansong/assets/hanjiang/src_hanjiang_commons_5906x3159.jpg`
- 备选：local:ColBase TA-140_E0041906.jpg 3000×1613（许可最清楚，出典 ColBase）
- 备注：e国宝 6122×3388 条款禁止转载，不收。东博说现状可能是裁切过的大画面，展签别说空白全出于本意。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/hanjiang_dudiao.jpg`

### 水图（十二段） · `shuitu` · 够
- 署名：马远《水图》卷，南宋，故宫博物院藏；图像：故宫名画记（Wikimedia Commons，公有领域）
- 本地：`~/claude-projects/china-art/series/ep02_nansong/assets/shuitu/preview_ds16_7988x212.jpg`；全分辨率 `~/claude-projects/china-art/series/ep02_nansong/assets/shuitu/shuitu_full_127821x3400.rgb`
- 备注：十二段已切在 shuitu/sections/。天然是"册页一开一开翻"。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/shuitu.jpg`

### 泼墨仙人 · `pomo_xianren` · 勉强
- 署名：名畫琳瑯　冊　宋梁楷潑墨仙人。國立故宮博物院，臺北，CC BY 4.0 @ www.npm.gov.tw
- 本地：`~/claude-projects/china-art/series/ep02_nansong/assets/pomo/npm_pomo_PAB.jpg`
- 备注：画页本身只有 1158×2037：竖挂整页够高（2037），推近余量很小。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/pomo_xianren.jpg`

### 南宋官窑青瓷瓶 · `guanyao_vase` · 够
- 署名：Vase (Guan ware), Southern Song dynasty, The Metropolitan Museum of Art, Rogers Fund 1918 (18.56.57), CC0
- 本地：`~/claude-projects/china-art/series/ep02_nansong/assets/guanyao/met_DP335586.jpg`
- 备注：馆方干净背景，另有 4 个角度。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/guanyao_vase.jpg`

### 建窑曜变天目茶碗 · `jian_yohen_tenmoku` · 不够
- 署名：建窑曜变天目茶碗，静嘉堂文库美术馆（另藤田美术馆、大德寺龙光院）；图像 Unknown author（高橋義雄？），Wikimedia Commons，Public domain（来源：高橋義雄編『大正名器鑑 第6編』宝雲舎、1937年6月15日。National Diet Library Digital Collections: Persistent ID 1686307）
- 备选：https://commons.wikimedia.org/wiki/File:Y%C5%8Dhen_Tenmoku_(Seikad%C5%8D_Bunko_Art_Museum)_02.jpg（1652×1366，Public domain）；https://commons.wikimedia.org/wiki/File:Temmoku_tea_bowl_Fujita_Bijutsukan.jpg（1413×2464，Public domain）；met:48117 建窑兔毫盏 CC0（非曜变）
- 备注：缩略图目验：静嘉堂那张是 1937 年图录的黑白照，看不出曜变的蓝色光斑。三家藏馆（静嘉堂、藤田、龙光院）无开放图。若要讲宋代茶盏，Met 有多件建窑兔毫盏 CC0 馆方图可替代。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/jian_yohen_tenmoku.jpg`

### 富春山居图（无用师卷） · `fuchun_wuyong` · 勉强
- 署名：富春山居图（无用师卷），台北故宫博物院；图像 Huang Gongwang，Wikimedia Commons，Public domain（来源：http://www.npm.gov.tw/exh100/fuchun/ch_02_1.html#t00）
- 备选：npm:台北故宫 IIIF cid=1194 共 81 张（全卷 13428×448 + 分段约 3058×2289，CC BY 4.0，可拼）；https://commons.wikimedia.org/wiki/File:%E5%AF%8C%E6%98%A5%E5%B1%B1%E5%B1%85%E5%9C%96(%E5%89%A9%E5%B1%B1%E5%9C%96).jpg（7260×900，Public domain）
- 备注：Commons 只有 900 高（不够）；拼台北故宫分段图后画心预计约 1500 高，才到"够"，需像万壑松风那样拼接实测。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/fuchun_wuyong.jpg`

### 容膝斋图 · `rongxi_zhai` · 够
- 署名：倪瓒《容膝斋图》，1372 年作、1374 年补题，台北故宫博物院藏；图像 Wikimedia Commons
- 本地：`~/claude-projects/china-art/trailer/src/s6_yuan_ni_zan/rongxi_commons.jpg`
- 备选：npm:台北故宫 IIIF cid=610 全图 1836×3812，CC BY 4.0
- 备注：竖挂整幅够（3674 高）；按宽铺满只有 0.96×。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/rongxi_zhai.jpg`

### 鹊华秋色图 · `queshua_qiuse` · 勉强
- 署名：鹊华秋色图，台北故宫博物院；图像 Zhao Mengfu，Wikimedia Commons，Public domain（来源：National Palace Museum Taipei）
- 备选：npm:台北故宫 IIIF cid=909 共 15 张（可拼），CC BY 4.0；https://commons.wikimedia.org/wiki/File:%E5%85%83%E8%B6%99%E5%AD%9F%E9%A0%AB%E9%B5%B2%E8%8F%AF%E7%A7%8B%E8%89%B2_%E5%8D%B7.jpg（1416×1060，CC0）
- 备注：Commons 最大 15868×900 含题跋，画心高 900 不够；需拼台北故宫 15 张。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/queshua_qiuse.jpg`

### 大维德瓶（青花云龙纹象耳瓶） · `david_vases` · 勉强
- 署名：青花云龙纹象耳瓶（大维德瓶），元至正十一年（1351），大维德基金会藏、大英博物馆展出（PDF B.614）；摄影 Marie-Lan Nguyen，Wikimedia Commons，CC BY 2.5
- 本地：`~/claude-projects/china-art/trailer/src/s7_yuan_blue_white/david_vase_n01.jpg`
- 备选：https://commons.wikimedia.org/wiki/File:The_David_Vases.jpg（2080×2342，Public domain）；met:39638 元青花鱼藻纹盘 4000×3002 CC0（馆方白底）
- 备注：展柜实拍，局部图；大英官方图 CC BY-NC-SA 且约 1000 px。若要干净背景的元青花，Met 鱼纹盘最好。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/david_vases.jpg`

### 鬼谷下山图罐 · `guiguzi_jar` · 不够
- 署名：—
- 备注：无开放图源，只有拍卖行与媒体图；私人藏品，不建议上墙。
- 缩略图：`无`

### 墨葡萄图 · `moputao` · 够
- 署名：徐渭《墨葡萄图》轴，明，故宫博物院藏；图像 故宫名画记 / Wikimedia Commons
- 本地：`~/claude-projects/china-art/trailer/assets_v3/moputao/preview_s4.jpg`；全分辨率 `~/claude-projects/china-art/trailer/assets_v3/moputao/work_full.npy`
- 备注：work_full.npy 已在 assets_v3/moputao。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/moputao.jpg`

### 庐山高图 · `lushan_gao` · 够
- 署名：沈周《庐山高图》轴，明成化三年（1467），台北故宫博物院藏；图像 Wikimedia Commons（书格），Public domain（来源：https://www.shuge.org/meet/topic/33163/）
- 备选：https://commons.wikimedia.org/wiki/File:Lofty_Mt.Lu_by_Shen_Zhou.jpg（1799×3549，Public domain）；npm:台北故宫 Open Data（未查）
- 备注：3204×6140（书格），竖挂够。Commons 文件名写"明成化二年"，但画上沈周自题作于成化三年丁亥（1467），展签以馆方为准。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/lushan_gao.jpg`

### 汉宫春晓图 · `hangong_chunxiao` · 够
- 署名：汉宫春晓图，台北故宫博物院；图像 Qiu Ying，Wikimedia Commons，Public domain（来源：scanned by Krause, Johansen）
- 备选：npm:台北故宫 Open Data（未查）
- 备注：52680×2683，来源不明，颜色待与馆方对。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/hangong_chunxiao.jpg`

### 青卞图 · `qingbian_tu` · 够
- 署名：Mt. Qingbian, The Cleveland Museum of Art, Leonard C. Hanna Jr. Fund (1980.10), CC0
- 原图：https://openaccess-cdn.clevelandart.org/1980.10/1980.10_full.tif
- 备注：馆方 CC0，竖幅 2376×6944。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/qingbian_tu.jpg`

### 黄花梨靠背椅（明式家具） · `huanghuali_armchair` · 够
- 署名：Yokeback armchair, The Metropolitan Museum of Art, Purchase, The Dillon Fund Gift, 1997 (1997.92), CC0
- 原图：https://images.metmuseum.org/CRDImages/as/original/1997_92_O2_sf.jpg
- 备注：馆方白底 CC0，只有一个角度。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/huanghuali_armchair.jpg`

### 宣德青花龙纹罐 · `xuande_dragon_jar` · 够
- 署名：Jar with dragon, The Metropolitan Museum of Art, Gift of Robert E. Tod, 1937 (37.191.1), CC0
- 原图：https://images.metmuseum.org/CRDImages/as/original/DP-32251-001.jpg
- 备注：馆方 CC0，共 6 个角度，可做"转着看"。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/xuande_dragon_jar.jpg`

### 成化斗彩鸡缸杯 · `chenghua_chicken_cup` · 够
- 署名：成化斗彩鸡缸杯，大都会艺术博物馆 1987.85（另台北故宫、北京故宫藏）；图像 佚名，Wikimedia Commons，CC0（来源：This file was donated to Wikimedia Commons as part of a project by the Metropolitan Museum of Art. See the Image and Data Resources Open Access Policy）
- 备选：https://commons.wikimedia.org/wiki/File:Porcelain_chicken_cup_in_doucai_painted_enamels.tif（3000×2250，CC BY 4.0）；https://commons.wikimedia.org/wiki/File:%E9%AC%A5%E5%BD%A9%E9%9B%9E%E7%BC%B8%E6%9D%AF.png（2829×2122，CC BY 4.0）
- 备注：本轮新发现：Met 42515（Chenghua mark and period）馆方图 5 个角度 4000×3100 左右，CC0，比台北故宫 3000×2250 更大。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/chenghua_chicken_cup.jpg`

### 荷石水鸟图 · `bada_heshi_shuiniao` · 够
- 署名：八大山人（朱耷）《荷石水鸟图》轴，清，故宫博物院藏（新00146234）；图像 故宫名画记
- 本地：`~/claude-projects/china-art/trailer/assets_v3/bada/preview_s4.jpg`；全分辨率 `~/claude-projects/china-art/trailer/assets_v3/bada/work_full.npy`
- 备注：work_full.npy 已在 assets_v3/bada。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/bada_heshi_shuiniao.jpg`

### 鱼石图 · `bada_fish_rocks` · 够
- 署名：Fish and Rocks, The Cleveland Museum of Art, John L. Severance Fund (1953.247), CC0
- 原图：https://openaccess-cdn.clevelandart.org/1953.247/1953.247_full.tif
- 备注：馆方 CC0，36789×4833 手卷，画心高 >4000。"孤禽图"本轮没找到开放高清。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/bada_fish_rocks.jpg`

### 搜尽奇峰打草稿图 · `shitao_soujin` · 够
- 署名：搜尽奇峰打草稿图，北京故宫博物院；图像 Shitao，Wikimedia Commons，Public domain（来源：https://minghuaji.dpm.org.cn/paint/detail?id=e07e185f66fc44238cd6d25d18d8c4d0）
- 备注：74164×5247，约 498 MB；"搜尽奇峰打草稿"与"一画"可直接上墙。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/shitao_soujin.jpg`

### 百骏图 · `baijun_tu` · 够
- 署名：郎世宁《百骏图》，台北故宫博物院藏；图像 台北故宫郎世宁主题网 / Wikimedia Commons
- 本地：`~/claude-projects/china-art/trailer/src_v3/baijun/baijun_commons.jpg`
- 备选：npm:台北故宫 Open Data 分段图（未查）
- 备注：画心高约 2000，只能轻推。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/baijun_tu.jpg`

### 各种釉彩大瓶 · `qianlong_glaze_vase` · 勉强
- 署名：各种釉彩大瓶，北京故宫博物院；图像 Chez Cåsver (Xuan Che)，Wikimedia Commons，CC BY 2.0（来源：https://www.flickr.com/photos/rosemania/3431319504/）
- 备注：游客隔玻璃实拍 2338×3524 CC BY 2.0；馆方大图未找到。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/qianlong_glaze_vase.jpg`

### 珐琅彩锦鸡牡丹纹瓶 · `falangcai_pheasant_vase` · 够
- 署名：Vase with Golden Pheasants, The Cleveland Museum of Art, John L. Severance Fund (1971.145), CC0
- 原图：https://openaccess-cdn.clevelandart.org/1971.145/1971.145_full.tif
- 备注：馆方 CC0，只有一个角度；馆方说明提到郎世宁式明暗，可与百骏图连。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/falangcai_pheasant_vase.jpg`

### 蛙声十里出山泉 · `qibaishi_washeng` · 勉强
- 署名：齐白石《蛙声十里出山泉》，1951，中国现代文学馆藏；图像 中国青年报
- 本地：`~/claude-projects/china-art/trailer/src_v3/washeng/washeng_cyol_873x3461.jpg`
- 备选：local:washeng_toutiao_900x3471.jpg
- 备注：只能整幅竖看（高 3461 够，宽 873），不能推近；无馆方高清。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/qibaishi_washeng.jpg`

### 画藤（齐白石） · `qibaishi_teng` · 够
- 署名：画藤（齐白石），北京故宫博物院；图像 Qi Baishi，Wikimedia Commons，Public domain（来源：https://minghuaji.dpm.org.cn/paint/detail?id=ffb04e8463ff4d9a8a5e47ba586cf7d3）
- 备注：7042×13914（名画记）。齐白石的"虾"本轮没找到开放高清，若要虾需另找（北京画院等）。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/qibaishi_teng.jpg`

### 齐白石 虾 · `qibaishi_shrimp` · 不够
- 署名：—
- 备注：Commons 与各馆开放库都没找到；可用"画藤""蛙声"代替。
- 缩略图：`无`

### 紫藤图（补充） · `wuchangshuo_zitang` · 够
- 署名：紫藤图（补充），北京故宫博物院；图像 Wu Chang-shuo，Wikimedia Commons，Public domain（来源：https://minghuaji.dpm.org.cn/paint/detail?id=9e6533e497fd4c218b430b46d6a7b0dd）
- 备注：3300×10653，金石气的代表，可与徐渭藤、齐白石藤串线。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/wuchangshuo_zitang.jpg`

### 奔马图 · `xubeihong_horse` · 不够
- 署名：奔马图，徐悲鸿纪念馆等；图像 Xu Beihong，Wikimedia Commons，Public domain（来源：LiveAuctioneers.com）
- 备注：只找到《立马》535×1100 小图；《奔马图》无开放高清。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/xubeihong_horse.jpg`

### 黄宾虹山水 · `huangbinhong` · 不够
- 署名：—
- 备注：本轮 Commons 搜索没命中可用图；黄宾虹 1955 年卒，中国大陆已公有。建议查故宫名画记/浙博。
- 缩略图：`无`

### 春如线 · `wuguanzhong_chunruxian` · 勉强
- 署名：吴冠中《春如线》，© 吴冠中；图像：帝圖藝術拍賣 2025 迎春 lot 3040-1
- 本地：`~/claude-projects/china-art/trailer/src_v3/wuguanzhong/wu_chunruxian_artemperor_3040-1_2524x2560.jpg`
- 备选：local:wu_artemperor_3040_2560x2253.jpg
- 备注：版权期作品、拍卖图，非馆藏；方幅，整幅看够。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/wuguanzhong_chunruxian.jpg`

### 天书 · `xubing_tianshu` · 不够
- 署名：徐冰《天书》，1987–91，普林斯顿大学美术馆藏 2002-281，© 徐冰；图像：Princeton University Art Museum
- 本地：`~/claude-projects/china-art/trailer/src/s9_contemporary/princeton_2002-281-1.jpg`
- 备选：local:trailer/src/s9_contemporary/xubing_*.jpg（工作室官网 ≤1354 px 展厅/书影 19 张）
- 备注：单页只有 843 高；更高清需向徐冰工作室或普林斯顿索取。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/xubing_tianshu.jpg`

### 蔡国强（火药/装置） · `caiguoqiang` · 勉强
- 署名：蔡国强（火药/装置），—；图像 Phillip Capper from Wellington, New Zealand，Wikimedia Commons，CC BY 2.0（来源：Cai Guo Qiang installation, Guggenheim, New York, 11 Feb. 2008）
- 备选：https://commons.wikimedia.org/wiki/File:Cai_Guo-Qiang_-_Cultural_Melting_Bath-_Project_for_Naoshima_(26718006181).jpg（5760×3840，CC BY-SA 2.0）；https://commons.wikimedia.org/wiki/File:Explosion_Event_by_Cai_Guo-Qiang007.JPG（2272×1704，CC BY-SA 3.0）
- 备注：只有观众拍的装置/活动照；火药草图无开放图，需工作室授权。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/caiguoqiang.jpg`

### 葵花籽 · `aiweiwei_sunflower_seeds` · 够
- 署名：葵花籽，泰特现代美术馆（涡轮大厅展出）；图像 Londonnodnol，Wikimedia Commons，CC0（来源：Own work）
- 备选：https://commons.wikimedia.org/wiki/File:Ai_Weiwei%27s_Sunflower_Seeds,_Tate_Modern_1.jpg（3888×2592，CC BY-SA 4.0）；https://commons.wikimedia.org/wiki/File:%27Sunflower_Seeds%27_by_Ai_Weiwei,_Tate_Modern_Turbine_Hall.jpg（3264×2448，CC BY-SA 2.0）
- 备注：观众实拍，细节图 CC0 3888×2592；作品本身 © 艾未未。
- 缩略图：`~/claude-projects/china-art/research/v2/thumbs/aiweiwei_sunflower_seeds.jpg`
