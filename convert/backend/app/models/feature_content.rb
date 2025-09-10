class FeatureContent < ApplicationRecord
  self.table_name = 'feature_content'

  def content_json
    JSON.parse(content || '{}')
  rescue
    {}
  end

  def update_json!(hash)
    update!(content: hash.to_json, updated_at: Time.current)
  end

  def self.initial_content(type)
    case type
    when 'chat'
      { 'subItems' => { 'general' => { 'id' => 'general', 'name' => '一般', 'type' => 'channel', 'messages' => [] } } }
    when 'forum'
      { 'subItems' => { 'announcements' => { 'id' => 'announcements', 'name' => 'お知らせ', 'type' => 'thread', 'posts' => [] } } }
    when 'whiteboard'
      { 'boards' => { 'main' => { 'id' => 'main', 'name' => 'メインボード', 'elements' => {} } } }
    when 'wiki'
      { 'pages' => { 'welcome' => { 'id' => 'welcome', 'title' => 'ようこそ', 'content' => "このWikiページへようこそ！\n\n自由に編集してください。", 'author' => 'システム', 'created_at' => Time.now.to_f, 'updated_at' => Time.now.to_f, 'tags' => ['歓迎'] } } }
    when 'calendar'
      { 'events' => {} }
    when 'budget'
      { 'accounts' => {}, 'transactions' => {} }
    when 'inventory'
      { 'items' => {}, 'categories' => ['機材','備品','書籍','電子機器'], 'locations' => ['メインオフィス','倉庫','研究室'] }
    when 'members'
      { 'members' => {}, 'roles' => { 'admin' => { 'name' => '管理者', 'permissions' => ['all'] }, 'moderator' => { 'name' => 'モデレーター', 'permissions' => ['moderate'] }, 'member' => { 'name' => 'メンバー', 'permissions' => ['basic'] } } }
    when 'album'
      { 'albums' => {} }
    when 'diary'
      { 'entries' => {} }
    when 'survey'
      { 'surveys' => {}, 'responses' => {} }
    when 'projects'
      { 'projects' => {}, 'tasks' => {} }
    else
      {}
    end
  end
end
