require 'rake'

desc 'JSONパーサーを実行'
task :start do
  ruby 'lib/json_parser.rb'
end

desc 'テストを実行'
task :test do
  sh 'bundle exec rspec'
end

# デフォルトタスクの設定
task default: :test
