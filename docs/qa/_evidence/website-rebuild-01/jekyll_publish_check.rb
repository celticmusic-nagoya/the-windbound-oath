# Jekyll publish-set check for WEBSITE-REBUILD-01 (not a full Jekyll build).
#
# Loads the real Jekyll 3.10.0 EntryFilter (the version used by
# actions/jekyll-build-pages via github-pages) and walks the repository the way
# Jekyll::Reader#read_directories does: filter the entries of each directory,
# recurse into the kept directories. Prints which tracked paths would be read
# (= published) under the default configuration (this repository has no
# _config.yml / .nojekyll).
#
# Usage:
#   git clone --depth 1 --branch v3.10.0 https://github.com/jekyll/jekyll /tmp/jekyll-src
#   ruby docs/qa/_evidence/website-rebuild-01/jekyll_publish_check.rb /tmp/jekyll-src .
require "pathname"
Encoding.default_external = Encoding::UTF_8
Encoding.default_internal = Encoding::UTF_8

jekyll_src, repo = ARGV
abort "usage: ruby jekyll_publish_check.rb <jekyll-src> <repo>" unless jekyll_src && repo
REPO = File.expand_path(repo)

# Minimal Pathutil stand-in covering what EntryFilter#glob_include? uses.
class Pathutil
  def initialize(path); @path = path.to_s; end
  def join(other); Pathutil.new(File.join(@path, other.to_s)); end
  def to_path; @path; end
  alias to_s to_path
  alias to_str to_path
  def in_path?(other); (@path + "/").start_with?(other.to_s.chomp("/") + "/"); end
  def =~(re); @path =~ re; end
end
module Jekyll; class << self; def logger; @l ||= Struct.new(:x) { def debug(*); end }.new(nil); end; end; end
require File.join(jekyll_src, "lib/jekyll/entry_filter")

# Defaults from lib/jekyll/configuration.rb (v3.10.0).
Site = Struct.new(:source, :include, :exclude, :safe) do
  def in_source_dir(*paths); File.join(source, *paths.map(&:to_s)); end
end
site = Site.new(REPO, [".htaccess"],
  %w(Gemfile Gemfile.lock node_modules vendor/bundle/ vendor/cache/ vendor/gems/ vendor/ruby/), true)

published = []
walk = lambda do |dir|
  base = site.in_source_dir(dir)
  kept = Dir.chdir(base) { Jekyll::EntryFilter.new(site, base).filter(Dir.entries(".") - %w(. ..)) }
  kept.sort.each do |e|
    rel = dir.empty? ? e : File.join(dir, e)
    File.directory?(site.in_source_dir(rel)) ? walk.call(rel) : published << rel
  end
end
walk.call("")

tracked = Dir.chdir(REPO) { `git ls-files -z`.force_encoding("UTF-8").split("\0") }
pub = published & tracked
puts "tracked=#{tracked.size} published=#{pub.size} not_published=#{tracked.size - pub.size}"
%w(docs/qa/_evidence/website-rebuild-01/ site/ docs/qa/evidence/ docs/).each do |pre|
  t = tracked.count { |f| f.start_with?(pre) }
  p = pub.count { |f| f.start_with?(pre) }
  puts format("%-42s tracked=%5d published=%5d", pre, t, p)
end
puts "game files published (index.html, js/, css/, img/, assets/, data/):"
%w(index.html js/ css/ img/ assets/ data/).each do |pre|
  t = tracked.count { |f| f.start_with?(pre) }
  p = pub.count { |f| f.start_with?(pre) }
  puts format("  %-12s tracked=%5d published=%5d", pre, t, p)
end
bytes = pub.sum { |f| File.size(File.join(REPO, f)) }
puts "published bytes (raw, before Jekyll rendering)=#{bytes}"
File.write(ENV["OUT"], (tracked - pub).sort.join("\n") + "\n") if ENV["OUT"]
