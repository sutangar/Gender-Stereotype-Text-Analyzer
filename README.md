# 性别刻板印象文本分析工具（Gender Stereotype Text Analyzer）

## 项目简介
本项目是一个用于分析文本中性别刻板印象的工具。通过分析文本中的性别相关词汇及其上下文，统计男性和女性角色被描述的形容词差异，揭示潜在的性别刻板印象。

## 功能特点
- 支持中文文本分析
- 自动识别性别相关词汇
- 动态扩展性别关联词汇（通过共现关系分析）
- 提取性别关键词附近的形容词
- 支持批量处理多个文件或整个目录
- 生成多种可视化结果（词云和对比柱状图）
- 输出详细的统计分析报告
- 可自定义配置（性别关键词、停用词、形容词标签等）

## 安装说明
1. 克隆项目到本地
2. 安装依赖包：
```bash
pip install -r requirements.txt
```
3. 准备中文字体文件 simhei.ttf（或在配置文件中指定其他字体）

## 使用方法

### 命令行参数
```
usage: main.py [-h] [-o OUTPUT] [-c CONFIG] input

性别刻板印象分析工具

positional arguments:
  input                 输入文件或目录的路径

options:
  -h, --help            显示帮助信息
  -o OUTPUT, --output OUTPUT
                        输出目录的路径
  -c CONFIG, --config CONFIG
                        配置文件的路径
```

### 示例用法
1. 分析单个文件：
```bash
python src/main.py data/example.txt -o output
```

2. 分析整个目录中的所有文本文件：
```bash
python src/main.py data/ -o output
```

3. 使用自定义配置：
```bash
python src/main.py data/example.txt -c src/config_example.json -o output
```

### 输出结果
- `wordcloud.png`：包含词云的可视化结果
- `comparison.png`：对比柱状图
- `report.csv`：详细统计分析报告，包含形容词使用频次和男女使用比例

## 自定义配置
可以通过创建JSON配置文件来自定义分析参数，配置文件格式如下：
```json
{
    "male_keywords": ["他", "男主", "父亲", ...],
    "female_keywords": ["她", "女主", "母亲", ...],
    "stopwords": ["的", "了", "和", ...],
    "adjective_pos_tags": ["a", "an", "ag", "al"],
    "window_size": 3,
    "font_path": "simhei.ttf"
}
```

## 项目结构
```
GSTA/
├── data/               # 数据目录
│   └── example.txt     # 示例文本
├── src/                # 源代码目录
│   ├── main.py         # 主程序
│   ├── run_example.py  # 示例运行脚本
│   └── config_example.json  # 配置文件示例
├── output/             # 输出目录（运行时自动创建）
├── requirements.txt    # 项目依赖
└── README.md           # 项目说明文档
```

## 改进特性
- 命令行接口：支持命令行参数，方便批处理
- 多文件支持：可以一次性处理整个目录中的多个文件
- 动态词汇扩展：通过分析名词和性别词的共现关系，自动扩展性别关联词
- 增强形容词判断：添加更多的形容词词性标记
- 错误处理机制：增加异常处理和日志记录
- 更丰富的可视化：添加对比柱状图
- 自定义配置：支持JSON配置文件
- 文件名前缀：输出文件带有输入文件名前缀，便于区分

## 注意事项
- 确保系统安装了中文字体（默认使用 simhei.ttf）
- 输入文本需要是 UTF-8 编码
- 建议使用 Python 3.7 或更高版本

## 许可证
MIT License 