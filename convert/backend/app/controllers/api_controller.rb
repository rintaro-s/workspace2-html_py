class ApiController < ApplicationController
  before_action :ensure_dirs

  def handle_request
    # params[:action] is the routed controller action name ("handle_request").
    # The client sends its desired API action as a parameter named "action",
    # which can come from the query string or POST body. Read it explicitly
    # from the request parameters to avoid collision with Rails routing.
    action = request.query_parameters['action'] || request.request_parameters['action'] || params[:action]
    case action
    when 'login' then handle_login
    when 'register' then handle_register
    when 'logout' then handle_logout
    when 'checkSession' then handle_check_session
    when 'addServer' then handle_add_server
    when 'addSubItem' then handle_add_subitem
    when 'addWhiteboard' then handle_add_whiteboard
    when 'saveWhiteboard' then handle_save_whiteboard
    when 'postMessage' then handle_post_message
    when 'createSurvey' then handle_create_survey
    when 'submitSurveyResponse' then handle_submit_survey_response
    when 'createProject' then handle_create_project
    when 'createTask' then handle_create_task
    when 'updateTaskStatus' then handle_update_task_status
    when 'updateProfile' then handle_update_profile
    when 'uploadFile' then handle_upload_file
    when 'createInvite' then handle_create_invite
    when 'acceptInvite' then handle_accept_invite
    when 'updateMemberRole' then handle_update_member_role
  when 'kickMember' then handle_kick_member
    when 'requestPasswordRecovery' then handle_request_password_recovery
    when 'approvePasswordRecovery' then handle_approve_password_recovery
    when 'resetPassword' then handle_reset_password
    when 'getServerMembers' then handle_get_server_members
    when 'saveWhiteboardImage' then handle_save_whiteboard_image
    when 'updateFeatureContent' then handle_update_feature_content
    when 'getFeatureContent' then handle_get_feature_content
    else
      render json: { success: false, error: "Unknown action: #{action}" }
    end
  rescue => e
    Rails.logger.error("API Error: #{e}")
    Rails.logger.error(e.backtrace.join("\n"))
    render json: { success: false, error: e.message }
  end

  private
  def ensure_dirs
    FileUtils.mkdir_p Rails.root.join('files', 'uploads')
    FileUtils.mkdir_p Rails.root.join('files', 'avatars')
    FileUtils.mkdir_p Rails.root.join('files', 'whiteboards')
    FileUtils.mkdir_p Rails.root.join('data')
  end

  def success(data)
    render json: { success: true, data: data }
  end

  def current_state
    return { loggedIn: false } unless current_user
    StateBuilder.new(current_user).build
  end

  # ---- Handlers (段階的にFlaskを移植) ----
  def handle_login
    username = params[:username]
    password = params[:password]
    return render json: { success: false, error: 'ユーザー名を入力してください' } if username.blank?
    return render json: { success: false, error: 'パスワードを入力してください' } if password.blank?

    user = User.find_by(username: username)
    return render json: { success: false, error: 'ユーザー名が見つかりません' } unless user

    if user.password_hash != User.sha256(password)
      return render json: { success: false, error: 'パスワードが間違っています' }
    end

    user.update!(last_login: Time.current)
    session[:user_id] = user.id
    session[:username] = user.username
    success({ loggedIn: true, state: current_state })
  end

  def handle_register
    username = params[:username]
    password = params[:password]
    if username.blank? || password.blank?
      return render json: { success: false, error: 'Username and password required' }
    end
    if username.length < 3
      return render json: { success: false, error: 'Username must be at least 3 characters' }
    end
    if password.length < 6
      return render json: { success: false, error: 'Password must be at least 6 characters' }
    end

    if User.exists?(username: username)
      return render json: { success: false, error: 'Username already exists' }
    end

    User.create!(username: username, password_hash: User.sha256(password))
    success({ message: 'User registered successfully' })
  end

  def handle_logout
    reset_session
    success({ message: 'Logged out successfully' })
  end

  def handle_check_session
    if current_user
      success({ loggedIn: true, state: current_state })
    else
      success({ loggedIn: false })
    end
  end

  def handle_add_server
    require_login!
    name = params[:name]
    icon = params[:icon].presence || '🎯'
    return render json: { success: false, error: 'Server name is required' } if name.blank?

    server = Server.create!(
      id: Server.gen_id,
      name: name,
      icon: icon,
      owner_id: current_user.id,
      invite_code: SecureRandom.urlsafe_base64(8)
    )
    ServerMember.create!(server_id: server.id, user_id: current_user.id, role: 'owner')

    Feature.create_defaults!(server.id)
    success current_state
  end

  def handle_add_subitem
    require_login!
    FeatureContentService.new(current_user).add_subitem!(params[:featureId], params[:name], params[:type] || 'channel')
    success current_state
  end

  def handle_add_whiteboard
    require_login!
    FeatureContentService.new(current_user).add_whiteboard!(params[:featureId], params[:name])
    success current_state
  end

  def handle_save_whiteboard
    require_login!
    FeatureContentService.new(current_user).save_whiteboard!(params[:featureId], params[:boardId], params[:elements])
    success current_state
  end

  def handle_post_message
    require_login!
    FeatureContentService.new(current_user).post_message!(params[:featureId], params[:subItemId], params[:content])
    success current_state
  end

  def handle_create_survey
    require_login!
    FeatureContentService.new(current_user).create_survey!(params[:featureId], params[:title], params[:questions])
    success current_state
  end

  def handle_submit_survey_response
    require_login!
    FeatureContentService.new(current_user).submit_survey_response!(params[:featureId], params[:surveyId], params[:responses])
    success current_state
  end

  def handle_create_project
    require_login!
    FeatureContentService.new(current_user).create_project!(params[:featureId], params[:name], params[:description])
    success current_state
  end

  def handle_create_task
    require_login!
    FeatureContentService.new(current_user).create_task!(params[:featureId], params[:projectId], params[:title], params[:description], params[:priority])
    success current_state
  end

  def handle_update_task_status
    require_login!
    FeatureContentService.new(current_user).update_task_status!(params[:featureId], params[:taskId], params[:status])
    success current_state
  end

  def handle_update_profile
    require_login!
    Updater::Profile.update!(current_user, params)
    success current_state
  end

  def handle_upload_file
    require_login!
    file = params[:file]
    return render json: { success: false, error: 'ファイルが選択されていません' } if file.nil? || file.size == 0
    if file.size > 10 * 1024 * 1024
      return render json: { success: false, error: 'ファイルサイズは10MB以下にしてください' }
    end

    server_id = params[:serverId]
    feature_id = params[:featureId]

    file_id = SecureRandom.uuid
    ext = File.extname(file.original_filename)
    safe = file_id + ext
    out_path = Rails.root.join('files', 'uploads', safe)
    File.open(out_path, 'wb') { |f| f.write(file.read) }

    FileRecord.create!(
      id: file_id,
      filename: safe,
      original_filename: file.original_filename,
      file_path: out_path.to_s,
      file_size: File.size(out_path),
      mime_type: file.content_type || 'application/octet-stream',
      upload_by: current_user.id,
      server_id: server_id,
      feature_id: feature_id
    )

    success({
      fileId: file_id,
      originalFilename: file.original_filename,
      storedFilename: safe,
      fileSize: File.size(out_path),
      url: "/files/uploads/#{safe}"
    })
  end

  def handle_create_invite
    require_login!
  result = InviteService.new(current_user).create!(params[:serverId])
  render json: result
  end

  def handle_accept_invite
    require_login!
    InviteService.new(current_user).accept!(params[:inviteCode])
    success current_state
  end

  def handle_update_member_role
    require_login!
    # 互換: フロントは userId / memberId の両方を使い分けている箇所がある
    target_id = params[:userId].presence || params[:memberId]
    MembershipService.new(current_user).update_role!(params[:serverId], target_id, params[:role])
    success({ message: 'ロールを更新しました' })
  end

  def handle_kick_member
    require_login!
    target_id = params[:userId].presence || params[:memberId]
    MembershipService.new(current_user).kick!(params[:serverId], target_id)
    success({ message: 'メンバーをキックしました' })
  end

  def handle_request_password_recovery
    PasswordRecoveryService.request!(params[:username], params[:partnerUsername])
  end

  def handle_approve_password_recovery
    require_login!
    PasswordRecoveryService.approve!(current_user, params[:recoveryToken])
  end

  def handle_reset_password
    PasswordRecoveryService.reset!(params[:recoveryToken], params[:newPassword])
  end

  def handle_get_server_members
    require_login!
    success ServerMember.members_payload!(params[:serverId], current_user)
  end

  def handle_save_whiteboard_image
    require_login!
    ImageService.new(current_user).save_whiteboard!(params[:featureId], params[:boardId], params[:imageData])
  end

  def handle_update_feature_content
    require_login!
    FeatureContentService.new(current_user).update_feature_content!(params[:featureId], params[:content])
    success current_state
  end

  def handle_get_feature_content
    require_login!
    content = FeatureContent.find_by(feature_id: params[:featureId])&.content_json || {}
    render json: { success: true, data: content }
  end

  def require_login!
    render(json: { success: false, error: 'Not authenticated' }) && return unless current_user
  end
end
