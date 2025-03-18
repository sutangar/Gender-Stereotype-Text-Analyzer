#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import sys
import glob
import argparse
import logging
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
            
            # 统计性别关键词的形容词
            male_adjectives = []
            female_adjectives = []
            
            for word, _ in words:
                if word in self.male_keywords:
                    adjectives = self.extract_adjectives(words, word)
                    male_adjectives.extend(adjectives)
                elif word in self.female_keywords:
                    adjectives = self.extract_adjectives(words, word)
                    female_adjectives.extend(adjectives)
            
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
            
            # 生成词云
            male_wordcloud = WordCloud(
                font_path=self.font_path,
                width=800,
                height=400,
                background_color='white'
            ).generate_from_frequencies(male_counter)
            
            female_wordcloud = WordCloud(
                font_path=self.font_path,
                width=800,
                height=400,
                background_color='white'
            ).generate_from_frequencies(female_counter)
            
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
            
            # 生成对比柱状图
            plt.figure(figsize=(12, 6))
            male_words = list(male_counter.keys())
            male_counts = list(male_counter.values())
            female_words = list(female_counter.keys())
            female_counts = list(female_counter.values())
            
            x = np.arange(len(male_words))
            width = 0.35
            
            plt.bar(x - width/2, male_counts, width, label='男性')
            plt.bar(x + width/2, female_counts, width, label='女性')
            
            plt.xlabel('形容词')
            plt.ylabel('频次')
            plt.title('性别形容词使用对比')
            plt.xticks(x, male_words, rotation=45)
            plt.legend()
            
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'comparison.png'))
            plt.close()
            
            # 生成CSV报告
            df = pd.DataFrame({
                '形容词': list(set(male_words + female_words)),
                '男性频次': [male_counter.get(word, 0) for word in set(male_words + female_words)],
                '女性频次': [female_counter.get(word, 0) for word in set(male_words + female_words)]
            })
            df.to_csv(os.path.join(output_dir, 'report.csv'), index=False, encoding='utf-8-sig')
            
        except Exception as e:
            logger.error(f"生成可视化结果失败: {e}")

def analyze_file(input_file, output_dir, config_file=None):
    """分析单个文件"""
    try:
        # 创建分析器
        analyzer = GenderStereotypeAnalyzer(config_file)
        
        # 读取文本
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # 分析文本
        male_counter, female_counter = analyzer.analyze(text)
        
        # 可视化结果
        analyzer.visualize(male_counter, female_counter, output_dir)
        
        logger.info(f"分析完成，结果保存在: {output_dir}")
        
    except Exception as e:
        logger.error(f"分析文件失败: {e}")
        sys.exit(1)

def analyze_directory(input_dir, output_dir, config_file=None):
    """分析整个目录"""
    try:
        # 获取所有文本文件
        text_files = glob.glob(os.path.join(input_dir, '*.txt'))
        
        if not text_files:
            logger.warning(f"在目录 {input_dir} 中没有找到文本文件")
            return
        
        # 为每个文件创建单独的输出目录
        for text_file in text_files:
            filename = os.path.basename(text_file)
            file_output_dir = os.path.join(output_dir, os.path.splitext(filename)[0])
            analyze_file(text_file, file_output_dir, config_file)
            
    except Exception as e:
        logger.error(f"分析目录失败: {e}")
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