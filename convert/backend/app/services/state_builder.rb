class StateBuilder
  def initialize(user)
    @user = user
  end

  def build
    servers = {}
    # 参加サーバ一覧
    # Use ActiveRecord to avoid raw bind parameter casting issues
    srv_rows = Server.joins("JOIN server_members sm ON sm.server_id = servers.id").where("sm.user_id = ?", @user.id).order('sm.joined_at')
    srv_rows.each do |server|
      member = ServerMember.find_by(server_id: server.id, user_id: @user.id)
      servers[server.id] = {
        id: server.id, name: server.name, description: server.description,
        icon: server.icon, banner: server.banner, owner_id: server.owner_id,
        is_public: server.is_public, invite_code: server.invite_code,
        userRole: member&.role, joinedAt: member&.joined_at
      }
    end

    # 機能
    features = {}
    servers.keys.each do |sid|
      features[sid] = Feature.where(server_id: sid).order(:position, :created_at).map do |f|
        { id: f.id, name: f.name, type: f.type, icon: f.icon, server_id: f.server_id }
      end
    end

    # コンテンツ
    content = {}
    FeatureContent.all.find_each do |fc|
      content[fc.feature_id] = fc.content_json
    end

    # ファイル
    files = []
    unless servers.empty?
      ids = servers.keys
      file_rows = FileRecord.joins('LEFT JOIN users u ON u.id = files.upload_by').where(server_id: ids).select('files.*, u.username as uploader_name').order(created_at: :desc)
      file_rows.each do |r|
        files << {
          id: r.id, filename: r.original_filename, serverId: r.server_id, featureId: r.feature_id,
          size: r.file_size, uploadedBy: r.try(:uploader_name), uploadedAt: r.created_at, mimeType: r.mime_type, downloadCount: r.download_count
        }
      end
    end

    {
      servers: servers,
      features: features,
      content: content,
      files: files,
      currentUser: { id: @user.id, username: @user.username, nickname: @user.nickname.presence || @user.username, admission_year: @user.admission_year, avatar: @user.avatar, ui_scale: @user.ui_scale, theme: @user.theme },
      loggedIn: true
    }
  end
end
