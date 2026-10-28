# Minimal Jekyll-compatible builder for previewing the site where Jekyll itself
# is unavailable. Uses the same engines GitHub Pages pins: Liquid 4.0.4,
# kramdown 2 (GFM) and Ruby Sass 3.7.4.
#
# Usage: ruby minijekyll.rb SRC OUT [--preview]
#   --preview  rewrite relative_url links to page-relative paths (for static hosting)
require 'yaml'
require 'date'
require 'fileutils'
require 'liquid'
require 'kramdown'
require 'kramdown-parser-gfm'
require 'sass'

SRC, OUT = ARGV[0], ARGV[1]
PREVIEW = ARGV.include?('--preview')
Dir.chdir(SRC)

def front_matter(path)
  text = File.read(path, encoding: 'utf-8')
  if text =~ /\A---\s*\n(.*?)\n?---\s*\n/m
    [YAML.safe_load(Regexp.last_match(1), [Date, Time]) || {}, Regexp.last_match.post_match]
  end
end

def deep_strings(o)
  case o
  when Hash then o.each_with_object({}) { |(k, v), h| h[k.to_s] = deep_strings(v) }
  when Array then o.map { |v| deep_strings(v) }
  when Date then o.to_time
  else o
  end
end

config = deep_strings(YAML.load_file('_config.yml'))
exclude = (config['exclude'] || []) + %w[_site]
data = {}
Dir['_data/*.yml'].sort.each { |f| data[File.basename(f, '.yml')] = deep_strings(YAML.load_file(f)) }

# ---- Liquid extensions ------------------------------------------------------
module SiteFilters
  def relative_url(input)
    path = input.to_s
    return (@context.registers[:baseurl].to_s + path) unless PREVIEW
    page_url = @context.registers[:page_url] || '/'
    depth = page_url.end_with?('/') ? page_url.count('/') - 1 : page_url.count('/') - 1
    rel = path.sub(%r{\A/}, '')
    rel += 'index.html' if rel.empty? || rel.end_with?('/')
    ('../' * depth) + rel
  end

  def absolute_url(input)
    @context.registers[:site_url].to_s + input.to_s
  end

  def date_to_xmlschema(input)
    input.respond_to?(:xmlschema) ? input.xmlschema : input.to_s
  end

  def where(input, property, value)
    Array(input).select { |o| o.is_a?(Hash) && Array(o[property.to_s]).map(&:to_s).include?(value.to_s) }
  end
end
Liquid::Template.register_filter(SiteFilters)

