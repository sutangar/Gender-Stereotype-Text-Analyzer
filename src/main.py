#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import sys
import glob
import argparse
import logging
import time
from pathlib import Path
from collections import Counter
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import pandas as pd
import numpy as np
import jieba
import jieba.posseg as pseg

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProgressBar:
    """进度条类"""
    def __init__(self, total, prefix='', suffix='', length=50, fill='█', empty='░', color=True):
        self.total = total
        self.prefix = prefix
        self.suffix = suffix
        self.length = length
        self.fill = fill
        self.empty = empty
        self.color = color
        self.start_time = time.time()
        self.count = 0
        
    def update(self, count=None):
        """更新进度条"""
        if count is not None:
            self.count = count
        else:
            self.count += 1
            
        percent = self.count / self.total
        filled_length = int(self.length * percent)
        bar = self.fill * filled_length + self.empty * (self.length - filled_length)
        
        # 计算剩余时间
        elapsed_time = time.time() - self.start_time
        if percent > 0:
            eta = elapsed_time / percent * (1 - percent)
            time_info = f" | {self._format_time(elapsed_time)}<{self._format_time(eta)}"
        else:
            time_info = ""
            
        # 带颜色的进度条
        if self.color:
            color_code = '\033[92m'  # 绿色
            if percent < 0.3:
                color_code = '\033[94m'  # 蓝色
            elif percent < 0.7:
                color_code = '\033[93m'  # 黄色
            reset_code = '\033[0m'
            bar = f"{color_code}{bar}{reset_code}"
            
        # 打印进度条
        sys.stdout.write(f"\r{self.prefix} |{bar}| {int(percent * 100)}%{time_info} {self.suffix}")
        sys.stdout.flush()
        
        # 完成时换行
        if self.count >= self.total:
            sys.stdout.write('\n')
            sys.stdout.flush()
            
    def _format_time(self, seconds):
        """格式化时间显示"""
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h:d}h{m:02d}m"
        elif m > 0:
            return f"{m:d}m{s:02d}s"
        else:
            return f"{s:d}s"

