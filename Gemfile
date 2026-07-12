source "https://rubygems.org"

# Use the github-pages gem so local builds match GitHub Pages exactly.
# (This pins Jekyll and all whitelisted plugins to GitHub's versions.)
gem "github-pages", group: :jekyll_plugins

# Required for `jekyll serve` on Ruby 3.0+ (webrick left the standard library).
gem "webrick", "~> 1.8"

# Faster file watching on macOS/Linux during local development.
group :jekyll_plugins do
  gem "jekyll-feed"
  gem "jekyll-seo-tag"
  gem "jekyll-sitemap"
end
