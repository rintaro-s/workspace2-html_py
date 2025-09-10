class Feature < ApplicationRecord
  self.table_name = 'features'
  self.inheritance_column = :_type_disabled

  def self.create_defaults!(server_id)
    defaults = [
      ['チャット','chat','message-circle'],
      ['フォーラム','forum','message-square'],
      ['ホワイトボード','whiteboard','edit-3'],
      ['ファイル共有','storage','folder'],
      ['アンケート','survey','clipboard-list'],
      ['プロジェクト','projects','git-branch'],
      ['Wiki','wiki','book'],
      ['カレンダー','calendar','calendar'],
      ['予算管理','budget','dollar-sign'],
      ['物品管理','inventory','package'],
      ['メンバー','members','users'],
      ['アルバム','album','image'],
      ['日記','diary','edit']
    ]
    defaults.each_with_index do |(name, type, icon), i|
      fid = "#{server_id}_#{type}_#{(Time.now.to_f*1000).to_i}_#{i}"
      Feature.create!(id: fid, server_id: server_id, name: name, type: type, icon: icon, position: i)
      FeatureContent.create!(feature_id: fid, content: FeatureContent.initial_content(type).to_json)
    end
  end
end