class GenderStereotypeAnalyzer:
    def __init__(self, config_file=None):
        """初始化分析器"""
        self.male_keywords = set()
        self.female_keywords = set()
        self.stopwords = set()
        self.adjective_pos_tags = set()
        self.window_size = 3
        self.font_path = None
        
        if config_file:
            self.load_config(config_file)
        else:
            self.load_default_config()
    
    def load_config(self, config_file):
        """加载配置文件"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.male_keywords = set(config.get('male_keywords', []))
                self.female_keywords = set(config.get('female_keywords', []))
                self.stopwords = set(config.get('stopwords', []))
                self.adjective_pos_tags = set(config.get('adjective_pos_tags', []))
                self.window_size = config.get('window_size', 3)
                self.font_path = config.get('font_path', 'simhei.ttf')
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self.load_default_config()
    
    def load_default_config(self):
        """加载默认配置"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'config.json')
            self.load_config(config_path)
        except Exception as e:
            logger.error(f"加载默认配置失败: {e}")
            # 使用硬编码的默认值
            self.male_keywords = {'他', '父亲', '儿子', '兄弟', '男人', '先生', '男孩'}
            self.female_keywords = {'她', '母亲', '女儿', '姐妹', '女人', '女士', '女孩'}
            self.stopwords = {'的', '了', '和', '是', '就', '都', '而', '及', '与', '着',
                            '或', '一个', '没有', '这个', '那个', '这样', '那样'}
            self.adjective_pos_tags = {'a', 'ad', 'an'}
            self.window_size = 3
            self.font_path = 'simhei.ttf'
    
    def save_config(self, config_file):
        """保存配置到文件"""
        try:
            config = {
                'male_keywords': list(self.male_keywords),
                'female_keywords': list(self.female_keywords),
                'stopwords': list(self.stopwords),
                'adjective_pos_tags': list(self.adjective_pos_tags),
                'window_size': self.window_size,
                'font_path': self.font_path
            }
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")

    def first_time_setup(self):
        """首次使用引导"""
        print("\n=== 欢迎使用性别刻板印象分析工具 ===")
        print("这是您首次使用本工具，请按照提示进行配置：")
        
        # 获取用户自定义的男性关键词
        print("\n请输入额外的男性相关词汇（用空格分隔，直接回车使用默认值）：")
        print(f"当前默认值：{' '.join(self.male_keywords)}")
        custom_male = input().strip()
        if custom_male:
            self.male_keywords.update(custom_male.split())
        
        # 获取用户自定义的女性关键词
        print("\n请输入额外的女性相关词汇（用空格分隔，直接回车使用默认值）：")
        print(f"当前默认值：{' '.join(self.female_keywords)}")
        custom_female = input().strip()
        if custom_female:
            self.female_keywords.update(custom_female.split())
        
        # 获取用户自定义的停用词
        print("\n请输入额外的停用词（用空格分隔，直接回车使用默认值）：")
        print(f"当前默认值：{' '.join(self.stopwords)}")
        custom_stopwords = input().strip()
        if custom_stopwords:
            self.stopwords.update(custom_stopwords.split())
        
        # 保存配置
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        self.save_config(config_path)
        print(f"\n配置已保存到：{config_path}")
        print("下次使用时将自动加载此配置。")
    
    def preprocess_text(self, text):
        """预处理文本"""
        try:
            # 分词和词性标注
            words = pseg.cut(text)
            return [(word, flag) for word, flag in words]
        except Exception as e:
            logger.error(f"文本预处理失败: {e}")
            return []
    
    def extract_adjectives(self, words, target_word):
        """提取形容词"""
        try:
            adjectives = []
            for i, (word, pos) in enumerate(words):
                if word == target_word:
                    # 向前查找
                    for j in range(max(0, i - self.window_size), i):
                        if words[j][1] in self.adjective_pos_tags:
                            adjectives.append(words[j][0])
                    # 向后查找
                    for j in range(i + 1, min(len(words), i + self.window_size + 1)):
                        if words[j][1] in self.adjective_pos_tags:
                            adjectives.append(words[j][0])
            return adjectives
        except Exception as e:
            logger.error(f"提取形容词失败: {e}")
            return []
    
    def find_cooccurrences(self, words):
        """查找性别关键词的共现"""
        try:
            cooccurrences = []
            for i, (word, _) in enumerate(words):
                if word in self.male_keywords or word in self.female_keywords:
                    # 获取上下文窗口
                    start = max(0, i - self.window_size)
                    end = min(len(words), i + self.window_size + 1)
                    context = [w for w, _ in words[start:end]]
                    cooccurrences.append((word, context))
            return cooccurrences
        except Exception as e:
            logger.error(f"查找共现失败: {e}")
            return []
    
    def analyze(self, text):
        """分析文本中的性别刻板印象"""
        try:
            # 预处理文本
            words = self.preprocess_text(text)
            
            # 创建进度条
            progress = ProgressBar(len(words), prefix='分析文本', suffix='', length=40)
            
            # 统计性别关键词的形容词
            male_adjectives = []
            female_adjectives = []
            
            for i, (word, _) in enumerate(words):
                if word in self.male_keywords:
                    adjectives = self.extract_adjectives(words, word)
                    male_adjectives.extend(adjectives)
                elif word in self.female_keywords:
                    adjectives = self.extract_adjectives(words, word)
                    female_adjectives.extend(adjectives)
                
                # 更新进度条（每10个词更新一次，以避免过多IO操作）
                if i % 10 == 0 or i == len(words) - 1:
                    progress.update(i + 1)
            
            # 统计词频
            male_counter = Counter(male_adjectives)
            female_counter = Counter(female_adjectives)
            
            return male_counter, female_counter
        except Exception as e:
            logger.error(f"分析文本失败: {e}")
            return Counter(), Counter()
    
    def visualize(self, male_counter, female_counter, output_dir):
        """可视化分析结果"""
        try:
            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)
            
            # 显示可视化进度
            print("\n开始生成可视化结果...")
            progress = ProgressBar(4, prefix='生成可视化', suffix='', length=40)
            
            # 生成词云
            male_wordcloud = WordCloud(
                font_path=self.font_path,
                width=800,
                height=400,
                background_color='white'
            ).generate_from_frequencies(male_counter)
            progress.update()
            
            female_wordcloud = WordCloud(
                font_path=self.font_path,
                width=800,
                height=400,
                background_color='white'
            ).generate_from_frequencies(female_counter)
            progress.update()
            
            # 保存词云图
            plt.figure(figsize=(10, 5))
            plt.subplot(1, 2, 1)
            plt.imshow(male_wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.title('男性形容词词云')
            
            plt.subplot(1, 2, 2)
            plt.imshow(female_wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.title('女性形容词词云')
            
            plt.savefig(os.path.join(output_dir, 'wordcloud.png'))
            plt.close()
            progress.update()
            
            # 生成对比柱状图和CSV报告
            plt.figure(figsize=(12, 6))
            male_words = list(male_counter.keys())
            male_counts = list(male_counter.values())
            female_words = list(female_counter.keys())
            female_counts = list(female_counter.values())
            
            # 获取所有出现的形容词
            all_words = list(set(male_words + female_words))
            
            if all_words:  # 确保有形容词
                x = np.arange(len(all_words))
                width = 0.35
                
                plt.bar(x - width/2, [male_counter.get(word, 0) for word in all_words], width, label='男性')
                plt.bar(x + width/2, [female_counter.get(word, 0) for word in all_words], width, label='女性')
                
                plt.xlabel('形容词')
                plt.ylabel('频次')
                plt.title('性别形容词使用对比')
                plt.xticks(x, all_words, rotation=45)
                plt.legend()
                
                plt.tight_layout()
                plt.savefig(os.path.join(output_dir, 'comparison.png'))
                plt.close()
            
            # 生成CSV报告
            df = pd.DataFrame({
                '形容词': all_words,
                '男性频次': [male_counter.get(word, 0) for word in all_words],
                '女性频次': [female_counter.get(word, 0) for word in all_words]
            })
            df.to_csv(os.path.join(output_dir, 'report.csv'), index=False, encoding='utf-8-sig')
            progress.update()
            
            print(f"\n✅ 分析完成！结果已保存到: {output_dir}")
            
        except Exception as e:
            logger.error(f"生成可视化结果失败: {e}")
            print(f"\n❌ 生成可视化结果失败: {e}")

def analyze_file(input_file, output_dir, config_file=None):
    """分析单个文件"""
    try:
        # 创建分析器
        analyzer = GenderStereotypeAnalyzer(config_file)
        
        # 显示文件信息
        file_size = os.path.getsize(input_file) / 1024  # KB
        print(f"\n📄 正在分析文件: {os.path.basename(input_file)} ({file_size:.2f} KB)")
        
        # 读取文本
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # 显示文本信息
        print(f"📊 文本长度: {len(text)} 字符")
        
        # 分析文本
        male_counter, female_counter = analyzer.analyze(text)
        
        # 显示统计信息
        print(f"\n📈 分析结果统计:")
        print(f"  - 识别出男性相关词汇: {sum(male_counter.values())} 个")
        print(f"  - 识别出女性相关词汇: {sum(female_counter.values())} 个")
        
        # 可视化结果
        analyzer.visualize(male_counter, female_counter, output_dir)
        
    except Exception as e:
        logger.error(f"分析文件失败: {e}")
        print(f"\n❌ 分析文件失败: {e}")
        sys.exit(1)

def analyze_directory(input_dir, output_dir, config_file=None):
    """分析整个目录"""
    try:
        # 获取所有文本文件
        text_files = glob.glob(os.path.join(input_dir, '*.txt'))
        
        if not text_files:
            logger.warning(f"在目录 {input_dir} 中没有找到文本文件")
            print(f"\n❗ 警告: 在目录 {input_dir} 中没有找到文本文件")
            return
        
        # 显示目录信息
        print(f"\n📁 正在分析目录: {input_dir}")
        print(f"📚 发现 {len(text_files)} 个文本文件")
        
        # 创建进度条
        progress = ProgressBar(len(text_files), prefix='分析文件', suffix='', length=40)
        
        # 为每个文件创建单独的输出目录
        for i, text_file in enumerate(text_files):
            filename = os.path.basename(text_file)
            file_output_dir = os.path.join(output_dir, os.path.splitext(filename)[0])
            
            # 更新进度条的后缀显示当前处理的文件
            progress.suffix = f"- {filename}"
            progress.update(i + 1)
            
            # 分析文件
            analyze_file(text_file, file_output_dir, config_file)
            
        print(f"\n✅ 目录分析完成！结果已保存到: {output_dir}")
            
    except Exception as e:
        logger.error(f"分析目录失败: {e}")
        print(f"\n❌ 分析目录失败: {e}")
        sys.exit(1)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='性别刻板印象分析工具')
    parser.add_argument('input', help='输入文件或目录的路径')
    parser.add_argument('-o', '--output', help='输出目录的路径', default='output')
    parser.add_argument('-c', '--config', help='配置文件的路径')
    parser.add_argument('--setup', action='store_true', help='重新运行首次使用引导')
    
    args = parser.parse_args()
    
    # 检查输入路径是否存在
    if not os.path.exists(args.input):
        logger.error(f"输入路径不存在: {args.input}")
        sys.exit(1)
    
    # 创建分析器
    analyzer = GenderStereotypeAnalyzer(args.config)
    
    # 检查是否需要运行首次使用引导
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if args.setup or not os.path.exists(config_path):
        analyzer.first_time_setup()
    
    # 根据输入类型选择分析函数
    if os.path.isfile(args.input):
        analyze_file(args.input, args.output, args.config)
    else:
        analyze_directory(args.input, args.output, args.config)

if __name__ == '__main__':
    main() 