class JekyllInclude < Liquid::Tag
  PARAM = /(\w+)=("[^"]*"|'[^']*'|[\w.\-\[\]]+)/
  @@cache = {}
  def initialize(tag, markup, tokens)
    super
    @file, @params = markup.strip.split(/\s+/, 2)
  end

  def render(context)
    params = {}
    (@params || '').scan(PARAM) do |k, v|
      params[k] = v =~ /\A["']/ ? v[1..-2] : context[v]
    end
    tpl = (@@cache[@file] ||= Liquid::Template.parse(File.read(File.join('_includes', @file), encoding: 'utf-8')))
    context.stack do
      context['include'] = params
      tpl.render(context)
    end
  end
end
Liquid::Template.register_tag('include', JekyllInclude)

class SeoTag < Liquid::Tag
  def render(context)
    site, page = context['site'], context['page']
    title = page['title'] && page['url'] != '/' ? "#{page['title']} | #{site['title']}" : "#{site['title']} | #{site['tagline']}"
    desc = (page['description'] || site['description']).to_s.strip
    "<title>#{title}</title>\n<meta name=\"description\" content=\"#{desc.gsub('"', '&quot;')}\">\n" \
      "<meta property=\"og:title\" content=\"#{title}\">\n<meta property=\"og:image\" content=\"#{site['url']}/assets/img/og-image.png\">"
  end
end
Liquid::Template.register_tag('seo', SeoTag)

class FeedMeta < Liquid::Tag
  def render(_context)
    '<link type="application/atom+xml" rel="alternate" href="/feed.xml">'
  end
end
Liquid::Template.register_tag('feed_meta', FeedMeta)

# ---- Collect pages, posts, layouts ------------------------------------------
layouts = {}
Dir['_layouts/*.html'].each do |f|
  fm, body = front_matter(f) || [{}, File.read(f, encoding: 'utf-8')]
  layouts[File.basename(f, '.html')] = [deep_strings(fm), body]
end

def url_for(rel, fm)
  return fm['permalink'] if fm['permalink']
  return '/' if rel == 'index.html'
  return '/' + rel.sub(/index\.html\z/, '') if rel.end_with?('index.html')
  '/' + rel.sub(/\.scss\z/, '.css').sub(/\.md\z/, '.html')
end

posts = Dir['_posts/*.md'].sort.reverse.map do |f|
  fm, body = front_matter(f)
  fm = deep_strings(fm)
  y, m, d, slug = File.basename(f, '.md').match(/(\d{4})-(\d\d)-(\d\d)-(.*)/).captures
  fm['date'] ||= Time.new(y.to_i, m.to_i, d.to_i)
  fm['slug'] = slug
  fm['url'] = config['permalink'].sub(':year', y).sub(':month', m).sub(':slug', slug)
  fm['layout'] ||= 'post'
  html = Kramdown::Document.new(body, input: 'GFM', hard_wrap: false).to_html
  fm['content'] = html
  fm['excerpt'] = Kramdown::Document.new(body.split(/\n\n/).first.to_s, input: 'GFM').to_html
  fm
end

pages = []
statics = []
Dir.glob('**/*', File::FNM_DOTMATCH).sort.each do |rel|
  next if File.directory?(rel)
  next if rel.split('/').any? { |part| part.start_with?('_', '.') }
  next if exclude.any? { |e| rel == e || rel.start_with?(e + '/') }
  fm, body = front_matter(rel) if rel =~ /\.(html|md|scss|xml)\z/
  if fm
    fm = deep_strings(fm)
    fm['url'] = url_for(rel, fm)
    pages << [rel, fm, body]
  else
    statics << rel
  end
end

site = config.merge('data' => data, 'posts' => posts, 'time' => Time.now,
                    'pages' => pages.map { |_, fm, _| fm })

def render_liquid(src, assigns, url, config)
  tpl = Liquid::Template.parse(src, error_mode: :warn)
  out = tpl.render(assigns, registers: { page_url: url, baseurl: config['baseurl'], site_url: config['url'] })
  tpl.errors.each { |e| warn "Liquid error at #{url}: #{e}" }
  out
end

def apply_layouts(html, fm, layouts, site, config)
  name = fm['layout']
  while name && layouts[name]
    lfm, lbody = layouts[name]
    html = render_liquid(lbody, { 'site' => site, 'page' => fm, 'content' => html, 'layout' => lfm }, fm['url'], config)
    name = lfm['layout']
  end
  html
end

def write_out(url, html)
  path = File.join(OUT, url.end_with?('/') ? url + 'index.html' : url)
  FileUtils.mkdir_p(File.dirname(path))
  File.write(path, html)
end

FileUtils.rm_rf(OUT)
pages.each do |rel, fm, body|
  if rel.end_with?('.scss')
    css = Sass::Engine.new(body, syntax: :scss, style: :compressed, load_paths: ['_sass'], cache: false).render
    write_out(fm['url'], css)
    next
  end
  fm['layout'] ||= 'page' if rel.end_with?('.html', '.md')
  content = render_liquid(body, { 'site' => site, 'page' => fm }, fm['url'], config)
  content = Kramdown::Document.new(content, input: 'GFM').to_html if rel.end_with?('.md')
  write_out(fm['url'], apply_layouts(content, fm, layouts, site, config))
end
posts.each do |fm|
  content = render_liquid(fm['content'], { 'site' => site, 'page' => fm }, fm['url'], config)
  write_out(fm['url'], apply_layouts(content, fm, layouts, site, config))
end
statics.each do |rel|
  FileUtils.mkdir_p(File.join(OUT, File.dirname(rel)))
  FileUtils.cp(rel, File.join(OUT, rel))
end
puts "built #{pages.size} pages, #{posts.size} posts, #{statics.size} static files -> #{OUT}"
