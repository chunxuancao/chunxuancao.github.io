// 自动生成文章索引 articles.json，供AI爬虫助手读取
const fs = require('fs');
const path = require('path');
const frontMatter = require('hexo-front-matter');

const postsDir = path.join(__dirname, '../source/_posts');
const outputDir = path.join(__dirname, '../public');
const outputFile = path.join(outputDir, 'articles.json');

// 确保输出目录存在
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

// raw目录，存放原始Markdown
const rawDir = path.join(outputDir, 'raw');
if (!fs.existsSync(rawDir)) {
  fs.mkdirSync(rawDir, { recursive: true });
}

const articles = [];

// 扫描所有md文件
const files = fs.readdirSync(postsDir).filter(f => f.endsWith('.md'));

files.forEach(file => {
  const filePath = path.join(postsDir, file);
  const content = fs.readFileSync(filePath, 'utf-8');
  const parsed = frontMatter.parse(content);
  
  // 生成文章URL（和hexo的permalink规则一致）
  const date = new Date(parsed.date);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const slug = file.replace('.md', '');
  const url = `/${year}/${month}/${day}/${slug}/`;
  const rawUrl = `/raw/${slug}.md`;
  
  articles.push({
    title: parsed.title,
    url: url,
    raw_url: rawUrl,
    category: parsed.category || '未分类',
    tags: parsed.tags || [],
    difficulty: parsed.difficulty || '未知',
    summary: parsed.summary || '',
    cover: parsed.cover || '',
    updated: parsed.date ? date.toISOString().split('T')[0] : ''
  });
  
  // 复制原始Markdown到raw目录
  fs.copyFileSync(filePath, path.join(rawDir, file));
});

// 按日期排序，最新的在前
articles.sort((a, b) => new Date(b.updated) - new Date(a.updated));

fs.writeFileSync(outputFile, JSON.stringify(articles, null, 2), 'utf-8');
console.log(`已生成 ${articles.length} 篇文章的索引: ${outputFile}`);
